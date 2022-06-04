import pandas as pd
import pandas_ta as ta
from services.indecator import get_supertrend, get_range_filter
from services.strategy import st_strategy, rf_strategy, macd_cross_strategy, macdh_cross_strategy

def get_df_ohlcv(exchange, symbol, timeframe, limit):
    df_ohlcv = exchange.fetch_ohlcv(symbol,timeframe=timeframe, limit=limit)
    df_ohlcv = pd.DataFrame(df_ohlcv, columns =['datetime', 'open','high','low','close','volume'])
    df_ohlcv['datetime'] = pd.to_datetime(df_ohlcv['datetime'], unit='ms')

    if len(df_ohlcv) <= 200:
        return pd.Series([])

    ema = df_ohlcv.ta.ema(length=200)
    atr = df_ohlcv.ta.atr(length=14)
    macd = df_ohlcv.ta.macd()
    rsi = df_ohlcv.ta.rsi()

    df_ohlcv = pd.concat([df_ohlcv, ema, atr, macd, rsi], axis=1)
    df_ohlcv = df_ohlcv.loc[:,~df_ohlcv.columns.duplicated()]

    df_ohlcv['Supertrend'], _, _ = get_supertrend(df_ohlcv['high'], df_ohlcv['low'], df_ohlcv['close'], 10, 3)
    df_ohlcv['st_signal'] = st_strategy(df_ohlcv['close'], df_ohlcv['Supertrend'])

    df_ohlcv['Filt'], df_ohlcv['Upward'], df_ohlcv['Downward'] = get_range_filter(df_ohlcv['close'], 100, 4)
    df_ohlcv['rf_signal'] = rf_strategy(df_ohlcv['close'], df_ohlcv['Filt'], df_ohlcv['Upward'], df_ohlcv['Downward']) 

    df_ohlcv['macd_signal'] = macd_cross_strategy(df_ohlcv['MACD_12_26_9'])
    df_ohlcv['macdh_signal'] = macdh_cross_strategy(df_ohlcv['MACDh_12_26_9'])

    return df_ohlcv

def find_signal_macd_updown_rf_sign(df_ohlcv):
    Signal = "Non-Signal"
    try:
        count = len(df_ohlcv)

        macd_signal = df_ohlcv['macd_signal'][count-2]
        rsi_0 = df_ohlcv['RSI_14'][count-2]
        rsi_1 = df_ohlcv['RSI_14'][count-3]
        macdh_signal_0 = df_ohlcv['macdh_signal'][count-2]
        macdh_signal_1 = df_ohlcv['macdh_signal'][count-3]
        macdh_signal_2 = df_ohlcv['macdh_signal'][count-4]
        macdh_signal_3 = df_ohlcv['macdh_signal'][count-5]
        macdh_signal_4 = df_ohlcv['macdh_signal'][count-6]

        upward = df_ohlcv['Upward'][count-2]
        downward = df_ohlcv['Downward'][count-2]

        if macd_signal == 1:
            if macdh_signal_0 == 1 or macdh_signal_1 == 1 or \
            macdh_signal_2 == 1 or macdh_signal_3 == 1 or macdh_signal_4 == 1:
                if rsi_0 > 50 and rsi_0 < 70 and (rsi_0 - rsi_1) > 1:
                    if upward > 0 and upward < 10:
                        Signal = "Buy_Signal"
        elif macd_signal == -1:
            if macdh_signal_0 == -1 or macdh_signal_1 == -1 or \
            macdh_signal_2 == -1 or macdh_signal_3 == -1 or macdh_signal_4 == -1:
                if rsi_0 > 30 and rsi_0 < 50 and (rsi_1 - rsi_0) > 1:
                    if downward > 0 and downward < 10:
                        Signal = "Sell_Signal"

        return Signal
    except:
        return Signal

def find_st_macd_cross_sign(df_ohlcv):
    Signal = "Non-Signal"
    try:
        count = len(df_ohlcv)

        st_signal = df_ohlcv['st_signal'][count-2]
        macd_signal_0 = df_ohlcv['macd_signal'][count-2]
        macd_signal_1 = df_ohlcv['macd_signal'][count-3]
        macd_signal_2 = df_ohlcv['macd_signal'][count-4]
        macd_signal_3 = df_ohlcv['macd_signal'][count-5]
        macd_signal_4 = df_ohlcv['macd_signal'][count-6]

        if st_signal == 1 and (macd_signal_0 == 1 or macd_signal_1 == 1 or macd_signal_2 == 1 or macd_signal_3 == 1 or macd_signal_4 == 1):
            Signal = "Buy_Signal"
        elif st_signal == -1 and (macd_signal_0 == -1 or macd_signal_1 == -1 or macd_signal_2 == -1 or macd_signal_3 == -1 or macd_signal_4 == -1):
            Signal = "Sell_Signal"

        return Signal
    except:
        return Signal

def find_ema_200_trend_st_macd_cross_sign(df_ohlcv):
    Signal = "Non-Signal"
    try:
        count = len(df_ohlcv)

        close_0 = df_ohlcv['close'][count-2]
        close_1 = df_ohlcv['close'][count-3]

        st_signal = df_ohlcv['st_signal'][count-2]
        ema_200 = df_ohlcv['EMA_200'][count-2]
        macd = df_ohlcv['MACD_12_26_9'][count-2]

        if st_signal == 1 and macd > 0 and close_0 > ema_200 and close_0 > close_1:
            Signal = "Buy_Signal"
        elif st_signal == -1 and macd < 0 and close_0 < ema_200 and close_0 < close_1:
            Signal = "Sell_Signal"

        return Signal
    except:
        return Signal

def find_rf_sign(df_ohlcv):
    Signal = "Non-Signal"
    try:
        count = len(df_ohlcv)

        rf_signal = df_ohlcv['rf_signal'][count-2]
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
        count = len(df_ohlcv)

        st_signal = df_ohlcv['st_signal'][count-2]
        if st_signal == 1:
            Signal = "Buy_Signal"
        elif st_signal == -1:
            Signal = "Sell_Signal"

        return Signal
    except:
        return Signal
