#!/bin/sh

# Run all `sample_settings`. Any extra flags (e.g., --test) are passed through
# to midani.

BASEDIR=$(dirname "$0")

for settings in "${BASEDIR}"/../sample_settings/settings*.py
do
    python3 "${BASEDIR}/../midani.py" --settings "$settings" "$@"
done
