#!/usr/bin/env python3

"""This module provides a network plugin class for benchmarking."""

import sys

from benchmark_suite import benchmarkessentials


class Plugin(benchmarkessentials.BenchmarkPlugin):
    """Uses abstract plugin class and returns a network plugin class"""
    def get_benchmarks(self) -> benchmarkessentials.Benchmark:
        return {"network": Network}


class Network(benchmarkessentials.ParentBenchmark):
    """Uses abstract ParentBenchmark class and creates a network class"""
    def __init__(self, benchmarks=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.benchmarks = benchmarks if benchmarks else []

    def get_name(self) -> str:
        return "Network"

    def add_benchmark(self, benchmark):
        self.benchmarks.append(benchmark)
        return self

    def run(self):
        results = {"benchmarks": {}}
        for benchmark in self.benchmarks:
            print(f"-Running {benchmark.get_name()} benchmark", file=sys.stderr)
            if benchmark.get_name() not in results["benchmarks"]:
                results["benchmarks"][benchmark.get_name()] = []

            results["benchmarks"][benchmark.get_name()].append(benchmark.run())

        return results
