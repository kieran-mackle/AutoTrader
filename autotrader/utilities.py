import sys
import yaml
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from autotrader.brokers.virtual.broker import Broker


def read_yaml(file_path: str) -> dict:
    """Function to read and extract contents from .yaml file.
    
    Parameters
    ----------
    file_path : str
        The absolute filepath to the yaml file.

    Returns
    -------
    dict
        The loaded yaml file in dictionary form.
    """
    with open(file_path, "r") as f:
        return yaml.safe_load(f)
    
    
def write_yaml(data: dict, filepath: str) -> None:
    """Writes a dictionary to a yaml file.

    Parameters
    ----------
    data : dict
        The dictionary to write to yaml.
    filepath : str
        The filepath to save the yaml file.

    Returns
    -------
    None
        The data will be written to the filepath provided.
    """
    with open(filepath, 'w') as outfile:
        yaml.dump(data, outfile, default_flow_style=False)
        
    
def get_config(environment: str, global_config: dict, feed: str) -> dict:
    """Returns the configuration dictionary based on the requested 
    environment.

    Parameters
    ----------
    environment : str
        The trading evironment ('demo' or 'real').
    global_config : dict
        The global configuration dictionary.
    feed : str
        The data feed.

    Raises
    ------
    Exception
        When an unrecognised data feed is provided.

    Returns
    -------
    dict
        The AutoTrader configuration dictionary.
    """
    
    if environment.lower() == 'real':
        # Live trading
        if feed.upper() == 'OANDA':
            data_source     = 'OANDA'
            api             = global_config['OANDA']['LIVE_API']
            access_token    = global_config['OANDA']['ACCESS_TOKEN']
            account_id      = global_config['OANDA']['DEFAULT_ACCOUNT_ID']
            port            = global_config['OANDA']['PORT']
            
            config_dict = {'data_source': data_source,
                           'API': api, 
                           'ACCESS_TOKEN': access_token, 
                           'ACCOUNT_ID': account_id, 
                           'PORT': port}
            
        elif feed.upper() == 'IB':
            # TODO - check port for live trading
            data_source = 'IB'
            host = global_config['host'] if 'host' in global_config else '127.0.0.1'
            port = global_config['port'] if 'port' in global_config else 7497
            client_id = global_config['clientID'] if 'clientID' in global_config else 1
            read_only = global_config['read_only'] if 'read_only' in global_config else False
            account = global_config['account'] if 'account' in global_config else ''
            
            config_dict = {'data_source': data_source,
                           'host': host,
                           'port': port,
                           'clientID': client_id,
                           'account': account,
                           'read_only': read_only}
            
        elif feed.upper() == 'YAHOO':
            data_source = 'yfinance'
            config_dict = {'data_source': data_source}
            
        else:
            print("Unrecognised data feed. Please check config and retry.")
            
    else:
        # Paper trading
        if feed.upper() == 'OANDA':
            data_source     = 'OANDA'
            api             = global_config['OANDA']['PRACTICE_API']
            access_token    = global_config['OANDA']['ACCESS_TOKEN']
            account_id      = global_config['OANDA']['DEFAULT_ACCOUNT_ID']
            port            = global_config['OANDA']['PORT']
            
            config_dict = {'data_source': data_source,
                           'API': api, 
                           'ACCESS_TOKEN': access_token, 
                           'ACCOUNT_ID': account_id, 
                           'PORT': port}
            
        elif feed.upper() == 'IB':
            # TODO - check port for paper trading
            data_source = 'IB'
            host = global_config['host'] if 'host' in global_config else '127.0.0.1'
            port = global_config['port'] if 'port' in global_config else 7497
            client_id = global_config['clientID'] if 'clientID' in global_config else 1
            read_only = global_config['read_only'] if 'read_only' in global_config else False
            account = global_config['account'] if 'account' in global_config else ''
            
            config_dict = {'data_source': data_source,
                           'host': host,
                           'port': port,
                           'clientID': client_id,
                           'account': account,
                           'read_only': read_only}
            
        elif feed.upper() == 'YAHOO':
            data_source = 'yfinance'
            config_dict = {'data_source': data_source}
            
        else:
            raise Exception(f"Unrecognised data feed: '{feed}'. " + \
                  "Please check global config and retry.")
    
    return config_dict
    

def get_watchlist(index, feed):
    """Returns a watchlist of instruments. 
    
    Notes
    ------
    The current implementation only support forex indices, with Oanda 
    formatting.
    
    Examples
    --------
    >>> get_warchlist('forex:major')
        [Out]: list of major forex pairs
    """
    
    if len(index) == 0:
        print("\nArgument for scan missing. Please specify instrument/index to scan.")
        print("Try $ ./AutoTrader.py -h s for more help.\n")
        sys.exit(0)
    
    if index == 'all':
        ''' Returns all currency pairs. '''
        watchlist = ['EUR_USD', 'USD_JPY', 'GBP_USD', 'AUD_USD', 
                     'USD_CAD', 'USD_CHF', 'NZD_USD', 'EUR_GBP',
                     'EUR_AUD', 'EUR_CAD', 'EUR_CHF', 'EUR_JPY',
                     'EUR_NZD', 'GBP_JPY', 'GBP_AUD', 'GBP_CAD',
                     'GBP_CHF', 'GBP_NZD', 'AUD_CAD', 'AUD_CHF',
                     'AUD_JPY', 'AUD_NZD', 'CAD_CHF', 'CAD_JPY',
                     'CHF_JPY', 'NZD_CHF', 'NZD_JPY']
    
    elif index == 'major':
        ''' Returns major currency pairs. '''
        if feed.lower() == 'oanda':
            watchlist = ['EUR_USD', 'USD_JPY', 'GBP_USD', 'AUD_USD', 
                         'USD_CAD', 'USD_CHF', 'NZD_USD']
            
        elif feed.lower() == 'yahoo':
            watchlist = ['EURUSD=X', 'USDJPY=X', 'GBPUSD=X', 'AUDUSD=X', 
                         'USDCAD=X', 'USDCHF=X', 'NZDUSD=X']
        
    elif index == 'minor':
        ''' Returns minor currency pairs. '''
        
        if feed.lower() == 'oanda':
            watchlist = ['EUR_GBP', 'EUR_AUD', 'EUR_CAD', 'EUR_CHF',
                         'EUR_JPY', 'EUR_NZD', 'GBP_JPY', 'GBP_AUD',
                         'GBP_CAD', 'GBP_CHF', 'GBP_NZD', 'AUD_CAD',
                         'AUD_CHF', 'AUD_JPY', 'AUD_NZD', 'CAD_CHF',
                         'CAD_JPY', 'CHF_JPY', 'NZD_CHF', 'NZD_JPY']
            
        elif feed.lower() == 'yahoo':
            watchlist = ['EURGBP=X', 'EURAUD=X', 'EURCAD=X', 'EURCHF=X',
                         'EURJPY=X', 'EURNZD=X', 'GBPJPY=X', 'GBPAUD=X',
                         'GBPCAD=X', 'GBPCHF=X', 'GBPNZD=X', 'AUDCAD=X',
                         'AUDCHF=X', 'AUDJPY=X', 'AUDNZD=X', 'CADCHF=X',
                         'CADJPY=X', 'CHFJPY=X', 'NZDCHF=X', 'NZDJPY=X']
    
    elif index == 'exotic':
        ''' Returns exotic currency pairs. '''
        watchlist = ['EUR_TRY', 'USD_HKD', 'JPY_NOK', 'NZD_SGD',
        	         'GBP_ZAR', 'AUD_MXN'] 
    
    elif index[3] == "_":
        watchlist = [index]
    
    else:
        print("Not supported.")
        sys.exit(0)

    
    return watchlist


def get_streaks(trade_summary):
    """Calculates longest winning and losing streaks from trade summary. 
    """
    profit_list = trade_summary[trade_summary['status']=='closed'].profit.values
    longest_winning_streak = 1
    longest_losing_streak = 1
    streak = 1
    
    for i in range(1, len(profit_list)):
        if np.sign(profit_list[i]) == np.sign(profit_list[i-1]):
            streak += 1
            
            if np.sign(profit_list[i]) > 0:
                # update winning streak
                longest_winning_streak  = max(longest_winning_streak, streak)
            else:
                # Update losing 
                longest_losing_streak   = max(longest_losing_streak, streak)

        else:
            streak = 1
    
    return longest_winning_streak, longest_losing_streak


class BacktestResults:
    """AutoTrader backtest results class.
    
    Attributes
    ----------
    instruments_traded : list
        The instruments traded during the backtest.
    account_history : pd.DataFrame
        A timeseries history of the account during the backtest.
    holding_history : pd.DataFrame
        A timeseries summary of holdings during the backtest, by portfolio
        allocation fraction.
    trade_history : pd.DataFrame
        A timeseries history of trades taken during the backtest.
    order_history : pd.DataFrame
        A timeseries history of orders placed during the backtest.
    open_trades : pd.DataFrame
        Trades which remained open at the end of the backtest.
    cancelled_orders : pd.DataFrame
        Orders which were cancelled during the backtest.
    
    """
    
    def __init__(self, broker: Broker, instrument: str = None):
        
        self.instruments_traded = None
        self.account_history = None
        self.holding_history = None
        self.trade_history = None
        self.order_history = None
        self.open_trades = None
        self.cancelled_orders = None
        self._bots = None # TODO - implement
        
        self.analyse_backtest(broker, instrument)
    
    
    def __str__(self):
        return 'AutoTrader Backtest Results'
    
    
    def __repr__(self):
        return 'AutoTrader Backtest Results'
        
    
    def analyse_backtest(self, broker: Broker, instrument: str = None):
        """Analyses backtest and creates summary of key details.
        """
        # Construct trade and order summaries
        trades = BacktestResults.create_trade_summary(trades=broker.trades, instrument=instrument)
        orders = BacktestResults.create_trade_summary(orders=broker.orders, instrument=instrument)
        
        # Construct account history
        account_history = broker.account_history.copy()
        
        # Create history of holdings
        holdings = broker.holdings.copy()
        holding_history = pd.DataFrame(columns=list(orders.instrument.unique()), 
                                        index=account_history.index)
        for i in range(len(holding_history)):
            try:
                holding_history.iloc[i] = holdings[i]
            except:
                pass
        holding_history.fillna(0, inplace=True)
        
        for col in holding_history.columns:
            holding_history[col] = holding_history[col] / account_history.NAV
        
        holding_history = holding_history[~holding_history.index.duplicated(keep='last')]
        holding_history['cash'] = 1 - holding_history.sum(1)
        
        account_history = account_history[~account_history.index.duplicated(keep='last')]
        account_history['drawdown'] = account_history.NAV/account_history.NAV.cummax() - 1
        
        # Assign attributes
        self.instruments_traded = list(orders.instrument.unique())
        self.account_history = account_history
        self.holding_history = holding_history
        self.trade_history = trades
        self.order_history = orders
        self.open_trades = trades[trades.status == 'open']
        self.cancelled_orders = orders[orders.status == 'cancelled']
    
    
    @staticmethod
    def create_trade_summary(trades: dict = None, orders: dict = None, 
                      instrument: str = None) -> pd.DataFrame:
        """Creates backtest trade summary dataframe.
        """
        # TODO - index by ID
        
        if trades is not None:
            iter_dict = trades
        else:
            iter_dict = orders
        
        iter_dict = {} if iter_dict is None else iter_dict 
        
        product = []
        status = []
        ids = []
        times_list = []
        order_price = []
        size = []
        direction = []
        stop_price = []
        take_price = []
        
        if trades is not None:
            entry_time = []
            fill_price = []
            profit = []
            portfolio_balance = []
            exit_times = []
            exit_prices = []
            trade_duration = []
            fees = []
        
        for ID, item in iter_dict.items():
            product.append(item.instrument)
            status.append(item.status)
            ids.append(item.id)
            size.append(item.size)
            direction.append(item.direction)
            times_list.append(item.order_time)
            order_price.append(item.order_price)
            stop_price.append(item.stop_loss)
            take_price.append(item.take_profit)
        
        if trades is not None:
            for trade_id, trade in iter_dict.items():
                entry_time.append(trade.time_filled)
                fill_price.append(trade.fill_price)
                profit.append(trade.profit)
                portfolio_balance.append(trade.balance)
                exit_times.append(trade.exit_time)
                exit_prices.append(trade.exit_price)
                fees.append(trade.fees)
                if trade.status == 'closed':
                    if type(trade.exit_time) == str:
                        exit_dt = datetime.strptime(trade.exit_time, "%Y-%m-%d %H:%M:%S%z")
                        entry_dt = datetime.strptime(trade.time_filled, "%Y-%m-%d %H:%M:%S%z")
                        trade_duration.append(exit_dt.timestamp() - entry_dt.timestamp())
                    elif isinstance(trade.exit_time, pd.Timestamp):
                        trade_duration.append((trade.exit_time - trade.time_filled).total_seconds())
                    elif trade.exit_time is None:
                        # Weird edge case
                        trade_duration.append(None)
                    else:
                        trade_duration.append(trade.exit_time.timestamp() - 
                                              trade.time_filled.timestamp())
                else:
                    trade_duration.append(None)
                
            dataframe = pd.DataFrame({"instrument": product,
                                      "status": status,
                                      "ID": ids, 
                                      "order_price": order_price,
                                      "order_time": times_list,
                                      "fill_time": entry_time,
                                      "fill_price": fill_price, "size": size,
                                      "direction": direction,
                                      "stop_loss": stop_price, "take_profit": take_price,
                                      "profit": profit, "balance": portfolio_balance,
                                      "exit_time": exit_times, "exit_price": exit_prices,
                                      "trade_duration": trade_duration,
                                      "fees": fees},
                                     index = pd.to_datetime(entry_time))
            
            # Fill missing values for balance
            dataframe.balance.fillna(method='ffill', inplace=True)
            
        else:
            dataframe = pd.DataFrame({"instrument": product,
                                      "status": status,
                                      "ID": ids, 
                                      "order_price": order_price,
                                      "order_time": times_list,
                                      "size": size,
                                      "direction": direction,
                                      "stop_loss": stop_price, 
                                      "take_profit": take_price},
                                     index = pd.to_datetime(times_list))
            
        dataframe = dataframe.sort_index()
        
        # Filter by instrument
        if instrument is not None:
            dataframe = dataframe[dataframe['instrument'] == instrument]
        
        return dataframe

    
    def summary(self):
        
        backtest_results = {}
        cpl = self.trade_history.profit.cumsum()
        
        # All trades
        no_trades = len(self.trade_history[self.trade_history['status'] == 'closed'])
        backtest_results['no_trades'] = no_trades
        backtest_results['start'] = self.account_history.index[0]
        backtest_results['end'] = self.account_history.index[-1]
        
        starting_balance = self.account_history.equity[0]
        ending_balance = self.account_history.equity[-1]
        ending_NAV = self.account_history.NAV[-1]
        abs_return = ending_balance - starting_balance
        pc_return = 100 * abs_return / starting_balance
        
        backtest_results['starting_balance'] = starting_balance
        backtest_results['ending_balance'] = ending_balance
        backtest_results['ending_NAV'] = ending_NAV
        backtest_results['abs_return'] = abs_return
        backtest_results['pc_return'] = pc_return
        
        if no_trades > 0:
            backtest_results['all_trades'] = {}
            wins = self.trade_history[self.trade_history.profit > 0]
            avg_win = np.mean(wins.profit)
            max_win = np.max(wins.profit)
            loss = self.trade_history[self.trade_history.profit < 0]
            avg_loss = abs(np.mean(loss.profit))
            max_loss = abs(np.min(loss.profit))
            win_rate = 100*len(wins)/no_trades
            longest_win_streak, longest_lose_streak  = get_streaks(self.trade_history)
            avg_trade_duration = np.nanmean(self.trade_history.trade_duration.values)
            min_trade_duration = np.nanmin(self.trade_history.trade_duration.values)
            max_trade_duration = np.nanmax(self.trade_history.trade_duration.values)
            max_drawdown = min(self.account_history.drawdown)
            total_fees = self.trade_history.fees.sum()
            
            backtest_results['all_trades']['avg_win'] = avg_win
            backtest_results['all_trades']['max_win'] = max_win
            backtest_results['all_trades']['avg_loss'] = avg_loss
            backtest_results['all_trades']['max_loss'] = max_loss
            backtest_results['all_trades']['win_rate'] = win_rate
            backtest_results['all_trades']['win_streak'] = longest_win_streak
            backtest_results['all_trades']['lose_streak'] = longest_lose_streak
            backtest_results['all_trades']['longest_trade'] = str(timedelta(seconds = int(max_trade_duration)))
            backtest_results['all_trades']['shortest_trade'] = str(timedelta(seconds = int(min_trade_duration)))
            backtest_results['all_trades']['avg_trade_duration'] = str(timedelta(seconds = int(avg_trade_duration)))
            backtest_results['all_trades']['net_pl'] = cpl.values[-1]
            backtest_results['all_trades']['max_drawdown'] = max_drawdown
            backtest_results['all_trades']['total_fees'] = total_fees
            
        # Cancelled and open orders
        backtest_results['no_open'] = len(self.open_trades)
        backtest_results['no_cancelled'] = len(self.cancelled_orders)
        
        # Long trades
        long_trades = self.trade_history[self.trade_history['direction'] > 0]
        no_long = len(long_trades)
        backtest_results['long_trades'] = {}
        backtest_results['long_trades']['no_trades'] = no_long
        if no_long > 0:
            long_wins = long_trades[long_trades.profit > 0]
            avg_long_win = np.mean(long_wins.profit)
            max_long_win = np.max(long_wins.profit)
            long_loss = long_trades[long_trades.profit < 0]
            avg_long_loss = abs(np.mean(long_loss.profit))
            max_long_loss = abs(np.min(long_loss.profit))
            long_wr = 100*len(long_trades[long_trades.profit > 0])/no_long
            
            backtest_results['long_trades']['avg_long_win'] = avg_long_win
            backtest_results['long_trades']['max_long_win'] = max_long_win 
            backtest_results['long_trades']['avg_long_loss'] = avg_long_loss
            backtest_results['long_trades']['max_long_loss'] = max_long_loss
            backtest_results['long_trades']['long_wr'] = long_wr
            
        # Short trades
        short_trades = self.trade_history[self.trade_history['direction'] < 0]
        no_short = len(short_trades)
        backtest_results['short_trades'] = {}
        backtest_results['short_trades']['no_trades'] = no_short
        if no_short > 0:
            short_wins = short_trades[short_trades.profit > 0]
            avg_short_win = np.mean(short_wins.profit)
            max_short_win = np.max(short_wins.profit)
            short_loss = short_trades[short_trades.profit < 0]
            avg_short_loss = abs(np.mean(short_loss.profit))
            max_short_loss = abs(np.min(short_loss.profit))
            short_wr = 100*len(short_trades[short_trades.profit > 0])/no_short
            
            backtest_results['short_trades']['avg_short_win'] = avg_short_win
            backtest_results['short_trades']['max_short_win'] = max_short_win
            backtest_results['short_trades']['avg_short_loss'] = avg_short_loss
            backtest_results['short_trades']['max_short_loss'] = max_short_loss
            backtest_results['short_trades']['short_wr'] = short_wr
        
        return backtest_results
    

class DataStream:
    """Data stream class.
    
    This class is intended to provide a means of custom data pipelines.
    
    Methods
    -------
    refresh
        Returns up-to-date data, multi_data, quote_data and auxdata.
    get_trading_bars
        Returns a dictionary of the current bars for the products being 
        traded, used to act on trading signals.
    
    Attributes
    ----------
    instrument : str
        The instrument being traded.
    feed : str
        The data feed.
    data_filepaths : str|dict
        The filepaths to locally stored data.
    quote_data_file : str
        The filepaths to locally stored quote data.
    auxdata_files : dict
        The auxiliary data files.
    strategy_params : dict
        The strategy parameters.
    get_data : GetData
        The GetData instance.
    data_start : datetime
        The backtest start date.
    data_end : datetime
        The backtest end date.
    portfolio : bool|list
        The instruments being traded in a portfolio, if any.
    
    Notes
    -----
    A 'dynamic' dataset is one where the specific products being traded 
    change over time. For example, trading contracts on an underlying product.
    In this case, dynamic_data should be set to True in AutoTrader.add_data
    method. When True, the datastream will be refreshed each update interval
    to ensure that data for the relevant contracts are being provided.
    
    When the data is 'static', the instrument being traded does not change
    over time. This is the more common scenario. In this case, the datastream
    is only refreshed during livetrading, to accomodate for new data coming in.
    In backtesting however, the entire dataset can be provided after the 
    initial call, as it will not evolve during the backtest. Note that future
    data will not be provided to the strategy; instead, the data returned from
    the datastream will be filtered by each AutoTraderBot before being passed
    to the strategy.
    
    """
    
    def __init__(self, **kwargs):
        # Attributes
        self.instrument = None
        self.feed = None
        self.data_filepaths = None
        self.quote_data_file = None
        self.auxdata_files = None
        self.strategy_params = None
        self.get_data  = None
        self.data_start = None
        self.data_end = None
        self.portfolio = None
        
        # Unpack kwargs
        for item in kwargs:
            setattr(self, item, kwargs[item])
        
    
    def refresh(self, timestamp: datetime = None):
        """Returns up-to-date trading data for AutoBot to provide to the 
        strategy.

        Parameters
        ----------
        timestamp : datetime, optional
            The current timestamp. The default is None.

        Returns
        -------
        data : pd.DataFrame
            The OHLC price data.
        multi_data : dict
            A dictionary of DataFrames.
        quote_data : pd.DataFrame
            The quote data.
        auxdata : dict
            Strategy auxiliary data.

        """
        # Retrieve main data
        if self.data_filepaths is not None:
            # Local data filepaths provided
            if isinstance(self.data_filepaths, str):
                # Single data filepath provided
                data = self.get_data.local(self.data_filepaths, self.data_start, 
                                            self.data_end)
                multi_data = None
                
            elif isinstance(self.data_filepaths, dict):
                # Multiple data filepaths provided
                if self.portfolio:
                    raise NotImplementedError("Locally-provided data not "+\
                                              "implemented for portfolios.")
                    # TODO - implement
                    for instrument, filepath in self.data_filepaths.items():
                        data = self.get_data.local(filepath, self.data_start, self.data_end)
                        multi_data[instrument] = data
                else:
                    multi_data = {}
                    for granularity, filepath in self.data_filepaths.items():
                        data = self.get_data.local(filepath, self.data_start, self.data_end)
                        multi_data[granularity] = data
                
                # Extract first dataset as base data (arbitrary)
                data = multi_data[list(self.data_filepaths.keys())[0]]
        
        else:
            # Download data
            multi_data = {}
            data_func = getattr(self.get_data, self.feed.lower())
            if self.portfolio:
                # Portfolio strategy
                if len(self.portfolio) > 1:
                    granularity = self.strategy_params['granularity']
                    data_key = self.portfolio[0]
                    for instrument in self.portfolio:
                        data = data_func(instrument, granularity=granularity, 
                                         count=self.strategy_params['period'], 
                                         start_time=self.data_start,
                                         end_time=self.data_end)
                        multi_data[instrument] = data
                else:
                    raise Exception("Portfolio strategies require more "+\
                                    "than a single instrument. Please set "+\
                                    "portfolio to False, or specify more "+\
                                    "instruments in the watchlist.")
            else:
                # Single instrument strategy
                granularities = self.strategy_params['granularity'].split(',')
                data_key = granularities[0]
                for granularity in granularities:
                    data = data_func(self.instrument, granularity=granularity, 
                                     count=self.strategy_params['period'], 
                                     start_time=self.data_start,
                                     end_time=self.data_end)
                    multi_data[granularity] = data
                
            # Take data as first element of multi-data
            data = multi_data[data_key]
            
            if len(multi_data) == 1:
                multi_data = None
        
        # Retrieve quote data
        if self.quote_data_file is not None:
            if isinstance(self.quote_data_file, str):
                # Single quote datafile
                quote_data = self.get_data.local(self.quote_data_file, 
                                              self.data_start, self.data_end)
                
            elif isinstance(quote_data, dict) and self.portfolio:
                # Multiple quote datafiles provided
                # TODO - support multiple quote data files (portfolio strategies)
                raise NotImplementedError("Locally-provided quote data not "+\
                                          "implemented for portfolios.")
                quote_data = {}
                for instrument, path in quote_data.items():
                    quote_data[instrument] = self.get_data.local(self.quote_data_file,  # need to specify 
                                                                 self.data_start, 
                                                                 self.data_end)
            else:
                raise Exception("Error in quote data file provided.")
            
        else:
            # Download data
            quote_data_func = getattr(self.get_data,f'_{self.feed.lower()}_quote_data')
            if self.portfolio:
                # Portfolio strategy - quote data for each instrument
                granularity = self.strategy_params['granularity']
                quote_data = {}
                for instrument in self.portfolio:
                    quote_df = quote_data_func(multi_data[instrument], 
                                                 instrument, 
                                                 granularity, 
                                                 self.data_start, 
                                                 self.data_end)
                    quote_data[instrument] = quote_df
                
            else:
                # Single instrument strategy - quote data for base granularity
                quote_data = quote_data_func(data, self.instrument, 
                                             self.strategy_params['granularity'].split(',')[0], 
                                             self.data_start, self.data_end)
        
        # Retrieve auxiliary data
        if self.auxdata_files is not None:
            if isinstance(self.auxdata_files, str):
                # Single data filepath provided
                auxdata = self.get_data.local(self.auxdata_files, self.data_start, 
                                               self.data_end)
                
            elif isinstance(self.auxdata_files, dict):
                # Multiple data filepaths provided
                auxdata = {}
                for key, filepath in self.auxdata_files.items():
                    data = self.get_data.local(filepath, self.data_start, self.data_end)
                    auxdata[key] = data
        else:
            auxdata = None
        
        # Correct any data mismatches
        if self.portfolio:
            for instrument in multi_data:
                matched_data, matched_quote_data = self.match_quote_data(multi_data[instrument], 
                                                                         quote_data[instrument])
                multi_data[instrument] = matched_data
                quote_data[instrument] = matched_quote_data
        else:
            data, quote_data = self.match_quote_data(data, quote_data)
        
        return data, multi_data, quote_data, auxdata
        
    
    def match_quote_data(self, data: pd.DataFrame, 
                         quote_data: pd.DataFrame) -> pd.DataFrame:
        """Function to match index of trading data and quote data.
        """
        datasets = [data, quote_data]
        adjusted_datasets = []
        
        for dataset in datasets:
            # Initialise common index
            common_index = dataset.index
            
            # Update common index by intersection with other data 
            for other_dataset in datasets:
                common_index = common_index.intersection(other_dataset.index)
            
            # Adjust data using common index found
            adj_data = dataset[dataset.index.isin(common_index)]
            
            adjusted_datasets.append(adj_data)
        
        # Unpack adjusted datasets
        adj_data, adj_quote_data = adjusted_datasets
        
        return adj_data, adj_quote_data
    
    
    def get_trading_bars(self, data: pd.DataFrame, quote_bars: bool,
                         timestamp: datetime = None, 
                         processed_strategy_data: dict = None) -> dict:
        """Returns a dictionary of the current bars of the products being 
        traded, based on the up-to-date data.

        Parameters
        ----------
        data : pd.DataFrame
            The strategy base OHLC data.
        quote_bars : bool
            Boolean flag to signal that quote data bars are being requested.
        processed_strategy_data : dict
            A dictionary containing all of the processed strategy data, 
            allowing flexibility in what bars are returned. 
    
        Returns
        -------
        dict
            A dictionary of bars, keyed by the product name.
        
        Notes
        -----
        The quote data bars dictionary must have the exact same keys as the
        trading bars dictionary. The quote_bars boolean flag is provided in
        case a distinction must be made when this method is called.
        """
        bars = {}
        strat_data = processed_strategy_data['base'] if 'base' in \
            processed_strategy_data else processed_strategy_data
        if isinstance(strat_data, dict):
            for instrument, data in strat_data.items():
                bars[instrument] = data.iloc[-1]
        else:
            bars[self.instrument] = strat_data.iloc[-1]
        
        return bars
    
    
