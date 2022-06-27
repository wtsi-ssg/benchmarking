#!/usr/bin/env python3

import json
import subprocess
import sys

from benchmark_suite import benchmarkessentials


class Plugin(benchmarkessentials.BenchmarkPlugin):
    def get_benchmarks(self) -> benchmarkessentials.Benchmark:
        return {"iperf": IPerf}

class IPerf(benchmarkessentials.Benchmark):
    """
    A tcp iperf run over given time to transmit.
    An iperf server is required to be running on the server_{address,port}
    Requires iperf to be in PATH
    """
    def __init__(self, server_address, install_dir, server_port, protocol, time_to_transmit, parallel_streams, program, programversion, **kwargs):
        super().__init__(**kwargs)
        self.server_address = server_address
        self.server_port = str(server_port)
        self.program = program
        self.programversion = programversion
        self.install_dir = install_dir
        self.server_port = server_port
        self.protocol = protocol
        self.time_to_transmit = str(time_to_transmit)
        self.parallel_streams = str(parallel_streams)
        self.settings = {
            "program":program,
            "programversion":programversion,
            "arguments":""
            }


    def get_name(self) -> str:
        return "iPerf"

    def run(self):
        results = {"program": self.program,
                   "version": self.programversion,
                   "server": self.server_address, 
                   "port": self.server_port, 
                   "protocol": self.protocol, 
                   "time_to_transmit": int(self.time_to_transmit), 
                   "parallel_streams": int(self.parallel_streams), 
                   "result_summary": {}}

        print("--Version: {}, Protocol: {}".format(self.programversion, self.protocol))
        command = self.install_dir+"iperf-v"+self.programversion+"/usr/bin/iperf3"
        exe_list = [command, "-c", self.server_address, "-p", self.server_port, "-J", "-t", self.time_to_transmit, "-P", self.parallel_streams]

        if self.protocol == "UDP":
            exe_list += ["-u"]

        with subprocess.Popen(exe_list, stdout=subprocess.PIPE, universal_newlines=True) as process:
            stdout, _ = process.communicate()
            stdout_dict = json.loads(stdout)
            if "error" in stdout_dict:
                print(stdout_dict["error"])
                print("Is your iPerf3 server running?")
                sys.exit()

            run_results = {}
            
            if stdout_dict["end"]:
                if self.protocol == "TCP":
                    run_results["sum_sent"] = stdout_dict["end"]["sum_sent"] if stdout_dict["end"]["sum_sent"] else {}
                    run_results["sum_received"] = stdout_dict["end"]["sum_received"] if stdout_dict["end"]["sum_received"] else {}
                elif self.protocol == "UDP":
                   run_results["sum"] = stdout_dict["end"]["sum"] if stdout_dict["end"]["sum"] else {}
            
                run_results["cpu_utilization_percent"] = stdout_dict["end"]["cpu_utilization_percent"] if stdout_dict["end"]["cpu_utilization_percent"] else {}
            else:
                print("No network data collected. Exiting...")
                sys.exit()
        
        results["result_summary"] = run_results

        return {"settings":self.settings, "results" : results }
