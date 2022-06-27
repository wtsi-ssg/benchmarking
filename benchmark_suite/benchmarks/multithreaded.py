#!/usr/bin/env python3

import os
import os.path
import resource
from threading import Thread
import psutil
import shlex
import subprocess
import sys
import tempfile
import time
from string import Template

from benchmark_suite import benchmarkessentials
from cpuinfo import get_cpu_info


class Plugin(benchmarkessentials.BenchmarkPlugin):
    def get_benchmarks(self):
        return {"multithreaded": MultiThread}

class MultiThread(benchmarkessentials.Benchmark):
    def __init__(self, command, install_dir, tag=None, shell=False, datadir=None, dataset_file=None, result_dir=None, clear_caches=False, repeats=1, program=None, programversion=None, dataset_tag=None, step=None, process_thread='1*1', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.program = program
        self.programversion = programversion
        self.install_dir = install_dir

        # TODO: make this more generic
        if self.program == "salmon":
            self.install_path = self.install_dir+self.program+"-v"+self.programversion+"/bin/"
        else: #bwa, etc
            self.install_path = self.install_dir+self.program+"-v"+self.programversion+"/"
        
        self.execution_string = command
        self.tag = tag if tag else os.path.basename(shlex.split(self.execution_string)[0]) 
        self.time_names = ["user", "system", "elapsed"] 
        self.original_datadir = os.path.abspath(os.path.expanduser(datadir)) if datadir else None
        self.dataset_file = dataset_file
        self.result_dir = result_dir
        self.shell = shell
        self.clear_caches = clear_caches
        self.repeats = repeats
        self.process_thread = process_thread.split(',')
        self.settings = {
            "program":program,
            "programversion":programversion,
            "arguments":command
            }

    def get_name(self):
        return "multithreaded_{tag}".format(tag=self.tag)

    def run(self):
        results = {
                   "configurations": []
                  }

        resulted_sam_dir, resulted_time_dir = self.create_result_dirs(self.get_name())

        for pt in self.process_thread:
            if self.clear_caches:
                print("--Clearing cache", file=sys.stderr)
                self.suite.clear_cache()

            ps, th = list(map(str, pt.split("*")))
            if th == "N":
                th = str(get_cpu_info()["count"])

            configuration = { "processes" : int(ps),
                        "threads" : int(th),
                        "runs" : []
                        }

            for repeat in range(1, self.repeats+1):
                print("-Running {tag} multithreaded numa interleaved: process={}, thread={}, run {repeat} of {repeats}".format(ps, th, tag=self.tag, repeat=repeat, repeats=self.repeats), file=sys.stderr)

                runresult = {}

                execstring = Template(self.execution_string)
                #  +" "+get_cpu_info()["arch"]+" "++""+resulted_time_dir
                processes =[]
                class TailChase(Thread):
                    def __init__(self, pid: int):
                        super(TailChase,self).__init__()
                        self.pid = pid
                    def run(self):
                        self.results = os.wait4(self.pid, 0)
                start_time = time.perf_counter()
                for i in range(1,int(ps)+1):
                    runstring =  execstring.substitute(threads=th, repeatn = str(repeat), install_path=self.install_path, result_path=resulted_sam_dir, input_datapath = self.original_datadir, processn = i) + '"'
                    print(f"runstring is: '{runstring}'")
                    process =  psutil.Popen([runstring], shell=True, universal_newlines=True)
                    t = TailChase(process.pid)
                    t.start()
                    processes.append(t)

                # wait for term
                for x in processes: x.join()
                runresult["elapsed"] = time.perf_counter() - start_time
                runresult["user"] = 0
                runresult["system"] = 0

                for x in processes:
                    runresult["user"] = runresult["user"] + x.results.ru_utime
                    runresult["user"] = runresult["user"] + x.results.ru_utime
                configuration["runs"].append(runresult)
            
            results["configurations"].append(configuration)
            
        return {"settings":self.settings,"results": results}

    def create_result_dirs(self, subdir):
        timestamp = time.strftime("%Y-%m-%d-%H%M%S")
        resulted_data_dir = os.path.join(self.result_dir, subdir, self.tag, timestamp, "data_files", "")
        os.makedirs(resulted_data_dir, exist_ok=True)

        resulted_time_dir = os.path.join(self.result_dir, subdir,  self.tag, timestamp, "time_files", "")
        os.makedirs(resulted_time_dir, exist_ok=True)

        return resulted_data_dir, resulted_time_dir

    def get_time_results_from_file(self, fileout):
        timedict = {}
        with open(fileout, "r") as time_file:
            time_lines = time_file.readlines()
            timelist = [float(n) for n in time_lines[-1].strip().split()]
            timedict = dict(zip(self.time_names, timelist))
        
        return timedict

    def generate_averages(self, time_list):
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


