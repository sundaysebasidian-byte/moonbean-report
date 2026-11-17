# moonbean-report

A standalone native `bean-report <ledger.beancount> [--year YYYY]` example by the
MoonBean authors. Author: **moonbean-report contributors**. This is a demonstration,
with synthetic data, not a claim of independent adoption.

The module `sundaysebasidian-byte/moonbean-report` depends on the published
[`sundaysebasidian-byte/moonbean@0.2.8`](https://mooncakes.io/docs/sundaysebasidian-byte/moonbean)
through the registry. There are no local-path dependencies and no remote for this
example. See [MoonBean's compatibility contract](https://github.com/sundaysebasidian-byte/moonbean/blob/v0.2.8/docs/compatibility.md)
before using this as a `bean-check` replacement: the engine has explicit compatibility
gaps, including Python plugins and some options. Warnings are displayed but do not
fail validation. Unsupported plugins may affect results; this is not full Beancount parity.

## Reproduce

Use MoonBit **0.1.20261104** (native C compiler required), already installed at the
following location. These commands do not install a toolchain or publish anything.
Run from this module directory:

```sh
export MOON_HOME=/tmp/moon-new
export PATH="$MOON_HOME/bin:$PATH"
moon version
moon add sundaysebasidian-byte/moonbean@0.2.8
moon fmt
moon check --target native
moon test --target native
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
uses all dates, at cost, without currency conversion; Equity includes all retained
earnings. Assets + Liabilities + Equity equals zero per currency for this sample.
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

The monthly report runs this BQL with the requested year:

```sql
SELECT month(date), root(account), currency, sum(number)
WHERE year(date) = 2024 AND account ~ '^(Income|Expenses):'
GROUP BY month(date), root(account), currency
ORDER BY month(date), root(account), currency
```

`golden/sample-2024.txt` and `golden/error.txt` are the expected CLI outputs.
MoonBit whitebox tests use embedded copies of these files and the two ledgers, so
`moon test` needs no filesystem or oracle. After an intentional fixture change,
regenerate copies using `sh scripts/embed-fixtures.sh`, review the golden diff,
and run tests. Verify embedded copies and CLI behavior with:

```sh
sh scripts/check-fixtures.sh
python3 scripts/cli-smoke.py
moon check --target all
moon test --target all
moon fmt --check
```

The pure package supports the dependency's other backends; the CLI is native only.
[examples/ci-validation.yml](examples/ci-validation.yml) is an **inactive** GitHub
Actions example, requiring the pinned toolchain on the runner. Copy it into a
workflow only when wanted; replace the sample path with the repository's ledger.

## Optional Python oracle

No oracle installation, download or dependency is required. If the external
`bean-check` / `bean-query` executables already exist:

```sh
python3 scripts/oracle-cross-check.py
# Or select an existing installation:
python3 scripts/oracle-cross-check.py --oracle-dir /tmp/moonbean-r4-oracle/bin --year 2025
```

The script invokes their CLIs as black boxes, compares exact Decimal values against
the actual report output, and exits nonzero on mismatches. It checks cost-basis
Assets/Liabilities and Equity plus Income/Expenses (retained earnings), and all
monthly cells including zero months. Missing tools produce an explicit SKIP.
The comparison is limited to this authored sample, not arbitrary ledgers.

## Packaging without publishing

```sh
moon package --list
moon package
moon publish --dry-run
```

On toolchain 0.1.20261104 the final command requires a registry login even for a
dry run; without credentials it stops at `Registry login is required`. `moon package`
validates offline archive creation, but does not verify registry publication
permissions. No login, publish, push or remote creation is needed or performed.
See [evidence/verification.md](evidence/verification.md) for actual verification.
