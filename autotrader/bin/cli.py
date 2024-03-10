import os
import time
import click
import shutil
import requests
import autotrader


def download_file(url):
    local_filename = url.split("/")[-1]
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return local_filename


@click.group()
def cli():
    """AutoTrader command line interface."""
    pass


@click.command()
def version():
    """Shows the installed version number of AutoTrader."""
    print(autotrader.__version__)


@click.command()
@click.option(
    "-s",
    "--strategies",
    help="The name of strategies to include in the initialised directory.",
)
@click.option(
    "-d",
    "--demo",
    is_flag=True,
    show_default=True,
    default=False,
    help="Initialise the directory with the AutoTrader demo repository.",
)
@click.argument("name", default=".")
def init(strategies, demo, name):
    """Initialises the directory NAME for trading with AutoTrader. If no
    directory NAME is provided, the current directory will be initialised.

    To include ready-to-go strategies in the initialised directory,
    specify them using the strategies option. You can provide the following
    arguments:

    \b
    - template: a strategy template module
    - config: a strategy configuration template
    - strategy_name: the name of a strategy to load

    Strategies are loaded from the AutoTrader demo repository here:
    https://github.com/kieran-mackle/autotrader-demo
    """
    autotrader.utilities.print_banner()

    # Construct filepaths
    file_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(file_dir, "..", "package_data")
    if name != ".":
        # Initialise directory specified
        dir_name = name
        if not os.path.isdir(dir_name):
            # Directory doesn't exist yet - create it
            os.mkdir(dir_name)
    else:
        # Initialise current directory
        dir_name = os.path.abspath(os.getcwd())

    if demo:
        # Clone demo repository
        click.echo("Initialising from demo repository.\n")

        demo_url = "https://github.com/kieran-mackle/autotrader-demo"
        os.system(f"git clone {demo_url} {dir_name}")
        click.echo("\nAutoTrader initialisation complete.")
        return

    # Check if config directory exists
    config_dir = os.path.join(dir_name, "config")
    if not os.path.isdir(config_dir):
        os.mkdir(config_dir)

    # Copy keys config
    keys_config_fp = os.path.join(data_dir, "keys.yaml")
    shutil.copyfile(keys_config_fp, os.path.join(config_dir, "keys.yaml"))

    # Check if strategy directory exists
    strategy_dir = os.path.join(dir_name, "strategies")
    if not os.path.isdir(strategy_dir):
        # Strategy directory doesn't exist - create it
        os.mkdir(strategy_dir)

    # Add strategies
    valid_args = [
        "config",
        "template",
        "macd",
        "ema_crossover",
        "long_ema_crossover",
        "supertrend",
        "rebalance",
    ]
    if strategies is not None:
        for strategy in strategies.replace(" ", "").split(","):
            strategy = strategy.lower()

            # Check
            if strategy not in valid_args:
                raise Exception(f"{strategy} is not a valid argument.")

            # Construct urls
            if strategy == "template":
                # Get strategy template from main repo
                urls = {
                    "strategies": "https://raw.githubusercontent.com/"
                    + "kieran-mackle/AutoTrader/main/templates/strategy.py",
                    "config": None,
                }

            elif strategy == "config":
                # Get strategy config file
                urls = {
                    "strategies": None,
                    "config": "https://raw.githubusercontent.com/"
                    + "kieran-mackle/AutoTrader/main/templates/strategy_config.yaml",
                }

            else:
                # Get from demo repo
                urls = {
                    "strategies": "https://raw.githubusercontent.com/kieran-mackle/"
                    + f"autotrader-demo/main/strategies/{strategy}.py",
                    "config": "https://raw.githubusercontent.com/kieran-mackle/"
                    + f"autotrader-demo/main/config/{strategy}.yaml",
                }

            for dir in ["strategies", "config"]:
                try:
                    # Download
                    filename = download_file(urls[dir])

                    # Move to appropriate directory
                    move_to = os.path.join(dir_name, dir, filename)
                    os.rename(filename, move_to)

                except:
                    pass

    # Print completion message
    click.echo("AutoTrader initialisation complete.")


@click.command()
def demo():
    """Runs a demo backtest in AutoTrader."""
    # Download the strategy file and data
    print("Loading demo files...")
    branch = "main"
    strat_filename = download_file(
        "https://raw.githubusercontent.com/kieran-mackle/"
        + f"AutoTrader/{branch}/tests/macd_strategy.py"
    )
    print("  Done.")

    # Run backtest
    os.system("python3 macd_strategy.py")

    # Clean up files
    os.remove(strat_filename)


@click.command()
@click.option("-p", "--port", default=8009, help="The port to serve data to.")
@click.option(
    "-i",
    "--initial-nav",
    default=None,
    help="The initial NAV to use for relative PnL calculations.",
)
@click.option(
    "-m",
    "--max-nav",
    default=None,
    help="The maximum NAV to use for drawdown calculations.",
)
@click.option(
    "-f", "--picklefile", help="The pickle file containing a virtual broker instance."
)
@click.option("-c", "--config", help="The monitor yaml configuration filepath.")
@click.option("-b", "--broker", help="The name of the broker to connect to.")
@click.option("-e", "--environment", default="paper", help="The trading environment.")
def monitor(port, initial_nav, max_nav, picklefile, config, broker, environment):
    """Monitors a broker/exchange and serves the information
    to a prometheus database.
    """
    # Print banner
    autotrader.utilities.print_banner()

    # Construct config dictionary
    if config is not None:
        # Read from file
        monitor_config = autotrader.utilities.read_yaml(config)

    else:
        monitor_config = {
            "port": port,
            "broker": broker,
            "picklefile": picklefile,
            "initial_nav": initial_nav,
            "max_nav": max_nav,
            "environment": environment,
            "sleep_time": 30,
        }

    # Create Monitor instance
    monitor = autotrader.utilities.Monitor(**monitor_config)

    # Run
    monitor.run()


@click.command()
@click.argument("pickle")
def snapshot(pickle):
    """Prints a snapshot of the trading account of a broker PICKLE instance
    file."""
    autotrader.utilities.print_banner()
    autotrader.AutoTrader.papertrade_snapshot(pickle)
    print("")


# Add commands to CLI
cli.add_command(version)
cli.add_command(init)
cli.add_command(monitor)
cli.add_command(snapshot)
cli.add_command(demo)
