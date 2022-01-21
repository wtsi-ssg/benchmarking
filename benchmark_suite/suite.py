#!/usr/bin/env python3

import platform
import sys
import datetime
import cpuinfo

class Suite(object):
    """
    Responsible for running all benchmarks

     - supplies high level system information: host, OS, CPUs, Arch
    """
    def __init__(self, benchmarks=None, install_dir=None):
        self.benchmarks = benchmarks if benchmarks else []
        self.install_dir = install_dir

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


    def add_benchmark(self, benchmark):
        """Add benchmarks to the list of benchmarks"""
        self.benchmarks.append(benchmark)
