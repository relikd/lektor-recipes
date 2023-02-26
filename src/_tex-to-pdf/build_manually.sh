#!/bin/sh

cd "${0%/*}" || exit 1
rm -rf out
mkdir -p out

build_dir=$(lektor project-info --output-path)
echo "\\\\def\\\\buildDir{$build_dir}" > out/builddir.tex

find "$build_dir" -name "*.tex" | while read -r x; do
	bname=$(basename "${x%.tex}") # remove extension and parent dir
	shortname=${x#"$build_dir"}
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
