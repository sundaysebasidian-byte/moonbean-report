#!/usr/bin/env python3
"""Optional black-box sample check; no Python accounting modules are imported."""
import argparse
import csv
from decimal import Decimal
import io
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BALANCE_QUERY = (
    "SELECT root(account), currency(cost(position)), sum(number(cost(position))) "
    "GROUP BY root(account), currency(cost(position)) "
    "ORDER BY root(account), currency(cost(position))"
)


def run(command):
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"{Path(command[0]).name} failed ({result.returncode}): {result.stderr.strip()}")
    return result.stdout


def query(binary, bql):
    rows = list(csv.reader(io.StringIO(run([str(binary), "-f", "csv", "sample/ledger.beancount", bql]))))
    if not rows:
        raise RuntimeError("bean-query produced no CSV header")
    return rows[1:]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--oracle-dir", type=Path, default=Path("/tmp/moonbean-r4-oracle/bin"))
    parser.add_argument("--year", type=int, default=2024)
    args = parser.parse_args()
    if not 1 <= args.year <= 9999:
        parser.error("year must be between 1 and 9999")
    check = args.oracle_dir / "bean-check"
    oracle = args.oracle_dir / "bean-query"
    if not check.is_file() or not oracle.is_file():
        print("SKIP: optional bean-check / bean-query oracle unavailable")
        return 0
    run([str(check), "sample/ledger.beancount"])
    output = run(["moon", "run", "--quiet", "cmd/bean-report", "--target", "native", "--", "sample/ledger.beancount", "--year", f"{args.year:04}"])
    actual_balances = {}
    actual_months = {}
    section = None
    for line in output.splitlines():
        if line == "Currency Assets Liabilities Equity":
            section = "balance"
        elif line == "Month Currency Income Expenses":
            section = "monthly"
        elif not line:
            section = None
        elif section == "balance":
            currency, assets, liabilities, equity = line.split()
            actual_balances[currency] = tuple(map(Decimal, (assets, liabilities, equity)))
        elif section == "monthly":
            month, currency, income, expenses = line.split()
            actual_months[(int(month.split("-")[1]), currency)] = (Decimal(income), Decimal(expenses))

    totals = {}
    for root, currency, amount in query(oracle, BALANCE_QUERY):
        totals[(root, currency)] = Decimal(amount.strip())
    currencies = {currency for _, currency in totals}
    zero = Decimal(0)
    expected_balances = {
        currency: (
            totals.get(("Assets", currency), zero),
            totals.get(("Liabilities", currency), zero),
            sum((totals.get((root, currency), zero) for root in ("Equity", "Income", "Expenses")), zero),
        ) for currency in currencies
    }
    bql = (
        "SELECT month(date), root(account), currency, sum(number) "
        f"WHERE year(date) = {args.year} AND account ~ '^(Income|Expenses):' "
        "GROUP BY month(date), root(account), currency "
        "ORDER BY month(date), root(account), currency"
    )
    activity = {}
    monthly_currencies = set()
    for month, root, currency, amount in query(oracle, bql):
        activity[(int(month), root, currency)] = Decimal(amount.strip())
        monthly_currencies.add(currency)
    expected_months = {
        (month, currency): (
            -activity.get((month, "Income", currency), zero),
            activity.get((month, "Expenses", currency), zero),
        ) for month in range(1, 13) for currency in monthly_currencies
    }
    if actual_balances != expected_balances or actual_months != expected_months:
        print("FAIL: report differs from bean-query")
        print("balance actual:", actual_balances)
        print("balance oracle:", expected_balances)
        print("monthly actual:", actual_months)
        print("monthly oracle:", expected_months)
        return 1
    print(f"PASS: bean-check; {len(expected_balances)} balance currencies; {len(expected_months)} monthly rows ({args.year}) agree with bean-query")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
