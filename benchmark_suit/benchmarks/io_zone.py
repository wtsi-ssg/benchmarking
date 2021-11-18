#!/usr/bin/env python3

import subprocess
import os
import time
import benchmarkessentials

class Plugin(benchmarkessentials.BenchmarkPlugin):
    def get_benchmarks(self):
        return {"iozone": IOZone}

class IOZone(benchmarkessentials.Benchmark):
    def __init__(self, install_dir, arguments="-a", program=None, programversion=None, result_dir=None):
        self.arguments = arguments
        self.install_path = "{}{}/src/current".format(install_dir, program+"-v"+programversion)
        self.result_dir = result_dir

    def get_name(self):
        return "IOZone"

    def _get_iozone_xls(self):
        timestr = time.strftime("%Y-%m-%d-%H%M%S")
        result_file_path = os.path.join(self.result_dir, self.get_name())
        os.makedirs(result_file_path, exist_ok=True)

        return os.path.join(result_file_path, timestr+"_iozone.xls")

    def run(self):
        iozone_result_file = self._get_iozone_xls()
        with subprocess.Popen([self.install_path + "/iozone", self.arguments, "-Rb", iozone_result_file], stdout=subprocess.PIPE, universal_newlines=True) as process:
            stdout, _ = process.communicate()

        return {"results": iozone_result_file} if stdout else {"results": ""}

