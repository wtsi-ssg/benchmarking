#!/usr/bin/env python3

import argparse
from cProfile import label
import json
import pathlib
import re
import sys

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

def yield_processthreadlabels(model:str, data:list):
    for m in data['configurations']:
        for i in range(0, len(m['runs'])):
            yield f" p{m['processes']}t{m['threads']}"

def yield_time(data:list, type:str):
    for keyData in data['configurations']:
        for m in keyData['runs']:
            yield m[type]

def plot_CPU(results : dict, pdf : PdfPages):
    for report, data in results['results']['CPU']['benchmarks'].items():
        if not re.match('multithreaded_.*', report):
            continue
        x_labels = list(yield_processthreadlabels(results['system-info']['model'],data[0]))
        x_user = list(yield_time(data[0],'user'))
        x_sys = list(yield_time(data[0],'system'))
        x_elapsed = list(yield_time(data[0],'elapsed'))

        # plot
        fig, ax = plt.subplots()

        ind = np.arange(len(x_user))    # the x locations for the groups
        width = 0.20         # the width of the bars

        rects1 = ax.bar(ind-1.3*width, x_user, width, label='User')
        rects2 = ax.bar(ind, x_sys, width, label='System')
        rects3 = ax.bar(ind+1.3*width, x_elapsed, width, label='Elapsed')

        ax.set_xticks(ind)
        ax.set_xticklabels(x_labels)
        ax.set_title(report)
        ax.set_xlabel('Platform')
        ax.set_ylabel('User-mode runtime (Seconds)')

        ax.bar_label(rects1, padding=3)
        ax.bar_label(rects2, padding=3)
        ax.bar_label(rects3, padding=3)

        pdf.savefig()
        plt.close()

def plot_MBW(results : dict, pdf : PdfPages):
    for report, data in results['results']['CPU']['benchmarks'].items():
        if not re.match('mbw', report):
            continue
        x_user = list(float(x['copy'].split(' ')[0]) for x in data[0]['results'] if x['method'] == 'MEMCPY')

        # plot
        fig, ax = plt.subplots()

        ind = np.arange(len(x_user))    # the x locations for the groups
        width = 0.20         # the width of the bars

        rects1 = ax.bar(ind, x_user, width)

        ax.set_xticks(ind)
        ax.set_title(f'Memory Bandwidth (mbw)')
        ax.set_xlabel('Replicate Number')
        ax.set_ylabel('Bandwidth (MiB/sec)')

        ax.bar_label(rects1, padding=3)

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
        ax = sns.heatmap(x)

        ax.set_xticklabels(x.columns.values)
        ax.set_yticklabels(x.index.values)

        ax.set_title(f'IOZone - {report}')
        ax.set_xlabel('Kb record')
        ax.set_ylabel('Kb file')

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
        plot_MBW(results, pdf)
    if 'Disk' in results['results']:
        plot_disk(results, pdf)
    if 'Network' in results['results']:
        plot_iperf(results, pdf)
