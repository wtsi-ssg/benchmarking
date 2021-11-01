#!/usr/bin/env python3

import sys
import benchmarkessentials

class Plugin(benchmarkessentials.BenchmarkPlugin):
    def get_benchmarks(self):
        return {"network": Network}

class Network(benchmarkessentials.ParentBenchmark):
    def __init__(self, benchmarks=None):
        self.benchmarks = benchmarks if benchmarks else []

    def get_name(self):
        return "Network"

    def add_benchmark(self, benchmark):
        self.benchmarks.append(benchmark)
        return self

    def run(self, install_dir):
        results = {"benchmarks": {}}
        for benchmark in self.benchmarks:
            print("-Running {} benchmark".format(benchmark.get_name()), file=sys.stderr)
            if benchmark.get_name() not in results["benchmarks"]:
                results["benchmarks"][benchmark.get_name()] = [] 
            
            results["benchmarks"][benchmark.get_name()].append(benchmark.run(install_dir))

        return results

