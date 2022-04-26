#!/usr/bin/env python3
import subprocess
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
import argparse
import sys
import os.path
from os import path
from pathlib import Path

from benchmark_suite.utility import Utility

base_dir = os.path.dirname(os.path.realpath(__file__))

def get_args():
    description = "Benchmarking suite for disk, cpu and network benchmarks!"
    verbose_help = "Increase output verbosity"
    yml_file_help = "YML file name"

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        '-v','--verbose', help=verbose_help,
        action="store_true")
    parser.add_argument(
        '-y','--yml_file', help=yml_file_help,
        required=True)

    return parser.parse_args()

def get_settings():
    """ this function gets a list of all programs, programversions, and datasets used by tests in the yml file"""
    settings_list = []
    set_keys = ["program_name", "required_version", "dataset_tag", "dataset_file", "datadir", "mode"]  
    for n in range(1, len(doc)) :
        for m in range(0, len(doc[n]['benchmarks'])):
            if doc[n]['benchmarks'][m]['type'] in implicit_program_type_benchmarks_list:
                program_name = doc[n]['benchmarks'][m]['type']
            else:
                if 'program' in doc[n]['benchmarks'][m]['settings'].keys():
                    program_name = doc[n]['benchmarks'][m]['settings']['program']
                else:
                    print("no program setting given")
                    sys.exit(1)

            #get program version
            required_version = doc[n]['benchmarks'][m]['settings']['programversion']
            #It uses a predefined default_version dictionary for each program if default version is mentioned
            if required_version == "default" and program_name in default_version.keys():
                required_version = default_version[program_name]

            #get dataset_tag and datadir
            if doc[n]['benchmarks'][m]['type'] in data_dependent_type_benchmarks_list:
                if 'dataset_tag' in doc[n]['benchmarks'][m]['settings'].keys():
                    dataset_tag = doc[n]['benchmarks'][m]['settings']['dataset_tag']
                else:
                    print("dataset_tag setting required, none set.")
                    sys.exit(1)
                if 'datadir' in doc[n]['benchmarks'][m]['settings'].keys():
                    datadir = doc[n]['benchmarks'][m]['settings']['datadir']
                else:
                    print("datadir setting required, none set.")
                    sys.exit(1)
                if 'dataset_file' in doc[n]['benchmarks'][m]['settings'].keys():
                    dataset_file = doc[n]['benchmarks'][m]['settings']['dataset_file']
                else:
                    dataset_file = ""
            
            else:
                dataset_tag = None
                datadir = None
                dataset_file = None

            #get mode for streams benchmark
            if program_name == "streams":
                mode = doc[n]['benchmarks'][m]['settings']['mode']
            else:
                mode = None

            set_values = [program_name, required_version, dataset_tag, dataset_file, datadir, mode] 
            settings_list.append(dict(zip(set_keys, set_values)))

    return settings_list


def download_and_install_programs(settings_list, install_dir):
    #check and create tools directory if doesn't exist
    os.makedirs(install_dir, exist_ok=True)

    for st in range(len(settings_list)):
        program_name = settings_list[st]["program_name"]
        required_version = settings_list[st]["required_version"]
        mode = settings_list[st]["mode"]
        name_and_version = program_name+'-v'+required_version
        
        print("Required program name and version: "+name_and_version)
        path_to_program = get_path_to_program(program_name, required_version)
        if path.exists(path_to_program):
            print("{} is already installed at {}".format(name_and_version, path_to_program))
            continue
        
        with open(base_dir+"/setup/binaryAddresses.txt", "r") as binary_url:
            for line in binary_url:
                pro_ver, url = line.strip().split(',')
                 
                if pro_ver == name_and_version:
                    file_name = Path(url).name
                    if not path.exists(install_dir+file_name):
                        rc = subprocess.call(["wget -q -O "+file_name+" "+ url], shell=True, cwd=install_dir)
                    #if the directory to install the program in does not exist, create it
                    os.makedirs(install_dir+name_and_version, exist_ok=True)
                    file_extension = Path(file_name).suffix
                    
                    #if the binary is in .tar or .tar.gz form, extract it using tar
                    if file_extension in [".bz2",".gz",".tar"]:
                        rc = subprocess.call(['tar', '-xf', file_name,'-C',name_and_version,'--strip-components=1'], cwd=install_dir)
                    #if the binary is in the .deb form, use dpkg to extract it 
                    elif file_extension in [".deb"]:
                        rc = subprocess.call(['dpkg', '-x', install_dir+file_name, install_dir+name_and_version], cwd=install_dir)
                    elif file_extension in [".zip"]:
                        rc = subprocess.call(['bsdtar', '-xf', file_name,'-C',name_and_version,'--strip-components=1'], cwd=install_dir)

                    if program_name == "iozone":
                        subprocess.check_call(["make"], shell=True, cwd=install_dir+name_and_version+"/src/current")
                        subprocess.check_call(["make linux"], shell=True, cwd=install_dir+name_and_version+"/src/current")

                    if program_name == "mbw":
                        subprocess.check_call(["make"], shell=True, cwd=install_dir+name_and_version+"/")

                    if program_name == "streams":
                        if mode == "single_processing":
                            subprocess.call("gcc -O stream.c -o stream", shell=True, cwd=install_dir)
                        if mode == "multi_processing":
                            subprocess.call("gcc -fopenmp -D_OPENMP stream.c -o stream", shell=True, cwd=install_dir)

                    if program_name in ["bwa"]:
                        subprocess.check_call(["make CFLAGS='-g -Wall -Wno-unused-function -O3 -march=native'"], shell=True, cwd=install_dir+name_and_version)
                    if program_name in ["bwa-mem2"]:
                        subprocess.check_call(["make arch=native"], shell=True, cwd=install_dir+name_and_version)

        if not path.exists(path_to_program):
            print("Entry for this tool is not found in the binaryAddress list. Please update the list and run again!")
            sys.exit(1)

        print("Successfully installed {}.".format(name_and_version))

def check_md5sum(path, correct_sum):
    md5sumproc = subprocess.Popen(["md5sum "+path], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    out, err = md5sumproc.communicate()
    md5sumcheck = out.split(" ")
    if md5sumcheck[0] == correct_sum:
        return True

    return False

def download_bwa_data(settings_dict):
    datadir = settings_dict["datadir"]
    #check and create datasets directory if doesn't exist
    os.makedirs(datadir, exist_ok=True)

    with open(settings_dict["dataset_file"], 'r') as data_f:
        for line in data_f:
            required_file_name, correct_md5sum = line.strip().split(',')
            file_name = Path(required_file_name).name
            
            if path.exists(datadir+file_name):
                if not check_md5sum(datadir+file_name, correct_md5sum):
                    if args.verbose:
                        print(required_file_name+" is not downloaded correctly. Trying to redownload now...")
                    subprocess.check_call(["wget -q https://it_randd.cog.sanger.ac.uk/"+required_file_name+" -O "+datadir+required_file_name], shell=True)
                else:
                    if args.verbose:
                        print(required_file_name+" is already downloaded.")
            else:
                if args.verbose:
                    print(file_name+" is not downloaded. Downloading now...")
                subprocess.check_call(["wget -q "+required_file_name+" -O "+datadir+file_name], shell=True)

    print("Required dataset is downloaded.")

def download_salmon_data(settings_dict):
    program = settings_dict["program_name"]
    required_version = settings_dict["required_version"]
    dataset_tag = settings_dict["dataset_tag"]
    datadir = settings_dict["datadir"]
    
    #check and create datasets directory if doesn't exist
    os.makedirs(datadir, exist_ok=True)

    #check if dataset_tag is default
    if dataset_tag == "default":
        for ds in dataset_required:
            if required_version in dataset_required[ds]:
                print("Benchmark is using data_set: {} ".format(ds))
                index_name = dataset_index[ds]
        
                #check and create datasets directory if doesn't exist
                os.makedirs(datadir+index_name, exist_ok=True)
                os.makedirs(datadir+"SRR10103759", exist_ok=True)
                
                with open(base_dir+"/setup/"+ds+".txt", 'r') as data_f:
                    for line in data_f:
                        required_file_name, correct_md5sum = line.strip().split(',')
                        
                        if path.exists(datadir+required_file_name):
                            if not check_md5sum(datadir+required_file_name, correct_md5sum):
                                if args.verbose:
                                    print(required_file_name+" is not downloaded correctly. Trying to redownload now...")
                                subprocess.check_call(["wget -q https://cl25-benchmarking.cog.sanger.ac.uk/data/"+required_file_name+" -O "+datadir+required_file_name], shell=True)
                            else:
                                if args.verbose:
                                    print(required_file_name+" is already downloaded.")
                        else:
                            if args.verbose:
                                print(required_file_name+" is not downloaded. Downloading now...")
                            subprocess.check_call(["wget -q https://cl25-benchmarking.cog.sanger.ac.uk/data/"+required_file_name+" -O "+datadir+required_file_name], shell=True)

def get_path_to_program(program_name, required_version):
    """get the path to the program"""
    name_and_version = program_name+"-v"+required_version
    if program_name in path_to_program_dict.keys():
        path_to_program= path_to_program_dict[program_name][0]
    else:
        path_to_program = "/"
    iperfvar = "iperf"+required_version[0]
    path_to_program = path_to_program.replace("name_and_version", name_and_version)
    path_to_program = path_to_program.replace("iperfvar",iperfvar)
    
    return path_to_program

if  __name__ == '__main__':
    #Get arguments
    args = get_args()

    yml_input_file = args.yml_file

    #Set a dictionary variable for all the default versions of programs
    default_version = { "salmon" : "1.0.0",
                        "iozone" : "3.488",
                        "iperf" : "3.1.3" }

    #set a dictionary variable for all programs that do not require a program setting
    implicit_program_type_benchmarks_list=(["iperf",
                                            "iozone",
                                            "streams"])

    #set a dictionary variable for all benchmarks that require data to be downloaded
    data_dependent_type_benchmarks_list=(["numactl",
                                          "command",
                                          "multithreaded"])

    dataset_index = { "index_format_1" : "referenceGenome_index1",
                      "index_format_2" : "referenceGenome_index2",
                      "index_format_3" : "referenceGenome_index3",
                      "index_format_4" : "referenceGenome_index4"
                   }

    #set a dictionary variable saying which version of the salmon index is required ifor a given version
    dataset_required = {}

    dataset_required["index_format_1"] = ["0.3.2", "0.4.0", "0.4.1", "0.4.2", "0.5.0", "0.5.1", "0.6.0", "0.6.1-pre", "0.7.0-pre", "0.7.0", "0.7.1", "0.7.2", "0.8.0", "0.8.1" , "0.8.2", "0.9.0", "0.9.1"]
    dataset_required["index_format_2"] = ["0.10.0", "0.10.1", "0.10.2", "0.11.1", "0.11.2", "0.11.3", "0.12.0-alpha", "0.12.0", "0.13.0"]
    dataset_required["index_format_3"] = ["0.14.0", "0.14.1", "0.14.2", "0.14.2-1", "0.15.0"]
    dataset_required["index_format_4"] = ["0.99.0-beta1", "0.99.0-beta1", "1.0.0", "1.1.0"]

    doc = yaml.load(open(yml_input_file, 'rb'), Loader=Loader)

    settings_list = get_settings()
    
    install_dir = Utility.get_install_dir(yml_input_file)

    path_to_program_dict= {}
    path_to_program_dict["salmon"] = ["{}name_and_version/bin/salmon".format(install_dir)]
    path_to_program_dict["iozone"] = ["{}name_and_version/src/current/iozone".format(install_dir)]
    path_to_program_dict["iperf"] = ["{}name_and_version/usr/bin/iperfvar".format(install_dir)]
    path_to_program_dict["bwa"] = ["{}name_and_version/bwa".format(install_dir)]
    path_to_program_dict["bwa-mem2"] = ["{}name_and_version/bwa-mem2".format(install_dir)]
    path_to_program_dict["streams"] = ["{}name_and_version/stream".format(install_dir)]
    path_to_program_dict["mbw"] = ["{}name_and_version/mbw".format(install_dir)]

    
    #Print the program list if verbose is set
    if args.verbose:
        print("List of programs from yml file :\n{}".format(settings_list))

    download_and_install_programs(settings_list, install_dir)
 
    for st in range(0, len(settings_list)):
        if settings_list[st]["dataset_file"] != "None":
            if settings_list[st]["program_name"] == "salmon":
                download_salmon_data(settings_list[st])
            if settings_list[st]["program_name"] == "bwa":
                download_bwa_data(settings_list[st])
