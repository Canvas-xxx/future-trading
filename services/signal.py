import pandas as pd
import pandas_ta as ta
from services.indecator import get_supertrend, get_range_filter
from services.strategy import st_strategy, rf_strategy, macd_cross_strategy, macdh_cross_strategy


def get_df_ohlcv(exchange, symbol, timeframe, limit):
    df_ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df_ohlcv = pd.DataFrame(
        df_ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df_ohlcv['datetime'] = pd.to_datetime(df_ohlcv['datetime'], unit='ms')

    if len(df_ohlcv) <= 200:
        return pd.Series([])

    df_ohlcv['EMA_200'] = df_ohlcv.ta.ema(length=200)
    df_ohlcv['ATR_14'] = df_ohlcv.ta.atr(length=14)
    df_ohlcv[['MACD_12_26_9', 'MACDh_12_26_9',
              'MACDs_12_26_9']] = df_ohlcv.ta.macd()
    df_ohlcv['RSI_14'] = df_ohlcv.ta.rsi()

    df_ohlcv['Supertrend'], _, _ = get_supertrend(
        df_ohlcv['high'], df_ohlcv['low'], df_ohlcv['close'], 10, 3)
    df_ohlcv['st_signal'] = st_strategy(
        df_ohlcv['close'], df_ohlcv['Supertrend'])

    df_ohlcv['Filt'], df_ohlcv['Upward'], df_ohlcv['Downward'] = get_range_filter(
        df_ohlcv['close'], 100, 4)
    df_ohlcv['rf_signal'] = rf_strategy(
        df_ohlcv['close'], df_ohlcv['Filt'], df_ohlcv['Upward'], df_ohlcv['Downward'])

    df_ohlcv['macd_signal'] = macd_cross_strategy(df_ohlcv['MACD_12_26_9'])
    df_ohlcv['macdh_signal'] = macdh_cross_strategy(df_ohlcv['MACDh_12_26_9'])

    return df_ohlcv


def find_signal_macd_updown_rf_sign(df_ohlcv):
    signal = "Non-Signal"
    try:
        macd_signal = df_ohlcv['macd_signal'].iloc[-2]
        rsi_0 = df_ohlcv['RSI_14'].iloc[-2]
        rsi_1 = df_ohlcv['RSI_14'].iloc[-3]
        macdh_signal = df_ohlcv['macdh_signal'].iloc[-2:-7:-1]
        upward = df_ohlcv['Upward'].iloc[-2]
        downward = df_ohlcv['Downward'].iloc[-2]

        if macd_signal == 1 and any(macdh_signal) and 50 < rsi_0 < 70 and rsi_0 - rsi_1 > 1 and 0 < upward < 10:
            signal = "Buy_Signal"
        elif macd_signal == -1 and any(macdh_signal) and 30 < rsi_0 < 50 and rsi_1 - rsi_0 > 1 and 0 < downward < 10:
            signal = "Sell_Signal"

        return signal
    except:
        return signal


def find_st_macd_cross_sign(df_ohlcv):
    Signal = "Non-Signal"
    try:
        st_signal = df_ohlcv['st_signal'].iloc[-2]
        macd_signal = df_ohlcv['macd_signal'].iloc[-2:-7:-1]

        if st_signal == 1 and any(macd_signal == 1):
            Signal = "Buy_Signal"
        elif st_signal == -1 and any(macd_signal == -1):
            Signal = "Sell_Signal"

        return Signal
    except:
        return Signal


def find_ema_200_trend_st_macd_cross_sign(df_ohlcv):
    signal = "Non-Signal"
    try:
        close_0 = df_ohlcv['close'].iloc[-2]
        close_1 = df_ohlcv['close'].iloc[-3]
        st_signal = df_ohlcv['st_signal'].iloc[-2]
        ema_200 = df_ohlcv['EMA_200'].iloc[-2]
        macd = df_ohlcv['MACD_12_26_9'].iloc[-2]
        if (st_signal == 1) and (macd > 0) and (close_0 > ema_200) and (close_0 > close_1):
            signal = "Buy_Signal"
        elif (st_signal == -1) and (macd < 0) and (close_0 < ema_200) and (close_0 < close_1):
            signal = "Sell_Signal"
        return signal
    except:
        return signal


def find_rf_sign(df_ohlcv):
    Signal = "Non-Signal"
    try:
        rf_signal = df_ohlcv['rf_signal'].iloc[-2]
        if rf_signal == 1:
            Signal = "Buy_Signal"
        elif rf_signal == -1:
            Signal = "Sell_Signal"

        return Signal
    except:
        return Signal


def find_st_sign(df_ohlcv):
    Signal = "Non-Signal"
    try:
        st_signal = df_ohlcv['st_signal'].iloc[-2]
        if st_signal == 1:
            Signal = "Buy_Signal"
        elif st_signal == -1:
            Signal = "Sell_Signal"

        return Signal
    except:
        return Signal
