import click


@click.group()
def cli():
    """AutoTrader command line interface."""
    click.echo('AutoTrader Command Line Interface coming soon!')


@click.command()
def init():
    """Initialises current directory for trading."""
    pass
    # click.echo("AutoTrader directory initialised.")


cli.add_command(init)