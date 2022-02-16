#!/usr/bin/env python3

import os
import shlex
import subprocess
import shutil
import sys
import time
from cpuinfo import get_cpu_info
from benchmark_suite import benchmarkessentials
import os.path
from os import path


class Plugin(benchmarkessentials.BenchmarkPlugin):
    def get_benchmarks(self):
        return {"command": TimedCommand}

class TimedCommand(benchmarkessentials.Benchmark):
    def __init__(self, command, install_dir, tag=None, shell=False, datadir=None, dataset_file=None, result_dir=None, clear_caches=False, repeats=1, program=None, programversion=None, dataset_tag=None, step=None, threads=None, process_thread=None, **kwargs): 
        super.__init__(self, **kwargs)
        self.program = program
        self.programversion = programversion
        self.install_dir = install_dir
        self.threads = threads

        if self.program == "bwa":
            self.install_path = self.install_dir+self.program+"-v"+programversion+"/"
        elif self.program == "salmon":
            self.install_path = self.install_dir+"/salmon-v"+self.programversion+"/bin/"
        
        
        self.execution_string = os.path.abspath(os.path.expanduser(command))
        self.tag = tag if tag else os.path.basename(shlex.split(self.execution_string)[0]) 
        self.time_names = ["user", "system", "elapsed"] 
        self.original_datadir = os.path.abspath(os.path.expanduser(datadir)) if datadir else None
        self.dataset_file = dataset_file
        self.result_dir = result_dir
        self.shell = shell
        self.clear_caches = clear_caches
        self.repeats = repeats

    def get_name(self):
        return "timedcommand_{tag}".format(tag=self.tag)

    def run(self):
        results = {"program": self.program,
                   "programversion": self.programversion,
                   "runs":[],
                   "average":{}}

        resulted_data_dir, resulted_time_dir = self.create_result_dirs(self.get_name())

        for repeat in range(1, self.repeats+1):
            runresult = {}

            if self.clear_caches:
                print("--Clearing cache", file=sys.stderr)
                self.suite.clear_cache()

            print("--Running command {0} (run {1} of {2})".format(self.tag, repeat, self.repeats), file=sys.stderr)
            
            with subprocess.Popen([self.execution_string+" "+get_cpu_info()["arch"]+" "+str(self.original_datadir)+" "+str(repeat)+" "+self.install_path+" "+resulted_data_dir+" "+resulted_time_dir], shell=True, stdout=subprocess.PIPE, universal_newlines=True) as process:
                    stdout, _ = process.communicate()
                    usr_sys_elp_list = stdout.strip().split(" ")
                    if len(usr_sys_elp_list) == 3:
                        runresult["user"], runresult["system"], runresult["elapsed"] = list(map(float, usr_sys_elp_list))

            results["runs"].append(runresult)
        
        results["average"] = self.generate_averages(results["runs"])

        return results

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

