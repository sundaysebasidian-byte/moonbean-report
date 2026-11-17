#!/bin/sh
# Verify embedded MoonBit test data still matches the external fixtures/goldens.
set -eu
cd "$(dirname "$0")/.."
sh scripts/embed-fixtures.sh
git diff --exit-code -- '*_wbtest.mbt'
