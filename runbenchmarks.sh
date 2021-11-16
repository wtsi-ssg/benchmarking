#!/bin/bash -e
ymlFileName="/benchmarking/setup/config_files/${1}.yml"
python3 /benchmarking/setup/prepareScript.py -yml $ymlFileName

if [ "$1" == "network" ]; then
	python3 /benchmarking/benchmark_suit/runbenchmarks.py -v -t "$1" -s_ip "$2" -s_port "$3" -o "${1}.json"
else
	python3 /benchmarking/benchmark_suit/runbenchmarks.py -v -t "$1" -o "${1}.json"
fi
