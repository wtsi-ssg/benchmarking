#!/usr/bin/env python3
import subprocess
import yaml
import argparse
import sys
import os.path
from os import path

os.chdir("/benchmarking")

def get_args():
    #Parse the input parameters for benchmarking

    description = "Benchmarking suite for disk, cpu and network benchmarks!"
    verbose_help = "Increase output verbosity"
    yml_file_help = "YML file name"

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        '-v','--verbose', help=verbose_help,
        action="store_true")
    parser.add_argument(
        '-yml','--yml_file', help=yml_file_help,
        required=True)

    return parser.parse_args()

def get_install_dir(yml_input_file):
    doc = yaml.load(open(yml_input_file, 'rb'))
    general_settings = doc[0]
    if 'install_dir' in general_settings.keys():
        install_dir = general_settings['install_dir']
    else:
        print("no install_dir set, automatic install failed")
    return install_dir

def get_settings():
    """ this function gets a list of all programs, programversions, and datasets used by tests in the yml file"""

    for n in range(1, len(doc)) :
        for m in range(0, len(doc[n]['benchmarks'])):
            #This nested for loop iterates through each benchmark in each type of test. It checks if benchmark under each type of test has multiple entries.

            #get program names (implicit programs are those that have th program name as the benchmark name - e.g. iperf benchmark, where iperf is the only program that can run the iperf test
            if doc[n]['benchmarks'][m]['type'] in implicit_program_type_benchmarks_list:
                program_name = doc[n]['benchmarks'][m]['type']
            else:
                if 'program' in doc[n]['benchmarks'][m]['settings'].keys():
                    program_name = doc[n]['benchmarks'][m]['settings']['program']
                else:
                    print("no program setting given")
                    exit()

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
                    exit()
                if 'datadir' in doc[n]['benchmarks'][m]['settings'].keys():
                    datadir = doc[n]['benchmarks'][m]['settings']['datadir']
                else:
                    print("datadir setting required, none set.")
                    exit()
            else:
                dataset_tag = None
                datadir = None

            #get mode for streams benchmark
            if program_name == "streams":
                mode = doc[n]['benchmarks'][m]['settings']['mode']
            else:
                mode = None

            #Print the [program, version] pair
            if args.verbose:
                print("Program: {},  Required version: {}, dataset_tag: {}".format(program_name, required_version, dataset_tag))
            settings_list.append([program_name, required_version, dataset_tag, datadir, mode])
    return settings_list


def download_and_install_programs(settings_list, install_dir):
    """ this function checks if salmon is downloaded, and downloads if not, then checks if it is installed and installs if not """
    for n in range(0, len(settings_list)):
    #set up required variables before function
        program_name = settings_list[n][0]
        required_version = settings_list[n][1]
        mode= settings_list[n][4]
        name_and_version = program_name+'-v'+required_version
        print("name and version: "+name_and_version)
        #get url of binary to download
        binary_urls = open("binaryAddresses.txt", "r")
        #check the desired program version is not yet installed
        path_to_program= get_path_to_program(program_name, required_version)
        if path.exists(path_to_program):
            print("already installed")
            continue
        for line in binary_urls:
            line = line.split(',')
            if line[0] == name_and_version:
                binary_url = line[1]
                file_name = binary_url.rsplit('/', 1)[-1]
                file_name = file_name.strip('\n')
                #if there is not already a file of the required name, download it
                if not path.exists(install_dir+file_name):
                    rc = subprocess.call(['wget -q -O '+file_name+' '+ binary_url], shell=True, cwd=install_dir)
                #if the directory to install the program in does not exist, create it
                subprocess.call(["mkdir", "-p", install_dir+name_and_version])
                file_extension = file_name.rsplit('.', 1)[-1]
                #if the binary is in .tar or .tar.gz form, extract it using tar
                if file_extension in ["bz2","gz","tar"]:
                    print(file_extension)
                    rc = subprocess.call(['tar', '-xf', file_name,'-C',name_and_version,'--strip-components=1'], cwd=install_dir)
                #if the binary is in the .deb form, use dpkg to extract it
                elif file_extension in ["deb"]:
                    rc = subprocess.call(['dpkg', '-x', "/data/"+file_name,"/data/"+name_and_version,], cwd=install_dir)
                #at the moment iozone is not a binary download, so needs compiling
                #TODO: get binary download for iozone
                if program_name == "iozone":
                    subprocess.check_call(["make"], shell=True, cwd=install_dir+name_and_version+"/src/current")
                    subprocess.check_call(["make linux"], shell=True, cwd=install_dir+name_and_version+"/src/current")
                if program_name == "streams":
                    if mode == "single_processing":
                        subprocess.call("gcc -O stream.c -o stream", shell=True, cwd=install_dir)
                    if mode == "multi_processing":
                        subprocess.call("gcc -fopenmp -D_OPENMP stream.c -o stream", shell=True, cwd=install_dir)
                if program_name == "bwa":
                    subprocess.check_call(["make"], shell=True, cwd=install_dir+name_and_version)
        binary_urls.close()


def download_bwa_data(settings_list):
    """download bwa data"""
    #check that the user has specified a place to download data to, and that it is a real place.
    program = settings_list[0]
    required_version = settings_list[1]
    dataset_tag = settings_list[2]
    datadir = settings_list[3]
    print(datadir)
    rc = subprocess.call(['ls'], shell=True, cwd=datadir, stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
    if rc == 0:
        print("datadir exists")
        dataset = "bwa_data"
        data_list = open(dataset+".txt", 'r')
        for line in data_list:
            line = line.split(',')
            required_file_name = line[0]
            correct_md5sum = line[1]
            file_name = required_file_name.rsplit('/', 1)[-1]
            if path.exists(datadir+file_name):
                print(file_name+" is downloaded")
                #md5sumcheck= subprocess.Popen(["md5sum "+datadir+file_name], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                #out, err = md5sumcheck.communicate()
                #md5sumcheck= out.split(" ")
                #if not md5sumcheck[0] == correct_md5sum:
                    #print(required_file_name+" is not downloaded correctly")
                    #subprocess.check_call(["wget https://it_randd.cog.sanger.ac.uk/"+required_file_name+" -O "+datadir+file_name], shell=True)
                #else:
                    #print(file_name+" is downloaded correctly")
            else:
                print(file_name+" is not downloaded")
                subprocess.check_call(["wget -q "+required_file_name+" -O "+datadir+file_name], shell=True)
    else:
        print("datadir does not exist")
        sys.exit(1)


def download_salmon_data(settings_list):
    """see what benchmark it is, wether it is using default data or not, and set default_data_list accordingly if it is using default data, then calls the default data downloader function"""
    #NOTE: would a dictionary be better here for code readability? as i could then index by the keys rather than their position in the list?
    program = settings_list[0]
    required_version = settings_list[1]
    dataset_tag = settings_list[2]
    datadir = settings_list[3]
    print(datadir)
    #check that the user has specified a place to download data to, and that it is a real place.
    rc = subprocess.call(['ls'], shell=True, cwd=datadir, stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
    if rc == 0:
        print("datadir exists")
    else:
        print("datadir does not exist")
        sys.exit(1)
    #check if dataset_tag is default
    if dataset_tag == "default":
#       print(list(dataset_required.keys())[0])
        for n in range(0, len(dataset_required)):
            #print(list(dataset_required.keys())[n])
            if required_version in (dataset_required.get(list(dataset_required.keys())[n])):
                dataset = list(dataset_required.keys())[n]
                print("benchmark is using data_set "+dataset)
                index_name = "referenceGenome_index"+dataset.rsplit('_', 1)[-1]
                subprocess.call(["mkdir", "-p", datadir+"/"+index_name])
                subprocess.Popen(["mkdir", "-p", datadir+"/SRR10103759"])
                    #TODO: add check to make sure this subprocess passes alright
                data_list = open(dataset+".txt", 'r')
                for line in data_list:
                    line = line.split(',')
                    required_file_name = line[0]
                    correct_md5sum = line[1]
                    if path.exists(datadir+required_file_name):
                        md5sumcheck= subprocess.Popen(["md5sum "+datadir+required_file_name], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                        out, err = md5sumcheck.communicate()
                        md5sumcheck= out.split(" ")
                        if not md5sumcheck[0] == correct_md5sum:
                            print(required_file_name+" is not downloaded correctly")
                            subprocess.check_call(["wget -q https://cl25-benchmarking.cog.sanger.ac.uk/data/"+required_file_name+" -O "+datadir+required_file_name], shell=True)
                        else:
                            print(required_file_name+" is downloaded correctly")
                    else:
                        print(required_file_name+" is not downloaded")
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
    print(path_to_program, program_name, required_version)
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

    #set a dictionary variable saying which version of the salmon index is required ifor a given version
    dataset_required = {}

    dataset_required["index_format_1"] = ["0.3.2", "0.4.0", "0.4.1", "0.4.2", "0.5.0", "0.5.1", "0.6.0", "0.6.1-pre", "0.7.0-pre", "0.7.0", "0.7.1", "0.7.2", "0.8.0", "0.8.1" , "0.8.2", "0.9.0", "0.9.1"]
    dataset_required["index_format_2"] = ["0.10.0", "0.10.1", "0.10.2", "0.11.1", "0.11.2", "0.11.3", "0.12.0-alpha", "0.12.0", "0.13.0"]
    dataset_required["index_format_3"] = ["0.14.0", "0.14.1", "0.14.2", "0.14.2-1", "0.15.0"]
    dataset_required["index_format_4"] = ["0.99.0-beta1", "0.99.0-beta1", "1.0.0", "1.1.0"]
    settings_list = []

    doc = yaml.load(open(yml_input_file, 'rb'))

    settings_list = get_settings()
    install_dir = get_install_dir(yml_input_file)

    path_to_program_dict= {}
    path_to_program_dict["salmon"] = ["{}name_and_version/bin/salmon".format(install_dir)]
    path_to_program_dict["iozone"] = ["{}name_and_version/src/current/iozone".format(install_dir)]
    path_to_program_dict["iperf"] = ["{}name_and_version/usr/bin/iperfvar".format(install_dir)]
    path_to_program_dict["bwa"] = ["{}name_and_version/bwa".format(install_dir)]
    path_to_program_dict["streams"] = ["{}name_and_version/stream".format(install_dir)]

    #Print the program list if verbose is set
    if args.verbose:
        print("List of programs from yml file :\n{}".format(settings_list))

    download_and_install_programs(settings_list, install_dir)
   
    #sort_programs(settings_list)
    for n in range(0, len(settings_list)):
        print(settings_list[n][3])
        if settings_list[n][3] != "none":
            print(settings_list[n])
            if settings_list[n][0] == "salmon":
                download_salmon_data(settings_list[n])
            if settings_list[n][0] == "bwa":
                download_bwa_data(settings_list[n])
