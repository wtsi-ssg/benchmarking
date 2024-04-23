#!/usr/bin/env python3

import argparse
import json
import os
import pathlib
import sys
import time
from decimal import Decimal
from typing import Tuple

import yaml
import yapsy.PluginFileLocator as pfl
import yapsy.PluginManager as pm

from benchmark_suite.benchmarkessentials import BenchmarkPlugin, ParentBenchmark
from benchmark_suite.resultsreturn import ResultsReturn
from benchmark_suite.datapreparer import DataPreparer
from benchmark_suite.plotresults import PlotResults
from benchmark_suite.utility import Utility
from benchmark_suite.suite import Suite

sys.path.insert(1, f"{sys.path[0]}/setup/")


def get_args():
    """Gets CLI arguments for running the benchmark suite."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--verbose", help="""Increase output verbosity""", action="store_true"
    )

    parser.add_argument("type", type=str, help="""Type of the benchmark""")

    parser.add_argument(
        "output_file_basename", type=str, help="""The output base file name"""
    )

    parser.add_argument(
        "nickname", type=str, help="""Nickname for host being evaluated"""
    )

    parser.add_argument(
        "-i",
        "--iperf_server_ip",
        type=str,
        help="""Server IP for iPerf server""",
    )

    parser.add_argument(
        "-p",
        "--iperf_server_port",
        type=str,
        help="""Server Port for iPerf server""",
    )

    parser.add_argument(
        "-c",
        "--clear_cache_bin",
        type=str,
        help="""Executable to drop test host cache""",
    )

    parser.add_argument(
        "--return_results",
        help="""Automatically upload results to Sanger""",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--cost_per_kwh", type=Decimal, help="""Cost of power per KWh for plots"""
    )

    parser.add_argument(
        "--carbon_per_kwh",
        type=Decimal,
        help="""Carbon dioxide in Kg per KWh for plots""",
    )

    parser.add_argument(
        "--override_power",
        type=Decimal,
        help="""Override detected power consumption in watts""",
    )

    parser.add_argument("--tco", type=Decimal, help="""TCO of machine in £""")

    parser.add_argument(
        "--geekbench5_email",
        type=str,
        help="""Geekbench 5 registered email""",
    )

    parser.add_argument(
        "--geekbench5_key",
        type=str,
        help="""Geekbench 5 key""",
    )

    return parser.parse_args()


def get_config_file(b_type):
    """Gets the config file for the benchmark type."""
    return os.path.join(sys.path[0] + "/setup/config_files", b_type + ".yml")


def get_config(c_file):
    with open(c_file, "r", encoding="UTF-8") as yamlconfig:
        config = yaml.safe_load(yamlconfig)

    return config


def get_benchmark_with_children(benchsuite, base_benchmark, benchmark_dict):
    settings = (
        base_benchmark["settings"]
        if "settings" in base_benchmark and base_benchmark["settings"] is not None
        else {}
    )
    if settings:
        base_benchmark["settings"]["install_dir"] = Utility.get_install_dir(
            get_config_file(args.type)
        )

    benchmark_object = benchmark_dict[base_benchmark["type"]](
        suite=benchsuite, **settings
    )
    if issubclass(type(benchmark_object), ParentBenchmark):
        for mark in base_benchmark["benchmarks"]:
            benchmark_object.add_benchmark(
                get_benchmark_with_children(benchsuite, mark, benchmark_dict)
            )

    return benchmark_object


def load_all_benchmarks():
    loaded_benchmarks = {}

    pluginmanager = pm.PluginManager(
        categories_filter={"Benchmarks": BenchmarkPlugin},
        plugin_locator=pfl.PluginFileLocator(
            analyzers=(
                pfl.PluginFileAnalyzerMathingRegex("", r"(?!^__init__.py$).*\.py$"),
            )
        ),
    )
    pluginmanager.setPluginPlaces([sys.path[0] + "/benchmark_suite/benchmarks"])
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
        if len(list(bmsettings.keys())) > 0 and list(bmsettings.keys())[0] == "type":
            benchsuite.add_benchmark(
                get_benchmark_with_children(benchsuite, bmsettings, loaded_benchmarks)
            )

    return benchsuite


def result_filename(
    b_type, output_basefile
) -> Tuple[str, str, pathlib.Path, pathlib.Path]:
    result_dir = os.path.join("/data/results", b_type)
    os.makedirs(result_dir, exist_ok=True)

    result_filebase = time.strftime("%Y-%m-%d-%H%M%S") + "_" + output_basefile
    result_filename = result_filebase + ".json"
    plot_filename = result_filebase + ".pdf"
    output_fullpath = os.path.join(result_dir, result_filename)
    plot_fullpath = os.path.join(result_dir, plot_filename)

    return [result_filename, plot_filename, output_fullpath, plot_fullpath]


def run_benchsuite(benchsuite, config_file, result_fullpath):
    install_dir = Utility.get_install_dir(config_file)
    results = benchsuite.run()

    with open(result_fullpath, "w", encoding="UTF-8") as file:
        json.dump(results, file, indent=2)

    if args.verbose:
        print(json.dumps(results, indent=2, sort_keys=True))

    return results


def update_iperf_server_address(config, server_address: str, port: str):
    for c in config:
        if "benchmarks" in c:
            for b in c["benchmarks"]:
                b["settings"]["server_address"] = server_address
                b["settings"]["server_port"] = port

    return config


def update_geekbench5(config, geekbench5_email: str, geekbench5_key: str):
    """Updates the geekbench5 email and key in the config file"""
    for c in config:
        if "benchmarks" in c:
            for b in c["benchmarks"]:
                b["settings"]["geekbench5_email"] = geekbench5_email
                b["settings"]["geekbench5_key"] = geekbench5_key

    return config


if __name__ == "__main__":
    args = get_args()

    dp = DataPreparer(
        "defaults.yml",
        f"/benchmarking/setup/config_files/{args.type}.yml",
        os.path.dirname(os.path.realpath(__file__)),
        args.verbose,
    )

    print("Preparing data for benchmarking...")

    if not dp.prepare_data():
        sys.exit(1)

    print("Benchmarking preparation complete.")

    if args.type == "network" and not (args.server_ip and args.server_port):
        print("-s_ip and -s_port required for iPerf network benchmark.")
        sys.exit(1)

    config_file = get_config_file(args.type)

    [
        raw_result_filename,
        raw_plot_file,
        result_fullpath,
        plot_fullpath,
    ] = result_filename(args.type, args.output_file_basename)

    if args.verbose:
        print(f"Chosen benchmark type:      {args.type}")
        print(f"Configuration file used:    {config_file}")
        print(f"Output will be stored at:   {args.output_file_basename}")

    config = get_config(config_file)

    if args.type == "network":
        config = update_iperf_server_address(
            config, args.iperf_server_ip, args.iperf_server_port
        )

    elif args.type == "geekbench5":
        config = update_geekbench5(config, args.geekbench5_email, args.geekbench5_key)

    loaded_benchmarks = load_all_benchmarks()

    benchsuite = Suite(
        clear_cache_bin=args.clear_cache_bin,
        nickname=args.nickname,
        override_power=args.override_power,
        tco=args.tco,
        path_to_program_dict=dp.path_to_program_dict,
    )

    set_wd(config_file)

    benchsuite = add_benchmark_to_benchsuite(benchsuite, config, loaded_benchmarks)

    print("Running benchmarks")
    results = run_benchsuite(benchsuite, config_file, result_fullpath)

    RESULT_FILE_PATH_TO_LOCAL = str(
        pathlib.Path(*pathlib.Path(result_fullpath).parts[2:])
    )
    print(f"Result stored at: <mount_point>/{RESULT_FILE_PATH_TO_LOCAL}")

    if args.return_results:
        print("Uploading results as requested.")
        r = ResultsReturn()
        r.post_results(
            raw_result_filename,
            json.dumps(results, indent=2, sort_keys=True),
            args.verbose,
        )

    PLOT_FILE_PATH_TO_LOCAL = str(pathlib.Path(*pathlib.Path(plot_fullpath).parts[2:]))

    pr = PlotResults(
        result_fullpath,
        [],
        plot_fullpath,
        args.cost_per_kwh,
        args.carbon_per_kwh,
        override_power=None,
        override_tco=None,
    )

    pr.plot_results()
    print(f"Plots in: <mount_point>/{PLOT_FILE_PATH_TO_LOCAL}")
