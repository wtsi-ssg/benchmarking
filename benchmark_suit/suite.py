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
    def __init__(self, benchmarks=None, release_date=None, install_dir=None, fs_name=None):
        self.benchmarks = benchmarks if benchmarks else []
        self.release_date = release_date
        self.fs_name = fs_name
        self.install_dir = install_dir

    def run(self):
        results = {
                  "date": datetime.datetime.now().strftime("%Y-%m-%d"), 
                  "general_settings": { "release date": self.release_date,
                                        "files system": self.fs_name
                                      },
                  "system-info": self._get_system_info(), 
                  "results": {}
                  }
        
        for benchmark in self.benchmarks:
            print("Running {0} benchmarks".format(benchmark.get_name()), file=sys.stderr)
            
            if benchmark.get_name() == "Disk":
                results["results"][benchmark.get_name()] = benchmark.run(self.fs_name)
            else:
                results["results"][benchmark.get_name()] = benchmark.run()
        
        return results

    def _get_system_info(self):
        return {  
                  "host":        platform.node(),
                  "OS":          platform.platform(),
                  "model":       cpuinfo.get_cpu_info()['brand_raw'],
                  "arch":        platform.processor(),
                  "releasedate": self.release_date
                }


    def add_benchmark(self, benchmark):
        """Add benchmarks to the list of benchmarks"""
        self.benchmarks.append(benchmark)

    def add_general_settings(self, key, value):
        self.general_settings = {}
        self.general_settings[key] = value
        
        if key == 'release_date':
            self.release_date = self.general_settings[key]
        if key == 'file_system':
            self.fs_name= self.general_settings[key]
        if key == 'install_dir':
            self.install_dir= self.general_settings[key]

