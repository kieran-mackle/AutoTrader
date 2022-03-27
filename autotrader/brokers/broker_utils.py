import os
import numpy as np
import pandas as pd
from datetime import datetime


class BrokerUtils:
    def __init__(self):
        pass
    
    
    def __repr__(self):
        return 'AutoTrader Broker Utilities'
    
    
    def __str__(self):
        return 'AutoTrader Broker Utilities'
    
    
    def response_to_df(self, response: pd.DataFrame):
        """Function to convert api response into a pandas dataframe.
        """
        candles = response.body["candles"]
        times = []
        close_price, high_price, low_price, open_price = [], [], [], []
        
        for candle in candles:
            times.append(candle.time)
            close_price.append(float(candle.mid.c))
            high_price.append(float(candle.mid.h))
            low_price.append(float(candle.mid.l))
            open_price.append(float(candle.mid.o))
        
        dataframe = pd.DataFrame({"Open": open_price, "High": high_price, "Low": low_price, "Close": close_price})
        dataframe.index = pd.to_datetime(times)
        
        return dataframe
    
    
    def truncate(self, f: float, n: int):
        """Truncates a float f to n decimal places without rounding. 
        """
        s = '{}'.format(f)
        
        if 'e' in s or 'E' in s:
            return '{0:.{1}f}'.format(f, n)
        i, p, d = s.partition('.')
        
        return '.'.join([i, (d+'0'*n)[:n]])
    
    
    def get_pip_ratio(self, pair):
        """Function to return pip value ($/pip) of a given forex pair.
        """
        if 'JPY' in pair:
            pip_value = 1e-2
        else:
            pip_value = 1e-4
        
        return pip_value
    
    
    def get_size(self, pair: str, amount_risked: float, price: float, 
                 stop_price: float, HCF: float, 
                 stop_distance: float = None) -> float:
        """Calculate position size based on account balance and risk profile.
        
        References
        ----------
        https://www.babypips.com/tools/position-size-calculator
        """
        if stop_price is None and stop_distance is None:
            # No stop loss being used, instead risk portion of account
            units               = amount_risked/(HCF*price)
        else:
            pip_value           = self.get_pip_ratio(pair)
            
            if stop_price is None:
                pip_stop_distance = stop_distance
            else:
                pip_stop_distance = abs(price - stop_price) / pip_value
            
            
            if pip_stop_distance == 0:
                units           = 0
            else:
                quote_risk      = amount_risked / HCF
                price_per_pip   = quote_risk / pip_stop_distance
                units           = price_per_pip / pip_value
        
        return units
    
    
    def check_precision(self, pair, original_stop, original_take):
        """Modify stop/take based on pair for required ordering precision. 
        """
        if pair[-3:] == 'JPY':
            N = 3
        else:
            N = 5
        
        take_price      = float(self.truncate(original_take, N))
        stop_price      = float(self.truncate(original_stop, N))
        
        return stop_price, take_price
    
    
    def interval_to_seconds(self, interval):
        """Converts the interval to time in seconds.
        """
        letter = interval[0]
        
        if len(interval) > 1:
            number = float(interval[1:])
        else:
            number = 1
        
        conversions = {'S': 1,
                       'M': 60,
                       'H': 60*60,
                       'D': 60*60*24
                       }
        
        my_int = conversions[letter] * number
        
        return my_int
    
    
    def write_to_order_summary(self, order, filepath: str):
        """Writes order details to summary file.
        """
        # Check if file exists already, if not, create
        if not os.path.exists(filepath):
            f = open(filepath, "w")
            f.write("order time, strategy, granularity, order_type, instrument, order_size, ")
            f.write("trigger_price, stop_loss, take_profit\n")
            f.close()
        
        order_time = order.order_time 
        strategy = order.strategy
        order_type = order.order_type
        instrument = order.instrument
        size = order.size
        trigger_price = order.order_price
        stop_loss = order.stop_loss
        take_profit = order.take_profit
        granularity = order.granularity
        
        f = open(filepath, "a")
        f.write("{}, {}, {}, {}, {}, {}, {}, {}, {}\n".format(order_time, strategy, 
              granularity, order_type, instrument, size, trigger_price, stop_loss, 
              take_profit))
        f.close()
        
    
    def check_dataframes(self, df_1: pd.DataFrame, df_2: pd.DataFrame):
        """Checks dataframe lengths and corrects if necessary.
        """
        if len(df_1) < len(df_2):
            new_df_1 = self.fix_dataframe(df_2, df_1)
            new_df_2 = df_2
        elif len(df_1) > len(df_2):
            new_df_2 = self.fix_dataframe(df_1, df_2)
            new_df_1 = df_1
            
        else:
            new_df_1 = df_1
            new_df_2 = df_2
        
        return new_df_1, new_df_2
    
    
    def fix_dataframe(self, df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
        """Ensures that the quote data and data dataframes are the same
        lenght.
        """
        # Would be good to check which one is shorter, which is longer, then 
        # return both with corrections
        
        i1 = list(df1.index)
        i2 = list(df2.index)
        new_indices = list(set(i1) - set(i2))
        
        new_df = df2
        
        for index in new_indices:
            
            df_row = df1.copy()[df1.index == index]
            
            df_row.Open = None
            df_row.High = None
            df_row.Low = None
            df_row.Close = None
            
            new_df = new_df.append(df_row)
        
        new_df = new_df.sort_index()
        new_df = new_df.interpolate()
        
        return new_df
    
    
    def trade_summary(self, trades: dict = None, orders: dict = None, 
                      instrument: str = None) -> pd.DataFrame:
        """Creates backtest trade summary dataframe.
        """
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
    
    
    def get_streaks(self, trade_summary):
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

