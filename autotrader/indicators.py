import numpy as np
import pandas as pd
from finta import TA
from typing import Union


def supertrend(
    data: pd.DataFrame,
    period: int = 10,
    ATR_multiplier: float = 3.0,
    source: pd.Series = None,
) -> pd.DataFrame:
    """SuperTrend indicator, ported from the SuperTrend indicator by
    KivancOzbilgic on TradingView.

    Parameters
    ----------
    data : pd.DataFrame
        The OHLC data.

    period : int, optional
        The lookback period. The default is 10.

    ATR_multiplier : int, optional
        The ATR multiplier. The default is 3.0.

    source : pd.Series, optional
        The source series to use in calculations. If None, hl/2 will be
        used. The default is None.

    Returns
    -------
    supertrend_df : pd.DataFrame
        A Pandas DataFrame of containing the SuperTrend indicator, with
        columns of 'uptrend' and 'downtrend' containing uptrend/downtrend
        support/resistance levels, and 'trend', containing -1/1 to indicate
        the current implied trend.

    References
    ----------
    https://www.tradingview.com/script/r6dAP7yi/
    """

    if source is None:
        source = (data["High"].values + data["Low"].values) / 2

    # Calculate ATR
    atr = TA.ATR(data, period)

    up = source - (ATR_multiplier * atr)
    up_list = [up[0]]
    up_times = [data.index[0]]
    N_up = 0

    dn = source + (ATR_multiplier * atr)
    dn_list = [dn[0]]
    dn_times = [data.index[0]]
    N_dn = 0

    trend = 1
    trend_list = [trend]

    for i in range(1, len(data)):
        if trend == 1:
            if data["Close"].values[i] > max(up[N_up:i]):
                up_list.append(max(up[N_up:i]))
                up_times.append(data.index[i])

                dn_list.append(np.nan)
                dn_times.append(data.index[i])
            else:
                trend = -1
                N_dn = i
                dn_list.append(dn[i])
                dn_times.append(data.index[i])

                up_list.append(np.nan)
                up_times.append(data.index[i])

        else:
            if data["Close"].values[i] < min(dn[N_dn:i]):
                dn_list.append(min(dn[N_dn:i]))
                dn_times.append(data.index[i])

                up_list.append(np.nan)
                up_times.append(data.index[i])
            else:
                trend = 1
                N_up = i
                up_list.append(up[i])
                up_times.append(data.index[i])

                dn_list.append(np.nan)
                dn_times.append(data.index[i])

        trend_list.append(trend)

    supertrend_df = pd.DataFrame(
        {"uptrend": up_list, "downtrend": dn_list, "trend": trend_list}, index=up_times
    )
    return supertrend_df


def halftrend(
    data: pd.DataFrame, amplitude: int = 2, channel_deviation: float = 2
) -> pd.DataFrame:
    """HalfTrend indicator, ported from the HalfTrend indicator by
    Alex Orekhov (everget) on TradingView.

    Parameters
    ----------
    data : pd.DataFrame
        OHLC price data.

    amplitude : int, optional
        The lookback window. The default is 2.

    channel_deviation : float, optional
        The ATR channel deviation factor. The default is 2.

    Returns
    -------
    htdf : TYPE
        DESCRIPTION.

    References
    ----------
    https://www.tradingview.com/script/U1SJ8ubc-HalfTrend/
    """

    # Initialisation
    atr2 = TA.ATR(data, 100) / 2
    dev = channel_deviation * atr2
    high_price = data["High"].rolling(amplitude).max().fillna(0)
    low_price = data["Low"].rolling(amplitude).min().fillna(0)
    highma = TA.SMA(data, period=amplitude, column="High")
    lowma = TA.SMA(data, period=amplitude, column="Low")

    trend = np.zeros(len(data))
    next_trend = np.zeros(len(data))
    max_low_price = np.zeros(len(data))
    max_low_price[0] = data["Low"].iloc[0]
    min_high_price = np.zeros(len(data))
    min_high_price[0] = data["High"].iloc[0]

    for i in range(1, len(data)):
        if next_trend[i - 1] == 1:
            max_low_price[i] = max(low_price.iloc[i - 1], max_low_price[i - 1])

            if (
                highma.iloc[i] < max_low_price[i]
                and data["Close"].iloc[i] < data["Low"].iloc[i - 1]
            ):
                trend[i] = 1
                next_trend[i] = 0
                min_high_price[i] = high_price.iloc[i]
            else:
                # assign previous values again
                trend[i] = trend[i - 1]
                next_trend[i] = next_trend[i - 1]
                min_high_price[i] = min_high_price[i - 1]
        else:
            min_high_price[i] = min(high_price.iloc[i - 1], min_high_price[i - 1])

            if (
                lowma.iloc[i] > min_high_price[i]
                and data["Close"].iloc[i] > data["High"].iloc[i - 1]
            ):
                trend[i] = 0
                next_trend[i] = 1
                max_low_price[i] = low_price.iloc[i]
            else:
                # assign previous values again
                trend[i] = trend[i - 1]
                next_trend[i] = next_trend[i - 1]
                max_low_price[i] = max_low_price[i - 1]

    up = np.zeros(len(data))
    up[0] = max_low_price[0]
    down = np.zeros(len(data))
    down[0] = min_high_price[0]
    atr_high = np.zeros(len(data))
    atr_low = np.zeros(len(data))

    for i in range(1, len(data)):
        if trend[i] == 0:
            if trend[i - 1] != 0:
                up[i] = down[i - 1]
            else:
                up[i] = max(max_low_price[i - 1], up[i - 1])

            atr_high[i] = up[i] + dev.iloc[i]
            atr_low[i] = up[i] - dev.iloc[i]

        else:
            if trend[i - 1] != 1:
                down[i] = up[i - 1]
            else:
                down[i] = min(min_high_price[i - 1], down[i - 1])

            atr_high[i] = down[i] + dev.iloc[i]
            atr_low[i] = down[i] - dev.iloc[i]

    halftrend = np.where(trend == 0, up, down)
    buy = np.where((trend == 0) & (np.roll(trend, 1) == 1), 1, 0)
    sell = np.where((trend == 1) & (np.roll(trend, 1) == 0), 1, 0)

    # Construct DataFrame
    htdf = pd.DataFrame(
        data={
            "halftrend": halftrend,
            "atrHigh": np.nan_to_num(atr_high),
            "atrLow": np.nan_to_num(atr_low),
            "buy": buy,
            "sell": sell,
        },
        index=data.index,
    )

    # Clear false leading signals
    htdf["buy"].values[:100] = np.zeros(100)
    htdf["sell"].values[:100] = np.zeros(100)

    # Replace leading zeroes with nan
    htdf["atrHigh"] = htdf.atrHigh.replace(to_replace=0, value=float("nan"))
    htdf["atrLow"] = htdf.atrLow.replace(to_replace=0, value=float("nan"))

    return htdf


def range_filter(
    data: pd.DataFrame,
    range_qty: float = 2.618,
    range_period: int = 14,
    smooth_range: bool = True,
    smooth_period: int = 27,
    av_vals: bool = False,
    av_samples: int = 2,
    mov_source: str = "body",
    filter_type: int = 1,
) -> pd.DataFrame:
    """Price range filter, ported from the Range Filter [DW] indicator by
    DonovanWall on TradingView. The indicator was designed to filter out
    minor price action for a clearer view of trends.

    Parameters
    ----------
    data : pd.DataFrame
        The OHLC price data.

    range_qty : float, optional
        The range size. The default is 2.618.

    range_period : int, optional
        The range period. The default is 14.

    smooth_range : bool, optional
        Smooth the price range. The default is True.

    smooth_period : int, optional
        The smooting period. The default is 27.

    av_vals : bool, optional
        Average values. The default is False.

    av_samples : int, optional
        The number of average samples to use. The default is 2.

    mov_source : str, optional
        The price movement source ('body' or 'wicks'). The default is 'body'.

    filter_type : int, optional
        The filter type to use in calculations (1 or 2). The default is 1.

    Returns
    -------
    rfi : pd.DataFrame
        A dataframe containing the range filter indicator bounds.

    References
    ----------
    https://www.tradingview.com/script/lut7sBgG-Range-Filter-DW/
    """
    high_val = 0.0
    low_val = 0.0

    # Get high and low values
    if mov_source == "body":
        high_val = data["Close"]
        low_val = data["Close"]
    elif mov_source == "wicks":
        high_val = data["High"]
        low_val = data["Low"]

    # Get filter values
    rng = _range_size(
        (high_val + low_val) / 2, "AverageChange", range_qty, range_period
    )
    rfi = _calculate_range_filter(
        high_val,
        low_val,
        rng,
        range_period,
        filter_type,
        smooth_range,
        smooth_period,
        av_vals,
        av_samples,
    )

    return rfi


def bullish_engulfing(data: pd.DataFrame, detection: str = None):
    """Bullish engulfing pattern detection."""
    if detection == "SMA50":
        sma50 = sma(data["Close"].values, 50)
        down_trend = np.where(data["Close"].values < sma50, True, False)

    elif detection == "SMA50/200":
        sma50 = sma(data["Close"].values, 50)
        sma200 = sma(data["Close"].values, 200)

        down_trend = np.where(
            (data["Close"].values < sma50) & (data["Close"].values < sma200),
            True,
            False,
        )
    else:
        down_trend = np.full(len(data), True)

    body_len = 14  # ema depth for bodyAvg

    body_high = np.maximum(data["Close"].values, data["Open"].values)
    body_low = np.minimum(data["Close"].values, data["Open"].values)
    body = body_high - body_low

    body_avg = ema(body, body_len)
    short_body = body < body_avg
    long_body = body > body_avg

    white_body = data["Open"].values < data["Close"].values
    black_body = data["Open"].values > data["Close"].values

    inside_bar = [False]
    for i in range(1, len(data)):
        val = (body_high[i - 1] > body_high[i]) and (body_low[i - 1] < body_low[i])
        inside_bar.append(val)

    engulfing_bullish = [False]
    for i in range(1, len(data)):
        condition = (
            down_trend[i]
            & white_body[i]
            & long_body[i]
            & black_body[i - 1]
            & short_body[i - 1]
            & (data["Close"].values[i] >= data["Open"].values[i - 1])
            & (data["Open"].values[i] <= data["Close"].values[i - 1])
            & (
                (data["Close"].values[i] > data["Open"].values[i - 1])
                | (data["Open"].values[i] < data["Close"].values[i - 1])
            )
        )

        engulfing_bullish.append(condition)

    return engulfing_bullish


def bearish_engulfing(data: pd.DataFrame, detection: str = None):
    """Bearish engulfing pattern detection."""
    if detection == "SMA50":
        sma50 = sma(data["Close"].values, 50)
        up_trend = np.where(data["Close"].values > sma50, True, False)
    elif detection == "SMA50/200":
        sma50 = sma(data["Close"].values, 50)
        sma200 = sma(data["Close"].values, 200)

        up_trend = np.where(
            (data["Close"].values > sma50) & (data["Close"].values > sma200),
            True,
            False,
        )
    else:
        up_trend = np.full(len(data), True)

    body_len = 14  # ema depth for bodyAvg
    body_high = np.maximum(data["Close"].values, data["Open"].values)
    body_low = np.minimum(data["Close"].values, data["Open"].values)
    body = body_high - body_low

    body_avg = ema(body, body_len)
    short_body = body < body_avg
    long_body = body > body_avg

    white_body = data["Open"].values < data["Close"].values
    black_body = data["Open"].values > data["Close"].values

    inside_bar = [False]
    for i in range(1, len(data)):
        val = (body_high[i - 1] > body_high[i]) and (body_low[i - 1] < body_low[i])
        inside_bar.append(val)

    engulfing_bearish = [False]
    for i in range(1, len(data)):
        condition = (
            up_trend[i]
            & black_body[i]
            & long_body[i]
            & white_body[i - 1]
            & short_body[i - 1]
            & (data["Close"].values[i] <= data["Open"].values[i - 1])
            & (data["Open"].values[i] >= data["Close"].values[i - 1])
            & (
                (data["Close"].values[i] < data["Open"].values[i - 1])
                | (data["Open"].values[i] > data["Close"].values[i - 1])
            )
        )

        engulfing_bearish.append(condition)

    return engulfing_bearish


def find_swings(data: pd.DataFrame, n: int = 2) -> pd.DataFrame:
    """Locates swings in the inputted data using a moving average gradient
    method.

    Parameters
    ----------
    data : pd.DataFrame | pd.Series | list | np.array
        An OHLC dataframe of price, or an array/list/Series of data from an
        indicator (eg. RSI).

    n : int, optional
        The moving average period. The default is 2.

    Returns
    -------
    swing_df : pd.DataFrame
        A dataframe containing the swing levels detected.

    pd.Series(hl2, name="hl2"),
    """
    # Prepare data
    if isinstance(data, pd.DataFrame):
        # OHLC data
        hl2 = (data["High"].values + data["Low"].values) / 2
        swing_data = pd.Series(ema(hl2, n), index=data.index)
        low_data = data["Low"].values
        high_data = data["High"].values

    elif isinstance(data, pd.Series):
        # Pandas series data
        swing_data = pd.Series(ema(data.fillna(0), n), index=data.index)
        low_data = data
        high_data = data

    else:
        # Find swings in alternative data source
        data = pd.Series(data)

        # Define swing data
        swing_data = pd.Series(ema(data, n), index=data.index)
        low_data = data
        high_data = data

    signed_grad = np.sign((swing_data - swing_data.shift(1)).bfill())
    swings = (signed_grad != signed_grad.shift(1).bfill()) * -signed_grad

    # Calculate swing extrema
    lows = []
    highs = []
    for i, swing in enumerate(swings):
        if swing < 0:
            # Down swing, find low price
            highs.append(0)
            lows.append(min(low_data[i - n + 1 : i + 1]))
        elif swing > 0:
            # Up swing, find high price
            highs.append(max(high_data[i - n + 1 : i + 1]))
            lows.append(0)
        else:
            # Price movement
            highs.append(0)
            lows.append(0)

    # Determine last swing
    trend = rolling_signal_list(-swings)
    swings_list = merge_signals(lows, highs)
    last_swing = rolling_signal_list(swings_list)

    # Need to return both a last swing low and last swing high list
    last_low = rolling_signal_list(lows)
    last_high = rolling_signal_list(highs)

    swing_df = pd.DataFrame(
        data={"Highs": last_high, "Lows": last_low, "Last": last_swing, "Trend": trend},
        index=swing_data.index,
    )

    return swing_df


def classify_swings(swing_df: pd.DataFrame, tol: int = 0) -> pd.DataFrame:
    """Classifies a dataframe of swings (from find_swings) into higher-highs,
    lower-highs, higher-lows and lower-lows.


    Parameters
    ----------
    swing_df : pd.DataFrame
        The dataframe returned by find_swings.

    tol : int, optional
        The classification tolerance. The default is 0.

    Returns
    -------
    swing_df : pd.DataFrame
        A dataframe containing the classified swings.
    """
    # Create copy of swing dataframe
    swing_df = swing_df.copy()

    new_level = np.where(swing_df.Last != swing_df.Last.shift(), 1, 0)

    candles_since_last = candles_between_crosses(new_level, initial_count=1)

    # Add column 'candles since last swing' CSLS
    swing_df["CSLS"] = candles_since_last

    # Find strong Support and Resistance zones
    swing_df["Support"] = (swing_df.CSLS > tol) & (swing_df.Trend == 1)
    swing_df["Resistance"] = (swing_df.CSLS > tol) & (swing_df.Trend == -1)

    # Find higher highs and lower lows
    swing_df["Strong_lows"] = (
        swing_df["Support"] * swing_df["Lows"]
    )  # Returns high values when there is a strong support
    swing_df["Strong_highs"] = (
        swing_df["Resistance"] * swing_df["Highs"]
    )  # Returns high values when there is a strong support

    # Remove duplicates to preserve indexes of new levels
    swing_df["FSL"] = unroll_signal_list(
        swing_df["Strong_lows"]
    )  # First of new strong lows
    swing_df["FSH"] = unroll_signal_list(
        swing_df["Strong_highs"]
    )  # First of new strong highs

    # Now compare each non-zero value to the previous non-zero value.
    low_change = np.sign(swing_df.FSL) * (
        swing_df.FSL
        - swing_df.Strong_lows.replace(to_replace=0, method="ffill").shift()
    )
    high_change = np.sign(swing_df.FSH) * (
        swing_df.FSH
        - swing_df.Strong_highs.replace(to_replace=0, method="ffill").shift()
    )

    # the first low_change > 0.0 is not a HL
    r_hl = []
    first_valid_idx = -1
    for i in low_change.index:
        v = low_change[i]
        if first_valid_idx == -1 and not np.isnan(v) and v != 0.0:
            first_valid_idx = i
        if first_valid_idx != -1 and i > first_valid_idx and v > 0.0:
            hl = True
        else:
            hl = False
        r_hl.append(hl)

    # the first high_change < 0.0 is not a LH
    r_lh = []
    first_valid_idx = -1
    for i in high_change.index:
        v = high_change[i]
        if first_valid_idx == -1 and not np.isnan(v) and v != 0.0:
            first_valid_idx = i
        if first_valid_idx != -1 and i > first_valid_idx and v < 0.0:
            lh = True
        else:
            lh = False
        r_lh.append(lh)

    swing_df["LL"] = np.where(low_change < 0, True, False)
    # swing_df["HL"] = np.where(low_change > 0, True, False)
    swing_df["HL"] = r_hl
    swing_df["HH"] = np.where(high_change > 0, True, False)
    # swing_df["LH"] = np.where(high_change < 0, True, False)
    swing_df["LH"] = r_lh

    return swing_df


def detect_divergence(
    classified_price_swings: pd.DataFrame,
    classified_indicator_swings: pd.DataFrame,
    tol: int = 2,
    method: int = 0,
) -> pd.DataFrame:
    """Detects divergence between price swings and swings in an indicator.

    Parameters
    ----------
    classified_price_swings : pd.DataFrame
        The output from classify_swings using OHLC data.

    classified_indicator_swings : pd.DataFrame
        The output from classify_swings using indicator data.

    tol : int, optional
        The number of candles which conditions must be met within. The
        default is 2.

    method : int, optional
        The method to use when detecting divergence (0 or 1). The default is 0.

    Raises
    ------
    Exception
        When an unrecognised method of divergence detection is requested.

    Returns
    -------
    divergence : pd.DataFrame
        A dataframe containing divergence signals.

    Notes
    -----
    Options for the method include:
        0: use both price and indicator swings to detect divergence (default)

        1: use only indicator swings to detect divergence (more responsive)
    """
    regular_bullish = []
    regular_bearish = []
    hidden_bullish = []
    hidden_bearish = []

    if method == 0:
        for i in range(len(classified_price_swings)):
            # Look backwards in each

            # REGULAR BULLISH DIVERGENCE
            if (
                sum(classified_price_swings["LL"][i - tol + 1 : i + 1])
                + sum(classified_indicator_swings["HL"][i - tol + 1 : i + 1])
                > 1
            ):
                regular_bullish.append(True)
            else:
                regular_bullish.append(False)

            # REGULAR BEARISH DIVERGENCE
            if (
                sum(classified_price_swings["HH"][i - tol + 1 : i + 1])
                + sum(classified_indicator_swings["LH"][i - tol + 1 : i + 1])
                > 1
            ):
                regular_bearish.append(True)
            else:
                regular_bearish.append(False)

            # HIDDEN BULLISH DIVERGENCE
            if (
                sum(classified_price_swings["HL"][i - tol + 1 : i + 1])
                + sum(classified_indicator_swings["LL"][i - tol + 1 : i + 1])
                > 1
            ):
                hidden_bullish.append(True)
            else:
                hidden_bullish.append(False)

            # HIDDEN BEARISH DIVERGENCE
            if (
                sum(classified_price_swings["LH"][i - tol + 1 : i + 1])
                + sum(classified_indicator_swings["HH"][i - tol + 1 : i + 1])
                > 1
            ):
                hidden_bearish.append(True)
            else:
                hidden_bearish.append(False)

        divergence = pd.DataFrame(
            data={
                "regularBull": unroll_signal_list(regular_bullish),
                "regularBear": unroll_signal_list(regular_bearish),
                "hiddenBull": unroll_signal_list(hidden_bullish),
                "hiddenBear": unroll_signal_list(hidden_bearish),
            },
            index=classified_price_swings.index,
        )
    elif method == 1:
        # Use indicator swings only to detect divergence
        # for i in range(len(classified_price_swings)):
        if True:
            price_at_indi_lows = (
                classified_indicator_swings["FSL"] != 0
            ) * classified_price_swings["Lows"]
            price_at_indi_highs = (
                classified_indicator_swings["FSH"] != 0
            ) * classified_price_swings["Highs"]

            # Determine change in price between indicator lows
            price_at_indi_lows_change = np.sign(price_at_indi_lows) * (
                price_at_indi_lows
                - price_at_indi_lows.replace(to_replace=0, method="ffill").shift()
            )
            price_at_indi_highs_change = np.sign(price_at_indi_highs) * (
                price_at_indi_highs
                - price_at_indi_highs.replace(to_replace=0, method="ffill").shift()
            )

            # DETECT DIVERGENCES
            regular_bullish = (classified_indicator_swings["HL"]) & (
                price_at_indi_lows_change < 0
            )
            regular_bearish = (classified_indicator_swings["LH"]) & (
                price_at_indi_highs_change > 0
            )
            hidden_bullish = (classified_indicator_swings["LL"]) & (
                price_at_indi_lows_change > 0
            )
            hidden_bearish = (classified_indicator_swings["HH"]) & (
                price_at_indi_highs_change < 0
            )

        divergence = pd.DataFrame(
            data={
                "regularBull": regular_bullish,
                "regularBear": regular_bearish,
                "hiddenBull": hidden_bullish,
                "hiddenBear": hidden_bearish,
            },
            index=classified_price_swings.index,
        )

    else:
        raise Exception("Error: unrecognised method of divergence detection.")

    return divergence


def autodetect_divergence(
    ohlc: pd.DataFrame,
    indicator_data: pd.DataFrame,
    tolerance: int = 1,
    method: int = 0,
) -> pd.DataFrame:
    """A wrapper method to automatically detect divergence from inputted OHLC price
    data and indicator data.

    Parameters
    ----------
    ohlc : pd.DataFrame
        A dataframe of OHLC price data.

    indicator_data : pd.DataFrame
        dataframe of indicator data.

    tolerance : int, optional
        A parameter to control the lookback when detecting divergence.
        The default is 1.

    method : int, optional
        The divergence detection method. Set to 0 to use both price and
        indicator swings to detect divergence. Set to 1 to use only indicator
        swings to detect divergence. The default is 0.

    Returns
    -------
    divergence : pd.DataFrame
        A DataFrame containing columns 'regularBull', 'regularBear',
        'hiddenBull' and 'hiddenBear'.

    See Also
    --------
    autotrader.indicators.find_swings
    autotrader.indicators.classify_swings
    autotrader.indicators.detect_divergence

    """

    # Price swings
    price_swings = find_swings(ohlc)
    price_swings_classified = classify_swings(price_swings)

    # Indicator swings
    indicator_swings = find_swings(indicator_data)
    indicator_classified = classify_swings(indicator_swings)

    # Detect divergence
    divergence = detect_divergence(
        price_swings_classified, indicator_classified, tol=tolerance, method=method
    )

    return divergence


def heikin_ashi(data: pd.DataFrame):
    """Calculates the Heikin-Ashi candlesticks from Japanese candlestick
    data.
    """
    # Create copy of data to prevent overwriting
    working_data = data.copy()

    # Calculate Heikin Ashi candlesticks
    ha_close = 0.25 * (
        working_data["Open"]
        + working_data["Low"]
        + working_data["High"]
        + working_data["Close"]
    )
    ha_open = 0.5 * (working_data["Open"] + working_data["Close"])
    ha_high = np.maximum(
        working_data["High"].values,
        working_data["Close"].values,
        working_data["Open"].values,
    )
    ha_low = np.minimum(
        working_data["Low"].values,
        working_data["Close"].values,
        working_data["Open"].values,
    )

    ha_data = pd.DataFrame(
        data={"Open": ha_open, "High": ha_high, "Low": ha_low, "Close": ha_close},
        index=working_data.index,
    )

    return ha_data


def ha_candle_run(ha_data: pd.DataFrame):
    """Returns a list for the number of consecutive green and red
    Heikin-Ashi candles.

    Parameters
    ----------
    ha_data: pd.DataFrame
        The Heikin Ashi OHLC data.

    See Also
    --------
    heikin_ashi
    """
    green_candle = np.where(ha_data["Close"] - ha_data["Open"] > 0, 1, 0)
    red_candle = np.where(ha_data["Close"] - ha_data["Open"] < 0, 1, 0)

    green_run = []
    red_run = []

    green_sum = 0
    red_sum = 0

    for i in range(len(ha_data)):
        if green_candle[i] == 1:
            green_sum += 1
        else:
            green_sum = 0

        if red_candle[i] == 1:
            red_sum += 1
        else:
            red_sum = 0

        green_run.append(green_sum)
        red_run.append(red_sum)

    return green_run, red_run


def N_period_high(data: pd.DataFrame, N: int):
    """Returns the N-period high."""
    highs = data["High"].rolling(N).max()
    return highs


def N_period_low(data: pd.DataFrame, N: int):
    """Returns the N-period low."""
    lows = data["Low"].rolling(N).min()
    return lows


def crossover(ts1: pd.Series, ts2: pd.Series) -> pd.Series:
    """Locates where two timeseries crossover each other, returning 1 when
    list_1 crosses above list_2, and -1 for when list_1 crosses below list_2.

    Parameters
    ----------
    ts1 : pd.Series
        The first timeseries.

    ts2 : pd.Series
        The second timeseries.

    Returns
    -------
    crossovers : pd.Series
        The crossover series.
    """

    signs = np.sign(ts1 - ts2)
    crossovers = pd.Series(data=signs * (signs != signs.shift(1)), name="crossovers")

    return crossovers


def cross_values(
    ts1: Union[list, pd.Series],
    ts2: Union[list, pd.Series],
    ts_crossover: Union[list, pd.Series] = None,
) -> Union[list, pd.Series]:
    """Returns the approximate value of the point where the two series cross.

    Parameters
    ----------
    ts1 : list | pd.Series
        The first timeseries..

    ts2 : list | pd.Series
        The second timeseries..

    ts_crossover : list | pd.Series, optional
        The crossovers between timeseries 1 and timeseries 2.

    Returns
    -------
    cross_points : list | pd.Series
        The values at which crossovers occur.
    """

    if ts_crossover is None:
        ts_crossover = crossover(ts1, ts2)

    last_cross_point = ts1.iloc[0]
    cross_points = [last_cross_point]
    for i in range(1, len(ts_crossover)):
        if ts_crossover.iloc[i] != 0:
            i0 = 0
            m_a = ts1.iloc[i] - ts1.iloc[i - 1]
            m_b = ts2.iloc[i] - ts2.iloc[i - 1]
            ix = (ts2.iloc[i - 1] - ts1.iloc[i - 1]) / (m_a - m_b) + i0

            cross_point = m_a * (ix - i0) + ts1.iloc[i - 1]

            last_cross_point = cross_point

        else:
            cross_point = last_cross_point

        cross_points.append(cross_point)

    # Replace nans with 0
    cross_points = [0 if x != x else x for x in cross_points]

    if isinstance(ts1, pd.Series):
        # Convert to Series
        cross_points = pd.Series(data=cross_points, index=ts1.index, name="crossval")

    return cross_points


def candles_between_crosses(
    crosses: Union[list, pd.Series], initial_count: int = 0
) -> Union[list, pd.Series]:
    """Returns a rolling sum of candles since the last cross/signal occurred.

    Parameters
    ----------
    crosses : list | pd.Series
        The list or Series containing crossover signals.

    Returns
    -------
    counts : TYPE
        The rolling count of bars since the last crossover signal.

    See Also
    ---------
    indicators.crossover
    """

    count = 0
    counts = []

    for i in range(len(crosses)):
        if crosses[i] == 0:
            # Change in signal - reset count
            count += 1
        else:
            count = initial_count

        counts.append(count)

    if isinstance(crosses, pd.Series):
        # Convert to Series
        counts = pd.Series(data=counts, index=crosses.index, name="counts")

    return counts


def rolling_signal_list(signals: Union[list, pd.Series]) -> list:
    """Returns a list which repeats the previous signal, until a new
    signal is given.

    Parameters
    ----------
    signals : list | pd.Series
        A series of signals. Zero values are treated as 'no signal'.

    Returns
    -------
    list
        A list of rolled signals.

    Examples
    --------
    >>> rolling_signal_list([0,1,0,0,0,-1,0,0,1,0,0])
        [0, 1, 1, 1, 1, -1, -1, -1, 1, 1, 1]

    """
    rolling_signals = [0]
    last_signal = rolling_signals[0]

    if isinstance(signals, list):
        for i in range(1, len(signals)):
            if signals[i] != 0:
                last_signal = signals[i]
            rolling_signals.append(last_signal)
    else:
        for i in range(1, len(signals)):
            if signals.iloc[i] != 0:
                last_signal = signals.iloc[i]
            rolling_signals.append(last_signal)

    if isinstance(signals, pd.Series):
        rolling_signals = pd.Series(data=rolling_signals, index=signals.index)

    return rolling_signals


def unroll_signal_list(signals: Union[list, pd.Series]) -> np.array:
    """Unrolls a rolled signal list.

    Parameters
    ----------
    signals : Union[list, pd.Series]
        DESCRIPTION.

    Returns
    -------
    unrolled_signals : np.array
        The unrolled signal series.

    See Also
    --------
    This function is the inverse of rolling_signal_list.

    Examples
    --------
    >>> unroll_signal_list([0, 1, 1, 1, 1, -1, -1, -1, 1, 1, 1])
        array([ 0.,  1.,  0.,  0.,  0., -1.,  0.,  0.,  1.,  0.,  0.])

    """
    unrolled_signals = np.zeros(len(signals))
    for i in range(1, len(signals)):
        if signals[i] != signals[i - 1]:
            unrolled_signals[i] = signals[i]

    if isinstance(signals, pd.Series):
        unrolled_signals = pd.Series(data=unrolled_signals, index=signals.index)

    return unrolled_signals


def merge_signals(signal_1: list, signal_2: list) -> list:
    """Returns a single signal list which has merged two signal lists.

    Parameters
    ----------
    signal_1 : list
        The first signal list.

    signal_2 : list
        The second signal list.

    Returns
    -------
    merged_signal_list : list
        The merged result of the two inputted signal series.

    Examples
    --------
    >>> s1 = [1,0,0,0,1,0]
    >>> s2 = [0,0,-1,0,0,-1]
    >>> merge_signals(s1, s2)
        [1, 0, -1, 0, 1, -1]

    """
    merged_signal_list = signal_1.copy()
    for i in range(len(signal_1)):
        if signal_2[i] != 0:
            merged_signal_list[i] = signal_2[i]

    return merged_signal_list


def build_grid_price_levels(
    grid_origin: float,
    grid_space: float,
    grid_levels: int,
    grid_price_space: float = None,
    pip_value: float = 0.0001,
) -> np.array:
    """Generates grid price levels."""
    # Calculate grid spacing in price units
    if grid_price_space is None:
        grid_price_space = grid_space * pip_value

    # Generate order_limit_price list
    grid_price_levels = np.linspace(
        grid_origin - grid_levels * grid_price_space,
        grid_origin + grid_levels * grid_price_space,
        2 * grid_levels + 1,
    )

    return grid_price_levels


def build_grid(
    grid_origin: float,
    grid_space: float,
    grid_levels: int,
    order_direction: int,
    order_type: str = "stop-limit",
    grid_price_space: float = None,
    pip_value: float = 0.0001,
    take_distance: float = None,
    stop_distance: float = None,
    stop_type: str = None,
) -> dict:
    """Generates a grid of orders.

    Parameters
    ----------
    grid_origin : float
        The origin of grid, specified as a price.

    grid_space : float
        The spacing between grid levels, specified as pip distance.

    grid_levels : int
        The number of grid levels either side of origin.

    order_direction : int
        The direction of each grid level order (1 for long, -1 for short).

    order_type : str, optional
        The order type of each grid level order. The default is 'stop-limit'.

    grid_price_space : float, optional
        The spacing between grid levels, specified as price units distance.
        The default is None.

    pip_value : float, optional
        The instrument-specific pip value. The default is 0.0001.

    take_distance : float, optional
        The distance (in pips) of each order's take profit. The default is None.

    stop_distance : float, optional
        The distance (in pips) of each order's stop loss. The default is None.

    stop_type : str, optional
        The stop loss type. The default is None.

    Returns
    -------
    grid : dict
        A dictionary containing all orders on the grid.

    """

    # Check if stop_distance was provided without a stop_type
    if stop_distance is not None and stop_type is None:
        # set stop_type to 'limit' by default
        stop_type = "limit"

    # Calculate grid spacing in price units
    if grid_price_space is None:
        grid_price_space = grid_space * pip_value

    # Generate order_limit_price list
    order_limit_prices = np.linspace(
        grid_origin - grid_levels * grid_price_space,
        grid_origin + grid_levels * grid_price_space,
        2 * grid_levels + 1,
    )

    # Construct nominal order
    nominal_order = {}
    nominal_order["order_type"] = order_type
    nominal_order["direction"] = order_direction
    nominal_order["stop_distance"] = stop_distance
    nominal_order["stop_type"] = stop_type
    nominal_order["take_distance"] = take_distance

    # Build grid
    grid = {}

    for order, limit_price in enumerate(order_limit_prices):
        grid[order] = nominal_order.copy()
        grid[order]["order_stop_price"] = order_limit_prices[order]
        grid[order]["order_limit_price"] = order_limit_prices[order]

    return grid


def merge_grid_orders(grid_1: np.array, grid_2: np.array) -> np.array:
    """Merges grid dictionaries into one and re-labels order numbers so each
    order number is unique.
    """
    order_offset = len(grid_1)
    grid = grid_1.copy()

    for order_no in grid_2:
        grid[order_no + order_offset] = grid_2[order_no]

    return grid


def last_level_crossed(data: pd.DataFrame, base: float) -> list:
    """Returns a list containing the last grid level touched.
    The grid levels are determined by the base input variable,
    which corresponds to the pip_space x pip_value.
    """
    last_level_crossed = np.nan
    levels_crossed = []
    for i in range(len(data)):
        high = data["High"].values[i]
        low = data["Low"].values[i]

        upper_prices = []
        lower_prices = []

        for price in [high, low]:
            upper_prices.append(base * np.ceil(price / base))
            lower_prices.append(base * np.floor(price / base))

        if lower_prices[0] != lower_prices[1]:
            # Candle has crossed a level
            last_level_crossed = lower_prices[0]

        levels_crossed.append(last_level_crossed)

    return levels_crossed


def build_multiplier_grid(
    origin: float,
    direction: int,
    multiplier: float,
    no_levels: int,
    precision: int,
    spacing: float,
) -> list:
    """Constructs grid levels with a multiplying grid space.

    Parameters
    ----------
    origin : float
        The origin of grid as price amount.

    direction : int
        The direction of grid (1 for long, -1 for short).

    multiplier : float
        The grid space multiplier when price moves away from the origin
        opposite to direction.

    no_levels : int
        The number of levels to calculate either side of the origin.

    precision : int
        The instrument precision (eg. 4 for most currencies, 2 for JPY).

    spacing : float
        The spacing of the grid in price units.
    """

    levels = [i for i in range(1, no_levels + 1)]

    pos_levels = [round(origin + direction * spacing * i, precision) for i in levels]
    neg_spaces = [spacing * multiplier ** (i) for i in levels]
    neg_levels = []
    prev_neg_level = origin
    for i in range(len(levels)):
        next_neg_level = prev_neg_level - direction * neg_spaces[i]
        prev_neg_level = next_neg_level
        neg_levels.append(round(next_neg_level, precision))

    grid = neg_levels + [origin] + pos_levels
    grid.sort()

    return grid


def last_level_touched(data: pd.DataFrame, grid: np.array) -> np.array:
    """Calculates the grid levels touched by price data."""
    # initialise with nan
    last_level_crossed = np.nan

    levels_touched = []
    for i in range(len(data)):
        high = data["High"].values[i]
        low = data["Low"].values[i]

        upper_prices = []
        lower_prices = []

        for price in [high, low]:
            # Calculate level above
            upper_prices.append(
                grid[next(x[0] for x in enumerate(grid) if x[1] > price)]
            )

            # calculate level below
            first_level_below_index = next(
                x[0] for x in enumerate(grid[::-1]) if x[1] < price
            )
            lower_prices.append(grid[-(first_level_below_index + 1)])

        if lower_prices[0] != lower_prices[1]:
            # Candle has crossed a level, since the level below the candle high
            # is different to the level below the candle low.
            # This essentially means the grid level is between candle low and high.
            last_level_crossed = lower_prices[0]

        levels_touched.append(last_level_crossed)

    return levels_touched


def stoch_rsi(
    data: pd.DataFrame,
    K_period: int = 3,
    D_period: int = 3,
    RSI_length: int = 14,
    Stochastic_length: int = 14,
):
    """Stochastic RSI indicator."""
    rsi1 = TA.RSI(data, period=RSI_length)
    stoch = stochastic(rsi1, rsi1, rsi1, Stochastic_length)

    K = sma(stoch, K_period)
    D = sma(K, D_period)

    return K, D


def stochastic(
    high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
) -> pd.Series:
    """Stochastics indicator."""
    K = np.zeros(len(high))

    for i in range(period, len(high)):
        low_val = min(low[i - period + 1 : i + 1])
        high_val = max(high[i - period + 1 : i + 1])

        K[i] = 100 * (close[i] - low_val) / (high_val - low_val)

    return K


def sma(data: pd.DataFrame, period: int = 14) -> list:
    """Smoothed Moving Average."""
    sma_list = []
    for i in range(len(data)):
        average = sum(data[i - period + 1 : i + 1]) / period
        sma_list.append(average)
    return sma_list


def ema(data: pd.DataFrame, period: int = 14, smoothing: int = 2) -> list:
    """Exponential Moving Average."""
    ema = [sum(data[:period]) / period]
    for price in data[period:]:
        ema.append(
            (price * (smoothing / (1 + period)))
            + ema[-1] * (1 - (smoothing / (1 + period)))
        )
    for i in range(period - 1):
        ema.insert(0, np.nan)
    return ema


def true_range(data: pd.DataFrame, period: int = 14):
    """True range."""
    high_low = data["High"] - data["Low"]
    high_close = np.abs(data["High"] - data["Close"].shift())
    low_close = np.abs(data["Low"] - data["Close"].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    return true_range


def atr(data: pd.DataFrame, period: int = 14):
    """Average True Range."""
    tr = true_range(data, period)
    atr = tr.rolling(period).sum() / period
    return atr


def create_bricks(data: pd.DataFrame, brick_size: float = 0.002, column: str = "Close"):
    """Creates a dataframe of price-sized bricks.

    Parameters
    ----------
    data : pd.DataFrame
        The OHLC price data.

    brick_size : float, optional
        The brick size in price units. The default is 0.0020.

    column : str, optional
        The column of the OHLC to use. The default is 'Close'.

    Returns
    -------
    bricks : pd.DataFrame
        The Open and Close prices of each brick, indexed by brick close time.

    """
    brick_open = data[column][0]
    opens = [brick_open]
    close_times = [data.index[0]]
    for i in range(len(data)):
        price = data[column][i]
        price_diff = price - brick_open
        if abs(price_diff) > brick_size:
            # New brick(s)
            no_new_bricks = abs(int(price_diff / brick_size))
            for b in range(no_new_bricks):
                brick_close = brick_open + np.sign(price_diff) * brick_size
                brick_open = brick_close
                opens.append(brick_open)
                close_times.append(data.index[i])

    bricks = pd.DataFrame(data={"Open": opens, "Close": opens}, index=close_times)
    bricks["Close"] = bricks["Close"].shift(-1)

    return bricks


def _conditional_ema(x, condition=1, n=14, s=2):
    "Conditional sampling EMA functtion"
    if type(condition) == int:
        condition = condition * np.ones(len(x))

    ema = np.zeros(len(x))
    for i in range(1, len(x)):
        if condition[i]:
            ema[i] = (x[i] - ema[i - 1]) * (s / (1 + n)) + ema[i - 1]
        else:
            ema[i] = ema[i - 1]

    return pd.Series(ema, x.index, name=f"{n} period conditional EMA")


def _conditional_sma(x, condition=1, n=14):
    "Conditional sampling SMA functtion"

    if type(condition) == int:
        condition = condition * np.ones(len(x))

    # Calculate SMA
    sma = x.rolling(n).mean()

    # Filter by condition
    sma = sma * condition

    return sma


def _stdev(x, n):
    "Standard deviation function"
    sd = np.sqrt(_conditional_sma(x**2, 1, n) - _conditional_sma(x, 1, n) ** 2)
    return sd


def _range_size(x, scale="AverageChange", qty=2.618, n=14):
    "Range size function"
    rng_size = 0

    if scale == "AverageChange":
        AC = _conditional_ema(abs(x - x.shift(1)), 1, n)
        rng_size = qty * AC
    elif scale == "ATR":
        tr = TA.TR(x)
        atr = _conditional_ema(tr, 1, n)
        rng_size = qty * atr
    elif scale == "StandardDeviation":
        sd = _stdev(x, n)
        rng_size = qty * sd

    return rng_size


def _calculate_range_filter(h, idx, rng, n, rng_type, smooth, sn, av_rf, av_n):
    """Two type range filter function."""

    smoothed_range = _conditional_ema(rng, 1, sn)
    r = smoothed_range if smooth else rng
    r_filt = (h + idx) / 2

    if rng_type == 1:
        for i in range(1, len(h)):
            if h[i] - r[i] > r_filt[i - 1]:
                r_filt[i] = h[i] - r[i]
            elif idx[i] + r[i] < r_filt[i - 1]:
                r_filt[i] = idx[i] + r[i]
            else:
                r_filt[i] = r_filt[i - 1]

    elif rng_type == 2:
        for i in range(1, len(h)):
            if h[i] >= r_filt[i - 1] + r[i]:
                r_filt[i] = (
                    r_filt[i - 1] + np.floor(abs(h[i] - r_filt[i - 1]) / r[i]) * r[i]
                )
            elif idx[i] <= r_filt[i - 1] - r[i]:
                r_filt[i] = (
                    r_filt[i - 1] - np.floor(abs(idx[i] - r_filt[i - 1]) / r[i]) * r[i]
                )
            else:
                r_filt[i] = r_filt[i - 1]

    # Define nominal values
    r_filt1 = r_filt.copy()
    hi_band1 = r_filt1 + r
    lo_band1 = r_filt1 - r

    # Calculate indicator for averaged filter changes
    r_filt2 = _conditional_ema(r_filt1, r_filt1 != r_filt1.shift(1), av_n)
    hi_band2 = _conditional_ema(hi_band1, r_filt1 != r_filt1.shift(1), av_n)
    lo_band2 = _conditional_ema(lo_band1, r_filt1 != r_filt1.shift(1), av_n)

    # Assign indicator
    rng_filt = r_filt2 if av_rf else r_filt1
    hi_band = hi_band2 if av_rf else hi_band1
    lo_band = lo_band2 if av_rf else lo_band1

    # Construct output
    rfi = pd.DataFrame(
        data={"upper": hi_band, "lower": lo_band, "rf": rng_filt}, index=rng_filt.index
    )

    # Classify filter direction
    rfi["fdir"] = np.sign(rfi.rf - rfi.rf.shift(1)).fillna(0)

    return rfi


def chandelier_exit(
    data: pd.DataFrame, length: int = 22, mult: float = 3.0, use_close: bool = False
):
    # ohlc4 = (data["Open"] + data["High"] + data["Low"] + data["Close"]) / 4

    atr = mult * TA.ATR(data, length)

    high_field = "Close" if use_close else "High"
    low_field = "Close" if use_close else "Low"

    longstop = data[high_field].rolling(length).max() - atr
    shortstop = data[low_field].rolling(length).min() + atr

    direction = np.where(data["Close"] > shortstop, 1, -1)

    chandelier_df = pd.concat(
        {
            "longstop": longstop,
            "shortstop": shortstop,
        },
        axis=1,
    )
    chandelier_df["direction"] = direction
    chandelier_df["signal"] = np.where(
        chandelier_df["direction"] != chandelier_df["direction"].shift(),
        chandelier_df["direction"],
        0,
    )

    return chandelier_df
