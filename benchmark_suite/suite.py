#!/usr/bin/env python3

import datetime
import json
import platform
import subprocess
import sys

import cpuinfo
import numa
import psutil


class Suite(object):
    """
    Responsible for running all benchmarks

     - supplies high level system information: host, OS, CPUs, Arch
    """
    def __init__(self, benchmarks=None, install_dir=None, clear_cache_bin=None, nickname=None, override_power=None, tco=None, path_to_program_dict=None):
        self.benchmarks = benchmarks if benchmarks else []
        self.install_dir = install_dir
        self.clear_cache_bin = clear_cache_bin
        self.nickname = nickname
        self.override_power = override_power
        self.tco = tco
        self.path_to_program_dict = path_to_program_dict

    def run(self):
        results = {
                  "nickname": self.nickname,
                  "tco": self.tco,
                  "power": self.override_power,
                  "date": datetime.datetime.now().strftime("%Y-%m-%d"), 
                  "system-info": self._get_system_info(), 
                  "results": {}
                  }
       
        for benchmark in self.benchmarks:
            print("Running {0} benchmarks".format(benchmark.get_name()), file=sys.stderr)

            results["results"][benchmark.get_name()] = benchmark.run()
        
        return results

    def get_numa_topology(self):
        numa_topology = []
        number_of_nodes = numa.get_max_node() + 1
        print("-Number of nodes:", number_of_nodes)
        try:
            for node in range(number_of_nodes):
                print("-Node id: {0}\n--cpus: {1}".format(node, numa.node_to_cpus(node)), file=sys.stderr)
                numa_topology.append(list(numa.node_to_cpus(node)))
            self.numa_topology = numa_topology
        except RuntimeError:
            pass

        return numa_topology

    def _get_system_info(self):
        return {  
                  "host":               platform.node(),
                  "OS":                 platform.platform(),
                  "model":              cpuinfo.get_cpu_info()['brand_raw'],
                  "arch":               platform.processor(),
                  "cpuinfo":            json.loads(cpuinfo.get_cpu_info_json()),
                  "NUMAtopology":       self.get_numa_topology(),
                  "totalRAM":           psutil.virtual_memory()[0]
                }

    def clear_cache(self):
        subprocess.call("sync")
        if self.clear_cache_bin is None:
            """
            Clear the system VFS cache, running sync first. Must be run as root.
            """
            with open("/proc/sys/vm/drop_caches", "w") as dropcaches:
                dropcaches.write("3")
        else:
            subprocess.call(self.clear_cache_bin)


    def add_benchmark(self, benchmark):
        """Add benchmarks to the list of benchmarks"""
        benchmark.suite = self
        self.benchmarks.append(benchmark)
