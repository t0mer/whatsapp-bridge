import configparser
import os
from os import path
import shutil

class ConfigHandler:

    @classmethod
    def __init__(self):
        self.config_file = 'config/config.ini'
        self.empty_configuration_file = 'config.ini'
        self.config = configparser.ConfigParser()
        self.config.optionxform = str
        self.read_configuration_from_file()
    
    @classmethod
    def read_configuration_from_file(self):
        if not path.exists(self.config_file):
            shutil.copy(self.empty_configuration_file,self.config_file)
        self.config.readfp(open(self.config_file, encoding="utf-8"))
        



