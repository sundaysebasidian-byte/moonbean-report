# Verification

Author: moonbean-report contributors. Local verification only.

Toolchain: `MOON_HOME=/tmp/moon-new PATH=/tmp/moon-new/bin:$PATH`,
`moon 0.1.20261104 (940aa18 2026-11-04)`, native macOS arm64.

| Command | Observed result |
| --- | --- |
| `moon add sundaysebasidian-byte/moonbean@0.2.8` | Registry-resolved cached 0.2.8; no local path dependency |
| `moon tree` | Direct dependency resolved to moonbean 0.2.8 |
| `moon fmt` / `moon fmt --check` | Pass |
| `moon check --target native --deny-warn` | Pass, no warnings |
| `moon test --target native` | 5/5 pass, including complete sample/error goldens |
| `moon check --target all` | Pass |
| `moon test --target all` | 5/5 each: wasm, wasm-gc, js, native |
| `python3 scripts/cli-smoke.py` | 12/12 native checks pass |
| `moon build cmd/bean-report --target native --release` | Pass; native release binary produced |
| `./bean-report sample/ledger.beancount --year 2024` | Exit 0; stdout matches golden byte for byte |
| `python3 scripts/oracle-cross-check.py` | bean-check passes; 2 balance currencies and 24 monthly rows agree for 2024 |
| `python3 scripts/oracle-cross-check.py --year 2025` | 2 balance currencies and 12 monthly rows agree for 2025 |
| `python3 scripts/oracle-cross-check.py --oracle-dir tests/fixtures/absent-oracle` | Explicit SKIP; exit 0 |
| `moon package --list` / `moon package` | Check passed; archive produced; no packaging errors |
| `moon publish --dry-run` | Exit 255: registry login required, even with --dry-run; no publish performed |

Archive: `_build/publish/sundaysebasidian-byte-moonbean-report-0.1.0.zip`.
The packaging command warns that `repository` is unset, intentionally: this
standalone example has no remote. This warning does not prevent archive creation.

The initial example query used `number(units)`, accepted by MoonBean but rejected
by the oracle because it has no `units` column. It was replaced with the portable
`sum(number)` query before final verification. The final sample comparisons found
no figure mismatch and produced no MoonBean bug repro. This does not prove general
compatibility; the upstream compatibility doc lists limitations.

The source/privacy scan found no email addresses, absolute home paths or phone
patterns in the deliverable source, fixtures, docs and evidence. Human-readable
author fields contain only `moonbean-report contributors`; the two explicitly
requested module identifiers are retained. Downloaded dependencies, generated
build outputs and Git internals are outside the authored-source scan. The final
package archive's text files are also checked for those patterns.

Not verified: registry-side publish permissions, actual publication, remote CI,
Windows/Linux execution, arbitrary Beancount parity. No credentials were supplied,
no remote was created and nothing was pushed or published.

Closeout: see `closeout-manifest.json` and `closeout-operations.jsonl`. No Trash
moves; current source, fixtures, evidence, binary, package and dependency/build
state are retained. No background service or browser tab was started.
