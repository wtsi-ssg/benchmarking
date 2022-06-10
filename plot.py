#!/usr/bin/env python3

import argparse
import pathlib
import sys

import benchmark_suite.plotresults

parser = argparse.ArgumentParser(description='Create plot for results file.')
parser.add_argument('results_file', metavar='results_file', type=pathlib.Path, nargs='?',
                    help='results JSON file', default=sys.stdin)
parser.add_argument('--compare_file', metavar='compare_file', type=pathlib.Path, nargs='?', action='append',
                    help='')
parser.add_argument('plot_file', metavar='plot_file', type=pathlib.Path, nargs='?',
                    help='file to plot results to', default=sys.stdout)

args = parser.parse_args()

pr = benchmark_suite.plotresults.PlotResults(args.results_file, args.compare_file, args.plot_file)
pr.plot_results()
