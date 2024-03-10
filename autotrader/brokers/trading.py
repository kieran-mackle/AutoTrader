import numpy as np
import pandas as pd
from decimal import Decimal
from datetime import datetime
from typing import Literal, Union


class Order:
    """AutoTrader Order object."""

    def __init__(
        self,
        instrument: str = None,
        direction: int = None,
        size: float = None,
        order_type: Literal["market", "limit", "stop-limit", "modify"] = "market",
        order_limit_price: float = None,
        order_stop_price: float = None,
        stop_loss: float = None,
        stop_type: str = "limit",
        take_profit: float = None,
        related_orders: list[Union[str, int]] = None,
        **kwargs,
    ):
        """Create a new order.

        Parameters
        ----------
        instrument : str
            The trading instrument of the order.

        direction : int
            The direction of the order (1 for long, -1 for short).

        order_type : str
            The type of order. The default is 'market'.

        size : float
            The number of units.

        order_limit_price : float
            The limit price of the order (for 'limit' and 'stop-limit' order
            types).

        order_stop_price : float
            The stop price of the order (for 'stop-limit' order types).

        stop_loss : float
            The price to set the stop-loss at.

        stop_type : str
            The type of stop-loss (limit or trailing). The default is 'limit'.

        take_profit : float
            The price to set the take-profit at.

        related_orders : list[str | int]
            A list of related order/trade ID's.

        secType : str
            The security type (IB only).

        contract_month : str
            The contract month string (IB only).

        localSymbol : str
            The exchange-specific instrument symbol (IB only).

        limit_fee : str, optional
            The maximum fee to accept as a percentage (dYdX only). The default
            is '0.015'.

        ccxt_params : dict, optional
            The CCXT parameters dictionary to pass when creating an order. The
            default is {}.
        """
        # TODO - implement post-only

        # Required attributes
        self.instrument = instrument if instrument is not None else None
        self.direction = np.sign(direction) if direction is not None else None
        self.order_type = order_type

        # Optional arguments
        self.size = Decimal(str(size)) if size is not None else None
        self.order_price = None
        self.order_time = None
        self.order_limit_price = (
            Decimal(str(order_limit_price)) if order_limit_price else None
        )
        self.order_stop_price = (
            Decimal(str(order_stop_price)) if order_stop_price else None
        )

        # Multi-exchange handling
        self.exchange = None

        # Stop loss arguments
        self.stop_loss = Decimal(str(stop_loss)) if stop_loss else None
        self.stop_type = stop_type

        # Take profit arguments
        self.take_profit = Decimal(str(take_profit)) if take_profit else None

        self.related_orders = related_orders

        # Reduce only order
        self.parent_order = None  # Parent order ID
        self.reduce_only = False
        self.OCO = []  # One-cancels-other

        # IB attributes
        self.currency = None
        self.secType = None
        self.contract_month = None
        self.localSymbol = None

        # Oanda attributes
        self.trigger_price = "DEFAULT"

        # CCXT attributes
        self.ccxt_params = {}  # CCXT order parameters
        self.ccxt_order = {}  # CCXT native order structure

        # Meta
        self.reason = None
        self.strategy = None
        self.granularity = None
        self._sizing = None
        self._risk_pc = None
        self.id: Union[int, str] = None
        self.status: Literal["submitted", "pending", "open", "cancelled", "filled"] = (
            None
        )

        # Unpack kwargs
        for item in kwargs:
            setattr(self, item, kwargs[item])

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        if self.instrument is None:
            # Blank order
            return "Blank order"

        else:
            # Order constructed with instrument
            if self.size is not None:
                if self.direction is None:
                    return "Invalid order (direction not specified)"

                side = "buy" if self.direction > 0 else "sell"

                string = (
                    f"{self.size} "
                    + f"unit {self.instrument} {self.order_type} "
                    + f"{side} order"
                )

                # Append additional information
                if self.order_type == "limit":
                    if self.order_limit_price is None:
                        return "Invalid order (limit price not provided)"
                    string += f" @ {self.order_limit_price}"

                elif self.order_type == "stop-limit":
                    if self.order_limit_price is None:
                        return "Invalid order (limit price not provided)"
                    elif self.order_stop_price is None:
                        return "Invalid order (stop price not provided)"
                    string += f" @ {self.order_stop_price} / {self.order_limit_price}"

                elif self.order_type == "stop":
                    if self.order_stop_price is None:
                        return "Invalid order (stop price not provided)"
                    string += f" @ {self.order_stop_price}"

                return string

            else:
                # Size un-assigned
                return f"{self.instrument} {self.order_type} Order"

    def __call__(
        self,
        order_price: Decimal = None,
        order_time: datetime = datetime.now(),
    ) -> None:
        """Order object, called before submission to broker in
        autobot._qualify_orders.

        Parameters
        ----------
        order_price : Decimal, optional
            The order price. The default is None.

        order_time : datetime, optional
            The time of the order. The default is datetime.now().

        precision : dict, optional
            A dictionary containing the precision for order size and price.
            The default is None.

        Returns
        -------
        None
            Calling an Order will ensure all information is present.
        """
        self.order_price = (
            Decimal(str(order_price)) if order_price else self.order_price
        )
        self.order_time = order_time if order_time else self.order_time

        # Enforce size scalar
        self.size = abs(Decimal(str(self.size))) if self.size is not None else self.size
        self.status = "submitted"
        self.submitted = True

    @classmethod
    def _partial_fill(cls, order: "Order", units_filled: Decimal) -> "Order":
        """Partially fills the order."""
        # Enforce Decimal type
        units_filled = Decimal(str(units_filled))

        # Instantiate new order
        order_to_be_filled = cls()

        # Inherit attributes from base order
        for attribute, value in order.__dict__.items():
            setattr(order_to_be_filled, attribute, value)

        # Reset ID
        order_to_be_filled.id = None

        # Transfer units
        order_to_be_filled.size = units_filled
        order.size -= units_filled

        return order_to_be_filled

    def _check_precision(
        self,
    ):
        # TODO - implement
        raise NotImplementedError("This method has not been implemented yet.")

    def _validate(
        self,
    ):
        # TODO - add order validation method, ie. for IB, check all attributes are
        # assigned (eg. sectype, etc)
        raise NotImplementedError("This method has not been implemented yet.")

    def as_dict(self) -> dict:
        """Converts Order object to dictionary.

        Returns
        -------
        dict
            The order instance returned as a dict object.

        Notes
        -----
        This method enables legacy code operation, returning order/trade
        objects as a dictionary.
        """
        return self.__dict__

    @classmethod
    def _from_dict(cls, order_dict: dict) -> "Order":
        return Order(**order_dict)

    def _modify_from(self, order: "Order"):
        """Modify this order from another order."""
        # TODO - review what can be changed here

        # Check order limit price
        if order.order_limit_price is not None:
            self.order_limit_price = Decimal(str(order.order_limit_price))

        # Check size
        if order.size is not None:
            self.size = Decimal(str(order.size))

        # Check stop loss
        if order.stop_loss is not None:
            self.stop_loss = Decimal(str(order.stop_loss))

        # Check take profit
        if order.take_profit is not None:
            self.take_profit = Decimal(str(order.take_profit))


class MarketOrder(Order):
    """Market order type."""

    def __init__(
        self,
        instrument: str = None,
        direction: int = None,
        size: float = None,
        **kwargs,
    ):
        # Create base Order
        super().__init__(
            instrument=instrument,
            direction=direction,
            order_type="market",
            size=size,
            **kwargs,
        )


class LimitOrder(Order):
    """Limit order type."""

    def __init__(
        self,
        instrument: str = None,
        direction: int = None,
        size: float = None,
        order_limit_price: float = None,
        **kwargs,
    ):
        # Create base Order
        super().__init__(
            instrument=instrument,
            direction=direction,
            order_type="limit",
            size=size,
            order_limit_price=order_limit_price,
            **kwargs,
        )


class StopLimitOrder(Order):
    """Stop-limit order type."""

    def __init__(
        self,
        instrument: str = None,
        direction: int = None,
        size: float = None,
        order_limit_price: float = None,
        order_stop_price: float = None,
        **kwargs,
    ):
        # Create base Order
        super().__init__(
            instrument=instrument,
            direction=direction,
            order_type="stop-limit",
            size=size,
            order_limit_price=order_limit_price,
            order_stop_price=order_stop_price,
            **kwargs,
        )


class IsolatedPosition(Order):
    """AutoTrader IsolatedPosition. Use to connect SL and TP orders to individual
    trades.

    Attributes
    ----------
    unrealised_PL : float
        The floating PnL of the trade.

    margin_required : float
        The margin required to maintain the trade.

    time_filled : datetime
        The time at which the trade was filled.

    fill_price : float
        The price at which the trade was filled.

    last_price : float
        The last price observed for the instrument associated with the trade.

    last_time : datetime
        The last time observed for the instrument associated with the trade.

    exit_price : float
        The price at which the trade was closed.

    exit_time : datetime
        The time at which the trade was closed.

    fees : float
        The fees associated with the trade.

    parent_id : int
        The ID of the order which spawned the trade.

    id : int
        The trade ID.

    status : str
        The status of the trade (open or closed).

    split : bool
        If the trade has been split.

    Notes
    -----
    When a trade is created from an Order, the Order will be marked as filled.
    """

    def __init__(self, order: Order = None, **kwargs):
        # Trade data
        self.unrealised_PL = 0
        self.margin_required = 0
        self.time_filled = None
        self.fill_price = None

        self.last_price = None
        self.last_time = None

        self.profit = 0
        self.balance = None
        self.exit_price = None
        self.exit_time = None
        self.fees = None

        # Meta data
        self.parent_id = None  # ID of order which spawned trade
        self.id = None
        self.status = None  # options: open -> closed
        self.split = False

        # Unpack kwargs
        for item in kwargs:
            setattr(self, item, kwargs[item])

        # Inherit order attributes
        if order:
            self._inheret_order(order)
            self.parent_id = order.id

    def __repr__(self):
        direction = "long" if self.direction > 0 else "short"
        return (
            f"{round(self.size,3)} unit {direction} {self.instrument} IsolatedPosition"
        )

    def __str__(self):
        return "AutoTrader IsolatedPosition"

    def _inheret_order(self, order: Order) -> None:
        for attribute, value in order.__dict__.items():
            setattr(self, attribute, value)

    @classmethod
    def _split(
        cls, trade: "IsolatedPosition", split_units: Decimal
    ) -> "IsolatedPosition":
        """Splits parent IsolatedPosition into new object for partial
        closures.

        split units are given to the new trade.
        """
        split_trade = cls()
        for attribute, value in trade.__dict__.items():
            setattr(split_trade, attribute, value)

        # Reset ID
        split_trade.parent_id = trade.parent_id
        split_trade.order_id = None

        # Transfer units
        split_trade.size = Decimal(str(split_units))
        trade.size -= Decimal(str(split_units))

        # Mark original trade as split
        trade.split = True

        return split_trade


class Trade:
    """AutoTrader Trade object. Represents an exchange of value."""

    def __init__(
        self,
        instrument: str,
        order_price: Decimal,
        order_time: datetime,
        order_type: str,
        size: Decimal,
        last_price: Decimal,
        fill_time: datetime,
        fill_price: Decimal,
        fill_direction: int,
        fee: Decimal,
        **kwargs,
    ):
        """Trade constructor."""
        # Trade data
        self.fill_time = fill_time
        self.fill_price = fill_price
        self.direction = fill_direction
        self.fee = fee
        self.last_price = last_price
        self.order_price = order_price
        self.order_time = order_time
        self.order_type = order_type
        self.size = size
        self.instrument = instrument

        # Precision attributes
        # TODO - review this!
        self._price_precision = 15
        self._size_precision = 15

        # Meta-data
        self.id = None
        self.order_id = None

        for item in kwargs:
            setattr(self, item, kwargs[item])

    def __repr__(self):
        direction = "long" if self.direction > 0 else "short"
        return f"{round(self.size,3)} unit {direction} {self.instrument} trade @ {self.fill_price}"

    def __str__(self):
        return "AutoTrader Trade"


class Position:
    """AutoTrader Position object.

    Attributes
    ----------
    instrument : str
        The trade instrument of the position.

    pnl : float
        The pnl of the position.

    long_units : float
        The number of long units in the position.

    long_PL : float
        The PnL of the long units in the position.

    long_margin : float
        The margin required to maintain the long units in the position.

    short_units : float
        The number of short units in the position.

    short_PL : float
        The PnL of the short units in the position.

    short_margin : float
        The margin required to maintain the short units in the position.

    total_margin : float
        The total margin required to maintain the position.

    trade_IDs : list[int]
        The trade ID's associated with the position.

    net_position : float
        The total number of units in the position.

    net_exposure : float
        The net exposure (in $ value) of the position.

    PL : float
        The floating PnL (IB only).

    contracts : list
        The contracts associated with the position (IB only).

    portfolio_items : list
        The portfolio items associated with the position (IB only).
    """

    def __init__(self, **kwargs):
        self.instrument = None
        self.net_position = None
        self.pnl = 0
        self.long_units = None
        self.long_PL = None
        self.long_margin = None
        self.short_units = None
        self.short_PL = None
        self.short_margin = None
        self.total_margin = None
        self.trade_IDs = None
        self.net_exposure = None
        self.notional = 0
        # TODO - review this!
        self.price_precision = 15
        self.size_precision = 15
        self.avg_price = None
        self._prev_avg_price = None

        # TODO - include position open time, close time
        # Also need to track max units ? I think that can all be built
        # from fills
        self.entry_time = None
        self.last_price = None
        self.last_time = None
        self.exit_time = None
        self.exit_price = None

        self.direction = None
        # self.max_size = None # ?

        # IB Attributes
        self.PL = None
        self.contracts = None
        self.portfolio_items = None

        # dYdX Attributes
        self.entry_price = None

        # CCXT Attributes
        self.ccxt = None

        for item in kwargs:
            setattr(self, item, kwargs[item])

    def __repr__(self):
        return f"Position in {self.instrument}"

    def __str__(self):
        return "AutoTrader Position"

    def _update_with_fill(self, trade: Trade):
        """Updates the position with the order provided."""
        net_position_before_fill = self.net_position

        # Update net position
        self.net_position += trade.size * trade.direction

        # Update average entry price
        self._prev_avg_price = self.avg_price
        if self.net_position * net_position_before_fill >= 0:
            # Position has not flipped
            if abs(self.net_position) > abs(net_position_before_fill):
                # Position has increased
                self.avg_price = round(
                    (
                        self.avg_price * abs(self.net_position)
                        + trade.fill_price * trade.size
                    )
                    / (abs(self.net_position) + trade.size),
                    self.price_precision,
                )
            # If position has reduced, average entry price will not change
        else:
            # Position has flipped
            self.avg_price = round(trade.fill_price, self.price_precision)

        # Update last price and last time
        self.last_price = trade.last_price
        self.last_time = trade.fill_time

        # TODO - update value of position
        # self.net_exposure
        self.notional = self.last_price * abs(self.net_position)

    @classmethod
    def _from_fill(cls, trade: Trade):
        """Returns a Position from a fill."""
        position = cls(
            instrument=trade.instrument,
            net_position=abs(trade.size) * trade.direction,
            last_price=trade.last_price,
            last_time=trade.fill_time,
            entry_time=trade.fill_time,
            entry_price=trade.fill_price,
            avg_price=trade.fill_price,
            notional=trade.fill_price * abs(trade.size),
            price_precision=trade._price_precision,
            size_precision=trade._size_precision,
            direction=trade.direction,
        )
        # TODO - update attributes created
        # - exposure, value, etc.
        return position

    def as_dict(self) -> dict:
        """Converts Position object to dictionary.

        Returns
        -------
        dict
            The Position instance returned as a dict object.

        Notes
        -----
        This method enables legacy code operation, returning order/trade
        objects as a dictionary.
        """
        return self.__dict__


class OrderBook:
    def __init__(self, instrument: str, initial_state: dict):
        # TODO - review, make all Decimals
        self.instrument = instrument
        self.bids = None
        self.asks = None
        self._midprice = None
        self._spread = None

        # Initialise from initial state
        self.bids = pd.DataFrame(initial_state["bids"]).astype(float)
        self.asks = pd.DataFrame(initial_state["asks"]).astype(float)

        # Sort quotes
        self.bids.sort_values(by="price", ascending=False, inplace=True)
        self.asks.sort_values(by="price", ascending=True, inplace=True)

        # Calculate spread and midprice
        spread = float(self.asks.price.min()) - float(self.bids.price.max())
        midprice = (float(self.asks.price.min()) + float(self.bids.price.max())) / 2

        # Quantize
        # TODO - use ticksize and step size to quantize
        ref = Decimal(str(self.bids["price"][0]))
        self.spread = float(Decimal(spread).quantize(ref))
        self.midprice = float(Decimal(midprice).quantize(ref))

    def __repr__(self):
        return f"{self.instrument} Order Book snapshot"

    @property
    def midprice(self):
        return self._midprice

    @midprice.setter
    def midprice(self, value):
        self._midprice = value

    @property
    def spread(self):
        return self._spread

    @spread.setter
    def spread(self, value):
        self._spread = value
