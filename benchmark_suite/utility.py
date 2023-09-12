import pathlib
import yaml

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

class Utility:
    @staticmethod
    def get_install_dir(yml_input_file) -> pathlib.Path:
        doc = yaml.load(open(yml_input_file, 'rb'), Loader=Loader)
        general_settings = doc[0]
        if 'install_dir' in general_settings.keys():
            install_dir = general_settings['install_dir']
        else:
            raise Exception("no install_dir set, automatic install failed")
        return pathlib.Path(install_dir)

    def get_env_dir(yml_input_file) -> pathlib.Path:
        doc = yaml.load(open(yml_input_file, 'rb'), Loader=Loader)
        general_settings = doc[0]
        if 'env_dir' in general_settings.keys():
            env_dir = general_settings['env_dir']
        else:
            raise Exception("no env_dir set, automatic install failed")
        return pathlib.Path(env_dir)
