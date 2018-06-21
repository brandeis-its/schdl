#!/bin/bash

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

export PYTHONPATH="${DIR}"

cd "${DIR}"

rm -rfv schdl/templates/generated

ARGS="--module=angular2tmpl.noscript --module=schdl.seo.schdl_mod"

for file in $(find ui/src/ -mindepth 2 -name '*.html' | cut -c8-); do
	dir="$(dirname "${file}")"
	mkdir -p "schdl/templates/generated/${dir}"
	angular2tmpl --infile=ui/src/${file} --outfile="schdl/templates/generated/${file}" $ARGS $@
done
angular2tmpl --infile=ui/build/index.html --outfile="schdl/templates/generated/index.html" --module=schdl.seo.heads $ARGS $@
