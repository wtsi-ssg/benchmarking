#!/usr/bin/env python3

"""Module to run a smaller/quicker version of the benchmarking suite"""

import argparse
from decimal import Decimal
import json
import sys
import time

import yapsy.PluginFileLocator as pfl
import yapsy.PluginManager as pm

from benchmark_suite.benchmarks.multithreaded import MultiThread
from benchmark_suite.benchmarkessentials import BenchmarkPlugin
from benchmark_suite.resultsreturn import ResultsReturn
from benchmark_suite.suite import Suite

sys.path.insert(1, f"{sys.path[0]}/setup/")


def get_args():
    """Get command line arguments to run the benchmarks."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--verbose", help="""Increase output verbosity""", action="store_true"
    )
    parser.add_argument(
        "-c",
        "--clear_cache_bin",
        type=str,
        help="""Executable to drop test host cache""",
    )
    parser.add_argument(
        "-n", "--name", type=str, help="""Name of program being tested""", required=True
    )
    parser.add_argument(
        "-t", "--tag", type=str, help="""Git tag of program being tested"""
    )
    parser.add_argument(
        "-r",
        "--revision",
        type=str,
        help="""Git revision hash of program being tested""",
    )
    parser.add_argument(
        "--datetime", type=str, help="""Commit date and time of program being tested"""
    )
    parser.add_argument(
        "-e", "--executable", type=str, help="""Executable to test""", required=True
    )
    parser.add_argument(
        "-a",
        "--arguments",
        type=str,
        help="""Arguments to executable being tested""",
        default="",
    )
    parser.add_argument(
        "-w", "--working", type=str, help="""Working dir""", required=True
    )
    parser.add_argument(
        "--override_power",
        type=Decimal,
        help="""Override detected power consumption in watts""",
    )
    parser.add_argument("--tco", type=Decimal, help="""TCO of machine in £""")
    parser.add_argument(
        "--return_results",
        help="""Automatically upload results to Sanger""",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "--repeats",
        help="""Number of times to repeat the experiment""",
        type=int,
        default=3,
    )
    return parser.parse_args()


args = get_args()

# Setup benchsuite
benchsuite = Suite(
    clear_cache_bin=args.clear_cache_bin,
    nickname=args.name,
    override_power=args.override_power,
    tco=args.tco,
)

# Create benchmark to run and add to benchsuite
pluginmanager = pm.PluginManager(
    categories_filter={"Benchmarks": BenchmarkPlugin},
    plugin_locator=pfl.PluginFileLocator(
        analyzers=(pfl.PluginFileAnalyzerMathingRegex("", r"(?!^__init__.py$).*\.py$"),)
    ),
)

pluginmanager.setPluginPlaces([sys.path[0] + "/benchmark_suite/benchmarks"])
pluginmanager.collectPlugins()
benchsuite.add_benchmark(
    MultiThread(
        suite=benchsuite,
        command=args.executable + " " + args.arguments,
        install_path=args.executable,
        result_dir=args.working,
        repeats=args.repeats,
    )
)

# Run benchmark and create JSON output
output = {
    "name": args.name,
    "tag": args.tag,
    "revision": args.revision,
    "datetime": args.datetime,
    "executable": args.executable,
    "arguments": args.arguments,
    "results": benchsuite.run(),
}
if args.return_results:
    r = ResultsReturn("https://it_randd.cog.sanger.ac.uk/post_signed_url_ci.json")
    result_filename = time.strftime("%Y-%m-%d-%H%M%S") + "_" + args.name + ".json"
    r.post_results(
        result_filename, json.dumps(output, indent=2, sort_keys=True), args.verbose
    )

print(json.dumps(output))
