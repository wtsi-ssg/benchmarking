#!/usr/bin/env python3

import abc
import json
from dataclasses import dataclass

import yapsy.IPlugin

from .suite import Suite


class BenchmarkPlugin(abc.ABC, yapsy.IPlugin.IPlugin):
    @abc.abstractmethod
    def get_benchmarks(self) -> dict:
        pass


@dataclass
class Benchmark(abc.ABC):
    suite : Suite
    """Abstract class defining an interface for Benchmarks to implement"""
    @abc.abstractmethod
    def run(self) -> "json.serializeable":
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
