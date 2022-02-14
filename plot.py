#!/usr/bin/env python3

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd
import json
import argparse
import pathlib
import sys

def plot_CPU(results : dict, pdf : PdfPages):
    for report, data in results['results']['CPU']['benchmarks'].items():
        x_labels = [results['system-info']['model']+ ' ' + m for m in data[0]['average'].keys()]
        x = (data[0]['average']['p1.t1']['user'],data[0]['average']['p1.t256']['user'])

        # plot
        fig, ax = plt.subplots()

        ind = np.arange(len(x))    # the x locations for the groups
        width = 0.35         # the width of the bars

        ax.bar(ind, x, width)

        ax.set_xticks(ind)
        ax.set_xticklabels(x_labels)
        ax.set_title(report)
        ax.set_xlabel('Platform')
        ax.set_ylabel('User-mode runtime (Seconds)')

        pdf.savefig()
        plt.close()

def plot_disk(results : dict, pdf : PdfPages):
    for report, data in results['results']['Disk']['benchmarks']['IOZone'][0]['results'].items():
        x = pd.DataFrame(data)
        x.index = x.index.astype(dtype=int)
        x.columns = x.columns.astype(dtype=int)
        x.sort_index(inplace=True)
        x.sort_index(axis = 1, inplace=True)

        # plot
        fig, ax = plt.subplots()

        im = ax.imshow(x, interpolation='none')

        # get the colors of the values, according to the 
        # colormap used by imshow
        values = np.unique(x.to_numpy().ravel())
        colors = [ im.cmap(im.norm(value)) for value in values]
        # create a patch (proxy artist) for every color 
        patches = [ mpatches.Patch(color=colors[i], label="Level {l}".format(l=values[i]) ) for i in range(len(values)) ]
        # put those patched as legend-handles into the legend
        plt.legend(handles=patches, bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0. )

        ax.set_xticklabels(x.columns.values)
        ax.set_yticklabels(x.index.values)

        ax.set_title(f'IOZone - {report}')
        ax.set_xlabel('Platform')
        ax.set_ylabel('User-mode runtime (Seconds)')

        pdf.savefig()
        plt.close()


parser = argparse.ArgumentParser(description='Create plot for results file.')
parser.add_argument('results_file', metavar='results_file', type=pathlib.Path, nargs='?',
                    help='results JSON file', default=sys.stdin)
parser.add_argument('plot_file', metavar='plot_file', type=pathlib.Path, nargs='?',
                    help='file to plot results to', default=sys.stdout)

args = parser.parse_args()

results = json.load(open(args.results_file))

with PdfPages(str(args.plot_file)) as pdf:
    if 'CPU' in results['results']:
        plot_CPU(results, pdf)
    if 'Disk' in results['results']:
        plot_disk(results, pdf)