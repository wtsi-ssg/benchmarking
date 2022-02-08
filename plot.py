#!/usr/bin/env python3

import matplotlib.pyplot as plt
import numpy as np
import json
import argparse
import pathlib
import sys

parser = argparse.ArgumentParser(description='Create plot for results file.')
parser.add_argument('results_file', metavar='results_file', type=pathlib.Path, nargs='?',
                    help='results JSON file', default=sys.stdin)
parser.add_argument('plot_file', metavar='plot_file', type=pathlib.Path, nargs='?',
                    help='file to plot results to', default=sys.stdin)

args = parser.parse_args()

results = json.load(open(args.results_file))
x_labels = [results['system-info']['model']+ ' ' + m for m in results['results']['CPU']['benchmarks']['multithreaded_bwa'][0]['average'].keys()]
x = (results['results']['CPU']['benchmarks']['multithreaded_bwa'][0]['average']['p1.t1']['user'],results['results']['CPU']['benchmarks']['multithreaded_bwa'][0]['average']['p1.t256']['user'])

# plot
fig, ax = plt.subplots()

ind = np.arange(len(x))    # the x locations for the groups
width = 0.35         # the width of the bars

ax.bar(ind, x, width)

ax.set_xticks(ind)
ax.set_xticklabels(x_labels)
ax.set_title('How fast do you want to go today?')
ax.set_xlabel('Platform')
ax.set_ylabel('User-mode runtime (Seconds)')

plt.savefig(args.plot_file)
