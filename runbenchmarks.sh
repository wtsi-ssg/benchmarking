#!/bin/bash
set -euo pipefail
settingsFileName="/benchmarking/setup/config_files/${1}.yml"
cd /benchmarking

export PYTHONPATH=/benchmarking
python3 /benchmarking/suite/prepareScript.py -s $settingsFileName

if [ $? == 0 ]; then
        if [ "$1" == "network" ]; then
                python3 /benchmarking/runbenchmarks.py -v -t "$1" -i "$2" -p "$3" -o "${1}.json" -n "$4"
        else
                python3 /benchmarking/runbenchmarks.py -v -t "$1" -o "${1}.json" -n "$2"
        fi
fi
