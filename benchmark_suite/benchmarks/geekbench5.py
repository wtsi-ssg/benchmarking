#!/usr/bin/env python3

import json
import os
import subprocess
import time

from benchmark_suite import benchmarkessentials


class Plugin(benchmarkessentials.BenchmarkPlugin):
    def get_benchmarks(self) -> benchmarkessentials.Benchmark:
        return {"geekbench5": GeekBench5}

class GeekBench5(benchmarkessentials.Benchmark):
    """
    """
    def __init__(self, install_dir, program, programversion, result_dir=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.program = program
        self.programversion = programversion
        self.install_dir = install_dir
        self.result_dir = result_dir
        self.settings = {
            "program":program,
            "programversion":programversion,
            "arguments":""
            }

    def get_name(self) -> str:
        return "GeekBench5"

    def _get_geekbench_json(self) -> str:
        timestr = time.strftime("%Y-%m-%d-%H%M%S")
        result_file_path = os.path.join(self.result_dir, self.get_name())
        os.makedirs(result_file_path, exist_ok=True)

        return os.path.join(result_file_path, timestr+"_geekbench.json")

    def run(self):
        results = {"program": self.program,
                   "version": self.programversion,
                   "result_summary": {}}

        print("--Version: {}".format(self.programversion))
        command = self.install_dir+"geekbench5-v"+self.programversion+ "/geekbench5"
        json_out = self._get_geekbench_json()
        exe_list = [command, '--no-upload', '--export-json', json_out]

        with subprocess.Popen(exe_list, stdout=subprocess.PIPE, universal_newlines=True) as process:
            return_code = process.wait()
            if return_code == 0:
                run_results = json.load(open(json_out,"r"))
            else:
                run_results = {}
        
        results["result_summary"] = run_results

        return {"settings":self.settings, "results" : results }
