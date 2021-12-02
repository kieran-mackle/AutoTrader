#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Module: lib.indicators
Purpose: AutoTrader custom indicators library
Author: Kieran Mackle
'''

from finta import TA
import numpy as np
import pandas as pd

''' -------------------------- PRICE INDICATORS --------------------------- '''
def supertrend(data, period = 10, ATR_multiplier = 3.0, source=None):
    ''' Based on the SuperTrend indicator by KivancOzbilgic on TradingView '''
    
    if source is None:
        source = (data.High.values + data.Low.values) / 2
    
    # Calculate ATR
    atr             = TA.ATR(data, period)
    
    up              = source - (ATR_multiplier*atr)
    up_list         = [up[0]]
    up_times        = [data.index[0]]
    N_up            = 0
    
    dn              = source + (ATR_multiplier*atr)
    dn_list         = [dn[0]]
    dn_times        = [data.index[0]]
    N_dn            = 0
    
    trend           = 1
    trend_list      = [trend]
    
    for i in range(1, len(data)):
        
        if trend == 1:
            if data.Close.values[i] > max(up[N_up:i]):
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
            if data.Close.values[i] < min(dn[N_dn:i]):
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
    
    # up_trend = pd.DataFrame({'uptrend': up_list}, index = up_times)
    # dn_trend = pd.DataFrame({'downtrend': dn_list}, index = dn_times)
    
    supertrend_df = pd.DataFrame({'uptrend': up_list,
                                  'downtrend': dn_list,
                                  'trend': trend_list}, 
                                 index = up_times)
    
    return supertrend_df


def stoch_rsi(data, K_period=3, D_period=3, RSI_length=14, Stochastic_length=14):

    rsi1 = TA.RSI(data, period=RSI_length)
    stoch = stochastic(rsi1, rsi1, rsi1, Stochastic_length)
    
    K = sma(stoch, K_period)
    D = sma(K, D_period)
    
    return K, D


def stochastic(high, low, close, period=14):
    
    K = np.zeros(len(high))
    
    for i in range(period, len(high)):
        low_val     = min(low[i-period+1:i+1])
        high_val    = max(high[i-period+1:i+1])
        
        K[i]        = 100 * (close[i] - low_val)/(high_val - low_val)
        
    return K
    

def sma(data, period=14):
    
    sma_list = []
    
    for i in range(len(data)):
        average = sum(data[i-period+1:i+1])/period
        sma_list.append(average)
    
    return sma_list


def ema(data, period=14, smoothing=2):
    
    ema = [sum(data[:period]) / period]
    
    for price in data[period:]:
        ema.append((price * (smoothing / (1 + period))) + ema[-1] * (1 - (smoothing / (1 + period))))
    
    for i in range(period-1):
        ema.insert(0, np.nan)
    
    return ema


def true_range(data, period=14):
    high_low = data['High'] - data['Low']
    high_close = np.abs(data['High'] - data['Close'].shift())
    low_close = np.abs(data['Low'] - data['Close'].shift())
    
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    
    return true_range


def atr(data, period=14):
    
    tr = true_range(data, period)
    
    atr = tr.rolling(period).sum()/period
    
    return atr


def bullish_engulfing(data, detection = None):
    ''' Bullish engulfing pattern detection. '''
    
    if detection == "SMA50":
        sma50       = sma(data.Close.values, 50)
        
        down_trend  = np.where(data.Close.values < sma50, True, False)
        up_trend    = np.where(data.Close.values > sma50, True, False)
        
    elif detection == "SMA50/200":
        sma50       = sma(data.Close.values, 50)
        sma200      = sma(data.Close.values, 200)
        
        down_trend  = np.where((data.Close.values < sma50) & 
                               (data.Close.values < sma200), 
                               True, False)
        up_trend    = np.where((data.Close.values > sma50) & 
                               (data.Close.values > sma200), 
                               True, False)
    else:
        down_trend  = np.full(len(data), True)
        up_trend    = np.full(len(data), True)
    
    body_len        = 14    # ema depth for bodyAvg
    shadow_pc       = 100.0   # size of shadows 
    doji_pc         = 5.0
    shadow_factor   = 2.0 # number of times shadow dominates candle body
    
    body_high       = np.maximum(data.Close.values, data.Open.values)
    body_low        = np.minimum(data.Close.values, data.Open.values)
    body            = body_high - body_low
    
    body_avg        = ema(body, body_len)
    short_body      = body < body_avg
    long_body       = body > body_avg
    up_shadow       = data.High.values - body_high
    down_shadow     = body_low - data.Low.values
    
    has_up_shadow   = up_shadow > (shadow_pc / 100 * body)
    has_dn_shadow   = down_shadow > (shadow_pc / 100 * body)
    white_body      = data.Open.values < data.Close.values
    black_body      = data.Open.values > data.Close.values
    candle_range    = data.High.values - data.Low.values
    
    inside_bar = [False]
    for i in range(1, len(data)):
        val  = (body_high[i-1] > body_high[i]) and (body_low[i-1] < body_low[i])
        inside_bar.append(val)
        
    body_mid        = body/2 + body_low
    shadow_equals   = (up_shadow == down_shadow) | \
                          (
                              ((abs(up_shadow - down_shadow) / down_shadow * 100) < shadow_pc) & \
                              ((abs(down_shadow - up_shadow) / up_shadow * 100) < shadow_pc)
                          )
    doji_body       = (candle_range > 0) & (body <= candle_range * doji_pc / 100)
    doji            = doji_body & shadow_equals
    
    
    engulfing_bullish = [False]
    for i in range(1, len(data)):
        condition = down_trend[i] & \
                    white_body[i] & \
                    long_body[i] & \
                    black_body[i-1] & \
                    short_body[i-1] & \
                    (data.Close.values[i] >= data.Open.values[i-1]) & \
                    (data.Open.values[i] <= data.Close.values[i-1]) & \
                    ((data.Close.values[i] > data.Open.values[i-1]) | (data.Open.values[i] < data.Close.values[i-1]))
        
        engulfing_bullish.append(condition)
        
    return engulfing_bullish


def bearish_engulfing(data, detection = None):
    ''' Bearish engulfing pattern detection. '''
    
    if detection == "SMA50":
        sma50       = sma(data.Close.values, 50)
        
        down_trend  = np.where(data.Close.values < sma50, True, False)
        up_trend    = np.where(data.Close.values > sma50, True, False)
        
    elif detection == "SMA50/200":
        sma50       = sma(data.Close.values, 50)
        sma200      = sma(data.Close.values, 200)
        
        down_trend  = np.where((data.Close.values < sma50) & 
                               (data.Close.values < sma200), 
                               True, False)
        up_trend    = np.where((data.Close.values > sma50) & 
                               (data.Close.values > sma200), 
                               True, False)
    else:
        down_trend  = np.full(len(data), True)
        up_trend    = np.full(len(data), True)
    
    body_len        = 14    # ema depth for bodyAvg
    shadow_pc       = 100.0   # size of shadows 
    doji_pc         = 5.0
    shadow_factor   = 2.0 # number of times shadow dominates candle body
    
    body_high       = np.maximum(data.Close.values, data.Open.values)
    body_low        = np.minimum(data.Close.values, data.Open.values)
    body            = body_high - body_low
    
    body_avg        = ema(body, body_len)
    short_body      = body < body_avg
    long_body       = body > body_avg
    up_shadow       = data.High.values - body_high
    down_shadow     = body_low - data.Low.values
    
    has_up_shadow   = up_shadow > (shadow_pc / 100 * body)
    has_dn_shadow   = down_shadow > (shadow_pc / 100 * body)
    white_body      = data.Open.values < data.Close.values
    black_body      = data.Open.values > data.Close.values
    candle_range    = data.High.values - data.Low.values
    
    inside_bar = [False]
    for i in range(1, len(data)):
        val  = (body_high[i-1] > body_high[i]) and (body_low[i-1] < body_low[i])
        inside_bar.append(val)
        
    body_mid        = body/2 + body_low
    shadow_equals   = (up_shadow == down_shadow) | \
                          (
                              ((abs(up_shadow - down_shadow) / down_shadow * 100) < shadow_pc) & \
                              ((abs(down_shadow - up_shadow) / up_shadow * 100) < shadow_pc)
                          )
    doji_body       = (candle_range > 0) & (body <= candle_range * doji_pc / 100)
    doji            = doji_body & shadow_equals
    
    
    engulfing_bearish = [False]
    for i in range(1, len(data)):
        condition = up_trend[i] & \
                    black_body[i] & \
                    long_body[i] & \
                    white_body[i-1] & \
                    short_body[i-1] & \
                    (data.Close.values[i] <= data.Open.values[i-1]) & \
                    (data.Open.values[i] >= data.Close.values[i-1]) & \
                    ((data.Close.values[i] < data.Open.values[i-1]) | (data.Open.values[i] > data.Close.values[i-1]))
        
        engulfing_bearish.append(condition)
        
    return engulfing_bearish


def heikin_ashi(data):
    ''' 
        Calculates the Heikin-Ashi candlesticks from Japanese candlestick 
        data. 
    '''
    
    # Create copy of data to prevent overwriting
    working_data = data.copy()
    
    # Calculate Heikin Ashi candlesticks
    ha_close = 0.25*(working_data.Open + working_data.Low + working_data.High + working_data.Close)
    ha_open = 0.5*(working_data.Open + working_data.Close)
    ha_high = np.maximum(working_data.High.values, working_data.Close.values, working_data.Open.values)
    ha_low = np.minimum(working_data.Low.values, working_data.Close.values, working_data.Open.values)
    
    ha_data = pd.DataFrame(data={'Open': ha_open, 
                                 'High': ha_high, 
                                 'Low': ha_low, 
                                 'Close': ha_close}, 
                           index=working_data.index)
    
    return ha_data
 
def half_trend(data, amplitude=2, channel_deviation=2):
    '''
    HalfTrend indicator, originally by Alex Orekhov (everget) on TradingView.
    
    Parameters:
        data (dataframe): OHLC price data
        
        amplitude (int): lookback window
            
        channel_deviation (int): ATR channel deviation factor
    
    (translated to Python 15/11/21)
    '''
    
    # Initialisation
    atr2 = TA.ATR(data, 100)/2
    dev = channel_deviation * atr2
    high_price = data.High.rolling(amplitude).max().fillna(0)
    low_price = data.Low.rolling(amplitude).min().fillna(0)
    highma = TA.SMA(data, period=amplitude, column='High')
    lowma = TA.SMA(data, period=amplitude, column='Low')
    
    trend = np.zeros(len(data))
    next_trend = np.zeros(len(data))
    max_low_price = np.zeros(len(data))
    max_low_price[0] = data.Low[0]
    min_high_price = np.zeros(len(data))
    min_high_price[0] = data.High[0]
    
    for i in range(1, len(data)):
        if next_trend[i-1] == 1:
            max_low_price[i] = max(low_price[i-1], max_low_price[i-1])

            if highma[i] < max_low_price[i] and data.Close[i] < data.Low[i-1]:
                trend[i] = 1
                next_trend[i] = 0
                min_high_price[i] = high_price[i]
            else:
                # assign previous values again
                trend[i] = trend[i-1]
                next_trend[i] = next_trend[i-1]
                min_high_price[i] = min_high_price[i-1]
        else:
            min_high_price[i] = min(high_price[i-1], min_high_price[i-1])
            
            if lowma[i] > min_high_price[i] and data.Close[i] > data.High[i-1]:
                trend[i] = 0
                next_trend[i] = 1
                max_low_price[i] = low_price[i]
            else:
                # assign previous values again
                trend[i] = trend[i-1]
                next_trend[i] = next_trend[i-1]
                max_low_price[i] = max_low_price[i-1]
                
    up = np.zeros(len(data))
    up[0] = max_low_price[0]
    down = np.zeros(len(data))
    down[0] = min_high_price[0]
    atr_high = np.zeros(len(data))
    atr_low = np.zeros(len(data))
    
    for i in range(1, len(data)):
        if trend[i] == 0:
            if trend[i-1] != 0:
                up[i] = down[i-1]
            else:
                up[i] = max(max_low_price[i-1], up[i-1])
            
            atr_high[i] = up[i] + dev[i]
            atr_low[i] = up[i] - dev[i]
            
        else:
            if trend[i-1] != 1:
                down[i] = up[i-1]
            else:
                down[i] = min(min_high_price[i-1], down[i-1]) 
                
            atr_high[i] = down[i] + dev[i]
            atr_low[i] = down[i] - dev[i]
    
    halftrend = np.where(trend == 0, up, down)
    buy = np.where((trend==0) & (np.roll(trend,1)==1), 1, 0)
    sell = np.where((trend==1) & (np.roll(trend,1)==0), 1, 0)
    
    # Construct DataFrame
    htdf = pd.DataFrame(data = {'halftrend': halftrend, 
                                'atrHigh': np.nan_to_num(atr_high),
                                'atrLow': np.nan_to_num(atr_low),
                                'buy': buy, 
                                'sell': sell},
                        index = data.index)
    
    # Clear false leading signals
    htdf.buy.values[:100] = np.zeros(100)
    htdf.sell.values[:100] = np.zeros(100)
    
    # Replace leading zeroes with nan
    htdf['atrHigh'] = htdf.atrHigh.replace(to_replace=0, value=float("nan"))
    htdf['atrLow'] = htdf.atrLow.replace(to_replace=0, value=float("nan"))
    
    return htdf

def N_period_high(data, N):
    ''' Returns the N-period high. '''
    highs = data.High.rolling(N).max()
    return highs

def N_period_low(data, N):
    ''' Returns the N-period low. '''
    lows = data.Low.rolling(N).min()
    return lows

''' ------------------------ UTILITY INDICATORS --------------------------- '''

def crossover(list_1, list_2):
    ''' 
    Returns a list of length len(list_1) with 1 when list_1 crosses above
    list_2 and -1 when list_1 crosses below list_2.
    '''
    
    sign_list = []
    for i in range(len(list_1)):
        if np.isnan(list_1[i]):
            sign_list.append(np.nan)
        else:
            difference = list_1[i] - list_2[i]
            if difference < 0:
                sign_list.append(-1)
            else:
                sign_list.append(1)
    
    crossover_list = [0]
    
    for i in range(1, len(sign_list)):
        if sign_list[i] - sign_list[i-1] != 0:
            val = sign_list[i]
        else:
            val = 0
        
        crossover_list.append(val)

    return crossover_list


def cross_values(a, b, ab_crossover):
    cross_point_list = [0]
    last_cross_point = 0
    for i in range(1, len(ab_crossover)):
        if ab_crossover[i] != 0:
            i0 = 0
            m_a = a[i] - a[i-1]
            m_b = b[i] - b[i-1]
            ix = (b[i-1] - a[i-1])/(m_a-m_b) + i0
            
            cross_point = m_a*(ix - i0) + a[i-1]
            
            last_cross_point = cross_point
            
        else:
            cross_point = last_cross_point #0
        
        cross_point_list.append(cross_point)
    
    # Replace nans with 0
    cross_point_list = [0 if x!=x  else x for x in cross_point_list]
    
    return cross_point_list


def candles_between_crosses(cross_list):
    '''
    Returns candles since last cross
    
    
    Behaviour:
    in:  [0, 0, 1, 0, 0, 0, -1, 0, 0, 0, 0, 0, 1]
    out: [1, 2, 0, 1, 2, 3,  0, 1, 2, 3, 4, 5, 0]
    '''
    
    count = 0
    count_list = []
    
    for i in range(len(cross_list)):

        if cross_list[i] == 0:
            # Change in signal - reset count
            count += 1
        else:
            count = 0
        
        count_list.append(count)
    
    return count_list

def find_swings(data, data_type='ohlc', n = 2):
    '''
    Locates swings in the inputted data and returns a dataframe.
    
    Parameters:
        data: an OHLC dataframe of price, or an array/list of data from an 
        indicator.
        
        data_type: specify 'ohlc' when data is OHLC, or 'other' when inputting
        an indicator.
    '''
    
    # Prepare data 
    if data_type == 'ohlc':
        # Find swings in OHLC price data
        # hl2     = (data.Open.values + data.Close.values)/2
        hl2     = (data.High.values + data.Low.values)/2
        swing_data = ema(hl2, n)
        
        low_data = data.Low.values
        high_data = data.High.values
        
    else:
        # Find swings in alternative data source
        swing_data = data
        low_data = data
        high_data = data
    
    # Calculate slope of data and points where slope changes
    grad = [swing_data[i] - swing_data[i-1] for i in range(len(swing_data))]
    swings = np.where(np.sign(grad) != np.sign(np.roll(grad,1)), -np.sign(grad), 0)

    # Construct columns
    low_list    = [0,0]
    high_list   = [0,0]
    for i in range(2,len(data)):
        if swings[i] == -1:
            # Down swing - find min price in the vicinity 
            high_list.append(0)
            low_list.append(min(low_data[i-n:i]))
            
        elif swings[i] == 1:
            # Up swing - find max price in the vicinity
            high_list.append(max(high_data[i-n:i]))
            low_list.append(0)
            
        else:
            # Price movement
            low_list.append(0)
            high_list.append(0)
    
    trend = rolling_signal_list(-swings)
    swings_list = merge_signals(low_list, high_list)
    last_swing = rolling_signal_list(swings_list)
    last_swing[0:n] = list(high_data[0:n])
    
    # Need to return both a last swing low and last swing high list
    last_low = rolling_signal_list(low_list)
    last_low[0:n] = list(low_data[0:n])     # Fill start of data
    last_high = rolling_signal_list(high_list)
    last_high[0:n] = list(high_data[0:n])   # Fill start of data
    
    swing_df = pd.DataFrame(data={'Highs': last_high, 
                                  'Lows' : last_low,
                                  'Last' : last_swing,
                                  'Trend': trend},
                            index = data.index)
    
    return swing_df
    
def classify_swings(swing_df, tol=0):
    ''' 
    Classify a dataframe of swings (from find_swings) into higher-high, 
    lower-high, higher-low and lower-low.
    
    Parameters:
        swing_df: the dataframe outputted from find_swings.
        
        tol: parameter to control strength of levels detected.
    '''
    
    # Create copy of swing dataframe
    swing_df = swing_df.copy()
    
    new_level = np.where(swing_df.Last != swing_df.Last.shift(), 1, 0)

    candles_since_last = candles_between_crosses(new_level)
    
    # Add column 'candles since last swing' CSLS
    swing_df['CSLS'] = candles_since_last
    
    # Find strong Support and Resistance zones
    swing_df['Support'] = (swing_df.CSLS > tol) & (swing_df.Trend == 1)
    swing_df['Resistance'] = (swing_df.CSLS > tol) & (swing_df.Trend == -1)
    
    # Find higher highs and lower lows
    swing_df['Strong_lows'] = swing_df['Support'] * swing_df['Lows'] # Returns high values when there is a strong support
    swing_df['Strong_highs'] = swing_df['Resistance'] * swing_df['Highs'] # Returns high values when there is a strong support
    
    # Remove duplicates to preserve indexes of new levels
    swing_df['FSL'] = unroll_signal_list(swing_df['Strong_lows']) # First of new strong lows
    swing_df['FSH'] = unroll_signal_list(swing_df['Strong_highs']) # First of new strong highs
    
    # Now compare each non-zero value to the previous non-zero value.
    low_change = np.sign(swing_df.FSL) * (swing_df.FSL - swing_df.Strong_lows.replace(to_replace=0, method='ffill').shift())
    high_change = np.sign(swing_df.FSH) * (swing_df.FSH - swing_df.Strong_highs.replace(to_replace=0, method='ffill').shift())
    
    swing_df['LL'] = np.where(low_change < 0, True, False)
    swing_df['HL'] = np.where(low_change > 0, True, False)
    swing_df['HH'] = np.where(high_change > 0, True, False)
    swing_df['LH'] = np.where(high_change < 0, True, False)
    
    return swing_df

def detect_divergence(classified_price_swings, classified_indicator_swings, tol=2,
                      method=0):
    '''
    Detects divergence between price swings and swings in an indicator.
    
    Parameters:
        classified_price_swings: output from classify_swings using OHLC data.
        
        classified_indicator_swings: output from classify_swings using indicator data.
        
        tol: number of candles which conditions must be met within. 
        
        method: the method to use when detecting divergence. Options include:
            0: use both price and indicator swings to detect divergence (default)
            1: use only indicator swings to detect divergence
    '''
    
    if method == 0:
        
        regular_bullish = []
        regular_bearish = []
        hidden_bullish = []
        hidden_bearish = []
        
        for i in range(len(classified_price_swings)):
            # Look backwards in each
            
            # REGULAR BULLISH DIVERGENCE
            if sum(classified_price_swings['LL'][i-tol:i]) + sum(classified_indicator_swings['HL'][i-tol:i]) > 1:
                regular_bullish.append(True)
            else:
                regular_bullish.append(False)
            
            # REGULAR BEARISH DIVERGENCE
            if sum(classified_price_swings['HH'][i-tol:i]) + sum(classified_indicator_swings['LH'][i-tol:i]) > 1:
                regular_bearish.append(True)
            else:
                regular_bearish.append(False)
            
            # HIDDEN BULLISH DIVERGENCE
            if sum(classified_price_swings['HL'][i-tol:i]) + sum(classified_indicator_swings['LL'][i-tol:i]) > 1:
                hidden_bullish.append(True)
            else:
                hidden_bullish.append(False)
            
            # HIDDEN BEARISH DIVERGENCE
            if sum(classified_price_swings['LH'][i-tol:i]) + sum(classified_indicator_swings['HH'][i-tol:i]) > 1:
                hidden_bearish.append(True)
            else:
                hidden_bearish.append(False)
            
            divergence = pd.DataFrame(data = {'regularBull': unroll_signal_list(regular_bullish),
                                              'regularBear': unroll_signal_list(regular_bearish),
                                              'hiddenBull': unroll_signal_list(hidden_bullish),
                                              'hiddenBear': unroll_signal_list(hidden_bearish)})
    elif method == 1:
        # Use indicator swings only to detect divergence
        for i in range(len(classified_price_swings)):
            
            price_at_indi_lows = (classified_indicator_swings['FSL'] != 0) * classified_price_swings['Lows']
            price_at_indi_highs = (classified_indicator_swings['FSH'] != 0) * classified_price_swings['Highs']
            
            # Determine change in price between indicator lows
            price_at_indi_lows_change = np.sign(price_at_indi_lows) * (price_at_indi_lows - price_at_indi_lows.replace(to_replace=0, method='ffill').shift())
            price_at_indi_highs_change = np.sign(price_at_indi_highs) * (price_at_indi_highs - price_at_indi_highs.replace(to_replace=0, method='ffill').shift())
            
            
            # DETECT DIVERGENCES
            regular_bullish = (classified_indicator_swings['HL']) & (price_at_indi_lows_change < 0 )
            regular_bearish = (classified_indicator_swings['LH']) & (price_at_indi_highs_change > 0 )
            hidden_bullish = (classified_indicator_swings['LL']) & (price_at_indi_lows_change > 0 )
            hidden_bearish = (classified_indicator_swings['HH']) & (price_at_indi_highs_change < 0 )
            
            divergence = pd.DataFrame(data = {'regularBull': regular_bullish,
                                              'regularBear': regular_bearish,
                                              'hiddenBull': hidden_bullish,
                                              'hiddenBear': hidden_bearish})
        
    else:
        raise Exception("Error: unrecognised method of divergence detection.")
        
    return divergence

def autodetect_divergence(ohlc, indicator_data, method=0):
    '''
    Wrapper method to automatically detect divergence from inputted OHLC price 
    data and indicator data.
    
    This method calls:
        find_swings()
        classify_swings()
        detect_divergence()
    
    Parameters:
        ohlc: dataframe of OHLC data
        
        indicator data: array of indicator data
        
        method: the method to use when detecting divergence. Options include:
            0: use both price and indicator swings to detect divergence (default)
            1: use only indicator swings to detect divergence
    '''
    
    # Price swings
    price_swings = find_swings(ohlc)
    price_swings_classified = classify_swings(price_swings)
    
    # Indicator swings 
    indicator_swings = find_swings(indicator_data, data_type='other')
    indicator_classified = classify_swings(indicator_swings)
    
    # Detect divergence
    divergence = detect_divergence(price_swings_classified, indicator_classified, method)
    
    return divergence

def rolling_signal_list(signals):
    ''' 
        Returns a list which maintains the previous signal, until a new 
        signal is given.
        
        [0,1,0,0,0,-1,0,0,1,0,0] ->  [0,1,1,1,1,-1,-1,-1,1,1,1]
        
    '''
    
    rolling_signals = [0]
    last_signal     = rolling_signals[0]
    
    for i in range(1, len(signals)):
        if signals[i] != 0:
            last_signal = signals[i]
        
        rolling_signals.append(last_signal)
    
    return rolling_signals

def unroll_signal_list(signals):
    ''' Unrolls a signal list. '''
    new_list = np.zeros(len(signals))
    
    for i in range(len(signals)):
        if signals[i] != signals[i-1]:
            new_list[i] = signals[i]
    
    return new_list


def merge_signals(signal_1, signal_2):
     ''' 
         Returns a single signal list which has merged two signal lists. 
     '''
     
     merged_signal_list = signal_1.copy()
     
     for i in range(len(signal_1)):
         if signal_2[i] != 0:
             merged_signal_list[i] = signal_2[i]
     
     return merged_signal_list


def ha_candle_run(ha_data):
    '''
        Returns a list for the number of consecutive green and red 
        Heikin-Ashi candles.
        
    '''
    green_candle    = np.where(ha_data.Close - ha_data.Open > 0, 1, 0)
    red_candle      = np.where(ha_data.Close - ha_data.Open < 0, 1, 0)
    
    green_run   = []
    red_run     = []
    
    green_sum   = 0
    red_sum     = 0
    
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


def build_grid_price_levels(grid_origin, grid_space, grid_levels, 
                            grid_price_space=None, pip_value=0.0001):
    
    # Calculate grid spacing in price units
    if grid_price_space is None:
        grid_price_space = grid_space*pip_value
    
    # Generate order_limit_price list 
    grid_price_levels = np.linspace(grid_origin - grid_levels*grid_price_space, 
                                     grid_origin + grid_levels*grid_price_space, 
                                     2*grid_levels + 1)
    
    return grid_price_levels

def build_grid(grid_origin, grid_space, grid_levels, order_direction, 
               order_type='stop-limit', grid_price_space=None, pip_value=0.0001, 
               take_distance=None, stop_distance=None, stop_type=None):
    '''
    grid_origin: origin of grid, specified as a price
    grid_space: spacing between grid levels, specified as pip distance
    grid_levels: number of grid levels either side of origin
    order_direction: the direction of each grid level order (1 for long, -1 for short)
    order_type: the order type of each grid level order
    '''
    # TODO - could add a limit price buffer, then use it to move the limit price
    # slightly away from the stop price
    
    # Check if stop_distance was provided without a stop_type
    if stop_distance is not None and stop_type is None:
        # set stop_type to 'limit' by default
        stop_type = 'limit'
    
    # Calculate grid spacing in price units
    if grid_price_space is None:
        grid_price_space = grid_space*pip_value
    
    # Generate order_limit_price list 
    order_limit_prices = np.linspace(grid_origin - grid_levels*grid_price_space, 
                                     grid_origin + grid_levels*grid_price_space, 
                                     2*grid_levels + 1)
    
    # Construct nominal order
    nominal_order = {}
    nominal_order["order_type"]         = order_type
    nominal_order["direction"]          = order_direction
    nominal_order["stop_distance"]      = stop_distance
    nominal_order["stop_type"]          = stop_type
    nominal_order["take_distance"]      = take_distance
    
    # Build grid
    grid = {}

    for order, limit_price in enumerate(order_limit_prices):
        grid[order] = nominal_order.copy()
        grid[order]["order_stop_price"]  = order_limit_prices[order]
        grid[order]["order_limit_price"] = order_limit_prices[order]
        
    
    return grid

def merge_grid_orders(grid_1, grid_2):
    '''
    Merges grid dictionaries into one and re-labels order numbers so each
    order number is unique.
    '''
    # TODO - use **args/**kwargs to generalise how many grids are inputted
    order_offset = len(grid_1)
    grid = grid_1.copy()
    
    for order_no in grid_2:
        grid[order_no + order_offset] = grid_2[order_no]
    
    return grid
    
def last_level_crossed(data, base):
    ''' 
    Returns a list containing the last grid level touched.
    The grid levels are determined by the base input variable, 
    which corresponds to the pip_space x pip_value.
    '''
    # base = 20*0.0001
    
    last_level_crossed = np.nan
    levels_crossed = []
    for i in range(len(data)):
        high = data.High.values[i]
        low = data.Low.values[i]
        
        upper_prices = []
        lower_prices = []
        
        for price in [high, low]:    
            upper_prices.append(base*np.ceil(price/base))
            lower_prices.append(base*np.floor(price/base))
        
        if lower_prices[0] != lower_prices[1]:
            # Candle has crossed a level
            last_level_crossed = lower_prices[0]
        
        levels_crossed.append(last_level_crossed)
    
    return levels_crossed


def build_multiplier_grid(origin, direction, multiplier, no_levels, precision, spacing):
    '''
    Constructs grid levels with a multiplying grid space.
    
        Parameters:
            origin (float): origin of grid as price amount.
            
            direction (int): direction of grid (1 for long, -1 for short).
            
            multiplier (float): grid space multiplier when price moves away 
            from the origin opposite to direction.
            
            no_levels (int): number of levels to calculate either side of the 
            origin.
            
            precision (int): instrument precision (eg. 4 for most currencies, 2 
            for JPY).
            
            spacing (float): spacing of grid in price units.
    '''
    
    levels = [i for i in range(1, no_levels + 1)]

    pos_levels = [round(origin + direction*spacing*i, precision) for i in levels]
    neg_spaces = [spacing*multiplier**(i) for i in levels]
    neg_levels = []
    prev_neg_level = origin
    for i in range(len(levels)):
        next_neg_level = prev_neg_level - direction*neg_spaces[i]
        prev_neg_level = next_neg_level
        neg_levels.append(round(next_neg_level, precision))
    
    grid = neg_levels + [origin] + pos_levels
    grid.sort()
    
    return grid


def last_level_touched(data, grid):
    '''
    Calculates the grid levels touched by price data.
    '''
    
    # initialise with nan
    last_level_crossed = np.nan 
    
    levels_touched = []
    for i in range(len(data)):
        high = data.High.values[i]
        low = data.Low.values[i]
        
        upper_prices = []
        lower_prices = []
        
        for price in [high, low]:    
            # Calculate level above
            upper_prices.append(grid[next(x[0] for x in enumerate(grid) if x[1] > price)])
            
            # calculate level below
            first_level_below_index = next(x[0] for x in enumerate(grid[::-1]) if x[1] < price)
            lower_prices.append(grid[-(first_level_below_index+1)])
        
        if lower_prices[0] != lower_prices[1]:
            # Candle has crossed a level, since the level below the candle high
            # is different to the level below the candle low.
            # This essentially means the grid level is between candle low and high.
            last_level_crossed = lower_prices[0]
        
        levels_touched.append(last_level_crossed)
    
    return levels_touched

