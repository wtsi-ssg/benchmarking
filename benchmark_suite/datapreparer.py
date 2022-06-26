#!/usr/bin/env python3
import pathlib
import string
import subprocess

import yaml

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

import os.path
import sys
from pathlib import Path

from .utility import Utility

class DataPreparer:

    def get_benchmark_list_settings(self, settings_doc) -> list:
        """ this function gets a list of all programs, programversions, and datasets used by tests in the yml file"""
        settings_list = []
        set_keys = ["program_name", "required_version", "dataset_tag", "dataset_file", "datadir", "mode"]
        for n in range(1, len(settings_doc)) :
            for m in range(0, len(settings_doc[n]['benchmarks'])):
                if settings_doc[n]['benchmarks'][m]['type'] in self.implicit_program_type_benchmarks:
                    program_name = settings_doc[n]['benchmarks'][m]['type']
                else:
                    if 'program' in settings_doc[n]['benchmarks'][m]['settings'].keys():
                        program_name = settings_doc[n]['benchmarks'][m]['settings']['program']
                    else:
                        print("no program setting given")
                        return None

                #get program version
                required_version = settings_doc[n]['benchmarks'][m]['settings']['programversion']
                #It uses a predefined default_version dictionary for each program if default version is mentioned
                if required_version == "default" and program_name in self.default_version.keys():
                    required_version = self.default_version[program_name]

                #get dataset_tag and datadir
                if settings_doc[n]['benchmarks'][m]['type'] in self.data_dependent_type_benchmarks:
                    if 'dataset_tag' in settings_doc[n]['benchmarks'][m]['settings'].keys():
                        dataset_tag = settings_doc[n]['benchmarks'][m]['settings']['dataset_tag']
                    else:
                        print("dataset_tag setting required, none set.")
                        return None
                    if 'datadir' in settings_doc[n]['benchmarks'][m]['settings'].keys():
                        datadir = settings_doc[n]['benchmarks'][m]['settings']['datadir']
                    else:
                        print("datadir setting required, none set.")
                        return None
                    if 'dataset_file' in settings_doc[n]['benchmarks'][m]['settings'].keys():
                        dataset_file = settings_doc[n]['benchmarks'][m]['settings']['dataset_file']
                    else:
                        dataset_file = ""
                else:
                    dataset_tag = None
                    datadir = None
                    dataset_file = None

                #get mode for streams benchmark
                #FIXME: hard coding for specific benchmark
                if program_name == "streams":
                    mode = settings_doc[n]['benchmarks'][m]['settings']['mode']
                else:
                    mode = None

                set_values = [program_name, required_version, dataset_tag, dataset_file, datadir, mode]
                settings_list.append(dict(zip(set_keys, set_values)))

        return settings_list


    def download_and_install_programs(self, settings_list : list, install_dir) -> bool:
        #check and create tools directory if doesn't exist
        os.makedirs(install_dir, exist_ok=True)

        for st in settings_list:
            program_name = st["program_name"]
            required_version = st["required_version"]
            mode = st["mode"]
            name_and_version = program_name+'-v'+required_version
            
            print("Required program name and version: "+name_and_version)
            path_to_program = self.get_path_to_program(program_name, required_version)
            if os.path.exists(path_to_program):
                print("{} is already installed at {}".format(name_and_version, path_to_program))
                continue

            with open(self.base_dir+"/setup/binaryAddresses.txt", "r") as binary_url:
                for line in binary_url:
                    pro_ver, url = line.strip().split(',')

                    if pro_ver == name_and_version:
                        file_name = Path(url).name
                        if not os.path.exists(install_dir+file_name):
                            rc = subprocess.call(["wget -O "+file_name+" "+ url], shell=True, cwd=install_dir)
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

                        # Should we invoke build command?
                        if not program_name in self.build_command:
                            print(f"An entry for the build_commandfor {program_name} was not found. Please update your settings and try again.")
                            sys.exit(1)
                        elif "no_build" in self.build_command[program_name]:
                            pass
                        else:
                            # Invoke build command
                            build_cmd = self.build_command[program_name]['cmd']
                            build_cwd = string.Template(self.build_command[program_name]['cwd']).substitute(install_dir=install_dir, name_and_version=name_and_version)
                            subprocess.check_call([build_cmd], shell=True, cwd=build_cwd)
            if not os.path.exists(path_to_program):
                print(f"Entry for this tool {program_name} is not found in the binaryAddress list. Please update the list and run again!")
                sys.exit(1)

            print("Successfully installed {}.".format(name_and_version))
        return True

    def check_md5sum(self, path, correct_sum):
        md5sumproc = subprocess.Popen(["md5sum "+path], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        out, err = md5sumproc.communicate()
        md5sumcheck = out.split(" ")
        if md5sumcheck[0] == correct_sum:
            return True
        else:
            return False

    def get_file_data(self, list_filename : Path, datadir : Path):
        with open(list_filename, 'r') as data_f:
            for line in data_f:
                required_file_name, correct_md5sum = line.strip().split(',')
                file_name = Path(required_file_name).name

                if os.path.exists(datadir+file_name):
                    if not self.check_md5sum(datadir+file_name, correct_md5sum):
                        if self.verbose:
                            print(f"{required_file_name} is not downloaded correctly. Trying to redownload now...")
                        subprocess.check_call([f"wget {required_file_name} -O {datadir}{file_name}"], shell=True)
                    else:
                        if self.verbose:
                            print(f"{file_name} is already downloaded.")
                else:
                    if self.verbose:
                        print(f"{file_name} is not downloaded. Downloading now...")
                    subprocess.check_call([f"wget {required_file_name} -O {datadir}{file_name}"], shell=True)


    def download_dataset_file(self, settings_dict):
        datadir = settings_dict["datadir"]
        #check and create datasets directory if doesn't exist
        os.makedirs(datadir, exist_ok=True)

        self.get_file_data(settings_dict["dataset_file"], datadir)

        print("Required dataset is downloaded.")

    def download_default_tagged_dataset(self, settings_dict):
        program = settings_dict["program_name"]
        required_version = settings_dict["required_version"]
        dataset_tag = settings_dict["dataset_tag"]
        datadir = settings_dict["datadir"]
        
        #check and create datasets directory if doesn't exist
        os.makedirs(datadir, exist_ok=True)

        #check if dataset_tag is default
        if dataset_tag == "default":
            for ds in self.dataset_required[program]:
                if required_version in self.dataset_required[program][ds]:
                    print("Benchmark is using data_set: {} ".format(ds))
                    index_name = self.dataset_index[ds]

                    #check and create datasets directory if doesn't exist
                    os.makedirs(datadir+index_name, exist_ok=True)
                    os.makedirs(datadir+"SRR10103759", exist_ok=True)

                    self.get_file_data(self.base_dir+"/setup/"+ds+".txt", datadir)

    def get_path_to_program(self, program_name, required_version):
        """get the path to the program"""
        name_and_version = f'{program_name}-v{required_version}'
        if program_name in self.path_to_program_dict.keys():
            path_to_program_template = string.Template(self.path_to_program_dict[program_name])
        else:
            path_to_program_template = string.Template("/")
        iperfvar = "iperf"+required_version[0]
        path_to_program = path_to_program_template.substitute(name_and_version=name_and_version,iperfvar=iperfvar)

        return path_to_program

    def __init__(self, defaults_yml_input_file : pathlib.Path, settings_yml_input_file : pathlib.Path, basedir : pathlib.Path, verbose : bool):
        self.defaults_yml_input_file = defaults_yml_input_file
        self.settings_yml_input_file = settings_yml_input_file
        self.base_dir = basedir
        self.verbose = verbose

        #set a dictionary variable for all programs that do not require a program setting
        self.implicit_program_type_benchmarks=(["iperf",
                                                "iozone",
                                                "streams"])

        #set a dictionary variable for all benchmarks that require data to be downloaded
        self.data_dependent_type_benchmarks=(["multithreaded"])

        self.install_dir = Utility.get_install_dir(settings_yml_input_file)

    def loadDefaults(self, defaults_doc):
        # Set a dictionary to show where executable will be stored
        self.path_to_program_dict = { key:f'{self.install_dir}{value}' for key, value in defaults_doc['path_to_program'].items() }
        #Set a dictionary variable for all the default versions of programs
        self.default_version = defaults_doc['default_version']
        #set a dictionary variable saying which version of the salmon index is required for a given version
        self.dataset_required = defaults_doc['dataset_required']
        # dataset index
        self.dataset_index = defaults_doc['dataset_index']
        # command to build program
        self.build_command = defaults_doc['build_command']

    def prepareData(self) -> bool:
        defaults_doc = yaml.load(open(self.defaults_yml_input_file, 'rb'), Loader=Loader)
        self.loadDefaults(defaults_doc)

        settings_doc = yaml.load(open(self.settings_yml_input_file, 'rb'), Loader=Loader)

        settings_list = self.get_benchmark_list_settings(settings_doc)

        if settings_list is None:
            return False

        #Print the program list if verbose is set
        if self.verbose:
            print("List of programs from yml file :\n{}".format(settings_list))

        self.download_and_install_programs(settings_list, self.install_dir)

        # Download datasets
        for st in settings_list:
            if st["dataset_tag"] == "default":
                self.download_default_tagged_dataset(st)
            if "dataset_file" in st:
                self.download_dataset_file(st)

        return True
