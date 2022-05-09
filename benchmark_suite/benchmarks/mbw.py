#!/usr/bin/env python3

import subprocess

from benchmark_suite import benchmarkessentials


class Plugin(benchmarkessentials.BenchmarkPlugin):
    def get_benchmarks(self):
        return {"mbw": MBW}

class MBW(benchmarkessentials.Benchmark):
    def __init__(self, install_dir, arguments="", program=None, programversion=None, **kwargs):
        super().__init__(**kwargs)
        self.arguments = arguments
        self.install_path = "{}{}/".format(install_dir, program+"-v"+programversion)
        self.settings = {
            "program":program,
            "programversion":programversion,
            "arguments":arguments
            }


    def get_name(self):
        return "mbw"

    def _parse_mbw_output(self, stdout_text: str):
        lines = stdout_text.splitlines()
        results = []
        for line in lines:
            splits = line.split('\t')
            if str.isalpha(splits[0]) == True:
                continue
            record = { 'iteration' : int(splits[0]),
                'method' : splits[1].split(':')[1].strip(),
                'elapsed' : splits[2].split(':')[1].strip(),
                'MiB' : splits[3].split(':')[1].strip(),
                'copy' : splits[4].split(':')[1].strip()
            }
            results.append(record)
        return results

    def run(self):
        with subprocess.Popen([self.install_path + "/mbw", "-q", self.arguments], stdout=subprocess.PIPE, universal_newlines=True) as process:
            stdout, _ = process.communicate()
            results = self._parse_mbw_output(stdout)

        return {"settings":self.settings,"results": results} if stdout else {"settings":self.settings,"results": ""}

