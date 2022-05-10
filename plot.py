#!/usr/bin/env python3

import argparse
import json
import pathlib
import re
import sys

import matplotlib.pyplot as plt
import matplotlib.transforms as transforms
import numpy as np
import numpy_indexed as npi
import pandas as pd
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle


def yield_processthreadlabels(model:str, data:list):
    for m in data['results']['configurations']:
        for i in range(0, len(m['runs'])):
            yield f"{m['processes']}*{m['threads']}"

def yield_time(data:list, type:str):
    for keyData in data['results']['configurations']:
        for m in keyData['runs']:
            yield m[type]

def find_matching_reports(report, compare_results):
    for compare_result in compare_results:
        if report in compare_result['results']['CPU']['benchmarks']:
            yield compare_result['nickname'], compare_result['results']['CPU']['benchmarks'][report]
 
def get_result_cpu_data(model, data):
    return list(yield_processthreadlabels(model, data)), list(yield_time(data,'user')), list(yield_time(data,'system')), list(yield_time(data,'elapsed'))

#based on: https://github.com/matplotlib/matplotlib/issues/6321#issuecomment-555587961
def annotate_xrange(xmin, xmax,
                    label=None,
                    offset=-0.1,
                    width=-0.1,
                    ax=None,
                    line_kwargs={'color':'black'},
                    text_kwargs={'rotation':'horizontal'}
):
    if ax is None:
        ax = plt.gca()

    # x-coordinates in axis coordinates,
    # y coordinates in data coordinates
    trans = ax.get_xaxis_transform()

    # delimiters at the start and end of the range mimicking ticks
    min_delimiter = Line2D((xmin, xmin), (offset, offset+width), 
                            transform=trans, clip_on=False, **line_kwargs)
    max_delimiter = Line2D((xmax, xmax), (offset, offset+width),
                           transform=trans, clip_on=False, **line_kwargs)
    ax.add_artist(min_delimiter)
    ax.add_artist(max_delimiter)

    # label
    if label:
        x = xmin + 0.5 * (xmax - xmin)
        y = offset + 0.5 * width
        # we need to fix the alignment as otherwise our choice of x
        # and y leads to unexpected results;
        # e.g. 'right' does not align with the minimum_delimiter
        ax.text(x, y, label,
                horizontalalignment='center', verticalalignment='center',
                clip_on=False, transform=trans, **text_kwargs)


def plot_CPU(main_results : dict, compare_results: 'list[dict]', pdf : PdfPages):
    for report, data in main_results['results']['CPU']['benchmarks'].items():
        matchdata = re.match(r'multithreaded_(.*)', report)
        if matchdata is None:
            continue
        tool = matchdata.group(1)

        x_labels, x_user, x_sys, x_elapsed = get_result_cpu_data(results['system-info']['model'], data[0])
        x_models = np.tile(results['nickname'], len(x_labels))
        for model, matching_result in find_matching_reports(report, compare_results):
            m_labels, m_user, m_sys, m_elapsed = get_result_cpu_data(model, matching_result[0])
            x_labels = x_labels + m_labels
            x_user = x_user + m_user
            x_sys = x_sys + m_sys
            x_elapsed = x_elapsed + m_elapsed
            m_models = np.tile(model, len(m_labels))
            x_models = np.hstack([x_models, m_models])

        a = np.array([x_models,x_labels]).T
        grp_model_pt = npi.group_by(a)

        x_unique, x_user_mean = grp_model_pt.mean(x_user)
        _, x_user_std = grp_model_pt.std(x_user)
        _, x_sys_mean = grp_model_pt.mean(x_sys)
        _, x_sys_std = grp_model_pt.std(x_sys)
        _, x_elapsed_mean = grp_model_pt.mean(x_elapsed)
        _, x_elapsed_std = grp_model_pt.std(x_elapsed)
        grp_model = npi.group_by(x_unique[:,0])

        # CPU times plot
        fig, ax = plt.subplots()
        fig.subplots_adjust(bottom=0.2)

        ind = np.arange(len(x_unique))    # the x locations for the groups
        width = 0.20         # the width of the bars

        rects1 = ax.bar(ind+width*-.5, x_user_mean, width, label='User')
        rects1a = ax.errorbar(ind+width*-.5, x_user_mean, yerr=x_user_std, fmt='o', ecolor='black')
        rects2 = ax.bar(ind-width*-.5, x_sys_mean, width, label='System')
        rects2a = ax.errorbar(ind-width*-.5, x_sys_mean, yerr=x_sys_std, fmt='o', ecolor='black')

        ax.set_xticks(ind)
        ax.set_xticklabels(f'{x[1]}' for x in x_unique)
        ax.set_title(f'CPU time of {tool}')
        ax.set_xlabel('(Processes * Threads)\nPlatform', labelpad=15, fontweight='semibold')
        ax.set_ylabel('User-mode + System runtime (Seconds)', fontweight='semibold')

        ax.bar_label(rects1, padding=3)
        ax.bar_label(rects2, padding=3)

        n_res = grp_model.count
        accum_x = 0
        for i in range(0,len(n_res)):
            annotate_xrange(accum_x-0.5, accum_x+n_res[i]-0.5, grp_model.unique[i], ax=ax, offset=-0.07, width=-0.05)
            accum_x = accum_x + n_res[i]

        pdf.savefig(fig)
        plt.close()

        # wall times plot
        fig, ax = plt.subplots()
        fig.subplots_adjust(bottom=0.2)

        ind = np.arange(len(x_elapsed_mean))    # the x locations for the groups
        width = 0.20         # the width of the bars

        rects3 = ax.bar(ind, x_elapsed_mean, width, label='Elapsed')
        rects3a = ax.errorbar(ind, x_elapsed_mean, yerr=x_elapsed_std, fmt='o', ecolor='black')

        ax.set_xticks(ind)
        ax.set_xticklabels(f'{x[1]}' for x in x_unique)
        ax.set_title(f'Walltime of {tool}')
        ax.set_xlabel('(Processes * Threads)\nPlatform', labelpad=15, fontweight='semibold')
        ax.set_ylabel('Walltime (Seconds)', fontweight='semibold')

        ax.bar_label(rects3, padding=3)

        n_res = grp_model.count
        accum_x = 0
        for i in range(0,len(n_res)):
            annotate_xrange(accum_x-0.5, accum_x+n_res[i]-0.5, grp_model.unique[i], ax=ax, offset=-0.07, width=-0.05)
            accum_x = accum_x + n_res[i]

        pdf.savefig(fig)
        plt.close()

def plot_MBW(main_results : dict, compare_results: 'list[dict]', pdf : PdfPages):
    for report, data in main_results['results']['CPU']['benchmarks'].items():
        if not re.match('mbw', report):
            continue

        x_bandwidth = list(float(x['copy'].split(' ')[0]) for x in data[0]['results'] if x['method'] == 'MEMCPY')
        x_models = np.tile(results['nickname'], len(x_bandwidth))

        for model, matching_result in find_matching_reports(report, compare_results):
            m_user = list(float(x['copy'].split(' ')[0]) for x in matching_result[0]['results'] if x['method'] == 'MEMCPY')
            m_models = np.tile(model, len(m_user))
            x_bandwidth = x_bandwidth + m_user
            x_models = np.hstack([x_models, m_models])

        a = np.array(x_models)
        grp_model_pt = npi.group_by(a)

        x_unique, x_bandwidth_mean = grp_model_pt.mean(x_bandwidth)
        _, x_user_std = grp_model_pt.std(x_bandwidth)

        # plot
        fig, ax = plt.subplots()

        ind = np.arange(len(x_bandwidth_mean))    # the x locations for the groups

        rects1 = ax.bar(ind, x_bandwidth_mean, width=0.4)
        rects2 = ax.errorbar(ind, x_bandwidth_mean, yerr=x_user_std, fmt='o')

        ax.set_ylim(bottom=0)
        ax.set_xticks(ind)
        ax.set_xticklabels(x_unique)
        ax.set_title(f'Mean Memory Bandwidth (mbw)')
        ax.set_xlabel('Platform', fontweight='semibold')
        ax.set_ylabel('Bandwidth (MiB/sec)', fontweight='semibold')

        #ax.errorbar_label(rects1, padding=3)

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
        ax.set_xlabel('Transfer size (Kb)', fontweight='semibold')
        ax.set_ylabel('File size (Kb)', fontweight='semibold')
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
    ax.set_xlabel('Protocol', fontweight='semibold')
    ax.set_ylabel('bits per second', fontweight='semibold')

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
parser.add_argument('--compare_file', metavar='compare_file', type=pathlib.Path, nargs='?', action='append',
                    help='')
parser.add_argument('plot_file', metavar='plot_file', type=pathlib.Path, nargs='?',
                    help='file to plot results to', default=sys.stdout)

args = parser.parse_args()

results = json.load(open(args.results_file))
comparison_results=[]
if args.compare_file:
    for arg in args.compare_file:
        comparison_results.append(json.load(open(arg)))

with PdfPages(str(args.plot_file)) as pdf:
    plot_title(results, pdf)
    if 'CPU' in results['results']:
        plot_CPU(results, comparison_results, pdf)
        plot_MBW(results, comparison_results, pdf)
    if 'Disk' in results['results']:
        plot_disk(results, pdf)
    if 'Network' in results['results']:
        plot_iperf(results, pdf)
