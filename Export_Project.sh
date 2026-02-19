#!/usr/bin/env bash

set -euo pipefail

OUTPUT="API_GetSomeSleep_AllSourceFiles.txt"

echo "Creating $OUTPUT ..."
> "$OUTPUT"

find . -type f \
    ! -path "*/.git/*" \
    ! -path "*/.venv/*" \
    ! -path "*/.vscode/*" \
    ! -path "*/app/__pycache__/*" \
    \( \
        -name "*.py" -o \
        -name "*.yml" -o \
        -name "*.yaml" -o \
        -name "*.txt" -o \
        -name "*.md" -o \
        -name "*.sh" -o \
        -name "Dockerfile" \
    \) \
    ! -name "$OUTPUT" \
    -print | sort | while read -r file; do

    RELATIVE_PATH="${file#./}"

    {
	echo "   "
	echo "   "
	echo "   "
        echo "############################################################"
        echo "# $RELATIVE_PATH"
        echo "############################################################"
        cat "$file"
        echo
    } >> "$OUTPUT"

done

echo "Done ✔  Output written to $OUTPUT"
