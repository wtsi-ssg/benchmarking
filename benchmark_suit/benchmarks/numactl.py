#!/usr/bin/env python3

import numa
import itertools
import time
import subprocess
import sys
import os
import benchmarkessentials
import benchmarks.timedcommand as timedcommand

#NOTE: initiate plugin thing as per benchmarkessentials
class Plugin(benchmarkessentials.BenchmarkPlugin):
    def get_benchmarks(self):
        return {"numactl": Numactl}

class Numactl(timedcommand.TimedCommand):
#NOTE: thomas's version of the numa benchmark wanted to run the command on 1, then 2, then 3, then n cpus, when benchmarking a node with hundreds of cpus this will take FOREVER, so I have added an option to select specific numbers of CPUs to run the command on e.g. run command on 1, then 10, then 100. this bit gets these numbers from the yaml file that was read by timedcommand
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        if "step" in kwargs.keys():
            self.step = kwargs['step']
        else:
            self.step = 1
       
        if "threads" in kwargs.keys():
            self.threads = kwargs['threads']
        else:
            self.threads = 1

        self.install_dir = kwargs['install_dir']

    def _roundrobin(self, *iterables):
        "roundrobin('ABC', 'D', 'EF') --> A D E B F C"
        # Recipe credited to George Sakkis
        num_active = len(iterables)
        nexts = itertools.cycle(iter(it).__next__ for it in iterables)
        while num_active:
            try:
                for next in nexts:
                    yield next()
            except StopIteration:
                # Remove the iterator we just exhausted from the cycle.
                num_active -= 1
                nexts = itertools.cycle(itertools.islice(nexts, num_active))

    def interleave(self):
        """
        Generator for cpus in an interleaved (balanced over numa nodes) order
        """
        print("in interleave")
        return list(self._roundrobin(*self.numa_topology))

    def sequential(self):
        print("in seq")
        """Generator for cpus in a sequential (0,1,2...) order"""
        for cpus in self.numa_topology:
            for cpu in cpus:
                yield cpu

    def system(self):
        print("in system")
        """placeholder for system core selection"""
        for cpus in self.numa_topology:
            for cpu in cpus:
                yield cpu

    def get_name(self):
        return "numactl_{tag}".format(tag=self.tag)

    def get_numa_topology(self):
        numa_topology = []
        # NOTE: make a list of all cpus
        for node in range(numa.get_max_node()+1):
            cpus = list(numa.node_to_cpus(node))
            numa_topology.append(cpus)
        print("numa_topo", numa_topology)
        return numa_topology
    
    def run(self, install_dir):
        n_cores = os.cpu_count()
        print("n cores ", n_cores)   
        results = {"program": self.program,
                   "program_version": self.programversion,
                   "core_scaling_runs": []}
        
        self.numa_topology = self.get_numa_topology()
        core_scaling_runresult = {}
        
        for cores in range(1, n_cores+1, self.step):
            print("COREEEEEES: ", cores)
            core_scaling_runresult["{0} cores".format(cores)] = {}
            for ordering in self.interleave, self.sequential, self.system:
                core_scaling_runresult["{0} cores".format(cores)][ordering.__name__] = {}
                core_scaling_runresult["{0} cores".format(cores)][ordering.__name__]["average"] = 0
                final_cpu_set = list(ordering())[:cores]
                repeat_number = 0 
                
                for repeat in range(self.repeats):
                    print("THIS IS REPEAT:" , repeat)
                    repeat_number += 1
                    run_result=self.core_scaling(final_cpu_set, ordering)
                    if not run_result == "null":
                        core_scaling_runresult["{0} core(s)".format(cores)][ordering.__name__][repeat_number] = run_result
                        core_scaling_runresult["{0} core(s)".format(cores)][ordering.__name__]["average"] += run_result
                    elif run_result == "null":
                        core_scaling_runresult.pop("{0} cores".format(cores))
                        results["core_scaling_runs"].append(core_scaling_runresult)
                        return results
                
                core_scaling_runresult["{0} cores".format(cores)][ordering.__name__]["average"] = core_scaling_runresult["{0} cores".format(cores)][ordering.__name__]["average"]/repeat_number
        results["core_scaling_runs"].append(core_scaling_runresult)

        print("Ac55 R: ", core_scaling_runresult)

        return results

    def core_scaling(self, cpu_list, ordering):
        print("IN CORE SCALING with CPUS: ", cpu_list)
        command = self.execution_string.format(threads=self.threads, data=self.original_datadir)
        jobs = []
        cpus = []
        out_of_ram=False
        print("cpu_list", cpu_list)
        print(command)
        start = time.time()
        for cpu in cpu_list:
            if not ordering.__name__ == "system":
                jobs.append(subprocess.Popen("taskset -c {cpu} {command}".format(cpu=cpu,command=command), shell=True, stdout=sys.stderr, stderr=subprocess.PIPE))
            elif ordering.__name__ == "system":
                jobs.append(subprocess.Popen("{command}".format(command=command), shell=True, stdout=sys.stderr, stderr=subprocess.PIPE))
        
        for job in jobs:
            job.wait()
            _, stderr = job.communicate()
            if job.returncode != 0:
               return "null"
        end = time.time() - start
        
        return end


