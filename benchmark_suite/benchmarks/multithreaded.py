#!/usr/bin/env python3

import ast
import operator as op
import os
import os.path
import pathlib
import shlex
import string
import subprocess
import sys
import threading
import time
from collections.abc import Iterable

from cpuinfo import get_cpu_info

from benchmark_suite import benchmarkessentials
from codecarbon import OfflineEmissionsTracker

# supported operators
operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
             ast.USub: op.neg}

def eval_expr(expr : str):
    """
    >>> eval_expr('2^6')
    4
    >>> eval_expr('2**6')
    64
    >>> eval_expr('1 + 2*3**(4^5) / (6 + -7)')
    -5.0
    """
    return eval_(ast.parse(expr, mode='eval').body)

def eval_(node):
    if isinstance(node, ast.Num): # <number>
        return node.n
    elif isinstance(node, ast.BinOp): # <left> <operator> <right>
        return operators[type(node.op)](eval_(node.left), eval_(node.right))
    elif isinstance(node, ast.UnaryOp): # <operator> <operand> e.g., -1
        return operators[type(node.op)](eval_(node.operand))
    elif isinstance(node, ast.Call) and node.func.id == 'range':
        begin = int(eval_(node.args[0])) # begin
        end = int(eval_(node.args[1])) # end
        if len(node.args) > 2:
            step = int(eval_(node.args[2])) # step
            return range(begin, end, step)
        else:
            return range(begin, end)
    else:
        raise TypeError(node)

class Plugin(benchmarkessentials.BenchmarkPlugin):
    def get_benchmarks(self) -> benchmarkessentials.Benchmark:
        return {"multithreaded": MultiThread}

class MultiThread(benchmarkessentials.Benchmark):
    def __init__(self, command, install_dir=None, install_path=None, tag=None, shell=False, cwd=None, datadir=None, dataset_file=None, result_dir=None, clear_caches=False, repeats=1, program=None, programversion=None, dataset_tag=None, process_thread=[{"processes":1,"threads":1}], units=None, cpu_affy="system", suite=None, *args, **kwargs):
        super().__init__(suite=suite, *args, **kwargs)
        self.program = program
        self.programversion = programversion
        self.install_dir = install_dir

        if install_path is None:
            # TODO: make this more generic
            if self.program == "salmon":
                self.install_path = self.install_dir+self.program+"-v"+self.programversion+"/bin/"
            else: #bwa, etc
                self.install_path = self.install_dir+self.program+"-v"+self.programversion+"/"
        else:
            self.install_path = install_path
        
        if isinstance(command,str):
            self.execution_string = command
            self.execution_array = shlex.split(command)
        else:
            self.execution_string = ' '.join(command)
            self.execution_array = command
        
        self.tag = tag if tag else os.path.basename(self.execution_array[0])

        self.time_names = ["user", "system", "elapsed"] 
        self.original_datadir = os.path.abspath(os.path.expanduser(datadir)) if datadir else None
        self.dataset_file = dataset_file
        self.result_dir = result_dir
        self.shell = shell
        self.cwd = cwd
        self.clear_caches = clear_caches
        self.repeats = repeats
        self.process_thread = process_thread
        self.settings = {
            "program":program,
            "programversion":programversion,
            "arguments":command,
            "units": units,
            "cpu_affinity": cpu_affy,
            }
        self.cpu_affy = cpu_affy
        if suite.path_to_program_dict:
            self.path_to_program = suite.path_to_program_dict[program]
        else:
            self.path_to_program = pathlib.Path(self.install_dir) / pathlib.Path(self.program+"-v"+self.programversion) / program

    def get_name(self) -> str:
        return "multithreaded_{tag}".format(tag=self.tag)

    def run(self):
        results = {
                   "configurations": []
                  }

        resulted_sam_dir = self.create_result_dirs(self.get_name())
        path_to_program_templated = string.Template(self.path_to_program).substitute(name_and_version=self.program+'-v'+self.programversion)

        for pt in self.process_thread:

            ps_list = eval_expr(string.Template(str(pt["processes"])).substitute(N=str(get_cpu_info()["count"])))
            th_list = eval_expr(string.Template(str(pt["threads"])).substitute(N=str(get_cpu_info()["count"])))
            if not isinstance(ps_list, Iterable):
                ps_list = [ps_list]
            if not isinstance(th_list, Iterable):
                th_list = [th_list]

            # Cross join the lists from processes x threads in a single statement
            for ps in ps_list:
                for th in th_list:
                    ps = int(ps)
                    th = int(th)
                    configuration = { "processes" :ps,
                                "threads" : int(th),
                                "runs" : []
                                }
                    if self.cpu_affy == "interleave":
                        configuration["cpu_affy"] = self.cpu_affy
                        l = [val for tup in zip(*self.suite.numa_topology) for val in tup]
                        cpu_affy_list = [l[i:i + th] for i in range(0, len(l), th)]
                    elif self.cpu_affy == "sequential":
                        configuration["cpu_affy"] = self.cpu_affy
                        l = range(0,len(sum(self.suite.numa_topology, [])), 1)
                        cpu_affy_list = [l[i:i + th] for i in range(0, len(l), th)]
                    else:
                        cpu_affy_list = None

                    for repeat in range(1, self.repeats+1):
                        if self.clear_caches:
                            print("--Clearing cache", file=sys.stderr)
                            self.suite.clear_cache()
                        print("-Running {tag} multithreaded: cpu affinity={}, process={}, thread={}, run {repeat} of {repeats}".format(self.cpu_affy, ps, th, tag=self.tag, repeat=repeat, repeats=self.repeats), file=sys.stderr)

                        runresult = {}

                        #  +" "+get_cpu_info()["arch"]+" "++""+resulted_time_dir
                        # Subclass Thread to collect resource usage
                        class TailChase(threading.Thread):
                            def __init__(self, pid: int):
                                super(TailChase,self).__init__()
                                self.pid = pid
                            def run(self):
                                _, self.exitstatus, self.results = os.wait4(self.pid, 0)
                        # Start wall time counter
                        start_time = time.perf_counter()

                        # Launch CodeCarbon to monitor power consumption
                        tracker = OfflineEmissionsTracker(country_iso_code = "GBR", save_to_file=False, log_level = "warning")
                        tracker.start()

                        # Run the processes to be evaluated
                        processes =[]
                        for i in range(1,int(ps)+1):
                            if self.shell:
                                runparam = string.Template(self.execution_string).substitute(threads=th, repeatn = str(repeat), install_path=self.install_path, result_path=resulted_sam_dir, input_datapath = self.original_datadir, processn = i, path_to_program=path_to_program_templated)
                            else:
                                execstring = [string.Template(x) for x in self.execution_array]
                                runparam = [x.substitute(threads=th, repeatn = str(repeat), install_path=self.install_path, result_path=resulted_sam_dir, input_datapath = self.original_datadir, processn = i, path_to_program=path_to_program_templated) for x in execstring]
                            # print(f"runstring is: '{runstring}'")
                            process =  subprocess.Popen(runparam, shell=self.shell, universal_newlines=True, cwd=self.cwd)
                            if cpu_affy_list is not None:
                                os.sched_setaffinity(process.pid, cpu_affy_list[i-1])
                            t = TailChase(process.pid)
                            t.start()
                            processes.append(t)

                        # wait for all processes to terminate
                        for x in processes: x.join()

                        # monitor power consumption: stop perf monitoring and collect result
                        tracker.stop()
                        power_list = {
                            "cpu_energy" : {"value": tracker.final_emissions_data.cpu_energy, "units": "kWh"},
                            "gpu_energy" : {"value": tracker.final_emissions_data.gpu_energy, "units": "kWh"},
                            "ram_energy" : {"value": tracker.final_emissions_data.ram_energy, "units": "kWh"},
                        }

                        # Total rusage
                        runresult["elapsed"] = time.perf_counter() - start_time
                        runresult["user"] = 0
                        runresult["system"] = 0
                        runresult["maxrss"] = 0
                        runresult["power"] = power_list

                        for x in processes:
                            if os.waitstatus_to_exitcode(x.exitstatus) != 0:
                                print("Non-zero exit code from test")
                                os._exit(1)
                            runresult["user"] = runresult["user"] + x.results.ru_utime
                            runresult["system"] = runresult["system"] + x.results.ru_stime
                            runresult["maxrss"] = runresult["maxrss"] + x.results.ru_maxrss
                        configuration["runs"].append(runresult)
                    results["configurations"].append(configuration)
            
        return {"settings":self.settings,"results": results}

    def create_result_dirs(self, subdir) -> str:
        timestamp = time.strftime("%Y-%m-%d-%H%M%S")
        resulted_data_dir = os.path.join(self.result_dir, subdir, self.tag, timestamp, "data_files", "")
        os.makedirs(resulted_data_dir, exist_ok=True)

        return resulted_data_dir

    def get_time_results_from_file(self, fileout) -> dict:
        timedict = {}
        with open(fileout, "r") as time_file:
            time_lines = time_file.readlines()
            timelist = [float(n) for n in time_lines[-1].strip().split()]
            timedict = dict(zip(self.time_names, timelist))
        
        return timedict

    def generate_averages(self, time_list) -> dict:
        averages = {}
        for timetype in self.time_names:
            averages[timetype] = round(float(sum(d[timetype] for d in time_list)) / len(time_list) ,2)

        return averages

    class ExecutionError(Exception): 
        """Exception that is raised when a command exits with non-zero exit code"""
        def __init__(self, command, return_val):
            message = "Command with tag {0} exited with non-zero exit code: {1}".format(
                command, return_val)
            super().__init__(message)


