"""Module to import data from config files, download datasets and install programs"""

#!/usr/bin/env python3
import os.path
import pathlib
import string
import subprocess
from typing import Literal

import yaml

from .utility import Utility

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


class DataPreparer:
    """Class to import data from config files, download datasets and install programs"""

    def __init__(
        self,
        defaults_yml_input_file: pathlib.Path,
        settings_yml_input_file: pathlib.Path,
        basedir: pathlib.Path,
        verbose: bool,
    ) -> None:
        self.defaults_yml_input_file: pathlib.Path = defaults_yml_input_file
        self.settings_yml_input_file: pathlib.Path = settings_yml_input_file
        self.base_dir: pathlib.Path = basedir
        self.verbose: bool = verbose

        # set a dictionary variable for all programs that do not require a program setting
        self.implicit_program_type_benchmarks: list[str] = [
            "iperf",
            "iozone",
            "streams",
        ]

        # set a dictionary variable for all benchmarks that require data to be downloaded
        self.data_dependent_type_benchmarks: list[str] = ["multithreaded"]

        self.install_dir = Utility.get_install_dir(settings_yml_input_file)

    def get_benchmark_list_settings(self, settings_doc: dict) -> list:
        """Gets a list of all programs, programversions, and datasets from yml file for tests"""
        settings_list: list = []
        set_keys: list[str] = [
            "program_name",
            "required_version",
            "dataset_tag",
            "dataset_file",
            "datadir",
            "mode",
        ]

        for n in range(1, len(settings_doc)):
            for m in range(0, len(settings_doc[n]["benchmarks"])):

                # Is there a program asssociated with this specific type of benchmark?
                if (
                    settings_doc[n]["benchmarks"][m]["type"]
                    in self.implicit_program_type_benchmarks
                ):
                    program_name = settings_doc[n]["benchmarks"][m]["type"]
                else:
                    if "program" in settings_doc[n]["benchmarks"][m]["settings"].keys():
                        program_name = settings_doc[n]["benchmarks"][m]["settings"][
                            "program"
                        ]
                    else:
                        print("no program setting given")
                        return None

                # get program version
                required_version = settings_doc[n]["benchmarks"][m]["settings"][
                    "programversion"
                ]

                # Uses predefined default_version dict for each program if default version is there
                if (
                    required_version == "default"
                    and program_name in self.default_version.keys()
                ):
                    required_version = self.default_version[program_name]

                # get dataset_tag and datadir
                if (
                    settings_doc[n]["benchmarks"][m]["type"]
                    in self.data_dependent_type_benchmarks
                ):
                    if (
                        "dataset_tag"
                        in settings_doc[n]["benchmarks"][m]["settings"].keys()
                    ):
                        dataset_tag = settings_doc[n]["benchmarks"][m]["settings"][
                            "dataset_tag"
                        ]

                    else:
                        dataset_tag = None

                    if "datadir" in settings_doc[n]["benchmarks"][m]["settings"].keys():
                        datadir = settings_doc[n]["benchmarks"][m]["settings"][
                            "datadir"
                        ]

                    else:
                        print("datadir setting required, none set.")
                        return None

                    if (
                        "dataset_file"
                        in settings_doc[n]["benchmarks"][m]["settings"].keys()
                    ):
                        dataset_file = settings_doc[n]["benchmarks"][m]["settings"][
                            "dataset_file"
                        ]

                    else:
                        dataset_file: Literal[""] = ""
                else:
                    dataset_tag = None
                    datadir = None
                    dataset_file = None

                # get mode for streams benchmark
                if program_name == "streams":
                    mode = settings_doc[n]["benchmarks"][m]["settings"]["mode"]
                else:
                    mode = None

                set_values: list = [
                    program_name,
                    required_version,
                    dataset_tag,
                    dataset_file,
                    datadir,
                    mode,
                ]
                settings_list.append(dict(zip(set_keys, set_values)))

        return settings_list

    def _get_binary_database(self) -> "dict[str,dict[str,str]]":
        loc_db: dict = {}
        with open(
            self.base_dir + "/setup/binaryAddresses.txt", "r", encoding="UTF-8"
        ) as binary_url:
            for line in binary_url:
                try:
                    pro_name, pro_ver, url = line.strip().split(",")
                except ValueError:
                    print(
                        f"Line in binary addresses does not have exactly 3 fields: '{line}'"
                    )
                    return False
                if pro_name in loc_db:
                    loc_db[pro_name][pro_ver] = url
                else:
                    version = {pro_ver: url}
                    loc_db[pro_name] = version
        return loc_db

    def download_and_install_programs(
        self, settings_list: "list[dict]", install_dir: str
    ) -> bool:
        """Downloads and installs programs from settings_list"""

        # check and create tools directory if doesn't exist
        os.makedirs(install_dir, exist_ok=True)

        # read in program database
        loc_db: dict[str, dict[str, str]] = self._get_binary_database()

        for st in settings_list:
            program_name = st["program_name"]
            required_version = st["required_version"]
            name_and_version = program_name + "-v" + required_version

            print("Required program name and version: " + name_and_version)
            path_to_program = self.get_path_to_program(program_name, required_version)
            if os.path.exists(path_to_program):
                print(f"{name_and_version} is already installed at {path_to_program}")
                continue

            if program_name in loc_db:
                if required_version in loc_db[program_name]:
                    # First download the binary package
                    url = loc_db[program_name][required_version]
                    file_name = pathlib.Path(url).name
                    if not os.path.exists(install_dir + file_name):
                        rc = subprocess.call(
                            ["wget -O " + file_name + " " + url],
                            shell=True,
                            cwd=install_dir,
                        )
                    # if the directory to install the program in does not exist, create it
                    os.makedirs(install_dir + name_and_version, exist_ok=True)
                    file_extension = pathlib.Path(file_name).suffix

                    # Extract it
                    # if the binary is in .tar or .tar.gz form, extract it using tar
                    if file_extension in [".bz2", ".gz", ".tar"]:
                        rc = subprocess.call(
                            [
                                "tar",
                                "-xf",
                                file_name,
                                "-C",
                                name_and_version,
                                "--strip-components=1",
                            ],
                            cwd=install_dir,
                        )
                    # if the binary is in the .deb form, use dpkg to extract it
                    elif file_extension in [".deb"]:
                        rc = subprocess.call(
                            [
                                "dpkg",
                                "-x",
                                install_dir + file_name,
                                install_dir + name_and_version,
                            ],
                            cwd=install_dir,
                        )
                    elif file_extension in [".zip"]:
                        rc = subprocess.call(
                            [
                                "bsdtar",
                                "-xf",
                                file_name,
                                "-C",
                                name_and_version,
                                "--strip-components=1",
                            ],
                            cwd=install_dir,
                        )

                    # Should we invoke build command?
                    if not program_name in self.build_command:
                        print(
                            f"An entry for the build_command for {program_name} was not found."
                            "Assuming no_build"
                        )
                        break
 
                    if "no_build" in self.build_command[program_name]:
                        break

                    # Invoke build command
                    build_cmd = self.build_command[program_name]["cmd"]
                    build_cwd: str = string.Template(
                        self.build_command[program_name]["cwd"]
                    ).substitute(
                        install_dir=install_dir, name_and_version=name_and_version
                    )
                    subprocess.check_call([build_cmd], shell=True, cwd=build_cwd)

                else:
                    print(
                        f"Entry for this tool {name_and_version} not found in binaryAddress list."
                        "Please update the list and run again."
                    )
                    return False
            else:
                print(
                    f"Entry for this tool {name_and_version} not found in the binaryAddress list. "
                    "Please update the list and run again!"
                )
                return False

            if not os.path.exists(path_to_program):
                print(f"Build or download for tool {program_name} failed!")
                return False

            print(f"Successfully installed {name_and_version}.")

        return True

    def check_md5sum(self, path: pathlib.Path, correct_sum) -> bool:
        """Checks md5sum of given file with the correct sum."""
        with subprocess.Popen(
            ["md5sum " + path.as_posix()],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        ) as md5sumproc:
            out, _ = md5sumproc.communicate()
            md5sumcheck: list[str] = out.split(" ")
            return bool(md5sumcheck[0] == correct_sum)

    def get_file_data(self, list_filename: pathlib.Path, datadir: pathlib.Path) -> None:
        """Downloads programs based on required_file_name."""
        with open(list_filename, "r", encoding="UTF-8") as data_f:
            for line in data_f:
                file_input: list[str] = line.strip().split(",")
                if len(file_input) == 2:
                    required_file_name, correct_md5sum = file_input
                    file_name: str = pathlib.Path(required_file_name).name
                elif len(file_input) == 3:
                    required_file_name, correct_md5sum, file_name = file_input
                    os.makedirs(datadir / pathlib.Path(file_name).parent, exist_ok=True)
                else:
                    raise ValueError("Bad number of fields in dataset list")

                if os.path.exists(datadir / file_name):
                    if not self.check_md5sum(datadir / file_name, correct_md5sum):
                        if self.verbose:
                            print(
                                f"{required_file_name} is not downloaded correctly."
                                "Trying to redownload now..."
                            )
                        subprocess.check_call(
                            [f"wget {required_file_name} -O {datadir/file_name}"],
                            shell=True,
                        )
                    else:
                        if self.verbose:
                            print(f"{file_name} is already downloaded.")
                else:
                    if self.verbose:
                        print(f"{file_name} is not downloaded. Downloading now...")
                    subprocess.check_call(
                        [f"wget {required_file_name} -O {datadir/file_name}"],
                        shell=True,
                    )

    def download_dataset_file(self, settings_dict) -> None:
        """Downloads dataset file specified in settings_dict"""
        datadir = pathlib.Path(settings_dict["datadir"])
        # check and create datasets directory if doesn't exist
        os.makedirs(datadir, exist_ok=True)

        if isinstance(settings_dict["dataset_file"], dict):
            datadir_dest = datadir / pathlib.Path(settings_dict["dataset_file"]["dest"])
            os.makedirs(datadir_dest, exist_ok=True)
            self.get_file_data(
                settings_dict["dataset_file"]["file"],
                datadir / settings_dict["dataset_file"]["dest"],
            )
        else:
            self.get_file_data(settings_dict["dataset_file"], datadir)

        print("Required dataset is downloaded.")

    def download_default_tagged_dataset(self, settings_dict) -> None:
        """Downloads default datasets if tagged in settings_dict"""
        program = settings_dict["program_name"]
        required_version = settings_dict["required_version"]
        dataset_tag = settings_dict["dataset_tag"]
        datadir = pathlib.Path(settings_dict["datadir"])

        # check and create datasets directory if doesn't exist
        os.makedirs(datadir, exist_ok=True)

        # check if dataset_tag is default
        if dataset_tag == "default":
            for ds in self.dataset_required[program]:
                if required_version in self.dataset_required[program][ds]:
                    print(f"Benchmark is using data_set: {ds} ")
                    index_name = pathlib.Path(self.dataset_index[program][ds])

                    # check and create datasets directory if doesn't exist
                    os.makedirs(datadir / index_name, exist_ok=True)
                    os.makedirs(datadir / "SRR10103759", exist_ok=True)

                    self.get_file_data(
                        self.base_dir + "/setup/" + ds + ".txt", datadir / index_name
                    )

    def get_path_to_program(
        self, program_name: str, required_version: str
    ) -> pathlib.Path:
        """get the path to the program"""
        name_and_version: str = f"{program_name}-v{required_version}"
        if program_name in self.path_to_program_dict.keys():
            path_to_program_template = string.Template(
                self.path_to_program_dict[program_name]
            )
        else:
            path_to_program_template = string.Template(
                name_and_version + "/" + program_name
            )
        iperfvar: str = "iperf" + required_version[0]
        path_to_program: str = path_to_program_template.substitute(
            name_and_version=name_and_version, iperfvar=iperfvar
        )

        return pathlib.Path(path_to_program)

    def load_defaults(self, defaults_doc) -> None:
        """Load the default settings from the defaults_doc"""

        # Set a dictionary to show where executable will be stored
        self.path_to_program_dict = {
            key: f"{self.install_dir}{value}"
            for key, value in defaults_doc["path_to_program"].items()
        }
        # Set a dictionary variable for all the default versions of programs
        self.default_version = defaults_doc["default_version"]
        # set a dictionary variable for which version of the salmon index is required
        self.dataset_required = defaults_doc["dataset_required"]
        # dataset index
        self.dataset_index = defaults_doc["dataset_index"]
        # command to build program
        self.build_command = defaults_doc["build_command"]

    def prepare_data(self) -> bool:
        """Prepare data for the benchmarks by downloading the datasets and installing programs"""
        with open(self.defaults_yml_input_file, "rb") as defaults_file:
            defaults_doc = yaml.load(defaults_file, Loader=Loader)
        self.load_defaults(defaults_doc)

        with open(self.settings_yml_input_file, "rb") as settings_file:
            settings_doc = yaml.load(settings_file, Loader=Loader)

        settings_list = self.get_benchmark_list_settings(settings_doc)

        if settings_list is None:
            return False

        # Print the program list if verbose is set
        if self.verbose:
            print(f"List of programs from yml file :\n{settings_list}")

        if not self.download_and_install_programs(settings_list, self.install_dir):
            return False

        # Download datasets
        for st in settings_list:
            if st["dataset_tag"] == "default":
                self.download_default_tagged_dataset(st)
            if (
                "dataset_file" in st
                and st["dataset_file"] is not None
                and st["dataset_file"] != ""
            ):
                self.download_dataset_file(st)

        return True
