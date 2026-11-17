///|
pub(all) struct ReportResult {
  text : String
  exit_code : Int32
}

///|
pub fn render_source(
  file : String,
  source : String,
  year~ : Int32? = None,
) -> ReportResult {
  render_ledger(@moonbean.check_source(file, source), year~)
}

///|
fn two_digits(n : Int32) -> String {
  if n < 10 {
    "0" + n.to_string()
  } else {
    n.to_string()
  }
}

///|
pub fn monthly_query(year : Int32) -> String {
  "SELECT month(date), root(account), currency, sum(number) " +
  "WHERE year(date) = " +
  year.to_string() +
  " AND account ~ '^(Income|Expenses):' " +
  "GROUP BY month(date), root(account), currency " +
  "ORDER BY month(date), root(account), currency"
}

///|
pub fn render_ledger(
  ledger : @validation.ValidatedLedger,
  year~ : Int32? = None,
) -> ReportResult {
  let lines : Array[String] = []
  let status = if ledger.has_errors() { "FAILED" } else { "OK" }
  lines.push(
    "Validation: " +
    status +
    " (" +
    ledger.error_count().to_string() +
    " errors, " +
    ledger.warning_count().to_string() +
    " warnings)",
  )
  for d in ledger.errors {
    lines.push(@moonbean.diagnostic_text(d))
  }
  for d in ledger.warnings {
    lines.push("warning: " + @moonbean.diagnostic_text(d))
  }
  if ledger.has_errors() {
    return { text: lines.join("\n") + "\n", exit_code: 1, }
  }
  let mut latest = 1970
  let mut has_transaction = false
  for entry in ledger.entries {
    if entry.directive is @ast.DTransaction(_) {
      if !has_transaction || entry.date.year > latest {
        latest = entry.date.year
      }
      has_transaction = true
    }
  }
  let year = year.unwrap_or(latest)
  if year < 1 || year > 9999 {
    lines.push("bean-report: year must be between 0001 and 9999")
    return { text: lines.join("\n") + "\n", exit_code: 2, }
  }
  // Library realization uses booked positions; equity includes retained earnings.
  let sheet = @realization.balance_sheet(@moonbean.realize(ledger))
  let currencies : Array[String] = []
  let balances : Map[String, @decimal.Decimal] = Map([])
  for row in sheet.rows {
    let root = @ast.account_root(row.label)
    let currency = row.amount.currency
    if !currencies.contains(currency) {
      currencies.push(currency)
    }
    let key = root + "/" + currency
    balances[key] = balances
      .get(key)
      .unwrap_or(@decimal.Decimal::zero())
      .add(row.amount.number)
  }
  currencies.sort()
  lines.push("")
  lines.push("Balance sheet (all dates; cost basis; signed balances)")
  lines.push("Currency Assets Liabilities Equity")
  for currency in currencies {
    let amounts : Array[String] = [currency]
    for root in ["Assets", "Liabilities", "Equity"] {
      amounts.push(
        balances
        .get(root + "/" + currency)
        .unwrap_or(@decimal.Decimal::zero())
        .to_string(),
      )
    }
    lines.push(amounts.join(" "))
  }
  let result = @moonbean.run_query(ledger, monthly_query(year))
  if result.error is Some(error) {
    lines.push("bean-report: BQL failed: " + error)
    return { text: lines.join("\n") + "\n", exit_code: 1, }
  }
  let monthly_currencies : Array[String] = []
  let monthly : Map[String, @decimal.Decimal] = Map([])
  for row in result.rows {
    match row {
      [
        @query.QInt(month),
        @query.QText(root),
        @query.QText(currency),
        @query.QNumber(amount),
      ] => {
        if !monthly_currencies.contains(currency) {
          monthly_currencies.push(currency)
        }
        monthly[month.to_string() + "/" + root + "/" + currency] = amount
      }
      _ => {
        lines.push("bean-report: unexpected BQL result shape")
        return { text: lines.join("\n") + "\n", exit_code: 1, }
      }
    }
  }
  monthly_currencies.sort()
  lines.push("")
  lines.push(
    "Monthly income/expenses " + year.to_string() + " (income sign reversed)",
  )
  lines.push("Month Currency Income Expenses")
  for month in 1..<13 {
    for currency in monthly_currencies {
      let prefix = month.to_string() + "/"
      let income = monthly
        .get(prefix + "Income/" + currency)
        .unwrap_or(@decimal.Decimal::zero())
        .neg()
      let expenses = monthly
        .get(prefix + "Expenses/" + currency)
        .unwrap_or(@decimal.Decimal::zero())
      lines.push(
        year.to_string() +
        "-" +
        two_digits(month) +
        " " +
        currency +
        " " +
        income.to_string() +
        " " +
        expenses.to_string(),
      )
    }
  }
  { text: lines.join("\n") + "\n", exit_code: 0, }
}
