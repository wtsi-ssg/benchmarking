#!/usr/bin/env python3

import argparse
import json
import pathlib
import re
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages


def yield_processthreadlabels(model:str, data:list):
    for m in data['results']['configurations']:
        for i in range(0, len(m['runs'])):
            yield f"{i+1}:{m['processes']}*{m['threads']}"

def yield_time(data:list, type:str):
    for keyData in data['results']['configurations']:
        for m in keyData['runs']:
            yield m[type]

def plot_CPU(results : dict, pdf : PdfPages):
    for report, data in results['results']['CPU']['benchmarks'].items():
        matchdata = re.match(r'multithreaded_(.*)', report)
        if matchdata is None:
            continue
        tool = matchdata.group(1)
        x_labels = list(yield_processthreadlabels(results['system-info']['model'],data[0]))
        x_user = list(yield_time(data[0],'user'))
        x_sys = list(yield_time(data[0],'system'))
        x_elapsed = list(yield_time(data[0],'elapsed'))

        # CPU times plot
        fig, ax = plt.subplots()

        ind = np.arange(len(x_user))    # the x locations for the groups
        width = 0.20         # the width of the bars

        rects1 = ax.bar(ind, x_user, width, label='User')
        rects2 = ax.bar(ind, x_sys, width, label='System', bottom=x_user)

        ax.set_xticks(ind)
        ax.set_xticklabels(x_labels)
        ax.set_title(f'CPU time of {tool}')
        ax.set_xlabel('Platform replicate:(Processes * Threads)')
        ax.set_ylabel('User-mode + System runtime (Seconds)')

        ax.bar_label(rects1, padding=3)
        ax.bar_label(rects2, padding=3)

        pdf.savefig(fig)
        plt.close()

        # wall times plot
        fig, ax = plt.subplots()

        ind = np.arange(len(x_user))    # the x locations for the groups
        width = 0.20         # the width of the bars

        rects3 = ax.bar(ind, x_elapsed, width, label='Elapsed')

        ax.set_xticks(ind)
        ax.set_xticklabels(x_labels)
        ax.set_title(f'Walltime of {tool}')
        ax.set_xlabel('Platform (Processes * Threads)')
        ax.set_ylabel('Walltime (Seconds)')

        ax.bar_label(rects3, padding=3)

        pdf.savefig(fig)
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

        pdf.savefig(fig)
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
        sns.heatmap(x, ax=ax, cbar_kws={'label': 'Performance (Kb/sec)'})

        ax.set_xticklabels(x.columns.values)
        ax.set_yticklabels(x.index.values)

        ax.set_title(f'IOZone - {report}')
        ax.set_xlabel('Transfer size (Kb)')
        ax.set_ylabel('File size (Kb)')
        ax.set

        pdf.savefig(fig)
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

    pdf.savefig(fig)
    plt.close()

def plot_title(results : dict, pdf : PdfPages):
    fig = plt.figure() 
    plt.axis('off')
    plt.text(0.5,0.5,f"Benchmarking results for {results['system-info']['model']}\n{results['date']}",ha='center',va='center')
    pdf.savefig(fig)
    plt.close() 

parser = argparse.ArgumentParser(description='Create plot for results file.')
parser.add_argument('results_file', metavar='results_file', type=pathlib.Path, nargs='?',
                    help='results JSON file', default=sys.stdin)
parser.add_argument('plot_file', metavar='plot_file', type=pathlib.Path, nargs='?',
                    help='file to plot results to', default=sys.stdout)

args = parser.parse_args()

results = json.load(open(args.results_file))

with PdfPages(str(args.plot_file)) as pdf:
    plot_title(results, pdf)
    if 'CPU' in results['results']:
        plot_CPU(results, pdf)
        plot_MBW(results, pdf)
    if 'Disk' in results['results']:
        plot_disk(results, pdf)
    if 'Network' in results['results']:
        plot_iperf(results, pdf)
