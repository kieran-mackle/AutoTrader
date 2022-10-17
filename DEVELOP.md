# Development

## Workflow

### First Time

```
$ git clone git@github.com:kieren-mackle/AutoTrader.git
$ cd AutoTrader
$ mkvirtualenv autotrader
$ workon autotrader
$ tox
```

### Regular

Build automation is achieved via Tox and is configured to mirror the CI/CD pipeline as closely as reasonably possible:

```
$ tox
```

