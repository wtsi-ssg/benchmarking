#!/usr/bin/env python3

import json
import os
import pathlib
import subprocess
import time

from benchmark_suite import benchmarkessentials
import pandas as pd


class Plugin(benchmarkessentials.BenchmarkPlugin):
    def get_benchmarks(self):
        return {"mbw": MBW}

class MBW(benchmarkessentials.Benchmark):
    def __init__(self, install_dir, arguments="-a", program=None, programversion=None, **kwargs):
        super().__init__(**kwargs)
        self.arguments = arguments
        self.install_path = "{}{}/src/current".format(install_dir, program+"-v"+programversion)

    def get_name(self):
        return "mbw"

    def _parse_mbw_output(self, stdout_text: str):
        lines = stdout_text.splitlines()
        results = ()
        for line in lines:
            splits = line.split('\t')
            if str.isalpha(splits[0]) == True:
                next
            record = { 'iteration' : splits[0],
                'method' : splits[2],
                'elapsed' : splits[4],
                'MiB' : splits[6],
                'copy' : splits[8]
            }
            results.append(record)
        return results

    def run(self):
        with subprocess.Popen([self.install_path + "/mbw", "-q"+self.arguments], stdout=subprocess.PIPE, universal_newlines=True) as process:
            stdout, _ = process.communicate()
            results = self._parse_mbw_output(stdout)

        return {"results": results} if stdout else {"results": ""}

