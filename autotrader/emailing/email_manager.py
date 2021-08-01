#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 23 10:19:44 2021

@author: kieran
"""

from getopt import getopt
import sys
import os
from autotrader.emailing import send_order_summary
import yaml


def main(uo_dict):
    email_dir   = os.path.dirname(os.path.abspath(__file__))
    file_dir    = os.path.join(email_dir, '../logfiles')
    file_path   = os.path.join(file_dir, uo_dict["filename"])
    
    global_config   = read_yaml(email_dir + '/../config/GLOBAL.yaml')
    host_email      = global_config["EMAILING"]["HOST_ACCOUNT"]
    mailing_list    = global_config["EMAILING"]["MAILING_LIST"]
    
    send_order_summary(file_path, mailing_list, host_email)


def read_yaml(file_path):
    '''Function to read and extract contents from .yaml file.'''
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


short_options = "f:"
long_options = ['file=']

if __name__ == '__main__':
    options, r = getopt(sys.argv[1:], 
                          short_options, 
                          long_options
                          )
    
    # Defaults
    filename = None
    
    for opt, arg in options:
        if opt in ('-f', '--file'):
            filename = arg
        
    uo_dict = {'filename': filename}

    main(uo_dict)
