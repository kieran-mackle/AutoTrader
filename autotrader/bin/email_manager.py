import os
import sys
from getopt import getopt
from autotrader.utilities import read_yaml
from autotrader.emailing import send_order_summary


def main(uo_dict: dict) -> None:
    email_dir = os.path.dirname(os.path.abspath(__file__))
    file_dir = os.path.join(email_dir, '../logfiles')
    file_path = os.path.join(file_dir, uo_dict["filename"])
    
    global_config = read_yaml(email_dir + '/../config/GLOBAL.yaml')
    host_email = global_config["EMAILING"]["HOST_ACCOUNT"]
    mailing_list = global_config["EMAILING"]["MAILING_LIST"]
    
    send_order_summary(file_path, mailing_list, host_email)


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
