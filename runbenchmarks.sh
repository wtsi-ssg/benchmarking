#!/bin/bash -e
ymlFileName="/benchmarking/setup/config_files/${1}.yml"
cd /benchmarking
python3 /benchmarking/prepareScript.py -yml $ymlFileName

export PYTHONPATH=/benchmarking

if [ $? == 0 ]; then
        if [ "$1" == "network" ]; then
                python3 /benchmarking/runbenchmarks.py -v -t "$1" -s_ip "$2" -s_port "$3" -o "${1}.json"
        else
                python3 /benchmarking/runbenchmarks.py -v -t "$1" -o "${1}.json"
        fi
fi
