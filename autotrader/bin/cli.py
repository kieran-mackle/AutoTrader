import os
import time
import click
import shutil
import requests
import autotrader
from art import tprint


def print_banner():
    tprint("AutoTrader", font="tarty1")


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
    "-m",
    "--minimal",
    is_flag=True,
    default=False,
    help="Minimal directory initialisation.",
)
@click.option(
    "-s",
    "--strategies",
    help="The name of strategies to include in the initialised directory.",
)
@click.argument("name", default=".")
def init(minimal, strategies, name):
    """Initialises the directory NAME for trading with AutoTrader. If no
    directory NAME is provided, the current directory will be initialised.
    """
    print_banner()

    # Construct filepaths
    file_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(file_dir, "..", "data")
    if name != ".":
        # Initialise directory specified
        dir_name = name
        if not os.path.isdir(dir_name):
            # Directory doesn't exist yet - create it
            os.mkdir(dir_name)
    else:
        # Initialise current directory
        dir_name = os.path.abspath(os.getcwd())

    if minimal:
        # Run minimial directory initialisation
        pass

    else:
        # Run full directory initialisation
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
    if strategies is not None:
        for strategy in strategies.split(","):
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
                    if minimal:
                        move_to = os.path.join(dir_name, filename)
                    else:
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
    strat_filename = download_file(
        "https://raw.githubusercontent.com/kieran-mackle/"
        + "AutoTrader/main/tests/macd_strategy.py"
    )
    data_filename = download_file(
        "https://raw.githubusercontent.com/kieran-mackle/"
        + "AutoTrader/main/tests/data/EUR_USD_H4.csv"
    )
    print("  Done.")

    # Run backtest


@click.command()
@click.option("-p", "--port", default=8009, help="The port to serve data to.")
@click.option(
    "-n", "--nav", default=None, help="The reference NAV to use for relative PnL."
)
@click.option(
    "-f", "--file", help="The pickle file containing a virtual broker instance."
)
@click.option("-b", "--broker", help="The name of the broker to connect to.")
@click.option("-e", "--environment", default="paper", help="The trading environment.")
def monitor(port, nav, file, broker, environment):
    """Monitors a broker and serves the information
    to a prometheus database."""
    broker_name = broker

    def start_server(port):
        """Starts the http server for Prometheus."""
        start_http_server(port)
        print(f"Server started on port {port}.")

    def get_broker(broker):
        """Returns the broker object."""
        if file is not None:
            # Unpickle latest broker instance
            broker = unpickle_broker(picklefile=picklepath)
        elif broker is not None:
            # Use existing broker instance
            pass
        elif broker_name is not None:
            # Create broker instance
            print(f"Connecting to {broker_name}...")
            at = autotrader.AutoTrader()
            at.configure(broker=broker_name, environment=environment, verbosity=0)
            broker = at.run()
            print("  Done.")
        return broker

    # Import packages
    from autotrader.utilities import unpickle_broker
    from prometheus_client import start_http_server, Gauge

    print_banner()

    # Unpack inputs
    ref_nav = nav
    picklepath = file

    if picklepath is not None:
        # Check picklefile exists
        if not os.path.exists(picklepath):
            raise Exception(f"\nPicklefile '{file}' does not exist!")
        else:
            print(f"Monitoring {file}.")

    # Set up instrumentation
    nav_gauge = Gauge("nav_gauge", "Net Asset Value gauge.")
    abs_PnL_gauge = Gauge("abs_pnl_gauge", "Absolute ($) PnL gauge.")
    rel_PnL_gauge = Gauge("rel_pnl_gauge", "Relative (%) PnL gauge.")
    pos_gauge = Gauge("pos_gauge", "Number of open positions gauge.")
    total_exposure_gauge = Gauge("total_exposure_gauge", "Total exposure gauge.")
    net_exposure_gauge = Gauge("net_exposure_gauge", "Total exposure gauge.")
    leverage_gauge = Gauge("leverage_gauge", "Total leverage gauge.")

    # Start up the server to expose the metrics
    try:
        start_server(port)
    except OSError:
        # Kill existing server
        from psutil import process_iter
        from signal import SIGKILL  # or SIGTERM

        for proc in process_iter():
            for conns in proc.connections(kind="inet"):
                if conns.laddr.port == port:
                    proc.send_signal(SIGKILL)  # or SIGKILL

        # Start server
        start_server(port)

    # Begin loop
    broker = None
    while True:
        try:
            # Get broker object
            broker = get_broker(broker)

            # Query broker
            nav = broker.get_NAV()
            if ref_nav is None:
                ref_nav = nav
            positions = broker.get_positions()
            pnl = nav - ref_nav
            rel_pnl = pnl / ref_nav

            # Calculate total exposure
            total_exposure = 0
            net_exposure = 0
            for instrument, position in positions.items():
                total_exposure += abs(position.notional)
                net_exposure += position.direction * position.notional

            # Calculate leverage
            leverage = total_exposure / nav

            # Update Prometheus server
            nav_gauge.set(nav)
            abs_PnL_gauge.set(pnl)
            rel_PnL_gauge.set(rel_pnl)
            pos_gauge.set(len(positions))
            total_exposure_gauge.set(total_exposure)
            net_exposure_gauge.set(net_exposure)
            leverage_gauge.set(leverage)

            # Sleep
            time.sleep(5)

        except KeyboardInterrupt:
            print("\n\nStopping monitoring.")
            break

        except Exception as e:
            # Unexpected exception, sleep briefly
            print(e)
            time.sleep(3)


@click.command()
@click.argument("pickle")
def snapshot(pickle):
    """Prints a snapshot of the trading account of a broker PICKLE instance
    file."""
    print_banner()
    autotrader.AutoTrader.papertrade_snapshot(pickle)
    print("")


# Add commands to CLI
cli.add_command(version)
cli.add_command(init)
cli.add_command(monitor)
cli.add_command(snapshot)
# cli.add_command(demo)
