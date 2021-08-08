# -*- coding: utf-8 -*-

import yaml

def read_yaml(file_path):
    '''Function to read and extract contents from .yaml file.'''
    with open(file_path, "r") as f:
        return yaml.safe_load(f)