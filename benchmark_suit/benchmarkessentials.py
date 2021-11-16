#!/usr/bin/env python3

import abc
import yapsy.IPlugin

class BenchmarkPlugin(abc.ABC, yapsy.IPlugin.IPlugin):
    @abc.abstractmethod
    def get_benchmarks(self) -> dict:
        pass

class Benchmark(abc.ABC):
    """Abstract class defining an interface for Benchmarks to implement"""
    @abc.abstractmethod
    def run(self) -> "json serializeable":
        """Run the benchmark, return JSON serializeable results"""
        pass

    @abc.abstractmethod
    def get_name(self) -> str:
        """Return the name of the benchmark"""
        pass

class ParentBenchmark(Benchmark):
    @abc.abstractmethod
    def add_benchmark(self, benchmark: Benchmark):
        """Add a benchmark to the list to be run"""
        pass
