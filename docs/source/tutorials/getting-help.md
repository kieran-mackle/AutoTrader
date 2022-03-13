# Getting Help


## From a Run File
To get help using a run file, use the `usage()` or `option_help('opt')` functions of AutoTrader. This can be achieved as shown below.
The command `at.usage()` will provide an overview of all [user options](../docs/autotrader#user-options), whereas the command
`at.print_help('<flag>')` can be used to get specific information about any of the user options.

```
from autotrader.autotrader import AutoTrader

at = AutoTrader()
at.usage()
at.option_help('scan')
```


In the example above, help for the `scan` flag is requested. The following output is provided.

```
    _   _   _ _____ ___ _____ ____      _    ____  _____ ____  
   / \ | | | |_   _/ _ \_   _|  _ \    / \  |  _ \| ____|  _ \ 
  / _ \| | | | | || | | || | | |_) |  / _ \ | | | |  _| | |_) |
 / ___ \ |_| | | || |_| || | |  _ <  / ___ \| |_| | |___|  _ < 
/_/   \_\___/  |_| \___/ |_| |_| \_\/_/   \_\____/|_____|_| \_\
                                                               

Help for '--scan' (-s) option:
-----------------------------------
Automated market scanner. When running AutoTrader in this mode,
the market will be scanned for entry conditions based on the
strategy in the configuration file.
When the notify flag is included, an email will be sent to
notify the recipients in the email list of the signal.
This option requires an index or instrument to scan as an
input.
Note: if email notifications are enabled and there are no scan
hits, no email will be sent. However, if you still wish to receive
emails regardless, set the verbosity of the code to 2. In this
case, an email will be sent on the completion of each scan,
regardless of the results.

Default value: False

For general help, use -h general.
```



## Contact
If you have any other queries or suggestions, please [raise an issue](https://github.com/kieran-mackle/AutoTrader/issues)
on GitHub or send me and [email](mailto:kemackle98@gmail.com).


