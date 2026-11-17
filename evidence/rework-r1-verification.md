# Rework round 1 verification

Author: moonbean-report contributors. Base commit: `7445a44872549cf04d0670f1fdf16f1fc1bb74ac`.
Toolchain actually tested: moon 0.1.20261104 (940aa18), native macOS arm64.

- B1 reproduced before the fix on `sample/conversion.beancount`: the old raw-position
  oracle query returned USD Equity -510.00 while the report returned -620.00.
  The original script was loaded in memory and its ledger argument redirected to
  the new fixture; no existing fixture or dependency was overwritten.
  `rework-r1-before.txt` records the mismatch. Oracle `FROM CLOSE CLEAR` agrees
  with the report (-620.00 USD, -895.00 EUR). The new default cross-check includes
  both valid samples. A conversion golden was added to MoonBit and CLI tests.
- B2 lookup order is explicit argument, BEAN_ORACLE_DIR, then PATH for each tool.
  Missing PATH tools explicitly SKIP; invalid configuration, non-executable tools,
  inaccessible paths and tool execution failures remain errors.
- B3 uses the supported `.moonignore` file. The manifest's old exclude option was
  probed, reported as deprecated by the toolchain, and removed. Internal evidence,
  audit, closeout-audit and evidence-bundle directories stay outside the archive.
- README and inactive CI snippet now use MoonBit on PATH, without fixed install
  paths. README states that Equity includes the priced-conversion residual.

| Command | Result |
| --- | --- |
| `moon fmt` / `moon fmt --check` | Pass |
| `moon check --deny-warn --target all` | Pass, no warnings |
| `moon test --deny-warn --target all` | 6/6 each: wasm, wasm-gc, js, native (24 total) |
| `python3 scripts/cli-smoke.py` | 13/13 pass, including conversion golden |
| `python3 -W error -m unittest discover -s tests -p 'test_*.py'` | 11/11 pass; discovery, precedence, absence, permissions and execution errors |
| `python3 scripts/oracle-cross-check.py --oracle-dir ORACLE_BIN` | Both valid samples pass: each 2 balance currencies and 24 monthly rows (2024) |
| `BEAN_ORACLE_DIR=ORACLE_BIN python3 scripts/oracle-cross-check.py --year 2025` | Both samples pass: 12 and 0 monthly rows respectively, 2 balance currencies each |
| `python3 scripts/oracle-cross-check.py` with oracle tools on PATH | Both samples pass (2024); no configured directory |
| explicit directory with invalid BEAN_ORACLE_DIR and `--ledger sample/conversion.beancount` | Pass; argument takes precedence and selects conversion sample |
| script entrypoint with truly absent PATH tools | SKIP, exit 0 |
| script entrypoint with invalid `--oracle-dir` | ERROR, exit 1 |
| `moon package --list` / `moon package` | Pass; no internal audit/evidence files or bytecode in list/archive |

The pre-existing repository-field warning remains intentional: there is no remote.
The archive contains the conversion ledger, its golden, the scripts and tests.
Authored-source and archive scans check absolute home paths, email and international
phone patterns. Author metadata remains `moonbean-report contributors` with no email.
The required module identifiers are retained.

Only this module was modified. No dependency changes, remote, push or publish.
Registry-side publication, remote CI, Windows/Linux and other MoonBit versions were
not verified. Closeout retains the current source, base commit, all evidence,
build/dependency state and deliverables; no Trash moves or space-reclamation claim.
