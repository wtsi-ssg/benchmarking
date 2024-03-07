#!/usr/bin/env python3
"""Implements CLI commands for results plotting."""

import argparse
import pathlib
import sys
from decimal import Decimal

import benchmark_suite.plotresults

parser = argparse.ArgumentParser(description="Create plot for results file.")

parser.add_argument(
    "results_file",
    metavar="results_file",
    type=pathlib.Path,
    nargs="?",
    help="results JSON file",
    default=sys.stdin,
)

parser.add_argument(
    "--compare_file",
    metavar="compare_file",
    type=pathlib.Path,
    nargs="?",
    action="append",
    help="",
)

parser.add_argument(
    "plot_file",
    metavar="plot_file",
    type=pathlib.Path,
    nargs="?",
    help="file to plot results to",
    default=sys.stdout,
)

parser.add_argument(
    "--cost_per_kwh", type=Decimal, help="""Cost of power per KWh for plots"""
)

parser.add_argument(
    "--carbon_per_kwh", type=Decimal, help="""Carbon dioxide in Kg per KWh for plots"""
)

parser.add_argument(
    "--override_power", type=Decimal, help="""Override power consumption in watts"""
)

parser.add_argument("--override_tco", type=Decimal, help="""TCO of machine in GBP""")

args = parser.parse_args()

pr = benchmark_suite.plotresults.PlotResults(
    args.results_file,
    args.compare_file,
    args.plot_file,
    args.cost_per_kwh,
    args.carbon_per_kwh,
    args.override_power,
    args.override_tco,
)

pr.plot_results()
