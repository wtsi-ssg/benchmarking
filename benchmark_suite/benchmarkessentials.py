#!/usr/bin/env python3

import abc
import json

import yapsy.IPlugin

from .suite import Suite


class BenchmarkPlugin(abc.ABC, yapsy.IPlugin.IPlugin):
    """Abstract class defining an interface for Benchmarks to implement"""
    @abc.abstractmethod
    def get_benchmarks(self) -> dict:
        """Returns a dictionary of benchmark classes"""


class Benchmark(abc.ABC):
    """Abstract class defining an interface for Benchmarks to implement"""
    suite : Suite
    def __init__(self, suite : Suite) -> None:
        super().__init__()
        self.suite = suite

    @abc.abstractmethod
    def run(self) -> "json.serializeable":
        """Returns JSON serializeable results after running the benchmark"""

    @abc.abstractmethod
    def get_name(self) -> str:
        """Return the name of the benchmark"""

class ParentBenchmark(Benchmark):
    """Abstract class defining an interface for Parent Benchmarks to implement"""
    def __init__(self, suite: Suite) -> None:
        super().__init__(suite)

    @abc.abstractmethod
    def add_benchmark(self, benchmark: Benchmark) -> None:
        """Add a benchmark to the list to be run"""
