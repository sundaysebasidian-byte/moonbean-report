#!/usr/bin/env python3
"""Optional black-box sample check; no Python accounting modules are imported."""
import argparse
import csv
from decimal import Decimal
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGERS = ("sample/ledger.beancount", "sample/conversion.beancount")
BALANCE_QUERY = (
    "SELECT root(account), currency(cost(position)), sum(number(cost(position))) "
    "FROM CLOSE CLEAR GROUP BY root(account), currency(cost(position)) "
    "ORDER BY root(account), currency(cost(position))"
)


def run(command):
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"{Path(command[0]).name} failed ({result.returncode}): {result.stderr.strip()}")
    return result.stdout


def find_tools(oracle_dir):
    configured = oracle_dir if oracle_dir is not None else os.environ.get("BEAN_ORACLE_DIR") or None
    names = ("bean-check", "bean-query")
    if configured is not None:
        directory = Path(configured).resolve()
        tools = tuple(directory / name for name in names)
        for tool in tools:
            if not tool.is_file() or not os.access(tool, os.X_OK):
                raise RuntimeError(f"configured oracle tool is missing or not executable: {tool}")
        return tools

    found = tuple(shutil.which(name) for name in names)
    # which() also returns None for broken/non-executable installations. Those
    # are configuration errors, rather than an optional dependency being absent.
    for name, tool in zip(names, found):
        if tool is None:
            for directory in os.get_exec_path():
                try:
                    (Path(directory) / name).lstat()
                except (FileNotFoundError, NotADirectoryError):
                    continue
                raise RuntimeError(f"oracle tool on PATH is not executable: {name}")
    missing = [name for name, tool in zip(names, found) if tool is None]
    if missing:
        print("SKIP: optional oracle tools absent from PATH: " + ", ".join(missing))
        return None
    return tuple(Path(tool).resolve() for tool in found)


def query(binary, ledger, bql):
    rows = list(csv.reader(io.StringIO(run([str(binary), "-f", "csv", ledger, bql]))))
    if not rows:
        raise RuntimeError("bean-query produced no CSV header")
    return rows[1:]


def cross_check(check, oracle, ledger, year):
    run([str(check), ledger])
    output = run(["moon", "run", "--quiet", "cmd/bean-report", "--target", "native", "--", ledger, "--year", f"{year:04}"])
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
    for root, currency, amount in query(oracle, ledger, BALANCE_QUERY):
        totals[(root, currency)] = Decimal(amount.strip())
    currencies = {currency for _, currency in totals}
    zero = Decimal(0)
    expected_balances = {
        currency: (
            totals.get(("Assets", currency), zero),
            totals.get(("Liabilities", currency), zero),
            totals.get(("Equity", currency), zero),
        ) for currency in currencies
    }
    bql = (
        "SELECT month(date), root(account), currency, sum(number) "
        f"WHERE year(date) = {year} AND account ~ '^(Income|Expenses):' "
        "GROUP BY month(date), root(account), currency "
        "ORDER BY month(date), root(account), currency"
    )
    activity = {}
    monthly_currencies = set()
    for month, root, currency, amount in query(oracle, ledger, bql):
        activity[(int(month), root, currency)] = Decimal(amount.strip())
        monthly_currencies.add(currency)
    expected_months = {
        (month, currency): (
            -activity.get((month, "Income", currency), zero),
            activity.get((month, "Expenses", currency), zero),
        ) for month in range(1, 13) for currency in monthly_currencies
    }
    if actual_balances != expected_balances or actual_months != expected_months:
        print(f"FAIL: {ledger}: report differs from bean-query")
        print("balance actual:", actual_balances)
        print("balance oracle:", expected_balances)
        print("monthly actual:", actual_months)
        print("monthly oracle:", expected_months)
        return 1
    print(f"PASS: {ledger}: bean-check; {len(expected_balances)} balance currencies; {len(expected_months)} monthly rows ({year}) agree with bean-query")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--oracle-dir", type=Path, help="oracle directory (overrides BEAN_ORACLE_DIR and PATH)")
    parser.add_argument("--year", type=int, default=2024)
    parser.add_argument("--ledger", action="append", help="ledger to check; repeatable (default: both bundled valid samples)")
    args = parser.parse_args(argv)
    if not 1 <= args.year <= 9999:
        parser.error("year must be between 1 and 9999")
    tools = find_tools(args.oracle_dir)
    if tools is None:
        return 0
    check, oracle = tools
    status = 0
    for ledger in args.ledger or DEFAULT_LEDGERS:
        status |= cross_check(check, oracle, ledger, args.year)
    return status


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
