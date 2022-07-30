import os
import click
import shutil


@click.group()
def cli():
    """AutoTrader command line interface."""
    pass


@click.command()
def init():
    """Initialises the current directory for trading."""
    # Construct filepaths
    file_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(file_dir, '..', 'data')
    cwd = os.path.abspath(os.getcwd())

    # Check is config directory exists
    config_dir = os.path.join(cwd, 'config')
    if not os.path.isdir(config_dir):
        os.mkdir(config_dir)

    # Copy keys config
    keys_config_fp = os.path.join(data_dir, 'keys.yaml')
    shutil.copyfile(keys_config_fp, os.path.join(config_dir, 'keys.yaml'))

    # Check if strategy directory exists
    strategy_dir = os.path.join(cwd, 'strategies')
    if not os.path.isdir(strategy_dir):
        os.mkdir(strategy_dir)
    
    click.echo("AutoTrader initialisation complete.")

# TODO - add init options: 
#   - 'minimal' option to initialise with a minimal strategy file,
#     with no strat config files or keys config, just locally 
#     defined config dicts.
#   - 'full' (default) option to initialise full directory strucuture, 
#     with config/ and strategies/ dir, with templates in each

# TODO - allow specifying a directory name to create for init, 
# load it with the files (rather than to cwd)

# TODO - option to initialise with a strategy - pull from demo repo using eg.
# wget https://raw.githubusercontent.com/kieran-mackle/autotrader-demo/main/strategies/ema_crossover.py

cli.add_command(init)