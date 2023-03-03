#!/bin/sh

BUILD_DIR=$1

if [ $# != 1 ] || [ ! -d "$BUILD_DIR" ]; then
	echo "Usage: ${0##*/} path/to/build-dir/"
	exit 1
fi

cd "${0%/*}" || exit 1
rm -rf out
mkdir -p out

echo "\\\\def\\\\buildDir{$BUILD_DIR}" > out/builddir.tex

find "$BUILD_DIR" -name "*.tex" | while read -r x; do
	bname=$(basename "${x%.tex}") # remove extension and parent dir
	shortname=${x#"$BUILD_DIR"}
	for i in 1 2; do
		echo lualatex "$shortname [$i/2]"
		lualatex --halt-on-error --output-directory out "$x" > /dev/null || exit 13
		cp -pv "out/$bname.pdf" "$(dirname "$x")" || exit 11
	done
done

ec=$?
if [ $ec -eq 0 ]; then
	# only delete if successful, on error keep logs
	rm -rf out
else
	tail -50 out/*.log
	echo "Error."
	exit $ec
fi
