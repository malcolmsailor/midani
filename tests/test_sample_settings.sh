#!/bin/sh

# Run all `sample_settings`.
# Should be run with either "--frames" or "--videos" as first argument
# Any extra flags (e.g., --test) are passed through
# to midani.

usage() {
    echo 'First argument must be either "--frames" or "--videos"'
    echo 'Subsequent arguments are passed through to midani'
    exit 1
}

MIDANI_DIR=$(dirname "$0")/..
TEMP_OUT="${MIDANI_DIR}"/tests/.temp_sample_settingsTEMP_OUT

# echo_and_run after https://stackoverflow.com/a/12240862/10155119
echo_and_run() {
    echo "\$ $*"
    "$@" >& "$TEMP_OUT"
}

try_to_run() {
    echo_and_run "$@"
    if [[ $? -ne 0 ]]
    then
        cat "$TEMP_OUT"
        echo Error running "$@", aborting
        rm "$TEMP_OUT"
        exit 1
    else
        rm "$TEMP_OUT"
        echo ===============================================================
    fi
}

case "$1" in
    --frames ) frames=1
        ;;
    --videos ) frames=0
        ;;
    * ) usage
esac



for settings in "${MIDANI_DIR}"/sample_settings/settings*.py
do
    if [[ $frames -eq 1 ]]
    then
        # try_to_run python3 "${MIDANI_DIR}/midani.py" --settings "$settings" \
        try_to_run midani --settings "$settings" \
            "${MIDANI_DIR}/tests/test_settings/frame_settings.py" \
            --frames 0,2,4 "${@:2}"
    else
        # try_to_run python3 "${MIDANI_DIR}/midani.py" \
        try_to_run midani \
            --settings "$settings" "${@:2}"
    fi
done
