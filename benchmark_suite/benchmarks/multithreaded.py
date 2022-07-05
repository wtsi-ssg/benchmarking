#!/usr/bin/env python3

import os
import os.path
import shlex
import signal
import subprocess
import sys
import tempfile
import time
from string import Template
from threading import Thread

from benchmark_suite import benchmarkessentials
from cpuinfo import get_cpu_info


class Plugin(benchmarkessentials.BenchmarkPlugin):
    def get_benchmarks(self) -> benchmarkessentials.Benchmark:
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

    def get_name(self) -> str:
        return "multithreaded_{tag}".format(tag=self.tag)

    def run(self):
        results = {
                   "configurations": []
                  }

        resulted_sam_dir = self.create_result_dirs(self.get_name())

        for pt in self.process_thread:

            ps, th = list(map(str, pt.split("*")))
            if th == "N":
                th = str(get_cpu_info()["count"])

            configuration = { "processes" : int(ps),
                        "threads" : int(th),
                        "runs" : []
                        }

            for repeat in range(1, self.repeats+1):
                if self.clear_caches:
                    print("--Clearing cache", file=sys.stderr)
                    self.suite.clear_cache()
                print("-Running {tag} multithreaded numa interleaved: process={}, thread={}, run {repeat} of {repeats}".format(ps, th, tag=self.tag, repeat=repeat, repeats=self.repeats), file=sys.stderr)

                runresult = {}

                execstring = Template(self.execution_string)
                #  +" "+get_cpu_info()["arch"]+" "++""+resulted_time_dir
                # Subclass Thread to collect resource usage
                class TailChase(Thread):
                    def __init__(self, pid: int):
                        super(TailChase,self).__init__()
                        self.pid = pid
                    def run(self):
                        _, self.exitstatus, self.results = os.wait4(self.pid, 0)
                start_time = time.perf_counter()

                # Launch perf to monitor power consumption
                perftempfd, perftemp = tempfile.mkstemp()

                perfprocess = subprocess.Popen(['/usr/bin/perf', 'stat', '-a', '-e','"power/energy-pkg/","power/energy-ram/"','-x',',', '-o', perftemp])
                # Run the processes to be evaluated
                processes =[]
                for i in range(1,int(ps)+1):
                    runstring =  execstring.substitute(threads=th, repeatn = str(repeat), install_path=self.install_path, result_path=resulted_sam_dir, input_datapath = self.original_datadir, processn = i)
                    # print(f"runstring is: '{runstring}'")
                    process =  subprocess.Popen([runstring], shell=True, universal_newlines=True)
                    t = TailChase(process.pid)
                    t.start()
                    processes.append(t)

                # wait for all processes to terminate
                for x in processes: x.join()

                # monitor power consumption: stop perf monitoring and collect result
                perfprocess.send_signal(signal.SIGINT)
                perfprocess.communicate()

                with os.fdopen(perftempfd, "w+") as perftempfo:
                    power_list = [line.strip().split(",")[0] for line in perftempfo.readlines()]

                    print(f'perf result: {power_list}')

                # Total rusage
                runresult["elapsed"] = time.perf_counter() - start_time
                runresult["user"] = 0
                runresult["system"] = 0
                runresult["maxrss"] = 0

                for x in processes:
                    if os.waitstatus_to_exitcode(x.exitstatus) != 0:
                        print("Non-zero exit code from test")
                        os.abort()
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


