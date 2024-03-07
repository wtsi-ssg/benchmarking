#!/usr/bin/env python3

"""This module provides a MBW plugin class for benchmarking."""

import subprocess

from benchmark_suite import benchmarkessentials


class Plugin(benchmarkessentials.BenchmarkPlugin):
    """Uses abstract plugin class and returns MBW plugin class"""
    def get_benchmarks(self) -> benchmarkessentials.Benchmark:
        return {"mbw": MBW}


class MBW(benchmarkessentials.Benchmark):
    """Uses abstract ParentBenchmark class and returns IOzone class"""
    def __init__(
        self, install_dir, arguments="", program=None, programversion=None, **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.arguments: str = arguments
        self.install_path: str = f"{install_dir}{program}-v{programversion}/"
        self.settings = {
            "program": program,
            "programversion": programversion,
            "arguments": arguments,
        }

    def get_name(self) -> str:
        return "mbw"

    def _parse_mbw_output(self, stdout_text: str):
        lines: list[str] = stdout_text.splitlines()
        results = []
        for line in lines:
            splits: list[str] = line.split("\t")
            if str.isalpha(splits[0]):
                continue
            record = {
                "iteration": int(splits[0]),
                "method": splits[1].split(":")[1].strip(),
                "elapsed": splits[2].split(":")[1].strip(),
                "MiB": splits[3].split(":")[1].strip(),
                "copy": splits[4].split(":")[1].strip(),
            }
            results.append(record)
        return results

    def run(self):
        with subprocess.Popen(
            [self.install_path + "/mbw", "-q", self.arguments],
            stdout=subprocess.PIPE,
            universal_newlines=True,
        ) as process:
            stdout, _ = process.communicate()
            results = self._parse_mbw_output(stdout)

        return (
            {"settings": self.settings, "results": results}
            if stdout
            else {"settings": self.settings, "results": ""}
        )
