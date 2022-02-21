#!/usr/bin/env python3

import argparse
import json
import pathlib
import sys

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

def yield_processthreadlabels(model:str, data:list):
    for m in data['configurations']:
        for i in range(0, len(m['runs'])):
            yield f" p{m['processes']}t{m['threads']}"

def yield_usertime(data:list):
    for keyData in data['configurations']:
        for m in keyData['runs']:
            yield m['user']

def plot_CPU(results : dict, pdf : PdfPages):
    for report, data in results['results']['CPU']['benchmarks'].items():
        x_labels = list(yield_processthreadlabels(results['system-info']['model'],data[0]))
        x = list(yield_usertime(data[0]))

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

def plot_iperf(results : dict, pdf : PdfPages):
    x_labels = ('UDP',)
    x = (results['results']['Network']['benchmarks']['iPerf'][0]['result_summary']['sum']['bits_per_second'],)

    # plot
    fig, ax = plt.subplots()

    ind = np.arange(len(x))    # the x locations for the groups
    width = 0.35         # the width of the bars

    ax.bar(ind, x, width)

    ax.set_xticks(ind)
    ax.set_xticklabels(x_labels)
    ax.set_title('IPerf')
    ax.set_xlabel('Protocol')
    ax.set_ylabel('bits per second')

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
    if 'Network' in results['results']:
        plot_iperf(results, pdf)
