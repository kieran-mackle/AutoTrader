<a name="readme-top"></a>

<p align="center">
  <a href="https://kieran-mackle.github.io/AutoTrader/">
    <img src="https://user-images.githubusercontent.com/60687606/132320916-23445f43-dfdc-4949-9881-e18f622605d2.png" alt="AutoTrader Logo" width="15%" >
  </a>
</p>

<h1 align="center">AutoTrader</h1>

<p align="center">
  <a href="https://pypi.org/project/autotrader">
    <img src="https://img.shields.io/pypi/v/autotrader.svg?color=blue&style=plastic" alt="Latest version" width=95 height=20>
  </a>
  
  <a href="https://pepy.tech/project/autotrader">
    <img src="https://pepy.tech/badge/autotrader" alt="Total downloads" >
  </a>
  
  <a href="https://pepy.tech/project/autotrader">
    <img src="https://pepy.tech/badge/autotrader/month" alt="Monthly downloads" >
  </a>

  <a href='https://autotrader.readthedocs.io/en/latest/?badge=latest'>
    <img src='https://readthedocs.org/projects/autotrader/badge/?version=latest' alt='Documentation Status' />
  </a>
  
  <a href="https://github.com/psf/black">
    <img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg">
  </a>
  
</p>


AutoTrader is Python-based platform intended to help in the development, optimisation and deployment of automated trading systems. 
A basic level of experience with Python is recommended for using AutoTrader, but the [docs](https://autotrader.readthedocs.io/en/latest/) 
aim to make using it as easy as possible with detailed tutorials and documentation.

## Latest News
- [CryptoBots](https://github.com/kieran-mackle/cryptobots) has been released along with version `1.0.0`, offering ready-to-trade crypto strategies from the command line
- Version 0.7 has been released, adding integrations with [CCXT](https://github.com/ccxt/ccxt) crypto exchanges. Many more powerful upgrades too.
- AutoTrader has been featured in GitClone's recent article, [*Top Crypto Trader Open-Source Projects on Github*](https://gitclone.dev/top-crypto-trader-open-source-projects-on-github/).

## Features
- A feature-rich trading simulator, supporting [backtesting](https://autotrader.readthedocs.io/en/latest/features/backtesting.html) and 
papertrading. The 'virtual broker' allows you to test your strategies in a risk-free, simulated environment before going live. Capable 
of simulating multiple order types, stop-losses and take-profits, cross-exchange arbitrage and portfolio strategies, AutoTrader has 
more than enough to build a profitable trading system.
- [Integrated data feeds](https://kieran-mackle.github.io/AutoTrader/tutorials/price-data), making OHLC data retrieval as easy as possible.
- [Automated interactive visualisation](https://autotrader.readthedocs.io/en/latest/features/visualisation.html) using [Bokeh](https://bokeh.org/)
- [Library of custom indicators](https://autotrader.readthedocs.io/en/latest/indicators.html).
- [Live trading](https://autotrader.readthedocs.io/en/latest/features/live-trading.html) supported for multiple venues.
- [Detailed documenation and tutorials](https://autotrader.readthedocs.io/en/latest/index.html)
- [Repository](https://github.com/kieran-mackle/autotrader-demo) of example strategies

<p align="right">[<a href="#readme-top">back to top</a>]</p>


## Supported Brokers and Exchanges

| Broker | Asset classes | Integration status |
| -------- | ------------- | ------------------ |
| [Oanda](https://www.oanda.com/)    | Forex CFDs    | Complete |
| [Interactive Brokers](https://www.interactivebrokers.com/en/home.php) | Many | In progress |
| [CCXT](https://github.com/ccxt/ccxt) | Cryptocurrencies | In progress |

<p align="right">[<a href="#readme-top">back to top</a>]</p>

## Installation
AutoTrader can be installed using pip:
```
pip install autotrader
```
### Updating
AutoTrader can be updated by appending the `--upgrade` flag to the install command:
```
pip install autotrader --upgrade
```

<p align="right">[<a href="#readme-top">back to top</a>]</p>

## Documentation
AutoTrader is very well documented in-code and on [Read the Docs](https://autotrader.readthedocs.io/en/latest/). There is also a [detailed walthrough](https://autotrader.readthedocs.io/en/latest/tutorials/walkthrough.html), covering everything from strategy concept to livetrading.

### Example Strategies
Example strategies can be found in the [demo repository](https://github.com/kieran-mackle/autotrader-demo).

<p align="right">[<a href="#readme-top">back to top</a>]</p>

## Backtest Demo
The chart below is produced by a backtest of the MACD trend strategy documented in the 
[tutorials](https://autotrader.readthedocs.io/en/latest/tutorials/building-strategy.html) (and available in the 
[demo repository](https://github.com/kieran-mackle/autotrader-demo)). Entry signals are defined by MACD crossovers, with exit targets defined
by a 1.5 risk-to-reward ratio. Stop-losses are automatically placed using the custom
[swing detection](https://autotrader.readthedocs.io/en/latest/indicators.html#swing-detection) indicator, and position sizes are dynamically calculated based 
on risk percentages defined in the strategy configuration.

Running this strategy with AutoTrader in backtest mode will produce the following interactive chart. 

[![MACD-backtest-demo](https://user-images.githubusercontent.com/60687606/128127659-bf81fdd2-c246-4cd1-b86d-ef624cac50a7.png)](https://autotrader.readthedocs.io/en/latest/tutorials/backtesting.html#interactive-chart)

Note that stop loss and take profit levels are shown for each trade taken. This allows you to see how effective your exit strategy is - are you being stopped out too 
early by placing your stop losses too tight? Are you missing out on otherwise profitable trades becuase your take profits are too far away? AutoTrader helps you 
visualise your strategy and answer these questions.

<p align="right">[<a href="#readme-top">back to top</a>]</p>


## Contributing
To contribute to `autotrader`, please read the instructions below,
and stick to the styling of the code.

### Setting up for Development

1. Create a new Python virtual environment to isolate the package. You 
can do so using [`venv`](https://docs.python.org/3/library/venv.html) or
[anaconda](https://www.anaconda.com/).

2. Install the code in editable mode using the command below (run from
inside the `autotrader` root directory). Also install all dependencies 
using the `[all]` command, which includes the developer dependencies.

```
pip install -e .[all]
```

3. Install the [pre-commit](https://pre-commit.com/) hooks.

```
pre-commit install
```

4. Start developing! After following the steps above, you are ready
to start developing the code. Make sure to follow the guidelines 
below.


### Developing AutoTrader

- Fork the repository and clone to your local machine for development.

- Run [black](https://black.readthedocs.io/en/stable/index.html) on any
code you modify. This formats it according to 
[PEP8](https://peps.python.org/pep-0008/) standards.

- Document as you go: use 
[numpy style](https://numpydoc.readthedocs.io/en/latest/format.html) 
docstrings, and add to the docs where relevant.

- Write unit tests for the code you add, and include them in `tests/`. 
This project uses [pytest](https://docs.pytest.org/en/7.2.x/).

- Commit code regularly to avoid large commits with many changes. 

- Write meaningful commit messages, following the 
[Conventional Commits standard](https://www.conventionalcommits.org/en/v1.0.0/).
The python package [commitizen](https://commitizen-tools.github.io/commitizen/)
is a great tool to help with this, and is already configured for this
repo. Simply stage changed code, then use the `cz c` command to make a 
commit.

- Open a [Pull Request](https://github.com/kieran-mackle/autoTrader/pulls) 
when your code is complete and ready to be merged.


### Building the Docs

To build the documentation, run the commands below. 

```
cd docs/
make html
xdg-open build/html/index.html
```

If you are actively developing the docs, consider using
[sphinx-autobuild](https://pypi.org/project/sphinx-autobuild/).
This will continuosly update the docs for you to see any changes
live, rather than re-building repeatadly. From the `docs/` 
directory, run the following command:

```
sphinx-autobuild source/ build/html --open-browser
```

<p align="right">[<a href="#readme-top">back to top</a>]</p>


## Legal 
### License
AutoTrader is licensed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html).

### Disclaimer
Never risk money you cannot afford to lose. Always test your strategies on a paper trading account before taking it live.

<p align="right">[<a href="#readme-top">back to top</a>]</p>
