#!/usr/bin/env python3

import abc
import yapsy.IPlugin

class BenchmarkPlugin(abc.ABC, yapsy.IPlugin.IPlugin):
    @abc.abstractmethod
    def get_benchmarks(self) -> dict:
        pass
# NOTE: setting up benchmark class, and setting ABCMeta as its metaclass. throughout, abstractmethod is used before functions to ensure that the functions are overwritten when an object of class benchmark is created. (such that code in get_name() would have to actually return something, rather than just pass when an object of class benchmark is made)
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
