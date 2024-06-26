# Genomics Benchmarking Suite

The purpose of the Sanger Genomics Benchmarking Suite is to provide a domain specific benchmarking suite which demonstrates the types of compute used in large genomics institutes. Specifically, the focus is on High Throughput Computing, the IO heavy tasks such as mapping and calling of variants which tend to be found in the early stages of genomics compute pipelines and are not well represented by conventional synthetic benchmarks used in High Performance Computing. The suite will be flexible enough to add new and updated tooling which is constantly evolving in this field.

Additionally, it can be used in conjunction with continuous integration systems to benchmark versions of a program, allowing developers to keep track of the impact of their changes on performance.

## **Setup**

### Prior to running this benchmarking suite, please ensure the following steps are taken

1. Install the latest version of docker (documentation at <https://docs.docker.com/get-docker/>)

2. If using singularity, please ensure singularity 3.5.3 or later is installed (documentation at <http://singularity.lbl.gov/install-linux>)

3. A data volume is available to be mounted to the `/data` directory of this container. (Approx volume size: 200 GB)

4. For network specific benchmark (i.e. iperf), an iperf server will need to be set up and be running on an appropriate machine (documentation on <https://iperf.fr/>)

5. All the benchmarks must be run as `root`.

### **Docker Image**

#### Using a pre built docker image

The recommended method for accessing this benchmarking suite is pulling the ISG built docker image directly from the quay.io `quay.io/wsi-ids/genomics_benchmarking:1.1.7.1` as below:

```text
docker pull quay.io/wsi-ids/genomics_benchmarking:1.1.7.1
```

#### Building the docker image locally

Alternatively, this docker image can be built from scratch by cloning this repository, and using docker build command, as below, this option is only applicable to those with access to the sanger internal gitlab site.

```text
git clone https://gitlab.internal.sanger.ac.uk/ISG/benchmarking.git

docker build -f Dockerfile . -t benchmarking:latest
```

### **Singularity Image**

This is necessary for running the container in environment where docker is either not available or is not an approprite approach due to security concerns.

#### Using a pre built singularity image

ISG has built the singularity image for this benchmarking suite which can be found at `/software/isg/benchmarking_suite/singularity_image/benchmarking.simg` location on farm cluster.

#### Building the singularity image from the docker image

Alternatively, this singularity image can be built from the docker image as:

```text
SINGULARITY_NOHTTPS=1 singularity build <NAME_OF_SINGULARITY_IMAGE>.simg docker://wsisci/benchmarking:1.0
```

Or from a local docker images as:

```text
docker run -d -p 5000:5000 --restart=always --name registry registry:2

docker tag <NAME_OF_LOCAL_DOCKER_IMAGE> localhost:5000/<NAME_OF_DOCKER_IMAGE>

docker push localhost:5000/<NAME_OF_DOCKER_IMAGE>

SINGULARITY_NOHTTPS=1 singularity build <NAME_OF_SINGULARITY_IMAGE>.simg docker://localhost:5000/<NAME_OF_DOCKER_IMAGE>
```

## **Benchmarks in docker container**

Currently for this version, all the benchmark configuration files are pre-defined (~/benchmarking/setup/config_files). You just need to pass the type of the benchmark to be run to the `docker run` command and that should be enough.

### Types of benchmarks

- Runnable program
  - `multithreaded` (BWA, Salmon)
- IO test
  - `disk` (iozone)
- Network test
  - `network` (iperf)
- Memory test
  - `mbw`

The respective configuration files are named based on these types, and this is to be passed to `docker run` command. Please refer [Running different benchmarks](## Running different benchmarks) section below for further details about each one.

#### Directory structure in docker container

|                       What                             |                  Path                    |
| ------------------------------------------------------ | ---------------------------------------- |
| Data and tools related files                           | /benchmarking/setup/                     |
| Config files                                           | /benchmarking/setup/config_files/        |
| Bash scripts for bwa, multithreading, salmon commands  | /benchmarking/scripts/                   |
| Benchmarks                                             | /benchmarking/benchmark_suit/benchmarks/ |
| Datasets*                                              | /data/datasets/                          |
| Tools*                                                 | /data/tools/                             |
| Results*                                               | /data/results/                           |

*These directories will be created on-the-go and can be easily accessible from the local machine under `/<mount_point_for_data_volume>` directory.

## **Benchmarks in singularity container**

Similar to docker, singularity container also follows the same format to run the benchmarking suite depending on its type. In addition to that, we need to specify the present working directory (`--pwd`) as "/" in the `singularity run` command.

## **Running different benchmarks**

Benchmarks can be run by passing their type to the `docker run` or `singularity run` commands as:

`docker run -v /<mount_point_for_volume>/:/data quay.io/wsi-ids/genomics_benchmarking:1.1.7.1 <type_of_benchmark> <outputfile.json> <machine nickname>`

or

`singularity run --pwd / -B /<mount_point_for_volume>/:/data benchmarking.simg <type_of_benchmark> <outputfile.json> <machine nickname>`

### Runnable program

#### general settings

```yml
- general_settings:
  install_dir: "/data/tools"
```

The benchmarking suite requires the installation directory for the programs to be set.

#### `multithreaded` (BWA+NUMA)

This benchmark is for running in a multi process-threaded setup, measuring the time taken to run a command on the dataset.

**Please note:** As we'll be clearing the cache between each run, docker must be run in --privileged mode for all the multithreaded related benchmarks.
Eg.

```bash
docker run --privileged -v /<mount_point_for_volume>/:/data quay.io/wsi-ids/genomics_benchmarking:1.1.7.1 multithreaded output.json 'Special machine'
```

Or

```bash
singularity run --pwd / -B /<mount_point_for_volume>/:/data benchmarking.simg multithreaded output.json 'Special machine'
```

Example config:

```yml
- type: cpu
  benchmarks:
    - type: multithreaded 
      settings:
        tag: bwa
        command: "/benchmarking/scripts/numactl_multithreaded.sh"
        program: "bwa"
        programversion: "0.7.17"
        shell: True
        dataset_tag: "bwa"
        dataset_file: "/benchmarking/setup/bwa_data.txt"
        datadir: "/data/datasets/bwa/"
        result_dir: "/data/results/runs/"
        repeats: 2
        process_thread: "1*1,1*N"
        clear_caches: True
```

The above configuration file will run bwa tool with numa, on process_thread configuration of `1*1` (one process, one thread) and `1*N` (one process and N threads). Here `N` is the maximum number of cores available to the system.
Additionally, multiple variations of the process_thread can be used in the same section as: `process_thread: "1*1,1*2,2*1,2*2,4*16,1*N,2*N"` (first entry is for process and second is for thread.)

The test will be run `repeat` number of times and an average will be stored in result file. If `clear_cache` is set to True, it'd clear the system cache between each run.

### IO test

#### `disk` (iozone)

This benchmark uses `iozone` tool that runs the IOzone filesystem benchmark, please see documentaion at <http://www.iozone.org/> for more information.

```bash
docker run -v /<mount_point_for_volume>/:/data quay.io/wsi-ids/genomics_benchmarking:1.1.7.1 disk output.json 'Special machine'
```

Or

```bash
singularity run --pwd / -B /<mount_point_for_volume>/:/data benchmarking.simg disk output.json 'Special machine'
```

Example config:

```yml
---
- type: disk
  settings:
    target_dir: /tmp
  benchmarks:
    - type: iozone
      settings:
        program: "iozone"
        programversion: "3.492"
        arguments: "-a"
        result_dir: "/data/results/runs"

```

Disk type benchmarks require a "target_dir" to be set for files to be input to and output from, default is set to `/tmp`.

`arguments: "-a"` launches iozone in default mode (recommended).

### Network test

#### `network` (iperf)

This benchmarking suite uses iperf exclusively for network benchmarking. To run the iperf benchmark successfully an iperf server must be started. (default port for iperf is 5201). In the `docker run` or `singularity run` command we must pass the iperf server address and port.

```bash
docker run -v /<mount_point_for_volume>/:/data quay.io/wsi-ids/genomics_benchmarking:1.1.7.1 -i <iperf_server_address> -p <iperf_port> network output.json 'Special machine'
```

Or

```bash
singularity run --pwd / -B /<mount_point_for_volume>/:/data benchmarking.simg -i <iperf_server_address> -p <iperf_port> network output.json 'Special machine'
```

Example config:

```yml
---
- type: network
  benchmarks:
    - type: iperf
      settings:
        program: "iperf"
        programversion: "3.1.3"
        server_address: ""
        server_port: ""
        protocol: "UDP"
        time_to_transmit: 60
        parallel_streams: 5
    - type: iperf
      settings:
        program: "iperf"
        programversion: "3.1.3"
        server_address: ""
        server_port: ""
        protocol: "TCP"
        time_to_transmit: 60
        parallel_streams: 5
```

This benchmark tests both `protocol: "UDP"` and `protocol: "TCP"`. The `time_to_transmit` specifies the time in seconds to transmit for and `parallel_streams` specifies the number of parallel client threads to run.

## **Results**

As mentioned above, results for each benchmark is stored in `/data/results/` on docker container i.e. `/<mount_point_for_volume>/results/` directory on local machine under their respective type.

Eg.

```bash
:~$/mnt/data_volume/results# ls 
disk  network  runs  threaded  timed_command
```

This directory will also have a `runs` directory which contains all the intermediate files and output .sam/.quant.sf files for each test run.

Example result file for network test:
<details>
  <summary>network.json</summary>
  
  ```json
  {
     "date":"2021-11-16",
     "system-info":{
        "host":"74004730f202",
        "OS":"Linux-4.15.0-153-generic-x86_64-with-Ubuntu-18.04-bionic",
        "model":"Intel Xeon Processor (Cascadelake)",
        "arch":"x86_64",
        "releasedate":"00-00-00"
     },
     "results":{
        "Network":{
           "benchmarks":{
              "iPerf":[
                 {
                    "program":"iperf",
                    "version":"3.1.3",
                    "server":"172.27.24.70",
                    "port":"5201",
                    "protocol":"UDP",
                    "time_to_transmit":60,
                    "parallel_streams":5,
                    "result_summary":{
                       "sum":{
                          "start":0,
                          "end":60.000361,
                          "seconds":60.000361,
                          "bytes":39321600,
                          "bits_per_second":5242848.458523,
                          "jitter_ms":0.104,
                          "lost_packets":0,
                          "packets":4795,
                          "lost_percent":0
                       },
                       "cpu_utilization_percent":{
                          "host_total":0.292503,
                          "host_user":0.128459,
                          "host_system":0.164047,
                          "remote_total":0.03121,
                          "remote_user":0.031211,
                          "remote_system":0
                       }
                    }
                 },
                 {
                    "program":"iperf",
                    "version":"3.1.3",
                    "server":"172.27.24.70",
                    "port":"5201",
                    "protocol":"TCP",
                    "time_to_transmit":60,
                    "parallel_streams":5,
                    "result_summary":{
                       "sum_sent":{
                          "start":0,
                          "end":60.000568,
                          "seconds":60.000568,
                          "bytes":26518526064,
                          "bits_per_second":3535770000.0,
                          "retransmits":5905
                       },
                       "sum_received":{
                          "start":0,
                          "end":60.000568,
                          "seconds":60.000568,
                          "bytes":26513534808,
                          "bits_per_second":3535104000.0
                       },
                       "cpu_utilization_percent":{
                          "host_total":11.97344,
                          "host_user":0.234955,
                          "host_system":11.73851,
                          "remote_total":14.124608,
                          "remote_user":0.644595,
                          "remote_system":13.480011
                       }
                    }
                 }
              ]
           }
        }
     }
  }
```

</details>

## **TODOs**

1. Add functionality to take user-defined configuration file as an input.
2. CI for building docker & singularity images
