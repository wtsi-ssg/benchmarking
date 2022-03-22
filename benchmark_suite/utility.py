import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

class Utility:
    @staticmethod
    def get_install_dir(yml_input_file):
        doc = yaml.load(open(yml_input_file, 'rb'), Loader=Loader)
        general_settings = doc[0]
        if 'install_dir' in general_settings.keys():
            install_dir = general_settings['install_dir']
        else:
            print("no install_dir set, automatic install failed")
        return install_dir
