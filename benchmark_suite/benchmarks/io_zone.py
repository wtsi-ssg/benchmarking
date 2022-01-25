#!/usr/bin/env python3

import json
import os
import pathlib
import subprocess
import time

import benchmarkessentials
import pandas as pd


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

    def _parse_iozone_xls(self, iozone_result_file: str):
        import pandas as pd
        results = {
            # Extract "Writer Report"
            'Writer Report' : pd.read_excel(iozone_result_file, engine='xlrd', skiprows=3, header=1, index_col=0, nrows=14, usecols='A:N').convert_dtypes(),
            'Re-writer Report' : pd.read_excel(iozone_result_file, engine='xlrd', skiprows=19, header=1, index_col=0, nrows=14, usecols='A:N').convert_dtypes(),
            'Reader Report' : pd.read_excel(iozone_result_file, engine='xlrd', skiprows=35, header=1, index_col=0, nrows=14, usecols='A:N').convert_dtypes(),
            'Re-reader Report' : pd.read_excel(iozone_result_file, engine='xlrd', skiprows=51, header=1, index_col=0, nrows=14, usecols='A:N').convert_dtypes(),
            'Random Read Report' : pd.read_excel(iozone_result_file, engine='xlrd', skiprows=67, header=1, index_col=0, nrows=14, usecols='A:N').convert_dtypes(),
            'Random Write Report' : pd.read_excel(iozone_result_file, engine='xlrd', skiprows=83, header=1, index_col=0, nrows=14, usecols='A:N').convert_dtypes(),
            'Backward Read Report' : pd.read_excel(iozone_result_file, engine='xlrd', skiprows=99, header=1, index_col=0, nrows=14, usecols='A:N').convert_dtypes(),
            'Record Rewrite Report' : pd.read_excel(iozone_result_file, engine='xlrd', skiprows=115, header=1, index_col=0, nrows=14, usecols='A:N').convert_dtypes(),
            'Stride Read Report' : pd.read_excel(iozone_result_file, engine='xlrd', skiprows=131, header=1, index_col=0, nrows=14, usecols='A:N').convert_dtypes(),
            'Fwrite Report' : pd.read_excel(iozone_result_file, engine='xlrd', skiprows=147, header=1, index_col=0, nrows=14, usecols='A:N').convert_dtypes(),
            'Re-fwrite Report' : pd.read_excel(iozone_result_file, engine='xlrd', skiprows=163, header=1, index_col=0, nrows=14, usecols='A:N').convert_dtypes(),
            'Fread Report' : pd.read_excel(iozone_result_file, engine='xlrd', skiprows=179, header=1, index_col=0, nrows=14, usecols='A:N').convert_dtypes(),
            'Re-fread Report' : pd.read_excel(iozone_result_file, engine='xlrd', skiprows=195, header=1, index_col=0, nrows=14, usecols='A:N').convert_dtypes()
        }
        return results

    def run(self):
        iozone_result_file = self._get_iozone_xls()
        with subprocess.Popen([self.install_path + "/iozone", self.arguments, "-Rb", iozone_result_file], stdout=subprocess.PIPE, universal_newlines=True) as process:
            stdout, _ = process.communicate()

        return {"results": self._parse_iozone_xls(iozone_result_file)} if stdout else {"results": ""}

