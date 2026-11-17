# moonbean-report

A standalone native `bean-report <ledger.beancount> [--year YYYY]` example by the
MoonBean authors. Author: **moonbean-report contributors**. This is a demonstration,
with synthetic data, not a claim of independent adoption.

The module `sundaysebasidian-byte/moonbean-report` depends on the published
[`sundaysebasidian-byte/moonbean@0.2.8`](https://mooncakes.io/docs/sundaysebasidian-byte/moonbean)
through the registry. There are no local-path dependencies. See [MoonBean's compatibility contract](https://github.com/sundaysebasidian-byte/moonbean/blob/v0.2.8/docs/compatibility.md)
before using this as a `bean-check` replacement: the engine has explicit compatibility
gaps, including Python plugins and some options. Warnings are displayed but do not
fail validation. Unsupported plugins may affect results; this is not full Beancount parity.

## Reproduce

Use **moon >= 0.1.20261104** on PATH (native C compiler required). These commands
do not install a toolchain or publish anything. Run from this module directory:

```sh
moon version
moon add sundaysebasidian-byte/moonbean@0.2.8
moon fmt
moon check --deny-warn --target native
moon test --deny-warn --target native
moon build cmd/bean-report --target native --release
moon run cmd/bean-report --target native -- sample/ledger.beancount --year 2024
```

`moon build` prints the executable path. On this toolchain its release output can
also be copied to a convenient command name:

```sh
cp _build/native/release/build/cmd/bean-report/bean-report.exe ./bean-report
./bean-report sample/ledger.beancount --year 2024
./bean-report sample/error.beancount --year 2024  # expected exit 1
```

Exit codes: **0** valid ledger and successful report; **1** input, validation,
booking, include, document or query error; **2** command usage / invalid year.
Diagnostics include original file and line numbers. Reports are omitted on ledger
errors. The native host expands relative includes and checks document existence;
the pure `render_source` API handles one source only, with library warnings.

`--year` selects the monthly table only. Omitted year means the latest transaction
year (1970 for no transactions), making runs deterministic. The balance sheet always
uses all dates at cost and keeps currencies separate. Equity includes retained
earnings **and the conversion residual** from priced postings (such as `@ 1.10 USD`).
Assets + Liabilities + Equity equals zero per currency for both valid samples.
All balances retain accounting signs; the monthly table reverses Income's sign and
keeps Expenses' sign, so refunds remain visible. It prints all 12 months for each
currency appearing in that year's income/expenses; a year without activity has
headers only. Decimal text retains source precision, with `0` for absent amounts.

## Library use and tests

`report.mbt` calls `check_source` (parser, interpolation, booking and validation),
`realize`, `balance_sheet`, and `run_query`. The CLI adds filesystem handling via
`IncludeExpander` and delegates reporting to the pure library. It never executes
MoonBean's CLI or Python at runtime. The sample includes inferred postings,
FIFO stock purchase/sale, a card liability, EUR/USD and adjacent-year transactions.
`sample/conversion.beancount` isolates a priced EUR-to-USD exchange and its Equity
residual; USD Equity is -620.00, including -110.00 from the conversion.

The monthly report runs this BQL with the requested year:

```sql
SELECT month(date), root(account), currency, sum(number)
WHERE year(date) = 2024 AND account ~ '^(Income|Expenses):'
GROUP BY month(date), root(account), currency
ORDER BY month(date), root(account), currency
```

`golden/sample-2024.txt`, `golden/conversion-2024.txt` and `golden/error.txt` are the
expected CLI outputs. MoonBit whitebox tests embed the goldens and all three ledgers, so
`moon test` needs no filesystem or oracle. After an intentional fixture change,
regenerate copies using `sh scripts/embed-fixtures.sh`, review the golden diff,
and run tests. Verify embedded copies and CLI behavior with:

```sh
sh scripts/check-fixtures.sh
python3 scripts/cli-smoke.py
python3 -m unittest discover -s tests -p 'test_*.py'
moon check --deny-warn --target all
moon test --deny-warn --target all
moon fmt --check
```

The pure package supports the dependency's other backends; the CLI is native only.
[examples/ci-validation.yml](examples/ci-validation.yml) is an **inactive** GitHub
Actions example, requiring MoonBit and a native C compiler on the runner. Copy it into a
workflow only when wanted; replace the sample path with the repository's ledger.

## Optional Python oracle

No oracle installation, download or dependency is required. Tool discovery uses
`--oracle-dir` first, then `BEAN_ORACLE_DIR`, then independent PATH lookups for
`bean-check` and `bean-query`:

```sh
python3 scripts/oracle-cross-check.py
BEAN_ORACLE_DIR=/path/to/oracle/bin python3 scripts/oracle-cross-check.py --year 2025
python3 scripts/oracle-cross-check.py --oracle-dir /path/to/oracle/bin --ledger sample/conversion.beancount
```

By default both valid bundled ledgers are checked; repeat `--ledger FILE` to select
other inputs. The script invokes the oracle CLIs as black boxes and compares exact
Decimal values against the actual report output. Its balance query uses
`FROM CLOSE CLEAR` to include retained earnings and conversion residuals in Equity,
and its monthly query checks all cells including zero months. Absent PATH tools
produce an explicit SKIP with exit 0. Invalid configured directories,
non-executable installations and tool execution failures are errors with nonzero
exit; they are never treated as a SKIP. The authored fixtures are regression
coverage, not a guarantee for arbitrary ledgers.

## Packaging without publishing

```sh
moon package --list
moon package
moon publish --dry-run
```

On toolchain 0.1.20261104 the final command requires a registry login even for a
dry run; without credentials it stops at `Registry login is required`. `moon package`
validates offline archive creation, but does not verify registry publication
permissions. Internal audit and closeout records are retained in Git but excluded from the
registry archive by `.moonignore`; `moon package --list` shows the payload.
