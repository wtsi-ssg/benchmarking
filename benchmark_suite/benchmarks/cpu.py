#!/usr/bin/env python3

from benchmark_suite import benchmarkessentials

class Plugin(benchmarkessentials.BenchmarkPlugin):
    def get_benchmarks(self) -> benchmarkessentials.Benchmark:
        return {"cpu": CPU}

class CPU(benchmarkessentials.ParentBenchmark):
    def __init__(self, benchmarks=None,  **kwargs):
        super().__init__(**kwargs)
        self.benchmarks = benchmarks if benchmarks else []

    def get_name(self) -> str:
        return "CPU"

    def add_benchmark(self, benchmark):
        self.benchmarks.append(benchmark)
        return self

    def run(self):
        results = { "benchmarks": {} }

        for benchmark in self.benchmarks:
            if benchmark.get_name() not in results["benchmarks"]:
                results["benchmarks"][benchmark.get_name()] = []
        
            results["benchmarks"][benchmark.get_name()].append(benchmark.run())

        return results
