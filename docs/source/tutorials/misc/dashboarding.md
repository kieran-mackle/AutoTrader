(trade-dashboard)=
# Trade Dashboard

An effective way of monitoring your trading bots performance while 
live trading is to use a dashboard. This provides a high level overview
of what is happening, allowing you to monitor that everything is going
as it should.

AutoTrader makes this an easy task, and even offers a template dashboard
to use with [Grafana](https://grafana.com/). This template uses the Python
[client](https://github.com/prometheus/client_python) of the data monitoring
software [Prometheus](https://prometheus.io/). The template file can be
found in the `templates` directory of the 
[AutoTrader repository](https://github.com/kieran-mackle/AutoTrader/tree/main/templates), and is previewed below.


```{image} ../../assets/images/dashboard-light.png
:align: center
:class: only-light
```
```{image} ../../assets/images/dashboard-dark.png
:align: center
:class: only-dark
```

## Getting Started
In order to set the dashboard up, you must first install Prometheus 
and Grafana.

### Prometheus
Follow the instructions 
[here](https://prometheus.io/docs/prometheus/latest/installation/) to 
install Prometheus. If you are on a Mac, you can run 
`brew install prometheus`.

Next, configure prometheus by editing `prometheus.yml`. This file is 
normally in the installation directory. If you installed via `brew`, it
will usually be in `/opt/homebrew/etc/prometheus.yml`. Add the following 
to the `scrape_configs`. Set the port (eg. `8009` in the example below) to
one which you plan to use, or leave as is.

```yaml
scrape_configs:
  - job_name: 'autotrader'
    static_configs:
      - targets: ['127.0.0.1:8009']
```

Once you have completed the above, install the Python client:

```
pip install prometheus-client
```


### Grafana
Follow the instructions 
[here](https://grafana.com/docs/grafana/latest/setup-grafana/installation/) to 
install Grafana. You will also need to create an account.

Once complete, open Grafana and add a Prometheus data source:
- Click the settings wheel
- Select "Data Sources"
- Select Prometheus
- Set the URL to `http://localhost:9090/`
- Save.

Finally, select "Import" under Dashboards. Click the "Upload JSON file", 
and provide the 
[dashboard template file](https://github.com/kieran-mackle/AutoTrader/tree/main/templates). 
No data will be shown yet, until we have Prometheus and the Monitor running.


## The Monitor
AutoTrader serves trading metrics via Prometheus from the 
[`Monitor` class](utils-monitor). This class can be instantiated
from a Python script, or via the 
[Command Line Interface](cli). The following metrics will be exposed.

| Metric | Description |
| ------ | ----------- |
| `nav_gauge` | The net asset value. |
| `drawdown_gauge` | The account drawdown. |
| `max_pos_gauge` | The notional value of the largest position. |
| `max_pos_frac_gauge` | The fractional size of the largest position. |
| `abs_pnl_gauge` | The absolute PnL of the account. |
| `rel_PnL_gauge` | The relative PnL of the account. |
| `pos_gauge` | The number of positions held. |
| `total_exposure_gauge` | The total exposure of the account. |
| `net_exposure_gauge` | The net exposure of the account. |
| `leverage_gauge` | The active leverage of the account. |


### Configuration
Add the following monitor configuration yaml file to your `config` 
[directory](rec-dir-struc).

````{tab} Exchange API
```yaml
# monitor.yaml
port: 8009 
broker: "ccxt:binanceusdm"
environment: "paper"  # paper or live
initial_nav: 1000  # Reference NAV for PnL calculations
max_nav: 1000  # Maximum NAV for drawdown calculations
sleep_time: 30  # Monitor update time (s)
```
````
````{tab} From Pickle
```yaml
# monitor.yaml
port: 8009 
picklefile: "broker_picklefile"
environment: "paper"  # paper or live
initial_nav: 1000  # Reference NAV for PnL calculations
max_nav: 1000  # Maximum NAV for drawdown calculations
sleep_time: 30  # Monitor update time (s)
```
````

### Start Prometheus
Before launching the monitor, make sure that Prometheus is running.
For Linux machines, use `./prometheus` to run the executable in install 
directory. For Mac machines, run `brew services start prometheus`.

### Launch Monitor from script
The snippet below provides a sample for launching the monitor 
from a Python script file.

```python
from autotrader.utilities import Monitor

monitor = Monitor(config_filepath="config/monitor.yaml")
monitor.run()
```

### Launch Monitor from CLI
Launching the monitor from the command line is as simple as specifying 
the monitor config filepath to the `monitor` function:

```
autotrader monitor -c config/local_monitor.yaml
```

You will see an output similar to that shown below.

```
░█████╗░██╗░░░██╗████████╗░█████╗░████████╗██████╗░░█████╗░██████╗░███████╗██████╗░
██╔══██╗██║░░░██║╚══██╔══╝██╔══██╗╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
███████║██║░░░██║░░░██║░░░██║░░██║░░░██║░░░██████╔╝███████║██║░░██║█████╗░░██████╔╝
██╔══██║██║░░░██║░░░██║░░░██║░░██║░░░██║░░░██╔══██╗██╔══██║██║░░██║██╔══╝░░██╔══██╗
██║░░██║╚██████╔╝░░░██║░░░╚█████╔╝░░░██║░░░██║░░██║██║░░██║██████╔╝███████╗██║░░██║
╚═╝░░╚═╝░╚═════╝░░░░╚═╝░░░░╚════╝░░░░╚═╝░░░╚═╝░░╚═╝╚═╝░░╚═╝╚═════╝░╚══════╝╚═╝░░╚═╝
Server started on port 8009.
Monitoring with 30 second updates.
Connecting to ccxt:binanceusdm (paper environment)...
  Done.
```

Note that you can also launch the monitor without a config file, by 
providing some additional information directly. See the 
[docs for the command line interface](cli-monitor) for more information.


## Papertrade Monitoring
When papertrading, the broker instances used can be pickled, to save their
state at that time. This allows us to glance into the simulated trading 
evironment and query the broker.



