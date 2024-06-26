"""Utility methods for benchmark_suite"""""
import yaml

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


class Utility:
    """Utility class for benchmark_suite"""
    @staticmethod
    def get_install_dir(yml_input_file):
        """Gets the install directory from the yml file"""
        doc = yaml.load(open(yml_input_file, "rb"), Loader=Loader)
        general_settings = doc[0]
        if "install_dir" in general_settings.keys():
            install_dir = general_settings["install_dir"]
        else:
            print("no install_dir set, automatic install failed")
        return install_dir
