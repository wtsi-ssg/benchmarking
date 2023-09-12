#!/usr/bin/env python3
import pathlib
import string
import subprocess
import tempfile

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

    def get_benchmark_list_settings(self, settings_doc : dict) -> list:
        """ this function gets a list of all programs, programversions, and datasets used by tests in the yml file"""
        settings_list = []
        set_keys = ["program_name", "required_version", "dataset_tag", "dataset_file", "datadir", "mode"]
        for n in range(1, len(settings_doc)) :
            for m in range(0, len(settings_doc[n]['benchmarks'])):
                # Is there a program asssociated with this specific type of benchmark
                if settings_doc[n]['benchmarks'][m]['type'] in self.implicit_program_type_benchmarks:
                    program_name = settings_doc[n]['benchmarks'][m]['type']
                else:
                    if 'program' in settings_doc[n]['benchmarks'][m]['settings'].keys():
                        program_name = settings_doc[n]['benchmarks'][m]['settings']['program']
                    else:
                        continue

                #get program version
                required_version = settings_doc[n]['benchmarks'][m]['settings']['programversion']
                #It uses a predefined default_version dictionary for each program if default version is mentioned
                if required_version == "default" and program_name in self.default_version.keys():
                    required_version = self.default_version[program_name]

                #get dataset_tag and datadir
                if settings_doc[n]['benchmarks'][m]['type'] in self.data_dependent_type_benchmarks:
                    if "dataset_tag" in settings_doc[n]['benchmarks'][m]['settings'].keys():
                        dataset_tag = settings_doc[n]['benchmarks'][m]['settings']['dataset_tag']
                    else:
                        dataset_tag = None
                    if "datadir" in settings_doc[n]['benchmarks'][m]['settings'].keys():
                        datadir = settings_doc[n]['benchmarks'][m]['settings']['datadir']
                    else:
                        print("datadir setting required, none set.")
                        return None
                    if "dataset_file" in settings_doc[n]['benchmarks'][m]['settings'].keys():
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

    def _get_binary_database(self) -> 'dict[str,dict[str,str]]':
        loc_db = {}
        with open(self.base_dir+"/setup/binaryAddresses.txt", "r") as binary_url:
            for line in binary_url:
                try:
                    pro_name, pro_ver, url = line.strip().split(',')
                except:
                    print(f"Line in binary addresses does not have exactly 3 fields: '{line}'")
                    return False
                if pro_name in loc_db:
                    loc_db[pro_name][pro_ver] = url
                else:
                    version = {pro_ver : url}
                    loc_db[pro_name] = version
        return loc_db
    
    def _download_extract(self, build_dir : str, req_program : str, req_program_version :str) -> bool:
        name_and_version = req_program+'-v'+req_program_version
        url = self.prog_binary_loc_db[req_program][req_program_version]
        file_name = Path(url).name
        if req_program in self.prog_binary_loc_db:
            if req_program_version in self.prog_binary_loc_db[req_program]:
                # First download the binary package
                if not os.path.exists(build_dir+file_name):
                    rc = subprocess.call(["wget -O "+file_name+" "+ url], shell=True, cwd=build_dir)
                #if the directory to install the program in does not exist, create it
                os.makedirs(self.install_dir+name_and_version, exist_ok=True)
                file_extension = Path(file_name).suffix

                # Extract it
                rc = 0
                #if the binary is in .tar or .tar.gz form, extract it using tar
                if file_extension in [".bz2",".gz",".tar"]:
                    rc = subprocess.call(['tar', '-xf', file_name,'-C',name_and_version,'--strip-components=1'], cwd=build_dir)
                #if the binary is in the .deb form, use dpkg to extract it
                elif file_extension in [".deb"]:
                    rc = subprocess.call(['dpkg', '-x', build_dir+file_name, build_dir+name_and_version], cwd=build_dir)
                elif file_extension in [".zip"]:
                    rc = subprocess.call(['bsdtar', '-xf', file_name,'-C',name_and_version,'--strip-components=1'], cwd=build_dir)
                if rc != 0:
                    print(f"Extract error for {req_program}.")
                    return False

        return True


    def download_and_install_environment(self, settings_doc : 'list[dict]') -> bool:
        #check and create env directory if doesn't exist
        os.makedirs(self.env_dir, exist_ok=True)

        for n_key, n_value in settings_doc.items():
            for m_key, m_value in n_value['benchmarks'].items:
                # Skip implicit type benchmarks
                if m_value['type'] in self.implicit_program_type_benchmarks:
                    continue
                settings = m_value["settings"]
                if "environment" not in settings:
                    continue
                env_name = settings["name"]
                env_version = settings["version"]
                env_components = settings["components"]

                for component in env_components:
                    with tempfile.TemporaryDirectory() as build_path:
                        req_program = component["program"]
                        req_program_version = component["program_version"]

                        if not self._download_extract(build_path, req_program, req_program_version):
                            return False
                        # Should we invoke build command?
                        if "build_cmd" not in component:
                            print(f"An entry for the build_command for {req_program} was not found. Assuming no_build")
                            break
                        else:
                            # Invoke build command
                            build_cmd = string.Template(component["build_cmd"]).substitute(prefix=self.env_dir)
                            build_cwd = string.Template(component["build_cwd"]).substitute(build_path=build_path, name_and_version=req_program+'-v'+req_program_version)
                            subprocess.check_call([build_cmd], shell=True, cwd=build_cwd)

        return True

    def download_and_install_programs(self, settings_list : 'list[dict]') -> bool:
        #check and create tools directory if doesn't exist
        os.makedirs(self.install_dir, exist_ok=True)

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

            if program_name in self.prog_binary_loc_db:
                if required_version in self.prog_binary_loc_db[program_name]:
                    # First download the binary package
                    url = self.prog_binary_loc_db[program_name][required_version]
                    file_name = Path(url).name
                    if not os.path.exists(self.install_dir+file_name):
                        rc = subprocess.call(["wget -O "+file_name+" "+ url], shell=True, cwd=self.install_dir)
                    #if the directory to install the program in does not exist, create it
                    os.makedirs(self.install_dir+name_and_version, exist_ok=True)
                    file_extension = Path(file_name).suffix

                    # Extract it
                    rc = 0
                    #if the binary is in .tar or .tar.gz form, extract it using tar
                    if file_extension in [".bz2",".gz",".tar"]:
                        rc = subprocess.call(['tar', '-xf', file_name,'-C',name_and_version,'--strip-components=1'], cwd=self.install_dir)
                    #if the binary is in the .deb form, use dpkg to extract it
                    elif file_extension in [".deb"]:
                        rc = subprocess.call(['dpkg', '-x', self.install_dir+file_name, self.install_dir+name_and_version], cwd=self.install_dir)
                    elif file_extension in [".zip"]:
                        rc = subprocess.call(['bsdtar', '-xf', file_name,'-C',name_and_version,'--strip-components=1'], cwd=self.install_dir)
                    if rc != 0:
                        print(f"Extract error for {program_name}.")
                        return False

                    # Should we invoke build command?
                    if not program_name in self.build_command:
                        print(f"An entry for the build_command for {program_name} was not found. Assuming no_build")
                        continue
                    elif "no_build" in self.build_command[program_name]:
                        continue
                    else:
                        # Invoke build command
                        build_cmd = self.build_command[program_name]['cmd']
                        build_cwd = string.Template(self.build_command[program_name]['cwd']).substitute(install_dir=self.install_dir, name_and_version=name_and_version)
                        subprocess.check_call([build_cmd], shell=True, cwd=build_cwd)
                else:
                    print(f"Entry for this tool {program_name} version {required_version} is not found in the binaryAddress list. Please update the list and run again!")
                    return False
            else:
                print(f"Entry for this tool {program_name} is not found in the binaryAddress list. Please update the list and run again!")
                return False
            
            if not os.path.exists(path_to_program):
                print(f"Build or download for tool {program_name} failed!")
                return False

            print("Successfully installed {}.".format(name_and_version))
        return True

    def check_md5sum(self, path : Path, correct_sum):
        md5sumproc = subprocess.Popen(["md5sum "+path.as_posix()], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        out, err = md5sumproc.communicate()
        md5sumcheck = out.split(" ")
        if md5sumcheck[0] == correct_sum:
            return True
        else:
            return False

    def get_file_data(self, list_filename : Path, datadir : Path):
        with open(list_filename, 'r') as data_f:
            for line in data_f:
                input = line.strip().split(',')
                if len(input) == 2:
                    required_file_name, correct_md5sum = input
                    file_name = Path(required_file_name).name
                elif len(input) == 3:
                    required_file_name, correct_md5sum, file_name = input
                    os.makedirs(datadir/Path(file_name).parent, exist_ok=True)
                else:
                    raise Exception("Bad number of fields in dataset list")

                if os.path.exists(datadir/file_name):
                    if not self.check_md5sum(datadir/file_name, correct_md5sum):
                        if self.verbose:
                            print(f"{required_file_name} is not downloaded correctly. Trying to redownload now...")
                        subprocess.check_call([f"wget {required_file_name} -O {datadir/file_name}"], shell=True)
                    else:
                        if self.verbose:
                            print(f"{file_name} is already downloaded.")
                else:
                    if self.verbose:
                        print(f"{file_name} is not downloaded. Downloading now...")
                    subprocess.check_call([f"wget {required_file_name} -O {datadir/file_name}"], shell=True)


    def download_dataset_file(self, settings_dict):
        datadir = pathlib.Path(settings_dict["datadir"])
        #check and create datasets directory if doesn't exist
        os.makedirs(datadir, exist_ok=True)

        if type(settings_dict["dataset_file"]) is dict:
            datadir_dest = datadir / pathlib.Path(settings_dict["dataset_file"]["dest"])
            os.makedirs(datadir_dest, exist_ok=True)
            self.get_file_data(settings_dict["dataset_file"]["file"], datadir/settings_dict["dataset_file"]["dest"])
        else:
            self.get_file_data(settings_dict["dataset_file"], datadir)

        print("Required dataset is downloaded.")

    def download_default_tagged_dataset(self, settings_dict):
        program = settings_dict["program_name"]
        required_version = settings_dict["required_version"]
        dataset_tag = settings_dict["dataset_tag"]
        datadir = pathlib.Path(settings_dict["datadir"])
        
        #check and create datasets directory if doesn't exist
        os.makedirs(datadir, exist_ok=True)

        #check if dataset_tag is default
        if dataset_tag == "default":
            for ds in self.dataset_required[program]:
                if required_version in self.dataset_required[program][ds]:
                    print("Benchmark is using data_set: {} ".format(ds))
                    index_name = pathlib.Path(self.dataset_index[program][ds])

                    #check and create datasets directory if doesn't exist
                    os.makedirs(datadir/index_name, exist_ok=True)
                    os.makedirs(datadir/"SRR10103759", exist_ok=True)

                    self.get_file_data(self.base_dir+"/setup/"+ds+".txt", datadir/index_name)

    def get_path_to_program(self, program_name : str, required_version : str) -> pathlib.Path:
        """get the path to the program"""
        name_and_version = f'{program_name}-v{required_version}'
        if program_name in self.path_to_program_dict.keys():
            path_to_program_template = string.Template(self.path_to_program_dict[program_name])
        else:
            path_to_program_template = string.Template(name_and_version+'/'+program_name)
        iperfvar = "iperf"+required_version[0]
        path_to_program = path_to_program_template.substitute(name_and_version=name_and_version,iperfvar=iperfvar)

        return pathlib.Path(path_to_program)

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
        self.env_dir = Utility.get_env_dir(settings_yml_input_file)

        # read in program database
        self.prog_binary_loc_db = self._get_binary_database()

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

        if not self.download_and_install_programs(settings_list):
            return False

        if not self.download_and_install_environment(settings_doc):
            return False

        # Download datasets
        for st in settings_list:
            if st["dataset_tag"] == "default":
                self.download_default_tagged_dataset(st)
            if "dataset_file" in st and st["dataset_file"] is not None and st["dataset_file"] != '':
                self.download_dataset_file(st)

        return True
