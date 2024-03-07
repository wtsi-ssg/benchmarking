#!/usr/bin/env python3

"""This module provides a Disk plugin class for benchmarking."""

import datetime
import os
import platform
import sys

from benchmark_suite import benchmarkessentials


class Plugin(benchmarkessentials.BenchmarkPlugin):
    """Uses abstract plugin class and returns CPU plugin class"""

    def get_benchmarks(self) -> benchmarkessentials.Benchmark:
        return {"disk": Disk}


class Disk(benchmarkessentials.ParentBenchmark):
    """Uses abstract ParentBenchmark class and returns CPU class"""

    def __init__(
        self, benchmarks=None, target_dir=None, install_dir=None, **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.benchmarks = benchmarks if benchmarks else []
        self.target_dir = target_dir if target_dir else "/tmp"
        self.install_dir = install_dir

    def get_name(self) -> str:
        return "Disk"

    def add_benchmark(self, benchmark) -> None:
        """Add benchmarks to the list of benchmarks"""
        self.benchmarks.append(benchmark)

    def run(self) -> None:
        startdir: str = os.getcwd()
        dirpath = (
            self.target_dir
            + "/benchmarking-"
            + platform.node()
            + "-"
            + datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
        )

        os.makedirs(dirpath, exist_ok=True)
        os.chdir(dirpath)

        results = {"benchmarks": {}}

        for benchmark in self.benchmarks:
            print(f"-Running {benchmark.get_name()} benchmark", file=sys.stderr)

            if benchmark.get_name() not in results["benchmarks"]:
                results["benchmarks"][benchmark.get_name()] = []

            results["benchmarks"][benchmark.get_name()].append(benchmark.run())

        os.chdir(startdir)
        return results

    def _find_mount_point(self, path):
        path = os.path.abspath(path)
        while not os.path.ismount(path):
            path = os.path.dirname(path)

        return path
