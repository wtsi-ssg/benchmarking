#!/usr/bin/env python3

import sys

from benchmark_suite import benchmarkessentials


class Plugin(benchmarkessentials.BenchmarkPlugin):
    def get_benchmarks(self) -> benchmarkessentials.Benchmark:
        return {"network": Network}

class Network(benchmarkessentials.ParentBenchmark):
    def __init__(self, benchmarks=None, **kwargs):
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
            print("-Running {} benchmark".format(benchmark.get_name()), file=sys.stderr)
            if benchmark.get_name() not in results["benchmarks"]:
                results["benchmarks"][benchmark.get_name()] = [] 
            
            results["benchmarks"][benchmark.get_name()].append(benchmark.run())

        return results

