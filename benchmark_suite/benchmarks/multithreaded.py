#!/usr/bin/env python3

import sys
import subprocess
from cpuinfo import get_cpu_info
from collections import Counter
from benchmark_suite import benchmarkessentials
import benchmark_suite.benchmarks.timedcommand as timedcommand

class Plugin(benchmarkessentials.BenchmarkPlugin):
    def get_benchmarks(self):
        return {"multithreaded": MultiThread}

class MultiThread(timedcommand.TimedCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.process_thread = kwargs['process_thread'].split(',')

    def get_name(self):
        return "multithreaded_{tag}".format(tag=self.tag)

    def run(self):
        results = {"program": self.program,
                   "programversion": self.programversion,
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

            pt_key = "p{}.t{}".format(ps,th)
            configuration = { "processes" : int(ps),
                        "threads" : int(th),
                        "runs" : []
                        }

            for repeat in range(1, self.repeats+1):
                print("-Running {tag} multithreaded numa interleaved: process={}, thread={}, run {repeat} of {repeats}".format(ps, th, tag=self.tag, repeat=repeat, repeats=self.repeats), file=sys.stderr)

                runresult = {}

                with subprocess.Popen([self.execution_string+" "+get_cpu_info()["arch"]+" "+self.original_datadir+" "+str(repeat)+" "+self.install_path+" "+ps+" "+th+" "+resulted_sam_dir+" "+resulted_time_dir], shell=True, stdout=subprocess.PIPE, universal_newlines=True) as process:
                    stdout, _ = process.communicate()
                    usr_sys_elp_list = stdout.strip().split(" ")
                    if len(usr_sys_elp_list) == 3:
                        runresult["user"], runresult["system"], runresult["elapsed"] = list(map(float, usr_sys_elp_list))

                configuration["runs"].append(runresult)
            
            results["configurations"].append(configuration)
            
        return results
