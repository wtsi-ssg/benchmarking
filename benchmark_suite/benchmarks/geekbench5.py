#!/usr/bin/env python3

"""This module provides a Geekbench5 plugin class for benchmarking."""

import json
import os
import subprocess
import time

from benchmark_suite import benchmarkessentials


class Plugin(benchmarkessentials.BenchmarkPlugin):
    """Uses abstract plugin class and returns Geekbench5 plugin class"""
    def get_benchmarks(self) -> benchmarkessentials.Benchmark:
        return {"geekbench5": GeekBench5}


class GeekBench5(benchmarkessentials.Benchmark):
    """Uses abstract ParentBenchmark class and returns CPU class"""

    def __init__(
        self,
        *args,
        install_dir,
        program,
        programversion,
        result_dir=None,
        geekbench5_email=None,
        geekbench5_key=None,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.program = program
        self.programversion = programversion
        self.install_dir = install_dir
        self.result_dir = result_dir
        self.geekbench5_email = geekbench5_email
        self.geekbench5_key = geekbench5_key
        self.settings = {
            "program": program,
            "programversion": programversion,
            "arguments": "",
        }

    def get_name(self) -> str:
        return "GeekBench5"

    def _get_geekbench_json(self) -> str:
        timestr = time.strftime("%Y-%m-%d-%H%M%S")
        result_file_path = os.path.join(self.result_dir, self.get_name())
        os.makedirs(result_file_path, exist_ok=True)

        return os.path.join(result_file_path, timestr + "_geekbench.json")

    def run(self):
        results = {
            "program": self.program,
            "version": self.programversion,
            "result_summary": {},
        }

        print(f"--Version: {self.programversion}")

        command = (
            self.install_dir + "geekbench5-v" + self.programversion + "/geekbench5"
        )
        json_out = self._get_geekbench_json()
        unlock_list = [command, "--unlock", self.geekbench5_email, self.geekbench5_key]
        subprocess.run(unlock_list, check=True)
        exe_list = [command, "--no-upload", "--export-json", json_out]

        with subprocess.Popen(
            exe_list, stdout=subprocess.PIPE, universal_newlines=True
        ) as process:
            return_code: int = process.wait()

            if return_code == 0:
                with open(json_out, "r", encoding="utf-8") as file:
                    run_results = json.load(file)
            else:
                run_results = {}

        results["result_summary"] = run_results

        return {"settings": self.settings, "results": results}
