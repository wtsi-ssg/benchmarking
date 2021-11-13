#!/usr/bin/env python3

import yaml
import json
import argparse
import os
import sys
import yapsy.PluginManager as pm
import yapsy.PluginFileLocator as pfl
import benchmarkessentials
import suite
import time

sys.path.insert(1, '/benchmarking/')
import prepareScript

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
        choices=['cpu_numa', 'disk', 'network', 'threaded', 'timed_command'],
        required=True
    )
    parser.add_argument(
        '-o', '--output_file_name',
        type=str,
        help="""The output file name""",
        required=True
    )
    
    return parser.parse_args()

def get_config_file(b_type):
    return os.path.join("/data/benchmarking/setup/config_files", b_type+".yml")

def get_config(c_file):
    with open(c_file, "r") as yamlconfig:
        config = yaml.safe_load(yamlconfig)

    return config

def get_benchmark_with_children(base_benchmark, benchmark_dict):
    settings = base_benchmark["settings"] if "settings" in base_benchmark and base_benchmark["settings"] is not None else {}
    if settings:
        base_benchmark["settings"]['install_dir'] = prepareScript.get_install_dir(get_config_file(args.type))

    benchmark_object = benchmark_dict[base_benchmark["type"]](**settings)
    if issubclass(type(benchmark_object), benchmarkessentials.ParentBenchmark):
        for mark in base_benchmark["benchmarks"]:
            benchmark_object.add_benchmark(get_benchmark_with_children(mark, benchmark_dict))

    return benchmark_object

def load_all_benchmarks():
    loaded_benchmarks = {}

    pluginmanager = pm.PluginManager(categories_filter={"Benchmarks": benchmarkessentials.BenchmarkPlugin}, plugin_locator=pfl.PluginFileLocator(analyzers=(pfl.PluginFileAnalyzerMathingRegex("", r"(?!^__init__.py$).*\.py$"),)))
    pluginmanager.setPluginPlaces([sys.path[0]+ "/benchmarks"])
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
            benchsuite.add_benchmark(get_benchmark_with_children(bmsettings, loaded_benchmarks))
        else:
            for k in ['general_settings','release_date', 'file_system']:
                benchsuite.add_general_settings(k, bmsettings[k])
                del bmsettings[k]

    return benchsuite

def result_file_name(b_type, output_file):
    result_dir = os.path.join("/data/results", b_type)
    os.makedirs(result_dir, exist_ok=True)

    output_file = os.path.join(result_dir, time.strftime("%Y%m%d-%H%M%S")+"_"+output_file) 
    
    return output_file

def run_benchsuite(benchsuite, config_file, result_file):
    install_dir = prepareScript.get_install_dir(config_file)
    results = benchsuite.run()
    
    with open(result_file, "w") as file:
        json.dump(results, file, indent=2)
    
    if args.verbose:
        print(json.dumps(results, indent=2, sort_keys=True))

if __name__ == '__main__':
    args = get_args()

    config_file = get_config_file(args.type)
    
    if args.verbose:
        print("Chosen benchmark type:      {}".format(args.type))
        print("Configuration file used:    {}".format(config_file))
        print("Output will be stored at:   {}".format(args.output_file_name))

    config_file = os.path.join("/data/benchmarking/setup/config_files", args.type+".yml")
    
    config = get_config(config_file)
    
    loaded_benchmarks = load_all_benchmarks()
    
    benchsuite = suite.Suite()
    
    set_wd(config_file)
    
    benchsuite = add_benchmark_to_benchsuite(benchsuite, config, loaded_benchmarks)
    
    result_file = result_file_name(args.type, args.output_file_name)

    run_benchsuite(benchsuite, config_file, result_file)
    
    print("Result stored at: {}".format(result_file))

