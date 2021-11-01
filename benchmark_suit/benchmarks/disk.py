#!/usr/bin/env python3

import datetime
import sys
import os
import platform
import benchmarkessentials
import suite

class Plugin(benchmarkessentials.BenchmarkPlugin):
    def get_benchmarks(self):
        return {"disk": Disk}

class Disk(benchmarkessentials.ParentBenchmark):
    """
    Responsible for running all disk benchmarks

     - Ensures benchmarks are run in the correct directory
     - Gets information about the target filesystem
    """

    def __init__(self, benchmarks=None, target_dir=None, fs_name=None, install_dir=None):
        """
        Create a new Disk benchmark

        Arguments:
         - benchmarks: A list of the benchmark objects to be run (optional)
         - target_dir: The directory to target disk benchmarks at, defaults to
                       /tmp
        """
        self.benchmarks = benchmarks if benchmarks else []
        self.target_dir = target_dir if target_dir else "/tmp"
        self.fs_name = fs_name if fs_name else self._find_mount_point(self.target_dir)
    
    def get_name(self):
        return "Disk"
 
    def add_benchmark(self, benchmark):
        """Add benchmarks to the list of benchmarks"""
        self.benchmarks.append(benchmark)

    def run(self, fs_name, install_dir):
        self.fs_name = fs_name
        startdir = os.getcwd()
        dirpath = self.target_dir + "/benchmarking-" + platform.node() + "-" + datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        os.makedirs(dirpath)
        os.chdir(dirpath)
        results = {"filesystem": self.fs_name, "benchmarks": {}}
        for benchmark in self.benchmarks:
            print("-Running {0} benchmark".format(benchmark.get_name()), file=sys.stderr)
            if benchmark.get_name() not in results["benchmarks"]:
                results["benchmarks"][benchmark.get_name()] = []
           
            results["benchmarks"][benchmark.get_name()].append(benchmark.run(install_dir))
            print("--Completed.")

        os.chdir(startdir)
        return results

    def _find_mount_point(self, path):
        path = os.path.abspath(path)
        while not os.path.ismount(path):
            path = os.path.dirname(path)
        return path

