import decimal
import itertools
import json
import pathlib
import re

import matplotlib.pyplot as plt
import numpy as np
import numpy_indexed as npi
import pandas as pd
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D


class PlotResults:
    JOULES_TO_KILOWATTHOURS = 3600000
    def __init__(self, results_filename : pathlib.Path, compare_filenames :list, plot_filename : pathlib.Path, cost_per_kwh : decimal.Decimal, carbon_per_kwh : decimal.Decimal, override_power : decimal.Decimal, override_tco : decimal.Decimal) -> None:
        self.results_filename = results_filename
        self.compare_filenames = compare_filenames
        self.plot_filename = plot_filename
        self.cost_per_kwh = cost_per_kwh
        self.carbon_per_kwh = carbon_per_kwh
        self.override_power = override_power
        self.override_tco = override_tco

    def get_result_cpu_single_data(main_results, data) -> tuple[list, list, list, list, list, list]:
        return [list(itertools.chain.from_iterable(itertools.repeat(m['threads'], len(m['runs'])) for m in data['results']['configurations'] if m['processes'] == 1)), # thread labels
                list(m['user'] for keyData in data['results']['configurations'] for m in keyData['runs'] if keyData['processes'] == 1),
                list(m['system'] for keyData in data['results']['configurations'] for m in keyData['runs'] if keyData['processes'] == 1),
                list(m['elapsed'] for keyData in data['results']['configurations'] for m in keyData['runs'] if keyData['processes'] == 1),
                list(m['maxrss'] for keyData in data['results']['configurations'] for m in keyData['runs'] if keyData['processes'] == 1),
                list(sum(float(x['value']) for x in m['power'].values()) for keyData in data['results']['configurations'] for m in keyData['runs'] if keyData['processes'] == 1 )]

    def find_matching_reports(report, compare_results):
        for compare_result in compare_results:
            if report in compare_result['results']['CPU']['benchmarks']:
                yield compare_result['nickname'], compare_result['results']['CPU']['benchmarks'][report]

    def get_result_cpu_throughput_data(main_results, data):
        return [list(itertools.chain.from_iterable(itertools.repeat(m['processes'], len(m['runs'])) for m in data['results']['configurations'] if m['processes'] * m['threads'] == main_results['system-info']['cpuinfo']['count'])), # processes
                list(itertools.chain.from_iterable(itertools.repeat(f"{m['processes']}*{m['threads']}", len(m['runs'])) for m in data['results']['configurations'] if m['processes'] * m['threads'] == main_results['system-info']['cpuinfo']['count'])), # process thread labels
                list(m['user'] for keyData in data['results']['configurations'] for m in keyData['runs'] if keyData['processes'] * keyData['threads'] == main_results['system-info']['cpuinfo']['count']),
                list(m['system'] for keyData in data['results']['configurations'] for m in keyData['runs'] if keyData['processes'] * keyData['threads']== main_results['system-info']['cpuinfo']['count']),
                list(m['elapsed'] for keyData in data['results']['configurations'] for m in keyData['runs'] if keyData['processes'] * keyData['threads'] == main_results['system-info']['cpuinfo']['count']),
                list(m['maxrss'] for keyData in data['results']['configurations'] for m in keyData['runs'] if keyData['processes'] * keyData['threads'] == main_results['system-info']['cpuinfo']['count']),
                list(sum(float(x['value']) for x in m['power'].values()) for keyData in data['results']['configurations'] if keyData['processes'] * keyData['threads'] == main_results['system-info']['cpuinfo']['count'] for m in keyData['runs'])]

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

    def kwh_to_co2(self, x):
        return x*float(self.carbon_per_kwh)
    def co2_to_kwh(self, x):
        return x/float(self.carbon_per_kwh)

    def plot_CPU_single_process(self, main_results : dict, compare_results: 'list[dict]', pdf : PdfPages):
        for report, data in main_results['results']['CPU']['benchmarks'].items():
            matchdata = re.match(r'multithreaded_(.*)', report)
            if matchdata is None:
                continue
            for subdata in data:
                tool = f"{subdata['settings']['program']} - {subdata['settings']['programversion']} per {subdata['settings']['units']}"

                x_labels, x_user, x_sys, x_elapsed, x_rss, x_power_per_run = PlotResults.get_result_cpu_single_data(main_results['system-info']['model'], subdata)
                if len(x_labels) == 0:
                    continue
                x_models = np.tile(main_results['nickname'], len(x_labels))
                # bring in results from matching tests in comparison reports
                for model, matching_result in PlotResults.find_matching_reports(main_results, compare_results):
                    # FIXME: may be multiple versions of same program tested in a run in future, fix the [0]
                    m_labels, m_user, m_sys, m_elapsed, m_rss, m_power_per_run = PlotResults.get_result_cpu_single_data(main_results, matching_result[0])
                    x_labels = x_labels + m_labels
                    x_user = x_user + m_user
                    x_sys = x_sys + m_sys
                    x_elapsed = x_elapsed + m_elapsed
                    x_rss = x_rss + m_rss
                    x_power_per_run = x_power_per_run + m_power_per_run
                    m_models = np.tile(model, len(m_labels))
                    x_models = np.hstack([x_models, m_models])

                x_outputs = [1 / (elapsed/3600) for elapsed in x_elapsed]

                a = np.array([x_models,x_labels]).T
                grp_model_pt = npi.group_by(a)

                x_unique, x_user_mean = grp_model_pt.mean(x_user)
                _, x_user_std = grp_model_pt.std(x_user)
                _, x_sys_mean = grp_model_pt.mean(x_sys)
                _, x_sys_std = grp_model_pt.std(x_sys)
                _, x_elapsed_mean = grp_model_pt.mean(x_elapsed)
                _, x_elapsed_std = grp_model_pt.std(x_elapsed)
                _, x_rss_mean = grp_model_pt.mean(x_rss)
                _, x_rss_std = grp_model_pt.std(x_rss)
                _, x_outputs_mean = grp_model_pt.mean(x_outputs)
                _, x_outputs_std = grp_model_pt.std(x_outputs)
                _, x_power_per_run_mean = grp_model_pt.mean(x_power_per_run)
                _, x_power_per_run_std =  grp_model_pt.std(x_power_per_run)
                grp_model = npi.group_by(x_unique[:,0])

                # CPU times plot
                fig, ax = plt.subplots()
                fig.subplots_adjust(bottom=0.2)

                ind = np.arange(len(x_unique))    # the x locations for the groups
                width = 0.20         # the width of the bars

                rects1 = ax.bar(ind, x_user_mean, width, yerr=x_user_std, label='User')
                rects2 = ax.bar(ind, x_sys_mean, width, yerr=x_sys_std, bottom=x_user_mean, label='System')

                ax.set_xticks(ind)
                ax.set_xticklabels(f'{x[1]}' for x in x_unique)
                ax.set_title(f'Single Process CPU time of {tool}')
                ax.set_xlabel('(Threads)\nPlatform', labelpad=15, fontweight='semibold')
                ax.set_ylabel('User-mode + System CPU time (Seconds)', fontweight='semibold')

                x_user_mean_label = [f"{x:.2f}\nSE+- {y:.2f}" for x, y in zip(x_user_mean, x_user_std)]
                x_sys_mean_label = [f"{x:.2f}\nSE+- {y:.2f}" for x, y in zip(x_sys_mean, x_sys_std)]
                ax.bar_label(rects1, labels=x_user_mean_label, label_type='center')
                ax.bar_label(rects2, labels=x_sys_mean_label, label_type='center')

                n_res = grp_model.count
                accum_x = 0
                for i in range(0,len(n_res)):
                    PlotResults.annotate_xrange(accum_x-0.5, accum_x+n_res[i]-0.5, grp_model.unique[i], ax=ax, offset=-0.07, width=-0.05)
                    accum_x = accum_x + n_res[i]

                pdf.savefig(fig)
                plt.close()

    def plot_CPU_throughput(self, main_results : dict, compare_results: 'list[dict]', pdf : PdfPages):
        for report, data in main_results['results']['CPU']['benchmarks'].items():
            matchdata = re.match(r'multithreaded_(.*)', report)
            if matchdata is None:
                continue
            for subdata in data:
                tool = f"{subdata['settings']['program']} - {subdata['settings']['programversion']}"
                units = subdata['settings']['units']

                x_processes, x_labels, x_user, x_sys, x_elapsed, x_rss, x_power_per_run = PlotResults.get_result_cpu_throughput_data(main_results, subdata)
                if len(x_processes) == 0:
                    continue
                x_models = np.tile(main_results['nickname'], len(x_labels))
                # bring in results from matching tests in comparison reports
                for model, matching_result in PlotResults.find_matching_reports(report, compare_results):
                    # FIXME: may be multiple versions of same program tested in a run in future, fix the [0]
                    m_processes, m_labels, m_user, m_sys, m_elapsed, m_rss, m_power_per_run = PlotResults.get_result_cpu_throughput_data(main_results, matching_result[0])
                    x_processes = x_processes + m_processes
                    x_labels = x_labels + m_labels
                    x_user = x_user + m_user
                    x_sys = x_sys + m_sys
                    x_elapsed = x_elapsed + m_elapsed
                    x_rss = x_rss + m_rss
                    x_power_per_run = x_power_per_run + m_power_per_run
                    m_models = np.tile(model, len(m_labels))
                    x_models = np.hstack([x_models, m_models])

                x_outputs = [process / (elapsed/3600) for process, elapsed in zip(x_processes, x_elapsed)]

                a = np.array([x_models,x_labels]).T
                grp_model_pt = npi.group_by(a)

                x_unique, x_user_mean = grp_model_pt.mean(x_user)
                _, x_user_std = grp_model_pt.std(x_user)
                _, x_sys_mean = grp_model_pt.mean(x_sys)
                _, x_sys_std = grp_model_pt.std(x_sys)
                _, x_elapsed_mean = grp_model_pt.mean(x_elapsed)
                _, x_elapsed_std = grp_model_pt.std(x_elapsed)
                _, x_rss_mean = grp_model_pt.mean(x_rss)
                _, x_rss_std = grp_model_pt.std(x_rss)
                _, x_outputs_mean = grp_model_pt.mean(x_outputs)
                _, x_outputs_std = grp_model_pt.std(x_outputs)
                _, x_power_per_run_mean = grp_model_pt.mean(x_power_per_run)
                _, x_power_per_run_std =  grp_model_pt.std(x_power_per_run)
                grp_model = npi.group_by(x_unique[:,0])

                # CPU times plot
                fig, ax = plt.subplots()
                fig.subplots_adjust(bottom=0.2)

                ind = np.arange(len(x_unique))    # the x locations for the groups
                width = 0.20         # the width of the bars

                rects1 = ax.bar(ind, x_user_mean, width, yerr=x_user_std, label='User')
                rects2 = ax.bar(ind, x_sys_mean, width, yerr=x_sys_std, bottom=x_user_mean, label='System')

                ax.set_xticks(ind)
                ax.set_xticklabels(f'{x[1]}' for x in x_unique)
                ax.set_title(f'CPU throughput of {tool} per {units}')
                ax.set_xlabel('(Processes * Threads)\nPlatform', labelpad=15, fontweight='semibold')
                ax.set_ylabel('User-mode + System CPU time (Seconds)', fontweight='semibold')

                x_user_mean_label = [f"{x:.2f}\nSE+- {y:.2f}" for x, y in zip(x_user_mean, x_user_std)]
                x_sys_mean_label = [f"{x:.2f}\nSE+- {y:.2f}" for x, y in zip(x_sys_mean, x_sys_std)]
                ax.bar_label(rects1, labels=x_user_mean_label, label_type='center')
                ax.bar_label(rects2, labels=x_sys_mean_label, label_type='center')

                n_res = grp_model.count
                accum_x = 0
                for i in range(0,len(n_res)):
                    PlotResults.annotate_xrange(accum_x-0.5, accum_x+n_res[i]-0.5, grp_model.unique[i], ax=ax, offset=-0.07, width=-0.05)
                    accum_x = accum_x + n_res[i]

                pdf.savefig(fig)
                plt.close()

                # wall times plot
                fig, ax = plt.subplots()
                fig.subplots_adjust(bottom=0.2)

                ind = np.arange(len(x_elapsed_mean))    # the x locations for the groups
                width = 0.20         # the width of the bars

                rects3 = ax.bar(ind, x_elapsed_mean, width, yerr=x_elapsed_std, label='Elapsed')

                ax.set_xticks(ind)
                ax.set_xticklabels(f'{x[1]}' for x in x_unique)
                ax.set_title(f'Walltime of {tool} per {units}')
                ax.set_xlabel('(Processes * Threads)\nPlatform', labelpad=15, fontweight='semibold')
                ax.set_ylabel('Walltime (Seconds)', fontweight='semibold')

                ax.bar_label(rects3, padding=3)

                n_res = grp_model.count
                accum_x = 0
                for i in range(0,len(n_res)):
                    PlotResults.annotate_xrange(accum_x-0.5, accum_x+n_res[i]-0.5, grp_model.unique[i], ax=ax, offset=-0.07, width=-0.05)
                    accum_x = accum_x + n_res[i]

                pdf.savefig(fig)
                plt.close()

                # RSS plot
                fig, ax = plt.subplots()
                fig.subplots_adjust(bottom=0.2)

                ind = np.arange(len(x_rss_mean))    # the x locations for the groups
                width = 0.20         # the width of the bars

                rects3 = ax.bar(ind, x_rss_mean, width, yerr=x_rss_std, label='Elapsed')

                ax.set_xticks(ind)
                ax.set_xticklabels(f'{x[1]}' for x in x_unique)
                ax.set_title(f'Max RSS of {tool} per {units}')
                ax.set_xlabel('(Processes * Threads)\nPlatform', labelpad=15, fontweight='semibold')
                ax.set_ylabel('Max RSS (kb)', fontweight='semibold')

                ax.bar_label(rects3, padding=3)

                n_res = grp_model.count
                accum_x = 0
                for i in range(0,len(n_res)):
                    PlotResults.annotate_xrange(accum_x-0.5, accum_x+n_res[i]-0.5, grp_model.unique[i], ax=ax, offset=-0.07, width=-0.05)
                    accum_x = accum_x + n_res[i]

                pdf.savefig(fig)
                plt.close()

                # outputs (genomes) per hour plot
                fig, ax = plt.subplots()
                fig.subplots_adjust(bottom=0.2)

                ind = np.arange(len(x_outputs_mean))    # the x locations for the groups
                width = 0.20         # the width of the bars

                rects3 = ax.bar(ind, x_outputs_mean, width, yerr=x_outputs_std, label=f'{units} per hour')

                ax.set_xticks(ind)
                ax.set_xticklabels(f'{x[1]}' for x in x_unique)
                ax.set_title(f'{units} per Hour of {tool}')
                ax.set_xlabel('(Processes * Threads)\nPlatform', labelpad=15, fontweight='semibold')
                ax.set_ylabel(f'{units} per hour', fontweight='semibold')

                ax.bar_label(rects3, padding=3)

                n_res = grp_model.count
                accum_x = 0
                for i in range(0,len(n_res)):
                    PlotResults.annotate_xrange(accum_x-0.5, accum_x+n_res[i]-0.5, grp_model.unique[i], ax=ax, offset=-0.07, width=-0.05)
                    accum_x = accum_x + n_res[i]

                pdf.savefig(fig)
                plt.close()

                # Power per output(run)
                fig, ax = plt.subplots()
                fig.subplots_adjust(bottom=0.2)

                ind = np.arange(len(x_power_per_run_mean))    # the x locations for the groups
                width = 0.20         # the width of the bars

                rects3 = ax.bar(ind, x_power_per_run_mean, width, yerr=x_power_per_run_std, label='Power per Output (kWh)')
                # TODO: make this right hand axis if defined
                if self.carbon_per_kwh:
                    # carbon per run
                    ax2=ax.secondary_yaxis('right', functions=(self.kwh_to_co2, self.co2_to_kwh))
                    ax2.set_ylabel('$CO^2$ per output', fontweight='semibold')
                    #x_outputs_per_kwh = [self.carbon_per_kwh * x_power_per_run_mean in x_outputs] FIXME

                ax.set_xticks(ind)
                ax.set_xticklabels(f'{x[1]}' for x in x_unique)
                ax.set_title(f'Power per {units} of {tool}')
                ax.set_xlabel('(Processes * Threads)\nPlatform', labelpad=15, fontweight='semibold')
                ax.set_ylabel(f'Power per {units} (kWh)', fontweight='semibold')

                ax.bar_label(rects3, padding=3)

                n_res = grp_model.count
                accum_x = 0
                for i in range(0,len(n_res)):
                    PlotResults.annotate_xrange(accum_x-0.5, accum_x+n_res[i]-0.5, grp_model.unique[i], ax=ax, offset=-0.07, width=-0.05)
                    accum_x = accum_x + n_res[i]

                pdf.savefig(fig)
                plt.close()

                #if TCO
                    # TCO over 5 years di
                    # x_outputs_per_cost = [tco / output * 8760 * 5 for output in x_outputs] FIXME
                    #pass

    def plot_MBW(main_results : dict, compare_results: 'list[dict]', pdf : PdfPages):
        for report, data in main_results['results']['CPU']['benchmarks'].items():
            if not re.match('mbw', report):
                continue

            x_bandwidth = list(float(x['copy'].split(' ')[0]) for x in data[0]['results'] if x['method'] == 'MEMCPY')
            x_models = np.tile(main_results['nickname'], len(x_bandwidth))

            for model, matching_result in PlotResults.find_matching_reports(report, compare_results):
                m_user = list(float(x['copy'].split(' ')[0]) for x in matching_result[0]['results'] if x['method'] == 'MEMCPY')
                m_models = np.tile(model, len(m_user))
                x_bandwidth = x_bandwidth + m_user
                x_models = np.hstack([x_models, m_models])

            a = np.array(x_models)
            grp_model_pt = npi.group_by(a)

            x_unique, x_bandwidth_mean = grp_model_pt.mean(x_bandwidth)
            _, x_bandwidth_std = grp_model_pt.std(x_bandwidth)

            # plot
            fig, ax = plt.subplots()

            ind = np.arange(len(x_bandwidth_mean))    # the x locations for the groups

            rects1 = ax.bar(ind, x_bandwidth_mean, yerr=x_bandwidth_std, width=0.4)

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

    def plot_results(self):
        self.results = json.load(open(self.results_filename))
        self.comparison_results=[]
        if self.compare_filenames:
            for compare_filename in self.compare_filenames:
                self.comparison_results.append(json.load(open(compare_filename)))

        # Set plot style sheet
        plt.style.use('ggplot')

        # Begin plot
        with PdfPages(str(self.plot_filename), metadata={'Creator': 'Genomics Benchmark', 'Title': f"Benchmarking results for {self.results['system-info']['model']}\n{self.results['date']}"}) as pdf:
            PlotResults.plot_title(self.results, pdf)
            if 'CPU' in self.results['results']:
                self.plot_CPU_single_process(self.results, self.comparison_results, pdf)
                self.plot_CPU_throughput(self.results, self.comparison_results, pdf)
                PlotResults.plot_MBW(self.results, self.comparison_results, pdf)
            if 'Disk' in self.results['results']:
                PlotResults.plot_disk(self.results, pdf)
            if 'Network' in self.results['results']:
                PlotResults.plot_iperf(self.results, pdf)
