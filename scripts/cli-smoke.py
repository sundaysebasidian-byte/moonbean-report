#!/usr/bin/env python3
"""Check the real native CLI, including status codes and host file handling."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def invoke(arguments, expected_code, text=None):
    result = subprocess.run(
        ["moon", "run", "--quiet", "cmd/bean-report", "--target", "native", "--", *arguments],
        cwd=ROOT, text=True, capture_output=True,
    )
    assert result.returncode == expected_code, (arguments, result.returncode, result.stdout, result.stderr)
    if text:
        assert text in result.stdout + result.stderr, (arguments, result.stdout, result.stderr)
    return result.stdout


assert invoke(["sample/ledger.beancount", "--year", "2024"], 0) == (ROOT / "golden/sample-2024.txt").read_text()
assert invoke(["sample/error.beancount", "--year", "2024"], 1) == (ROOT / "golden/error.txt").read_text()
invoke([], 2, "usage:")
invoke(["sample/ledger.beancount", "--year", "0000"], 2, "year must be")
invoke(["sample/ledger.beancount", "--year", "20x4"], 2, "usage:")
invoke(["sample/ledger.beancount", "--year", "2024", "extra"], 2, "usage:")
invoke(["sample/ledger.beancount", "--unknown", "2024"], 2, "usage:")
invoke(["tests/fixtures/not-present.beancount"], 1, "cannot read")
invoke(["tests/fixtures/include.beancount"], 1, "tests/fixtures/invalid-child.beancount:3:")
invoke(["tests/fixtures/missing-include.beancount"], 1, "include.missing")
invoke(["tests/fixtures/document.beancount"], 0, "0 warnings")
invoke(["tests/fixtures/missing-document.beancount"], 1, "validation.document_missing")
print("PASS: 12 native CLI checks (goldens, exit codes, arguments, includes, documents)")
