#!/usr/bin/env python3

import argparse
import json
import os
import pathlib
import sys
import time

import requests
import yaml
import yapsy.PluginFileLocator as pfl
import yapsy.PluginManager as pm

from benchmark_suite.suite import Suite
from benchmark_suite.benchmarkessentials import (BenchmarkPlugin,
                                                 ParentBenchmark)
from benchmark_suite.prepareScript import DataPreparer

sys.path.insert(1, f'{sys.path[0]}/setup/')
from benchmark_suite.utility import Utility

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-v','--verbose', 
        help="""Increase output verbosity""",
        action="store_true"
    )
    parser.add_argument(
        '-t','--type',
        type=str,
        help="""Type of the benchmark""",
        required=True
    )
    parser.add_argument(
        '-o', '--output_file_name',
        type=str,
        help="""The output file name""",
        required=True
    )
    parser.add_argument(
        '-i', '--server_ip',
        type=str,
        help="""Server IP for iPerf server""",
    )
    parser.add_argument(
        '-p', '--server_port',
        type=str,
        help="""Server Port for iPerf server""",
    )
    parser.add_argument(
        '-d', '--clear_cache_bin',
        type=str,
        help="""Executable to drop test host cache"""
    )
    parser.add_argument(
        '-n', '--nickname',
        type=str,
        help="""Nickname for host being evaluated"""
    )
    
    return parser.parse_args()

def get_config_file(b_type):
    return os.path.join(sys.path[0]+"/setup/config_files", b_type+".yml")

def get_config(c_file):
    with open(c_file, "r") as yamlconfig:
        config = yaml.safe_load(yamlconfig)

    return config

def get_benchmark_with_children(benchsuite, base_benchmark, benchmark_dict):
    settings = base_benchmark["settings"] if "settings" in base_benchmark and base_benchmark["settings"] is not None else {}
    if settings:
        base_benchmark["settings"]['install_dir'] = Utility.get_install_dir(get_config_file(args.type))

    benchmark_object = benchmark_dict[base_benchmark["type"]](suite=benchsuite, **settings)
    if issubclass(type(benchmark_object), ParentBenchmark):
        for mark in base_benchmark["benchmarks"]:
            benchmark_object.add_benchmark(get_benchmark_with_children(benchsuite, mark, benchmark_dict))

    return benchmark_object

def load_all_benchmarks():
    loaded_benchmarks = {}

    pluginmanager = pm.PluginManager(categories_filter={"Benchmarks": BenchmarkPlugin}, plugin_locator=pfl.PluginFileLocator(analyzers=(pfl.PluginFileAnalyzerMathingRegex("", r"(?!^__init__.py$).*\.py$"),)))
    pluginmanager.setPluginPlaces([sys.path[0]+ "/benchmark_suite/benchmarks"])
    pluginmanager.collectPlugins()

    for plugin in pluginmanager.getAllPlugins():
        loaded_benchmarks.update(plugin.plugin_object.get_benchmarks())
    
    if args.verbose:
        print("Benchmarks are loaded", file=sys.stderr)
    
    return loaded_benchmarks

def set_wd(config_file):
    os.chdir(os.path.dirname(os.path.abspath(os.path.expanduser(config_file))))

def add_benchmark_to_benchsuite(benchsuite, config, loaded_benchmarks):
    for bmsettings in config:
        if len(list(bmsettings.keys())) > 0 and list(bmsettings.keys())[0] == 'type':
            benchsuite.add_benchmark(get_benchmark_with_children(benchsuite, bmsettings, loaded_benchmarks))

    return benchsuite

def result_file_name(b_type, output_file):
    result_dir = os.path.join("/data/results", b_type)
    os.makedirs(result_dir, exist_ok=True)

    result_file =  time.strftime("%Y-%m-%d-%H%M%S") + "_" + output_file
    output_fullpath = os.path.join(result_dir,result_file) 
    
    return [result_file, output_fullpath]

def post_results(raw_result_file : str, jsondata : str):
    # Fetch signed post URL from s3 cog
    post_signed_url = "https://it_randd.cog.sanger.ac.uk/post_signed_url.json"
    r = requests.get(url=post_signed_url)
    myurl_raw = json.loads(r.text)

    # POST results JSON to fetched URL
    files = {'file': (raw_result_file, jsondata.encode('utf-8'))}
    resp = requests.post(myurl_raw['url'], data=myurl_raw['fields'], files=files)
    if not resp.ok:
        print(f'Error {r.status_code} uploading results: {r.text}')
    else:
        print('Results returned successfully.')

def run_benchsuite(benchsuite, config_file, result_fullpath, raw_result_file):
    install_dir = Utility.get_install_dir(config_file)
    results = benchsuite.run()
    
    with open(result_fullpath, "w") as file:
        json.dump(results, file, indent=2)
    post_results(raw_result_file, json.dumps(results, indent=2, sort_keys=True))
    
    if args.verbose:
        print(json.dumps(results, indent=2, sort_keys=True))

def update_iperf_server_address(config, server_address, port):
    for c in config:
        if "benchmarks" in c:
            for b in c["benchmarks"]:
                b["settings"]["server_address"] = server_address
                b["settings"]["server_port"] = port

    return config
    

if __name__ == '__main__':
    args = get_args()

    dp = DataPreparer('defaults.yml', args.type)
    if not dp.prepareData():
        sys.exit(1)
 
    if args.type == "network" and not (args.server_ip and args.server_port):
        print("-s_ip and -s_port required for iPerf network benchmark.")
        sys.exit(1)

    config_file = get_config_file(args.type)
    
    if args.verbose:
        print("Chosen benchmark type:      {}".format(args.type))
        print("Configuration file used:    {}".format(config_file))
        print("Output will be stored at:   {}".format(args.output_file_name))

    config = get_config(config_file)

    if args.type == "network":
        config = update_iperf_server_address(config, args.server_ip, args.server_port)

    loaded_benchmarks = load_all_benchmarks()
    
    benchsuite = Suite(clear_cache_bin=args.clear_cache_bin, nickname=args.nickname)
    
    set_wd(config_file)
    
    benchsuite = add_benchmark_to_benchsuite(benchsuite, config, loaded_benchmarks)
    
    [raw_result_file, result_fullpath] = result_file_name(args.type, args.output_file_name)

    run_benchsuite(benchsuite, config_file, result_fullpath, raw_result_file)

    result_file_path_to_local = str(pathlib.Path(*pathlib.Path(result_fullpath).parts[2:]))
    print("Result stored at: {}".format("<mount_point>/"+result_file_path_to_local))
