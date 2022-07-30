from __future__ import annotations
import os
import pickle
import numpy as np
import pandas as pd
from decimal import Decimal
from datetime import date, datetime
from autotrader.autodata import AutoData
from autotrader.utilities import get_data_config
from autotrader.brokers.broker_utils import BrokerUtils
from autotrader.brokers.trading import Order, Trade, Position


class Broker:
    """Autotrader virtual broker to simulate trading in backtest.

    Attributes
    ----------
    verbosity : int
        The verbosity of the broker.
    pending_orders : dict
        A dictionary containing pending orders.
    open_orders : dict
        A dictionary containing open orders yet to be filled.
    filled_orders : dict
        A dictionary containing filled orders.
    cancelled_orders : dict
        A dictionary containing cancelled orders.
    open_trades : dict
        A dictionary containing currently open trades (fills).
    closed_trades : dict
        A dictionary containing closed trades.
    base_currency : str
        The base currency of the account. The default is 'AUD'.
    NAV : float
        The net asset value of the account.
    equity : float
        The account equity balance.
    floating_pnl : float
        The floating PnL.
    margin_available : float
        The margin available on the account.
    leverage : int
        The account leverage.
    spread : float
        The average spread to use when opening and closing trades.
    spread_units : str
        The units of the spread (eg. 'price' or 'percentage'). The default
        is 'price'.
    hedging : bool
        Flag whethere hedging is enabled on the account. The default is False.
    margin_closeout : float
        The fraction of margin available at margin call. The default is 0.
    commission_scheme : str
        The commission scheme being used ('percentage', 'fixed_per_unit'
        or 'flat'). The default is 'percentage'.
    commission : float
        The commission value associated with the commission scheme.
    maker_commission : float
        The commission value associated with liquidity making orders.
    taker_commission : float
        The commission value associated with liquidity taking orders.
    """

    def __init__(self, broker_config: dict = None, 
                 utils: BrokerUtils = None) -> None:
        """Initialise virtual broker. Attributes are updated by 
        AutoTrader._assign_broker.
        """
        # TODO - improve floating point precision, not currently realistic
        if broker_config is not None:
            self.verbosity = broker_config['verbosity']
        else:
            self.verbosity = 0
        self.utils = utils
        
        # Orders
        self.pending_orders = {}       # {instrument: {id: Order}}
        self.open_orders = {}          # {instrument: {id: Order}}
        self.filled_orders = {}
        self.cancelled_orders = {}
        self._order_id_instrument = {} # mapper from order_id to instrument
        
        # Trades
        self.open_trades = {}
        self.closed_trades = {}
        self._trade_id_instrument = {} # mapper from order_id to instrument

        # Account 
        self.base_currency = 'AUD'
        self.NAV = 0                    # Net asset value
        self.equity = 0                 # Account equity (balance)
        self.floating_pnl = 0
        self.margin_available = 0
        
        self.leverage = 1               # The account leverage
        self.spread = 0                 # The bid/ask spread
        self.spread_units = 'price'     # The units of the spread 
        self.hedging = False            # Allow simultaneous trades on opposing sides
        self.margin_closeout = 0.0      # Fraction at margin call
        
        # Commissions
        self.commission_scheme = 'percentage' # Either percentage, fixed_per_unit or flat
        self.commission = 0
        self.maker_commission = 0       # Liquidity 'maker' trade commission
        self.taker_commission = 0       # Liquidity 'taker' trade commission
        
        # History
        self._NAV_hist = []
        self._equity_hist = []
        self._margin_hist = []
        self._time_hist = []
        self.holdings = []
        
        # Last order and trade counts
        self._last_order_id = 0
        self._last_trade_id = 0

        # Paper trading mode
        self._paper_trading = False             # Paper trading mode boolean
        self._public_trade_access = False       # Use public trades to update orders
        self._autodata = None                   # AutoData instance
        self._state = None                      # Last state snapshot
        self._picklefile = None                 # Pickle filename

    
    def __repr__(self):
        data_feed = self._autodata._feed
        if data_feed == 'ccxt':
            data_feed = self._autodata._ccxt_exchange
        return f'AutoTrader Virtual Broker ({data_feed} data feed)'
    
    
    def __str__(self):
        return self.__repr__()
    
    
    def configure(self, verbosity: int = None, 
                  initial_balance: float = None, 
                  leverage: int = None, 
                  spread: float = None, 
                  spread_units: str = None,
                  commission: float = None, 
                  commission_scheme: str = None,
                  maker_commission: float = None, 
                  taker_commission: float = None,
                  hedging: bool = None, 
                  base_currency: str = None, 
                  paper_mode: bool = None, 
                  public_trade_access: bool = None,
                  margin_closeout: float = None,
                  autodata_config: dict = None, 
                  picklefile: str = None,
                  **kwargs):
        """Configures the broker and account settings.
        
        Parameters
        ----------
        verbosity : int, optional
            The verbosity of the broker. The default is 0.
        initial_balance : float, optional
            The initial balance of the account, specified in the 
            base currency. The default is 0.
        leverage : int, optional
            The leverage available. The default is 1.
        spread : float, optional
            The bid/ask spread to use in backtest (specified in units defined
            by the spread_units argument). The default is 0.
        spread_units : str, optional
            The unit of the spread specified. Options are 'price', meaning that 
            the spread is quoted in price units, or 'percentage', meaning that 
            the spread is quoted as a percentage of the market price. The default
            is 'price'.
        commission : float, optional
            Trading commission as percentage per trade. The default is 0.
        commission_scheme : str, optional
            The method with which to apply commissions to trades made. The options
            are (1) 'percentage', where the percentage specified by the commission 
            argument is applied to the notional trade value, (2) 'fixed_per_unit',
            where the monetary value specified by the commission argument is 
            multiplied by the number of units in the trade, and (3) 'flat', where 
            a flat monetary value specified by the commission argument is charged
            per trade made, regardless of size. The default is 'percentage'.
        maker_commission : float, optional
            The commission to charge on liquidity-making orders. The default is 
            None, in which case the nominal commission argument will be used.
        taker_commission: float, optional
            The commission to charge on liquidity-taking orders. The default is 
            None, in which case the nominal commission argument will be used.
        hedging : bool, optional
            Allow hedging in the virtual broker (opening simultaneous 
            trades in oposing directions). The default is False.
        base_currency : str, optional
            The base currency of the account. The default is AUD.
        paper_mode : bool, optional
            A boolean flag to indicate if the broker is in paper trade mode.
            The default is False.
        public_trade_access : bool, optional
            A boolean flag to signal if public trades are being used to update
            limit orders. The default is False.
        margin_closeout : float, optional
            The fraction of margin usage at which a margin call will occur.
            The default is 0.
        picklefile : str, optional
            The filename of the picklefile to load state from. If you do not 
            wish to load from state, leave this as None. The default is None.
        """
        self.verbosity = verbosity if verbosity is not None else self.verbosity
        self.leverage = leverage if leverage is not None else self.leverage
        self.commission = commission if commission is not None else self.commission
        self.commission_scheme = commission_scheme if commission_scheme is not None \
            else self.commission_scheme
        self.spread = spread if spread is not None else self.spread
        self.spread_units = spread_units if spread_units is not None else \
            self.spread_units
        self.base_currency = base_currency if base_currency is not None else \
            self.base_currency
        self._paper_trading = paper_mode if paper_mode is not None else \
            self._paper_trading
        self._public_trade_access = public_trade_access if public_trade_access is \
            not None else self._public_trade_access
        self.margin_closeout = margin_closeout if margin_closeout is not None \
            else self.margin_closeout
        self.hedging = hedging if hedging is not None else self.hedging
        self._picklefile = picklefile if picklefile is not None else self._picklefile

        # Assign commissions for making and taking liquidity
        self.maker_commission = maker_commission if maker_commission is not None \
            else self.commission
        self.taker_commission = taker_commission if taker_commission is not None \
            else self.commission

        if autodata_config is not None:
            # Instantiate AutoData from config
            data_config = get_data_config(global_config=autodata_config['global_config'], 
                                          feed=autodata_config['feed'])
            self._autodata = AutoData(data_config, **autodata_config)

        else:
            # Create local data instance
            self._autodata = AutoData()
        
        # Initialise balance
        if initial_balance is not None:
            self._make_deposit(initial_balance)

        # Check for pickled state
        if self._paper_trading and self._picklefile is not None:
            # Load state 
            if os.path.exists(picklefile):
                self._load_state()
        
    
    def get_NAV(self) -> float:
        """Returns Net Asset Value of account."""
        return self.NAV
    
    
    def get_balance(self) -> float:
        """Returns balance of account."""
        return self.equity
    
    
    def place_order(self, order: Order, **kwargs) -> None:
        """Place order with broker."""
        # Call order to set order time
        datetime_stamp = kwargs['order_time'] if 'order_time' in \
            kwargs else datetime.now()
        order(order_time = datetime_stamp)

        if order.order_type == 'limit' or order.order_type == 'stop-limit':
            ref_price = order.order_limit_price
        elif order.order_type == 'modify':
            # Get direction of related trade
            related_trade = self.open_trades[order.instrument][order.related_orders]
            order.direction = related_trade.direction
            ref_price = order.order_price
        else:
            ref_price = order.order_price
        
        # Convert stop distance to price
        if order.stop_loss is None and order.stop_distance:
            order.stop_loss = ref_price - order.direction * \
                order.stop_distance*order.pip_value
        
        # Verify SL price
        invalid_order = False
        if order.stop_loss and order.direction*(ref_price - order.stop_loss) < 0:
            direction = 'long' if order.direction > 0 else 'short'
            SL_placement = 'below' if order.direction > 0 else 'above'
            reason = "Invalid stop loss request: stop loss must be "+ \
                    f"{SL_placement} the order price for a {direction}" + \
                    " trade order.\n"+ \
                    f"Order Price: {ref_price}\nStop Loss: {order.stop_loss}"
            invalid_order = True
        
        # Verify TP price
        if order.take_profit is not None and \
            order.direction*(ref_price - order.take_profit) > 0:
            direction = 'long' if order.direction > 0 else 'short'
            TP_placement = 'above' if order.direction > 0 else 'below'
            reason = "Invalid take profit request: take profit must be "+ \
                  f"{TP_placement} the order price for a {direction}" + \
                  " trade order.\n"+ \
                  f"Order Price: {ref_price}\nTake Profit: {order.take_profit}"
            invalid_order = True
        
        # Verify order size
        if order.order_type in ['market', 'limit', 'stop-limit'] and \
            order.size == 0:
            # Invalid order size
            reason = "Invalid order size (must be non-zero)."
            invalid_order = True
        
        # Check limit order does not cross book
        try:
            if order.order_type in ['limit']:
                if self._paper_trading:
                    # Get live midprice
                    orderbook = self.get_orderbook(order.instrument)
                    ref_price = (float(orderbook['bids'][0]['price']) + \
                        float(orderbook['asks'][0]['price']))/2
                else:
                    # Use order / stop price
                    ref_price = order.order_stop_price if order.order_stop_price \
                        is not None else order.order_price
                invalid_order = order.direction*(ref_price - order.order_limit_price) < 0
                reason = f"Invalid limit price for {order.__repr__()} "+\
                            f"(reference price: {ref_price}, "+\
                            f"limit price: {order.order_limit_price})"
        except:
            pass

        # Assign order ID
        order.id = self._get_new_order_id()
        self._order_id_instrument[order.id] = order.instrument
        
        # Move order to pending_orders dict
        order.status = 'pending'
        try:
            self.pending_orders[order.instrument][order.id] = order
        except KeyError:
            self.pending_orders[order.instrument] = {order.id: order}
        
        # Submit order
        if invalid_order:
            if self.verbosity > 0:
                print(f"  Order {order.id} rejected.\n")
            self.cancel_order(order.id, reason, 'pending_orders')
        else:
            # Move order to open_orders or leave in pending
            immediate_orders = ['close', 'reduce', 'modify']
            if order.order_type in immediate_orders or self._paper_trading:
                # Move to open orders
                self._move_order(order, from_dict='pending_orders',
                                    to_dict='open_orders', new_status='open')
            
            # Print
            if self.verbosity > 0:
                print("Order recieved: ", order.__repr__())
        
    
    def get_orders(self, instrument: str = None, 
                   order_status: str = 'open') -> dict:
        """Returns orders."""
        all_orders = getattr(self, order_status+'_orders')
        if instrument:
            # Return orders for instrument specified
            try:
                orders = all_orders[instrument]
            except KeyError:
                # There are currently no orders for this instrument
                orders = {}
        else:
            # Return all orders
            orders = {}
            for instr, instr_orders in all_orders.items():
                orders.update(instr_orders)
        return orders.copy()
    
    
    def cancel_order(self, order_id: int, reason: str = None, 
                     from_dict: str = 'open_orders') -> None:
        """Cancels the order."""
        instrument = self._order_id_instrument[order_id]
        from_dict = getattr(self, from_dict)[instrument]
        reason = reason if reason is not None else "User cancelled."

        if instrument not in self.cancelled_orders: 
            self.cancelled_orders[instrument] = {}
        self.cancelled_orders[instrument][order_id] = from_dict.pop(order_id)
        self.cancelled_orders[instrument][order_id].reason = reason
        self.cancelled_orders[instrument][order_id].status = 'cancelled'
        
        if self.verbosity > 0 and reason:
            print(f"Order {order_id} cancelled - {reason}")
    
    
    def get_trades(self, instrument: str = None,
                   trade_status: str = 'open') -> dict:
        """Returns open trades for the specified instrument."""
        all_trades = getattr(self, trade_status+'_trades')
        if instrument:
            # Specific instruments requested
            try:
                trades = all_trades[instrument]
            except KeyError:
                trades = {}
        else:
            # Return all currently open trades
            trades = {}
            for instr, instr_trades in all_trades.items():
                trades.update(instr_trades)
        return trades.copy()
    
    
    def get_trade_details(self, trade_ID: int) -> Trade:
        """Returns the trade specified by trade_ID."""
        raise DeprecationWarning("This method is deprecated, and will "+\
                "be removed in a future release. Please use the "+\
                "get_trades method instead.")
        instrument = self._trade_id_instrument[trade_ID]
        return self.open_trades[instrument][trade_ID]
    
    
    def get_positions(self, instrument: str = None) -> dict:
        """Returns the positions held by the account.
        
        Parameters
        ----------
        instrument : str, optional
            The trading instrument name (symbol). If 'None' is provided,
            all positions will be returned. The default is None.
            
        Returns
        -------
        open_positions : dict
            A dictionary containing details of the open positions.
        """
        if instrument:
            # instrument provided
            instruments = [instrument]
        else:
            # No specific instrument requested, use all
            instruments = list(self.open_trades.keys())
            
        open_positions = {}
        for instrument in instruments:
            # First get open trades
            open_trades = self.get_trades(instrument)
            if len(open_trades) > 0:
                long_units = 0
                long_PL = 0
                long_margin = 0
                short_units = 0
                short_PL = 0
                short_margin = 0
                total_margin = 0
                trade_IDs = []
                
                for trade_id, trade in open_trades.items():
                    trade_IDs.append(trade.id)
                    total_margin += trade.margin_required
                    if trade.direction > 0:
                        # Long trade
                        long_units += trade.size
                        long_PL += trade.unrealised_PL
                        long_margin += trade.margin_required
                    else:
                        # Short trade
                        short_units += trade.size
                        short_PL += trade.unrealised_PL
                        short_margin += trade.margin_required
            
                # Construct instrument position dict
                instrument_position = {'long_units': long_units,
                                       'long_PL': long_PL,
                                       'long_margin': long_margin,
                                       'short_units': short_units,
                                       'short_PL': short_PL,
                                       'short_margin': short_margin,
                                       'total_margin': total_margin,
                                       'trade_IDs': trade_IDs,
                                       'instrument': instrument,
                                       'net_position': long_units-short_units}
                
                instrument_position = Position(**instrument_position)
                
                # Append position dict to open_positions dict
                open_positions[instrument] = instrument_position
                
        return open_positions
    
    
    def get_margin_available(self) -> float:
        """Returns the margin available on the account.
        """
        return self.margin_available
    
    
    def get_orderbook(self, instrument: str, midprice: float = None):
        """Returns the orderbook."""
        # Get public orderbook
        if self._paper_trading:
            # Papertrading, try get realtime orderbook
            orderbook = self._autodata.L2(instrument, 
                                          spread_units=self.spread_units,
                                          spread=self.spread)
        else:
            # Backtesting, use local pseudo-orderbook
            orderbook = self._autodata._local_orderbook(instrument=instrument,
                    spread_units=self.spread_units,
                    spread=self.spread, 
                    midprice=midprice)

        # TODO - Add local orders to the book?
        
        return orderbook
    

    def _update_positions(self, instrument: str, candle: pd.Series = None, 
                          L1: dict = None, trade: dict = None) -> None:
        """Updates orders and open positions based on the latest data.

        Parameters
        ----------
        instrument : str
            The name of the instrument being updated.
        candle : pd.Series
            An OHLC candle used to update orders and trades.
        L1 : dict, optional
            A dictionary a containing level 1 price snapshot to update
            the positions with. This dictionary must have the keys 
            'bid', 'ask', 'bid_size' and 'ask_size'.
        trade : dict, optional
            A public trade, used to update virtual limit orders.
        """
        def stop_trigger_condition(order_stop_price, order_direction):
            """Returns True if the order stop price has been triggered
            else False."""
            if L1 is not None:
                # Use L1 data to trigger
                reference_price = L1['bid'] if order_direction > 0 else L1['ask']
                triggered = order_direction*(reference_price-order_stop_price) > 0
                
            else:
                # Use OHLC data to trigger
                triggered = candle.Low < order.order_stop_price < candle.High
            return triggered

        def get_last_price(trade_direction):
            """Returns the last reference price for a trade. If the 
            trade is long, this will refer to the bid price. If short,
            this refers to the ask price."""
            if L1 is not None:
                last_price = L1['bid'] if trade_direction > 0 else L1['ask']
            else:
                last_price = candle.Close
            return last_price

        def get_market_ref_price(order_direction):
            """Returns the reference price for a market order."""
            if L1 is not None:
                reference_price = L1['bid'] if order_direction > 0 else L1['ask']
            else:
                reference_price = candle.Open
            return reference_price

        def get_new_stop(trade_direction, distance):
            """Returns the new stop loss for a trailing SL order."""
            if L1 is not None:
                ref_price = L1['ask'] if trade_direction > 0 else L1['bid']
            else:
                ref_price = candle.High if trade_direction > 0 else candle.Low
            new_stop = ref_price - trade_direction*distance
            return new_stop
        
        def get_sl_tp_ref_prices(trade_direction):
            """Returns the SL and TP reference prices."""
            if L1 is not None:
                sl_ref = L1['ask'] if trade_direction > 0 else L1['bid']
                tp_ref = sl_ref
            else:
                sl_ref = getattr(candle, 'Low' if trade_direction > 0 else 'High')
                tp_ref = getattr(candle, 'High' if trade_direction > 0 else 'Low')
            return sl_ref, tp_ref
        
        def limit_trigger_condition(order_direction, order_limit_price):
            """Returns True if the order limit price has been triggered
            else False."""
            if L1 is not None:
                # Use L1 data to trigger (based on midprice)
                ref_price = (L1['bid'] + L1['ask'])/2
            else:
                # Use OHLC data to trigger
                ref_price = candle.Low if order_direction > 0 else candle.High
            triggered = order_direction*(ref_price - float(order_limit_price)) <= 0
            return triggered

        # Check for data availability
        if L1 is not None:
            # Using L1 data to update
            latest_time = datetime.now()

        elif candle is not None:
            # Using OHLC data to update
            latest_time = candle.name
        
        else:
            # No new price data
            if trade is None:
                # No trade either, exit
                return
            else:
                # Public trade recieved, only update limit orders
                self._public_trade(instrument, trade)
                return

        # Open pending orders
        pending_orders = self.get_orders(instrument, 'pending').copy()
        for order_id, order in pending_orders.items():
            if latest_time > order.order_time:
                self._move_order(order, from_dict='pending_orders',
                                 to_dict='open_orders', new_status='open')
        
        # Update open orders for current instrument
        open_orders = self.get_orders(instrument).copy()
        for order_id, order in open_orders.items():
            if order.order_type == 'market':
                # Market order type - proceed to fill
                reference_price = get_market_ref_price(order.direction)
                self._fill_order(order=order, fill_time=latest_time,
                                 reference_price=reference_price)
            
            elif order.order_type == 'stop-limit':
                # Check if order_stop_price has been reached yet
                if stop_trigger_condition(order.order_stop_price, order.direction):
                    # order_stop_price has been reached, change order type to 'limit'
                    order.order_type = 'limit'
            
            elif order.order_type == 'modify':
                # Modification order
                self._modify_order(order)
            
            elif order.order_type == 'close':
                # Market close trade/position
                self._close_position(instrument=order.instrument,
                                     trade_id=order.related_orders,
                                     order_type='market')
                self._move_order(order)
                
            elif order.order_type == 'reduce':
                # Market reduce position
                reference_price = get_market_ref_price(order.direction)
                self._reduce_position(order, 
                                      exit_price=reference_price,
                                      exit_time=latest_time)
                self._move_order(order)
                
            # Check for limit orders
            if order.order_type == 'limit':
                # Limit order type
                if not self._public_trade_access:
                    # Update limit orders based on price feed
                    triggered = limit_trigger_condition(order.direction, 
                                                        order.order_limit_price)
                    if triggered:
                        self._fill_order(order=order, fill_time=latest_time,
                                    reference_price=order.order_limit_price)
                else:
                    # Update limit orders based on trade feed
                    if trade is not None: self._public_trade(instrument, trade)
        
        # Update open trades
        open_trades = self.get_trades(instrument).copy()
        for trade_id, trade in open_trades.items():
            # Update stop losses
            if trade.stop_type == 'trailing':
                # Trailing stop loss type, check if price has moved SL
                if trade.stop_distance is not None:
                    pip_distance = trade.stop_distance
                    distance = pip_distance*trade.pip_value # price units
                else:
                    distance = abs(trade.fill_price - trade.stop_loss)
                    trade.stop_distance = distance / trade.pip_value
                    
                # Update price of stop loss
                new_stop = get_new_stop(trade.direction, distance)
                if trade.direction*(new_stop - trade.stop_loss) > 0:
                    self._update_stop_loss(instrument, trade_id, new_stop, 
                                               new_stop_type='trailing')
            
            # Check if SL or TP have been hit
            sl_ref, tp_ref = get_sl_tp_ref_prices(trade.direction)
            if trade.stop_loss and trade.direction*(sl_ref - trade.stop_loss) < 0:
                # Stop loss hit
                self._close_trade(instrument=instrument, trade_id=trade_id, 
                                  exit_price=trade.stop_loss, exit_time=latest_time,
                                  order_type='limit')
            elif trade.take_profit and trade.direction*(tp_ref - trade.take_profit) > 0:
                # Take Profit hit
                self._close_trade(instrument=instrument, trade_id=trade_id, 
                                  exit_price=trade.take_profit, exit_time=latest_time)
            else:
                # Position is still open, update value of holding
                trade.last_price = get_last_price(trade.direction)
                trade.last_time = latest_time
                trade.unrealised_PL = trade.direction*trade.size * \
                    (trade.last_price - trade.fill_price)*trade.HCF
                    
        # Update floating pnl and margin available 
        self._update_margin(instrument=instrument, latest_time=latest_time)
        
        # Update open position value
        self.NAV = self.equity + self.floating_pnl
        
        # Update account history
        self._NAV_hist.append(self.NAV)
        self._equity_hist.append(self.equity)
        self._margin_hist.append(self.margin_available)
        self._time_hist.append(latest_time)
        
        holdings = self._get_holding_allocations()
        self.holdings.append(holdings)

        # Save state
        if self._paper_trading and self._picklefile is not None:
            self._save_state()
        
    
    def _update_all(self):
        """Convenience method to update all open positions when paper trading."""
        # TODO - update public trades too 
        # Get latest trades
        # trades = broker._autodata.trades(symbol)
        # tw.update(trades)

        # # Update broker trades
        # for trade in tw.get_latest_trades():
        # 	broker._update_positions(instrument=symbol, trade=trade)

        # Update orders
        orders = self.open_orders
        for instrument in orders:
            l1 = self._autodata.L1(instrument=instrument)
            self._update_positions(instrument=instrument, L1=l1)

        # Update positions
        positions = self.get_positions()
        for instrument in positions:
            l1 = self._autodata.L1(instrument=instrument)
            self._update_positions(instrument=instrument, L1=l1)
    
    
    def _update_instrument(self, instrument):
        """Convenience method to update a single instrument when paper 
        trading."""
        # Update orders
        orders = self.get_orders(instrument=instrument)
        positions = self.get_positions(instrument=instrument)
        if len(orders) + len(positions) > 0:
            # Update instrument
            l1 = self._autodata.L1(instrument=instrument)
            self._update_positions(instrument=instrument, L1=l1)

    
    def _fill_order(self, order: Order,
                    fill_time: datetime = None, 
                    reference_price : float = None,
                    trade_size: float = None):
        """Attempts to fill an order.
        
        Notes
        -----
        If hedging is not enabled, any orders which are contrary to an open
        position will first reduce (or close) the open position before 
        being filled via market orders. If the remaining units of the order 
        (after reducing the open position) exceed margin requirements, the 
        entire order will be cancelled, and the original position will not 
        be impacted.

        If hedging is enabled, trades can be opened against one another, and
        will be treated in isolation. 
        """
        if trade_size is not None:
            # Fill limit order with trade_size provided
            if trade_size < order.size:
                # Create new order as portion to be filled 
                order = Order._partial_fill(order=order, units_filled=trade_size)

                # Assign new order ID
                order.id = self._get_new_order_id()
                self._order_id_instrument[order.id] = order.instrument

                # Move new order to open_orders
                self.open_orders[order.instrument][order.id] = order

        # Check order against current position
        close_existing_position = False
        if not self.hedging:
            # Check if current order will reduce or add to existing position
            current_position = self.get_positions(order.instrument)
            if current_position:
                # Currently in a position
                net_position = current_position[order.instrument].net_position
                if order.direction != np.sign(net_position):
                    # The order opposes the current position
                    if order.size > abs(net_position):
                        # Modify order size to the net remaining units
                        order.size -= abs(net_position)
                        
                        # Also close out existing position
                        close_existing_position = True

                    else:
                        # Simply reduce the current position
                        self._reduce_position(order=order, 
                                              exit_price=reference_price,
                                              exit_time=fill_time)
                        self._move_order(order)
                        if self.verbosity > 0:
                            print(f"Order filled: {order}")
                        return
        
        # Calculate margin requirements
        position_value = order.size * float(reference_price) * order.HCF # Net position
        margin_required = self._calculate_margin(position_value)
        
        if margin_required < self.margin_available:
            # Enough margin in account to fill order, determine average fill price
            avg_fill_price = order.order_limit_price if order.order_type == 'limit' \
                else self._trade_through_book(instrument=order.instrument, 
                                              direction=order.direction,
                                              size=order.size, 
                                              reference_price=reference_price)

            if close_existing_position:
                # Close the open position before proceeding
                # Note: limit order type is enforced since spread is already
                # accounted for in avg_fill price
                self._close_position(instrument=order.instrument, 
                                     exit_price=avg_fill_price,
                                     exit_time=fill_time,
                                     order_type='limit')

            # Mark order as filled
            trade_id = self._get_new_trade_id()
            self._trade_id_instrument[trade_id] = order.instrument # Track ID-instrument pair
            trade = Trade(order)
            trade.id = trade_id
            trade.fill_price = float(avg_fill_price)
            trade.time_filled = fill_time
            trade.margin_required = margin_required
            trade.value = position_value
            try:
                self.open_trades[order.instrument][trade_id] = trade
            except KeyError:
                self.open_trades[order.instrument] = {trade_id: trade}
            
            # Move order to filled_orders dict
            self._move_order(order)

            # Charge commission for trade
            commission = self._calculate_commissions(price=avg_fill_price, 
                                                     units=order.size, 
                                                     HCF=order.HCF,
                                                     order_type=order.order_type)
            self._add_funds(commission)

            if self.verbosity > 0:
                print(f"Order filled: {order}")

        else:
            # Cancel order
            cancel_reason = "Insufficient margin to fill order."
            self.cancel_order(order.id, cancel_reason)

    
    def _move_order(self, order: Order, 
                    from_dict: str = 'open_orders', 
                    to_dict: str = 'filled_orders', 
                    new_status: str = 'filled') -> None:
        """Moves an order from the from_dict to the to_dict."""
        order.status = new_status
        from_dict = getattr(self, from_dict)[order.instrument]
        to_dict = getattr(self, to_dict)
        popped_item = from_dict.pop(order.id)
        try:
            to_dict[order.instrument][order.id] = popped_item
        except KeyError:
            to_dict[order.instrument] = {order.id: popped_item}
    
    
    def _close_position(self, instrument: str, 
                        exit_price: float = None, 
                        exit_time: datetime = None,
                        trade_id: int = None,
                        order_type: str = 'market') -> None:
        """Market closes the position (or single trade) of an instrument.

        Parameters
        -----------
        instrument : str
            The name of the instrument.
        exit_price : float, optional
            The exit price. The default is None.
        exit_time : datetime, optional
            The position exit time. The default is None.
        trade_id : int, optional
            The ID of the trade to close out. The default is None.
        order_type : str, optional
            The type of order used to close the position. The default 
            is 'market'.
        """
        if trade_id:
            # Single trade specified to close
            self._close_trade(instrument=instrument, trade_id=trade_id,
                              order_type=order_type, exit_price=exit_price,
                              exit_time=exit_time)
        else:
            # Close all positions for instrument
            open_trades = self.open_trades[instrument].copy()
            for trade_id, trade in open_trades.items():
                self._close_trade(instrument, trade_id=trade_id,
                                  order_type=order_type, exit_price=exit_price,
                                  exit_time=exit_time)
    
    
    def _close_trade(self, instrument: str, 
                     trade_id: int = None, 
                     exit_price: float = None,
                     exit_time: datetime = None,
                     order_type: str = 'market') -> None:
        """Closes trade by order number.

        Parameters
        ----------
        trade_id : int, optional
            The trade id. The default is None.
        exit_price : float, optional
            The trade exit price. If none is provided, the market price
            will be used. The default is None.
        exit_time : datetime, optional
            The trade exit time. The default is None.
        order_type : str, optional
            The order type used to calculate commissions. The default
            is 'market'.

        Returns
        -------
        None
            The trade will be marked as closed and the appropriate
            commission will be charged for the trade.
        """
        # Get trade to be closed
        trade = self.open_trades[instrument][trade_id]
        fill_price = trade.fill_price
        size = trade.size
        direction = trade.direction

        reference_price = exit_price if exit_price is not None else trade.last_price
        if order_type == 'limit':
            # Use exit price provided
            exit_price = reference_price
        else:
            # Exit price provided as reference for midprice
            exit_price = self._trade_through_book(instrument=instrument, 
                                                  direction=-direction, 
                                                  size=size, 
                                                  reference_price=reference_price)
        
        # Update portfolio with profit/loss
        gross_PL = direction*size*(float(exit_price) - float(fill_price))*trade.HCF
        commission = self._calculate_commissions(price=exit_price, 
                                                 units=size, 
                                                 HCF=trade.HCF,
                                                 order_type=order_type)
        net_profit = gross_PL - commission
        
        # Update trade closure attributes
        trade.profit = net_profit
        trade.balance = self.equity
        trade.exit_price = exit_price
        trade.fees = commission
        trade.exit_time = exit_time if exit_time is not None else trade.last_time
        trade.status = 'closed'
        
        # Add trade to closed positions
        popped_trade = self.open_trades[instrument].pop(trade_id)
        try:
            self.closed_trades[instrument][trade_id] = popped_trade
        except KeyError:
            self.closed_trades[instrument] = {trade_id: popped_trade}
        
        # Update account
        self._add_funds(net_profit)
    
    
    def _reduce_position(self, order: Order,
                         exit_price: float = None,
                         exit_time: datetime = None) -> None:
        """Reduces the position of the specified instrument using the 
        original order. 

        The direction of the order is used to specify whether 
        to reduce long or short units. 
        """
        # Assign reference price: use limit price for limit order, else market price
        reference_price = order.order_limit_price if order.order_limit_price is \
            not None else exit_price

        # Consired long vs. short units to be reduced
        instrument = order.instrument
        reduction_direction = order.direction
        
        # Get open trades for instrument
        open_trades = self.get_trades(instrument)
        
        # Modify existing trades until there are no more units to reduce
        units_to_reduce = order.size
        while units_to_reduce > 0:
            # There are units to be reduced
            for trade_id, trade in open_trades.items():
                if trade.direction != reduction_direction:
                    # Reduce this trade
                    if units_to_reduce >= trade.size:
                        # Entire trade must be closed
                        self._close_trade(instrument=instrument, 
                                          trade_id=trade_id,
                                          exit_price=reference_price,
                                          exit_time=exit_time,
                                          order_type=order.order_type)
                        
                        # Update units_to_reduce
                        units_to_reduce -= abs(trade.size)
                        
                    elif units_to_reduce > 0:
                        # Partially close trade
                        self._partial_trade_close(instrument=instrument, 
                                                  trade_id=trade_id, 
                                                  units=units_to_reduce,
                                                  exit_price=reference_price,
                                                  exit_time=exit_time,
                                                  order_type=order.order_type)
                        
                        # Update units_to_reduce
                        units_to_reduce = 0
                    
    
    def _partial_trade_close(self, instrument: str, 
                             trade_id: int, 
                             units: float, 
                             exit_price: float = None,
                             exit_time: datetime = None,
                             order_type: str = 'market') -> None:
        """Partially closes a trade.
        
        The original trade ID remains, but the trade size may be reduced. The
        portion that gets closed is assigned a new ID.
        """
        trade = self.open_trades[instrument][trade_id]
        
        # Create new trade for the amount to be reduced
        partial_trade = Trade._split(trade, units)
        partial_trade_id = self._get_new_trade_id()
        partial_trade.id = partial_trade_id

        # Add partial trade to open trades, then close it
        self.open_trades[instrument][partial_trade_id] = partial_trade
        self._close_trade(instrument=instrument, 
                          trade_id=partial_trade_id,
                          exit_price=exit_price,
                          exit_time=exit_time,
                          order_type=order_type)

        # Keep track of partial trade id instrument for reference
        self._trade_id_instrument[partial_trade_id] = instrument
        
    
    def _trade_through_book(self, instrument, direction, size, 
                            reference_price=None):
        """Returns an average fill price by filling an order through
        the orderbook.
        
        Parameters
        -----------
        instrument : str
            The instrument to fetch the orderbook for.
        direction : int
            The direction of the trade (1 for long, -1 for short). Used
            to specify either bid or ask prices. 
        size : float
            The size of the trade.
        reference_price : float, optional
            The reference price to use if artificially creating an 
            orderbook.
        """
        # Get order book
        book = self.get_orderbook(instrument, reference_price)

        # Work through the order book
        units_to_fill = size
        side = 'bids' if direction < 0 else 'asks'
        fill_prices = []
        fill_sizes = []
        level_no = 0
        while units_to_fill > 0:
            # Consume liquidity
            level = getattr(book, side).iloc[level_no]
            units_consumed = min(units_to_fill, float(level['size']))
            fill_prices.append(float(level['price']))
            fill_sizes.append(units_consumed)

            # Iterate
            level_no += 1
            units_to_fill -= units_consumed

        avg_fill_price = sum([fill_sizes[i]*fill_prices[i] for i \
                in range(len(fill_prices))])/sum(fill_sizes)
        return avg_fill_price


    def _calculate_commissions(self, price: float, 
                               units: float = None,
                               HCF: float = 1, 
                               order_type: str = 'market') -> float:
        """Calculates trade commissions.
        """
        # Get appropriate commission value
        commission_val = self.taker_commission if order_type == 'market' else \
            self.maker_commission

        if self.commission_scheme == 'percentage':
            # Commission charged as percentage of trade value
            trade_value = abs(units)*float(price)*HCF
            commission  = (commission_val/100) * trade_value
        
        elif self.commission_scheme == 'fixed_per_unit':
            # Fixed commission per unit traded
            commission = commission_val * units
        
        elif self.commission_scheme == 'flat':
            # Flat commission value per trade
            commission = commission_val

        return commission
    
    
    def _add_funds(self, amount: float) -> None:
        """Adds funds to brokerage account.
        """
        self.equity += amount
        self._update_margin()
    
    
    def _make_deposit(self, deposit: float) -> None:
        """Adds deposit to account balance and NAV.
        """
        self.equity += deposit
        self.NAV += deposit
        self._update_margin()
    
    
    def _calculate_margin(self, position_value: float) -> float:
        """Calculates margin required to take a position.
        """
        margin = position_value / self.leverage
        return margin
    
    
    def _update_margin(self, instrument: str = None, 
                       latest_time: datetime = None) -> None:
        """Updates margin available in account.
        """
        margin_used = 0
        floating_pnl = 0
        open_trades = self.get_trades()
        for trade_id, trade in open_trades.items():
            size = trade.size
            HCF = trade.HCF
            last_price = trade.last_price
            trade_value = abs(size) * last_price * HCF if last_price else trade.value
            margin_required = self._calculate_margin(trade_value)
            margin_used += margin_required
            
            # Update margin required in trade dict
            trade.margin_required = margin_required
            trade.value = trade_value
            
            # Floating pnl
            floating_pnl += trade.unrealised_PL
                
        # Update unrealised PnL
        self.floating_pnl = floating_pnl
        
        # Update margin available
        self.margin_available = self.NAV - margin_used
        
        # Check for margin call
        if self.leverage > 1 and self.margin_available/self.NAV < self.margin_closeout:
            # Margin call
            if self.verbosity > 0:
                print("MARGIN CALL: closing all positions.")
            self._margin_call(instrument, latest_time)

    
    def _modify_order(self, order: Order) -> None:
        """Modify order with updated parameters. Called when order_type = 'modify', 
        modifies trade specified by related_orders key.
        """
        # Get ID of trade to modify
        modify_trade_id = order.related_orders
        instrument = order.instrument
        
        if order.stop_loss is not None:
            # New stop loss provided
            self._update_stop_loss(instrument, modify_trade_id, order.stop_loss, 
                                   order.stop_type)
            
        if order.take_profit is not None:
            self._update_take_profit(instrument, modify_trade_id, order.take_profit)
        
        # Move order to filled_orders dict
        self._move_order(order)
        
        
    def _update_stop_loss(self, instrument: str, 
                          trade_id: int, 
                          new_stop_loss: float, 
                          new_stop_type: str = 'limit') -> None:
        """Updates stop loss on open trade.
        """
        self.open_trades[instrument][trade_id].stop_loss = new_stop_loss
        self.open_trades[instrument][trade_id].stop_type = new_stop_type
    
    
    def _update_take_profit(self, instrument: str, trade_id: int, 
                            new_take_profit: float) -> None:
        """Updates take profit on open trade.
        """
        self.open_trades[instrument][trade_id].take_profit = new_take_profit
        
        
    def _get_new_order_id(self):
        self._last_order_id += 1
        return self._last_order_id
    
    
    def _get_new_trade_id(self):
        self._last_trade_id += 1
        return self._last_trade_id
    
    
    def _margin_call(self, instrument: str, latest_time: datetime):
        """Closes open positions.
        """
        self._close_position(instrument=instrument, exit_time=latest_time)
    
    
    def _get_holding_allocations(self):
        """Returns a dictionary containing the nominal value of
        all open trades."""
        open_trades = self.get_trades()
        values = {}
        for trade_id, trade in open_trades.items():
            if trade.instrument in values:
                values[trade.instrument] += trade.size * trade.last_price
            else:
                values[trade.instrument] = trade.size * trade.last_price
                
        if len(values) == 0:
            values = {None: None}
            
        return values

    
    def _add_orders_to_book(self, instrument, orderbook):
        """Adds local orders to the orderbook."""
        # TODO - implement
        orders = self.get_orders(instrument)
        for order in orders:
            if order.order_type == 'limit':
                side = 'bids' if order.direction > 0 else 'asks'

                # Add to the book
                orderbook[side]

        return orderbook


    def _save_state(self):
        """Pickles the current state of the broker."""
        try:
            # Remove old picklefile (if it exists)
            os.remove(self._picklefile)
        except:
            pass

        with open(self._picklefile, 'wb') as file:
            pickle.dump(self, file)


    def _load_state(self):
        """Loads the state of the broker from a pickle."""
        verbosity = self.verbosity
        try:
            with open(self._picklefile, 'rb') as file:
                state = pickle.load(file)
            
            # Overwrite present state from pickle
            for key, item in state.__dict__.items():
                self.__dict__[key] = item

            if verbosity > 0:
                print("Virtual broker state loaded from pickle.")
        except:
            print("Failed to load virtual broker state.")
        

    def _public_trade(self, instrument: str, 
                      trade: dict):
        """Uses a public trade to update virtual orders."""
        # TODO - use a Trade object
        trade_direction = trade['direction']
        trade_price = trade['price']
        trade_size = trade['size']
        trade_time = trade['time']

        trade_units_remaining = trade_size
        open_orders = self.get_orders(instrument).copy()
        for order_id, order in open_orders.items():
            if order.order_type == 'limit':
                if order.direction != trade_direction:
                    # Buy trade for sell orders, Sell trade for buy orders
                    order_price = Decimal(str(order.order_limit_price)).quantize(Decimal(str(trade_price)))
                    if trade_price == order_price and trade_units_remaining > 0:
                        # Fill as much as possible
                        trade_units_consumed = min(trade_units_remaining, order.size)
                        self._fill_order(order=order, 
                                         fill_time=trade_time,
                                         reference_price=order.order_limit_price,
                                         trade_size=trade_units_consumed)
                        
                        # Update trade_units_remaining
                        trade_units_remaining -= trade_units_consumed
                    