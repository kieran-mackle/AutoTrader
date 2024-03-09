# Getting Started with AutoTrader
This page has all the information required to download and install AutoTrader.


## Installation

AutoTrader can be installed in two ways; through 
[PyPI](https://pypi.org/project/autotrader/) or by cloning the repository 
directly.


### PyPI Install
The easiest (and recommended) way to get AutoTrader is by running the following command.

```
pip install autotrader
```

This will download AutoTrader from the 
[Python Package Index](https://pypi.org/project/autotrader/) and install it 
on your machine.


### Install from Source
If you are interested in developing AutoTrader, or would like to view the source code while you work, cloning from 
GitHub is the way to go. Simply clone the 
[Github repository](https://github.com/kieran-mackle/AutoTrader) 
onto your machine and run `pip install` locally to install.

```
git clone https://github.com/kieran-mackle/AutoTrader
cd AutoTrader
pip install .
```

```{tip}
If you plan on developing AutoTrader, you can also perform an [editable install](https://www.python.org/dev/peps/pep-0660/) 
to avoid re-installing the source code each time you make a change. To do so, include the '-e' flag: `pip install -e .`.
```


## Optional Dependencies

The installation methods described above will install the minimum required depencencies to get AutoTrader running. You can 
optionally install more dependencies, depending on where you plan to trade or where you would like to download price 
data from.

Options include:
- ccxt: to include CCXT dependencies
- oanda: : to include Oanda v20 dependencies
- ib: to include Interactive Broker dependencies
- yfinance: to include Yahoo Finance dependencies

To install AutoTrader with any of these extra dependencies, include them in the pip install command in square brackets. For 
example:

```
pip install autotrader[ccxt,yfinance]
```

## Demo Repository
To make getting started with AutoTrader even easier, download the demo repository from
[here](https://github.com/kieran-mackle/autotrader-demo). This repo contains example run files, strategies and configuration
files.

```
git clone https://github.com/kieran-mackle/autotrader-demo/ 
```
