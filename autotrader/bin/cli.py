import os
import click
import shutil


@click.group()
def cli():
    """AutoTrader command line interface."""
    pass


@click.command()
def init():
    """Initialises current directory for trading."""
    # Construct filepaths
    file_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(file_dir, '..', 'data')
    cwd = os.path.abspath(os.getcwd())

    # Check is config directory exists
    config_dir = os.path.join(cwd, 'config')
    if not os.path.isdir(config_dir):
        os.mkdir(config_dir)

    # Copy global config
    global_config_fp = os.path.join(data_dir, 'GLOBAL.yaml')
    shutil.copyfile(global_config_fp, os.path.join(config_dir, 'GLOBAL.yaml'))

    # Check if strategy directory exists
    strategy_dir = os.path.join(cwd, 'strategies')
    if not os.path.isdir(strategy_dir):
        os.mkdir(strategy_dir)
    
    click.echo("AutoTrader initialisation complete.")


cli.add_command(init)