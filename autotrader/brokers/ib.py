import random
import ib_insync
import numpy as np
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from autotrader.brokers.broker import Broker
from autotrader.brokers.trading import Order, IsolatedPosition, Position


class Broker(Broker):
    """AutoTrader-InteractiveBrokers API interface.

    Attributes
    ----------
    utils : Utils
        The broker utilities.

    ib : ib_insync connection
        Used to query IB.

    account : str
        The active IB account.

    Notes
    -----
        - when closing a position using close_position(), if there are attached SL
          and/or TP orders, they must be closed manually using cancel_pending_order().
          Usually only one of the pair needs to be cancelled, and the other will too.
        - required signal_dict keys for different security types (eg. futures
          require symbol, exchange and contract_month)
        - The products localSymbol will always take precedence over the symbol.
          As such, it should be used as much as possible to avoid accidental
          actions.
    """

    def __init__(self, config: dict) -> None:
        """Initialise AutoTrader-Interactive Brokers API interface.

        Parameters
        ----------
        config : dict
            The IB configuration dictionary. This can contain the host, port,
            clientID and read_only boolean flag.

        utils : Utils, optional
            Broker utilities class instance. The default is None.
        """
        self.host = config["host"] if "host" in config else "127.0.0.1"
        self.port = config["port"] if "port" in config else 7497
        self.client_id = (
            config["clientID"] if "clientID" in config else random.randint(0, 9999)
        )
        self.read_only = config["read_only"] if "read_only" in config else False
        self.account = config["account"] if "account" in config else ""

        self.ib = ib_insync.IB()
        self._check_connection()
        self.account = self._get_account() if self.account == "" else self.account

        # Assign data broker
        self._data_broker = self

    def __repr__(self):
        return "AutoTrader-InteractiveBrokers interface"

    def __str__(self):
        return "AutoTrader-InteractiveBrokers interface"

    @property
    def data_broker(self):
        return self._data_broker

    def get_NAV(self) -> float:
        """Returns the net asset/liquidation value of the account."""
        self._check_connection()
        summary = self.get_summary()
        return float(summary["NetLiquidation"]["value"])

    def get_balance(self) -> float:
        """Returns account balance."""
        self._check_connection()
        summary = self.get_summary()
        return float(summary["TotalCashValue"]["value"])

    def place_order(self, order: Order, **kwargs) -> None:
        """Disassembles order_details dictionary to place order.

        Parameters
        ----------
        order: Order
            The AutoTrader Order.

        Returns
        -------
        None
            Orders will be submitted to IB.
        """
        self._check_connection()

        # Call order to set order time
        order()

        if order.order_type == "market":
            self._place_market_order(order)
        elif order.order_type == "stop-limit":
            self._place_stop_limit_order(order)
        elif order.order_type == "limit":
            self._place_limit_order(order)
        elif order.order_type == "close":
            self._close_position(order)
        else:
            print("Order type not recognised.")

        self._refresh()

    def get_orders(self, instrument: str = None, **kwargs) -> dict:
        """Returns all pending orders (have not been filled) in the account.

        Parameters
        ----------
        instrument : str, optional
            The trading instrument's symbol. The default is None.

        Returns
        -------
        dict
            Pending orders for the requested instrument. If no instrument is provided,
            all pending orders will be returned.
        """
        self._check_connection()

        # Get all open trades
        open_trades = self.ib.openTrades()

        pending_orders = {}
        for trade in open_trades:
            trade_dict = trade.dict()
            contract = trade_dict["contract"]
            order_dict = trade_dict["order"].dict()
            order_status_dict = trade_dict["orderStatus"].dict()
            order_status = order_status_dict["status"]

            if order_status in ib_insync.OrderStatus.ActiveStates:
                # Order is still active (not yet filled)
                new_order = {}
                new_order["order_ID"] = order_dict["orderId"]
                new_order["order_type"] = order_dict["orderType"]
                new_order["order_stop_price"] = order_dict["auxPrice"]
                new_order["order_limit_price"] = order_dict["lmtPrice"]
                new_order["direction"] = 1 if order_dict["action"] == "BUY" else -1
                new_order["order_time"] = None
                new_order["instrument"] = contract.symbol
                new_order["size"] = order_dict["totalQuantity"]
                new_order["order_price"] = None
                new_order["take_profit"] = None
                new_order["take_distance"] = None
                new_order["stop_type"] = None
                new_order["stop_distance"] = None
                new_order["stop_loss"] = None
                new_order["related_orders"] = None
                new_order["granularity"] = None
                new_order["strategy"] = None

                if instrument is not None and contract.symbol == instrument:
                    pending_orders[new_order["order_ID"]] = Order._from_dict(new_order)
                elif instrument is None:
                    pending_orders[new_order["order_ID"]] = Order._from_dict(new_order)

        return pending_orders

    def cancel_order(self, order_id: int, **kwargs) -> list:
        """Cancels pending order by order ID.

        Parameters
        ----------
        order_id : int
            The ID of the order to be concelled.

        Returns
        -------
        list
            A list of the cancelled trades.

        """
        self._check_connection()

        open_trades = self.ib.openTrades()
        cancelled_trades = []
        for trade in open_trades:
            order = trade.order
            if order.orderId == order_id:
                cancel_trade = self.ib.cancelOrder(order)
                cancelled_trades.append(cancel_trade)

        return cancelled_trades

    def get_trades(self, instrument: str = None, **kwargs) -> dict:
        """Returns the open trades held by the account.

        Parameters
        ----------
        instrument : str, optional
            The trading instrument's symbol. The default is None.

        Returns
        -------
        dict
            The open trades.
        """
        self._check_connection()

        # Get all open trades
        all_open_trades = self.ib.openTrades()

        open_trades = {}
        for trade in all_open_trades:
            trade_dict = trade.dict()
            contract = trade_dict["contract"]
            order_dict = trade_dict["order"].dict()
            order_status_dict = trade_dict["orderStatus"].dict()
            order_status = order_status_dict["status"]

            if order_status == "Filled":
                # Trade order has been filled
                new_trade = {}
                new_trade["order_ID"] = order_dict["orderId"]
                new_trade["order_stop_price"] = order_dict["auxPrice"]
                new_trade["order_limit_price"] = order_dict["lmtPrice"]
                new_trade["direction"] = 1 if order_dict["action"] == "BUY" else -1
                new_trade["order_time"] = None
                new_trade["instrument"] = contract.symbol
                new_trade["size"] = order_dict["totalQuantity"]
                new_trade["order_price"] = None
                new_trade["entry_price"] = order_status_dict["lastFillPrice"]
                new_trade["order_type"] = None
                new_trade["take_profit"] = None
                new_trade["take_distance"] = None
                new_trade["stop_type"] = None
                new_trade["stop_distance"] = None
                new_trade["stop_loss"] = None
                new_trade["related_orders"] = None
                new_trade["granularity"] = None
                new_trade["strategy"] = None

                if instrument is not None and contract.symbol == instrument:
                    open_trades[new_trade["order_ID"]] = IsolatedPosition(new_trade)
                elif instrument is None:
                    open_trades[new_trade["order_ID"]] = IsolatedPosition(new_trade)

        return open_trades

    def get_trade_details(self, trade_ID: str, **kwargs) -> dict:
        """Returns the details of the trade specified by trade_ID.

        Parameters
        ----------
        trade_ID : str
            The ID of the trade.

        Returns
        -------
        dict
            The details of the trade.
        """
        raise NotImplementedError(
            "This method is not available, and will "
            + "be deprecated with a future release. Please use the "
            + "get_trades method instead."
        )

    def get_positions(self, instrument: str = None, **kwargs) -> dict:
        """Gets the current positions open on the account.

        Parameters
        ----------
        instrument : str, optional
            The trading instrument's symbol. This can be either the naive
            symbol, or the localSymbol. The default is None.

        Returns
        -------
        open_positions : dict
            A dictionary containing details of the open positions.

        Notes
        -----
        This function returns the position in an underlying product. If
        there are multiple contracts on the underlying, they will be
        appended to the returned Position objects' "contracts" and
        "portfolio_items" attributes.
        """

        def adjust_position(existing_pos, portfolio_item, pos_dict):
            # Position item already exists, append portfolio item
            existing_pos.long_units += pos_dict["long_units"]
            existing_pos.long_PL += pos_dict["long_PL"]
            existing_pos.short_units += pos_dict["short_units"]
            existing_pos.short_PL += pos_dict["short_PL"]
            existing_pos.net_position += pos_dict["net_position"]
            existing_pos.PL += pos_dict["PL"]
            existing_pos.contracts.append(portfolio_item.contract)
            existing_pos.portfolio_items.append(portfolio_item)

        self._check_connection()

        all_portfolio_items = self.ib.portfolio()
        open_positions = {}
        for item in all_portfolio_items:
            units = item.position
            pnl = item.unrealizedPNL
            pos_symbol = item.contract.symbol
            pos_dict = {
                "long_units": units if np.sign(units) > 0 else 0,
                "long_PL": pnl if np.sign(units) > 0 else 0,
                "short_units": abs(units) if np.sign(units) < 0 else 0,
                "short_PL": pnl if np.sign(units) < 0 else 0,
                "net_position": units,
                "PL": pnl,
                "contracts": [item.contract],
                "portfolio_items": [item],
                "instrument": pos_symbol,
            }

            symbol_match = instrument == pos_symbol  # Product symbol match
            localSymbol_match = (
                instrument == item.contract.localSymbol
            )  # localSymbol match
            unique_match = symbol_match or localSymbol_match

            if instrument is not None and unique_match:
                # The current item matches the request, append it
                key_symbol = (
                    item.contract.localSymbol
                    if localSymbol_match
                    else item.contract.symbol
                )

                pos_dict["instrument"] = key_symbol

                if pos_symbol in open_positions:
                    # Portfolio item already exists, append portfolio item
                    existing_pos = open_positions[pos_symbol]
                    adjust_position(existing_pos, item, pos_dict)
                else:
                    # New position
                    open_positions[key_symbol] = Position(**pos_dict)

            elif instrument is None:
                # Append all positions
                if pos_symbol in open_positions:
                    # Position item already exists, append portfolio item
                    existing_pos = open_positions[pos_symbol]
                    adjust_position(existing_pos, item, pos_dict)
                else:
                    # New position
                    open_positions[pos_symbol] = Position(**pos_dict)

        return open_positions

    def get_candles(
        self,
        instrument: str,
        granularity: str = None,
        count: int = None,
        start_time: datetime = None,
        end_time: datetime = None,
        *args,
        **kwargs,
    ) -> pd.DataFrame:
        """Get the historical OHLCV candles for an instrument."""
        raise NotImplementedError(
            "Historical market data from IB is not yet supported."
        )

    def get_orderbook(self, instrument: str, *args, **kwargs):
        """Get the orderbook for an instrument."""
        pass

    def get_public_trades(self, instrument: str, *args, **kwargs):
        """Get the public trade history for an instrument."""
        pass

    def get_summary(self) -> dict:
        """Returns account summary."""
        self._check_connection()
        raw_summary = self.ib.accountSummary(self.account)
        summary = self.accsum_to_dict(self.account, raw_summary)

        return summary

    def _get_historical_data(
        self, instrument: str, interval: str, from_time: str, to_time: str
    ):
        """Returns historical price data."""
        # self._check_connection()
        # self.ib.reqHistoricalData()
        raise NotImplementedError("This method is not available.")

    def _connect(self):
        """Connects from IB application."""
        self.ib.connect(
            host=self.host,
            port=self.port,
            clientId=self.client_id,
            readonly=self.read_only,
            account=self.account,
        )

    def _disconnect(self):
        """Disconnects from IB application."""
        self.ib.disconnect()

    def _check_connection(self):
        """Checks if there is an active connection to IB. If not, will
        attempt to reconnect.
        """
        self._refresh()
        connected = self.ib.isConnected()

        while not connected:
            try:
                # Try to connect
                self.ib = ib_insync.IB()
                self._connect()
            except:
                print("Connection to IB failed... trying to reconnect.")
                # Connection failed, increment client ID
                self.client_id = random.randint(0, 9999)

                # Sleep for a little while
                self.ib.sleep(10)

            # Update connection status
            connected = self.ib.isConnected()

    def _refresh(self):
        """Refreshes IB session events."""
        self.ib.sleep(0)

    def _get_account(
        self,
    ):
        """Returns the first managed account."""
        self._check_connection()
        accounts = self.ib.managedAccounts()
        return accounts[0]

    def _close_position(self, order: Order, **kwargs):
        """Closes open position of symbol by placing opposing market order.

        Warning
        -------
        If the order instrument is for an underlying product, all contracts
        held attributed to the underlying will be closed.
        """
        self._check_connection()

        symbol = (
            order.localSymbol if order.localSymbol is not None else order.instrument
        )
        positions = self.get_positions(instrument=symbol)
        position = positions[symbol]

        for item in position.portfolio_items:
            # Place opposing market order
            item_units = item.position
            action = "BUY" if item_units < 0 else "SELL"
            units = abs(item_units)
            IB_order = ib_insync.MarketOrder(action, units)
            contract = item.contract
            self.ib.qualifyContracts(contract)
            self.ib.placeOrder(contract, IB_order)

    def _place_market_order(self, order: Order):
        """Places a market order."""
        self._check_connection()

        # Build contract
        contract = self.build_contract(order)

        # Create market order
        action = "BUY" if order.direction > 0 else "SELL"
        units = abs(order.size)
        market_order = ib_insync.MarketOrder(
            action, units, orderId=self.ib.client.getReqId(), transmit=False
        )

        # Attach SL and TP orders
        orders = self._attach_auxiliary_orders(order, market_order)

        # Submit orders
        self._process_orders(contract, orders)

    def _place_stop_limit_order(self, order):
        """Places stop-limit order."""
        self._check_connection()

        # Build contract
        contract = self.build_contract(order)

        # Create stop limit order
        action = "BUY" if order.direction > 0 else "SELL"
        units = abs(order.size)
        lmtPrice = order.order_limit_price
        stopPrice = order.order_stop_price
        IBorder = ib_insync.StopLimitOrder(
            action,
            units,
            lmtPrice,
            stopPrice,
            orderId=self.ib.client.getReqId(),
            transmit=False,
        )

        # Attach SL and TP orders
        orders = self._attach_auxiliary_orders(order, IBorder)

        # Submit orders
        self._process_orders(contract, orders)

    def _place_limit_order(self, order):
        """Places limit order."""
        self._check_connection()

        # Build contract
        contract = self.build_contract(order)

        action = "BUY" if order.direction > 0 else "SELL"
        units = abs(order.size)
        lmtPrice = order.order_limit_price
        IBorder = ib_insync.LimitOrder(
            action, units, lmtPrice, orderId=self.ib.client.getReqId(), transmit=False
        )

        # Attach SL and TP orders
        orders = self._attach_auxiliary_orders(order, IBorder)

        # Submit orders
        self._process_orders(contract, orders)

    def _attach_auxiliary_orders(
        self, order: Order, parent_order: ib_insync.order
    ) -> list:
        orders = [parent_order]

        # TP order
        if order.take_profit is not None:
            takeProfit_order = self._create_take_profit_order(
                order, parent_order.orderId
            )
            orders.append(takeProfit_order)

        # SL order
        if order.stop_loss is not None:
            stopLoss_order = self._create_stop_loss_order(order, parent_order.orderId)
            orders.append(stopLoss_order)

        return orders

    def _process_orders(self, contract: ib_insync.Contract, orders: list) -> None:
        """Processes a list of orders for a given contract."""
        self._check_connection()

        # Submit orders
        for i, order in enumerate(orders):
            if i == len(orders) - 1:
                # Final order; set transmit to True
                order.transmit = True
            else:
                order.transmit = False
            self.ib.placeOrder(contract, order)

    def _convert_to_oca(
        self, orders: list, oca_group: str = None, oca_type: int = 1
    ) -> list:
        """Converts a list of Orders to One Cancels All group of orders.

        Parameters
        ----------
        orders : list
            A list of orders.

        Returns
        -------
        oca_orders : list
            The orders modified to be in a OCA group.
        """
        self._check_connection()

        if oca_group is None:
            oca_group = f"OCA_{self.ib.client.getReqId()}"

        oca_orders = self.ib.oneCancelsAll(orders, oca_group, oca_type)
        return oca_orders

    def _create_take_profit_order(self, order: Order, parentId: int):
        """Constructs a take profit order."""
        quantity = order.size
        takeProfitPrice = order.take_profit
        action = "BUY" if order.direction < 0 else "SELL"
        takeProfit_order = ib_insync.LimitOrder(
            action,
            quantity,
            takeProfitPrice,
            orderId=self.ib.client.getReqId(),
            transmit=False,
            parentId=parentId,
        )
        return takeProfit_order

    def _create_stop_loss_order(self, order: Order, parentId: int):
        """Constructs a stop loss order."""
        # TODO - add support for trailing SL
        quantity = order.size
        stopLossPrice = order.stop_loss
        action = "BUY" if order.direction < 0 else "SELL"
        stopLoss_order = ib_insync.StopOrder(
            action,
            quantity,
            stopLossPrice,
            orderId=self.ib.client.getReqId(),
            transmit=True,
            parentId=parentId,
        )
        return stopLoss_order

    @staticmethod
    def check_response(response):
        """Checks API response for errors.

        Parameters
        ----------
        response : TYPE
            DESCRIPTION.

        Returns
        -------
        output : TYPE
            DESCRIPTION.
        """

        if response.status != 201:
            message = response.body["errorMessage"]
        else:
            message = "Success."

        output = {"Status": response.status, "Message": message}

        return output

    def check_precision(self, pair, price):
        """Modify a price based on required ordering precision for pair."""
        N = self.get_precision(pair)
        corrected_price = round(price, N)
        return corrected_price

    def get_precision(self, instrument: str, *args, **kwargs):
        """Returns the precision of the instrument."""
        # TODO - implement
        return {"size": 5, "price": 5}

    def check_trade_size(self, pair, units):
        """Checks the requested trade size against the minimum trade size
        allowed for the currency pair."""
        response = self.api.account.instruments(
            accountID=self.ACCOUNT_ID, instruments=pair
        )
        # minimum_units = response.body['instruments'][0].minimumTradeSize
        trade_unit_precision = response.body["instruments"][0].tradeUnitsPrecision

        return round(units, trade_unit_precision)

    @staticmethod
    def build_contract(order: Order) -> ib_insync.contract.Contract:
        """Builds IB contract from the order details."""
        instrument = order.instrument
        security_type = order.secType

        # Get contract object
        contract_object = getattr(ib_insync, security_type)

        if security_type == "Stock":
            # symbol='', exchange='', currency=''
            exchange = order.exchange if order.exchange else "SMART"
            currency = order.currency if order.currency else "USD"
            contract = contract_object(
                symbol=instrument, exchange=exchange, currency=currency
            )

        elif security_type == "Options":
            raise NotImplementedError(
                f"Contract building for {security_type.lower()} trading is not supported yet."
            )

        elif security_type == "Future":
            # Requires order_details{'instrument', 'exchange', 'contract_month'}
            exchange = order.exchange if order.exchange else "GLOBEX"
            currency = order.currency if order.currency else "USD"
            contract_month = order.contract_month
            local_symbol = order.localSymbol if order.localSymbol else ""
            contract = contract_object(
                symbol=instrument,
                exchange=exchange,
                currency=currency,
                lastTradeDateOrContractMonth=contract_month,
                localSymbol=local_symbol,
            )

        elif security_type == "ContFuture":
            raise NotImplementedError(
                f"Contract building for {security_type.lower()} trading is not supported yet."
            )

        elif security_type == "Forex":
            # pair='', exchange='IDEALPRO', symbol='', currency='', **kwargs)
            exchange = order.exchange if order.exchange else "IDEALPRO"
            contract = contract_object(pair=instrument, exchange=exchange)

        elif security_type == "Index":
            raise NotImplementedError(
                f"Contract building for {security_type.lower()} trading is not supported yet."
            )

        elif security_type == "CFD":
            # symbol='', exchange='', currency='',
            exchange = order.exchange if order.exchange else "SMART"
            currency = order.currency if order.currency else "USD"
            contract = contract_object(
                symbol=instrument, exchange=exchange, currency=currency
            )

        elif security_type == "Commodity":
            raise NotImplementedError(
                f"Contract building for {security_type.lower()} trading is not supported yet."
            )
        elif security_type == "Bond":
            raise NotImplementedError(
                f"Contract building for {security_type.lower()} trading is not supported yet."
            )
        elif security_type == "FuturesOption":
            raise NotImplementedError(
                f"Contract building for {security_type.lower()} trading is not supported yet."
            )
        elif security_type == "MutualFund":
            raise NotImplementedError(
                f"Contract building for {security_type.lower()} trading is not supported yet."
            )
        elif security_type == "Warrant":
            raise NotImplementedError(
                f"Contract building for {security_type.lower()} trading is not supported yet."
            )
        elif security_type == "Bag":
            raise NotImplementedError(
                f"Contract building for {security_type.lower()} trading is not supported yet."
            )
        elif security_type == "Crypto":
            raise NotImplementedError(
                f"Contract building for {security_type.lower()} trading is not supported yet."
            )

        return contract

    @staticmethod
    def accsum_to_dict(account: str = None, data: list = None) -> dict:
        """Returns account summary list as a dictionary.

        Parameters
        ----------
        account : str
            DESCRIPTION.
        data : list
            DESCRIPTION.

        Returns
        -------
        out
            DESCRIPTION.
        """

        if account is None:
            account = "All"

        out = {}
        for av in data:
            if av.account == account:
                out[av.tag] = {
                    "value": av.value,
                    "currency": av.currency,
                    "modelCode": av.modelCode,
                }

        return out

    @staticmethod
    def positionlist_to_dict(positions: list) -> dict:
        """Returns position list as a dictionary.

        Parameters
        ----------
        positions : list
            DESCRIPTION.

        Returns
        -------
        dict
            DESCRIPTION.

        """
        pass

    @staticmethod
    def _futures_expiry(dt: datetime = datetime.now(), months: int = 1) -> str:
        """Returns a string of format YYYYMM corresponding to the leading
        contract month, from the inputted datetime object.

        Parameters
        ----------
        dt : datetime, optional
            The datetime object to convert to string. The default is datetime.now().
        months : int, optional
            The month offset from dt. The default is 1.

        Returns
        -------
        str
            A string corresponding to the expiry.
        """
        # TODO - if current date is past last trade date... error
        expiry_dt = dt + relativedelta(months=months)
        return expiry_dt.strftime("%Y") + expiry_dt.strftime("%m")

    def get_precision(self, instrument, *args, **kwargs):
        """Returns the precision of the instrument."""
        # NOTE: this has not been formally implemented yet.
        # TODO - implement
        return {"size": 5, "price": 5}
