#!/bin/sh

# Run all `sample_settings`.
# Should be run with either "--frames" or "--videos" as first argument
# Any extra flags (e.g., --test) are passed through
# to midani.

function usage() {
    echo 'First argument must be either "--frames" or "--videos"'
    echo 'Subsequent arguments are passed through to midani'
    exit 1
}

case "$1" in
    --frames ) frames=1
        ;;
    --videos ) frames=0
        ;;
    * ) usage
esac

MIDANI_DIR=$(dirname "$0")/..

for settings in "${MIDANI_DIR}"/sample_settings/settings*.py
do
    if [[ $frames -eq 1 ]]
    then
        python3 "${MIDANI_DIR}/midani.py" --settings "$settings" \
            "${MIDANI_DIR}/tests/test_settings/frame_settings.py" \
            --frames 0,2,4 "${@:2}"
        if [[ $? -ne 0 ]]
        then
            echo Error with "$settings", aborting...
            exit 1
        fi
    else
        python3 "${MIDANI_DIR}/midani.py" --settings "$settings" "${@:2}"
    fi
done
