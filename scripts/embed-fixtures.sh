#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
moon tool embed --text --input sample/ledger.beancount --output sample_wbtest.mbt --name sample_source
moon tool embed --text --input sample/error.beancount --output error_wbtest.mbt --name error_source
moon tool embed --text --input golden/sample-2024.txt --output golden_wbtest.mbt --name sample_expected
moon tool embed --text --input golden/error.txt --output error_golden_wbtest.mbt --name error_expected
moon fmt
