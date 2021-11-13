#!/usr/bin/env python3

import sys
import numa
import benchmarkessentials

class Plugin(benchmarkessentials.BenchmarkPlugin):
    def get_benchmarks(self):
        return {"cpu": CPU}

class CPU(benchmarkessentials.ParentBenchmark):
    def __init__(self, benchmarks=None):
        self.benchmarks = benchmarks if benchmarks else []

    def get_name(self):
        return "CPU"

    def add_benchmark(self, benchmark):
        self.benchmarks.append(benchmark)
        return self

    def run(self):
        """
        numa_topology = []
        number_of_nodes = numa.get_max_node() + 1
        print("-Number of nodes:", number_of_nodes)
        for node in range(number_of_nodes):
            print("-Node id: {0}\n--cpus: {1}".format(node, numa.node_to_cpus(node)), file=sys.stderr)
            numa_topology.append(list(numa.node_to_cpus(node)))

        results = {"NUMAtopology": numa_topology, "benchmarks":{}}
        """
        results = { "benchmarks": {} }

        for benchmark in self.benchmarks:
            numa_topology = self.get_numa_topology(benchmark)
            if len(numa_topology) > 0:
                results["NUMAtopology"] = numa_topology

            if benchmark.get_name() not in results["benchmarks"]:
                results["benchmarks"][benchmark.get_name()] = []
        
            results["benchmarks"][benchmark.get_name()].append(benchmark.run())

        return results

    def get_numa_topology(self, benchmark):
        numa_topology = []
        if benchmark.get_name() in ["multithreaded_bwa", "numactl_bwa"]:
            number_of_nodes = numa.get_max_node() + 1
            print("-Number of nodes:", number_of_nodes)
            for node in range(number_of_nodes):
                print("-Node id: {0}\n--cpus: {1}".format(node, numa.node_to_cpus(node)), file=sys.stderr)
                numa_topology.append(list(numa.node_to_cpus(node)))

        return numa_topology
