#!/usr/bin/env python3

import subprocess
import os
import time
import benchmarkessentials

class Plugin(benchmarkessentials.BenchmarkPlugin):
    def get_benchmarks(self):
        return {"iozone": IOZone}

class IOZone(benchmarkessentials.Benchmark):
    def __init__(self, install_dir, arguments="-a", bindir=None, program=None, programversion=None):
        self.arguments = arguments
        #self.bindir = os.path.abspath(os.path.expanduser(bindir or os.getcwd()))
        self.bindir = "{}iozone-v3.488/src/current".format(install_dir)

    def get_name(self):
        return "IOZone"

    def _get_iozone_xls(self):
        timestr = time.strftime("%Y%m%d-%H%M%S")

        return timestr+"_"+ self.get_name() + ".xls"

    def run(self, install_dir):
        iozone_result_file = self._get_iozone_xls()
        with subprocess.Popen([self.bindir + "/iozone", self.arguments, "-Rb", iozone_result_file], stdout=subprocess.PIPE, universal_newlines=True) as process:
            stdout, _ = process.communicate()

        return {"results": iozone_result_file} if stdout else {"results": ""}

