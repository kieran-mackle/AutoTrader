# Live Trade Dashboarding

An effective way of monitoring your trading bots performance while 
live trading is to use a dashboard. This provides a high level overview
of what is happening, allowing you to monitor that everything is going
as it should.

AutoTrader makes this an easy task, and even offers a template dashboard
to use with [Grafana](https://grafana.com/). This template uses the Python
[client](https://github.com/prometheus/client_python) of the data monitoring
software [Prometheus](https://prometheus.io/). 


[ insert screenshot of dashboard ]

[ Export grafana dashboard and save to repo ]


## Papertrade Monitoring 
When papertrading, the broker instances used can be pickled, to save their
state at that time. This allows us to glance into the simulated trading 
evironment and query the broker.



## Command Line Tool
```
autotrader monitor [OPTIONS] PICKLEFILE
```


Also need to add the option to specify a broker(s) to listen into rather
than a picklefile.


