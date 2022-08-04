import os
from turtle import down
import click
import shutil
import pyfiglet
import requests


@click.group()
def cli():
    """AutoTrader command line interface."""
    pass


@click.command()
@click.option('-f', '--full', is_flag=True, default=True, show_default=True,
    help='Full directory initialisation.')
@click.option('-m', '--minimal', is_flag=True,
    help='Minimal directory initialisation.')
# @click.option('-s', '--strategy', )
@click.argument('name', default='.')

def init(full, minimal, name):
    """Initialises the directory NAME for trading with AutoTrader. If no
    directory NAME is provided, the current directory will be initialised.
    """

    print(pyfiglet.figlet_format("AutoTrader", font='slant'))

    # TODO - implement init options: 
    #   - 'minimal' option to initialise with a minimal strategy file,
    #     with no strat config files or keys config, just locally 
    #     defined config dicts.
    #   - 'full' (default) option to initialise full directory strucuture, 
    #     with config/ and strategies/ dir, with templates in each

    # TODO - option to initialise with a strategy - pull from demo repo using eg.
    # wget https://raw.githubusercontent.com/kieran-mackle/autotrader-
    # demo/main/strategies/ema_crossover.py

    # Construct filepaths
    file_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(file_dir, '..', 'data')
    if name != '.':
        # Initialise directory specified
        dir_name = name
        if not os.path.isdir(dir_name):
            # Directory doesn't exist yet - create it
            os.mkdir(dir_name)
    else:
        # Initialise current directory
        dir_name = os.path.abspath(os.getcwd())

    # Check is config directory exists
    config_dir = os.path.join(dir_name, 'config')
    if not os.path.isdir(config_dir):
        os.mkdir(config_dir)

    # Copy keys config
    keys_config_fp = os.path.join(data_dir, 'keys.yaml')
    shutil.copyfile(keys_config_fp, os.path.join(config_dir, 'keys.yaml'))

    # Check if strategy directory exists
    strategy_dir = os.path.join(dir_name, 'strategies')
    if not os.path.isdir(strategy_dir):
        # Strategy directory doesn't exist - create it
        os.mkdir(strategy_dir)
    
    click.echo("AutoTrader initialisation complete.")


def download_file(url):
    local_filename = url.split('/')[-1]
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                f.write(chunk)
    return local_filename


@click.command()
def demo():
    """Runs a demo backtest in AutoTrader.
    """
    # Download the strategy file and data
    print("Loading demo files...")
    strat_filename = download_file('https://raw.githubusercontent.com/kieran-mackle/'+\
        'AutoTrader/main/tests/macd_strategy.py')
    data_filename = download_file('https://raw.githubusercontent.com/kieran-mackle/'+\
        'AutoTrader/main/tests/data/EUR_USD_H4.csv')
    print("  Done.")

    # Run backtest

    


# Add commands to CLI
cli.add_command(init)
# cli.add_command(demo)