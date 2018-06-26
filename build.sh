#!/bin/bash

set -e
set -o pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TARGET="$( readlink -f "$1" )"

cd "${DIR}"

cd ui

grunt build compile

cd "${DIR}"

python schdl/test_all.py

find "${TARGET}" -mindepth 1 -maxdepth 1 -not -name .git | xargs rm -rvf

cp -av -t "${TARGET}" \
    requirements.txt \
    schdl \
    brandeis \
    bin \
    wsgi

find gae -mindepth 1 -maxdepth 1 | xargs cp -av -t "${TARGET}"

cp -av ui/bin "${TARGET}/wsgi/static"

rm "${TARGET}/schdl/ui"
ln -s ../wsgi/static "${TARGET}/schdl/ui"
