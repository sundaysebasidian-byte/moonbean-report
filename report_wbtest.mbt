///|
test "sample report matches bundled golden" {
  let result = render_source(
    "sample/ledger.beancount",
    sample_source,
    year=Some(2024),
  )
  assert_eq(result.exit_code, 0)
  assert_eq(result.text, sample_expected)
}

///|
test "invalid ledger returns failure and original line" {
  let result = render_source(
    "sample/error.beancount",
    error_source,
    year=Some(2024),
  )
  assert_eq(result.exit_code, 1)
  assert_eq(result.text, error_expected)
  assert_true(result.text.contains("sample/error.beancount:3:"))
  assert_false(result.text.contains("Balance sheet"))
}

///|
test "year restricts BQL but leaves balance sheet unchanged" {
  let result = render_source(
    "sample/ledger.beancount",
    sample_source,
    year=Some(2025),
  )
  assert_eq(result.exit_code, 0)
  assert_true(result.text.contains("2025-01 USD 50.00 0"))
  assert_false(result.text.contains("2024-01 USD"))
  assert_true(result.text.contains("USD 4849.50 -80.25 -4769.25"))
}

///|
test "default year is latest transaction year" {
  assert_eq(
    render_source("sample/ledger.beancount", sample_source).text,
    render_source("sample/ledger.beancount", sample_source, year=Some(2025)).text,
  )
}

///|
test "empty ledger and invalid year" {
  assert_eq(render_source("empty.beancount", "").exit_code, 0)
  assert_eq(render_source("empty.beancount", "", year=Some(0)).exit_code, 2)
  assert_eq(render_source("empty.beancount", "", year=Some(10000)).exit_code, 2)
}

///|
test "priced conversion includes equity residual and matches golden" {
  let result = render_source(
    "sample/conversion.beancount",
    conversion_source,
    year=Some(2024),
  )
  assert_eq(result.exit_code, 0)
  assert_eq(result.text, conversion_expected)
  assert_true(result.text.contains("USD 620.00 0 -620.00"))
  assert_true(result.text.contains("EUR 895.00 0 -895.00"))
}
