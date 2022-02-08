#!/usr/bin/env python3

import platform
import sys
import datetime
import cpuinfo
import subprocess

class Suite(object):
    """
    Responsible for running all benchmarks

     - supplies high level system information: host, OS, CPUs, Arch
    """
    def __init__(self, benchmarks=None, install_dir=None, clear_cache_bin=None):
        self.benchmarks = benchmarks if benchmarks else []
        self.install_dir = install_dir
        self.clear_cache_bin = clear_cache_bin

    def run(self):
        results = {
                  "date": datetime.datetime.now().strftime("%Y-%m-%d"), 
                  "system-info": self._get_system_info(), 
                  "results": {}
                  }
       
        for benchmark in self.benchmarks:
            print("Running {0} benchmarks".format(benchmark.get_name()), file=sys.stderr)

            results["results"][benchmark.get_name()] = benchmark.run()
        
        return results

    def _get_system_info(self):
        return {  
                  "host":        platform.node(),
                  "OS":          platform.platform(),
                  "model":       cpuinfo.get_cpu_info()['brand_raw'],
                  "arch":        platform.processor()
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
