import pandas as pd
import pandas_ta as ta

def detect_signal_sign(exchange, pair, timeframe, limit):
    Signal = "HOLD_POSITION"

    try:
        df_ohlcv = exchange.fetch_ohlcv(pair ,timeframe=timeframe, limit=limit)
        df_ohlcv = pd.DataFrame(df_ohlcv, columns =['datetime', 'open','high','low','close','volume'])
        df_ohlcv['datetime'] = pd.to_datetime(df_ohlcv['datetime'], unit='ms')

        macd = df_ohlcv.ta.macd()

        df_ohlcv = pd.concat([df_ohlcv, macd], axis=1)

        count = len(df_ohlcv)

        macd_a = df_ohlcv['MACD_12_26_9'][count-2]
        macd_b = df_ohlcv['MACD_12_26_9'][count-3]
    except:
        return Signal

    if macd_a > 0 and macd_b < 0:
        Signal = "BUY_POSITION"
    elif macd_a < 0 and macd_b > 0:
        Signal = "SELL_POSITION"
    else:
        Signal = "HOLD_POSITION"

    return Signal

def find_signal_macd_4c_sign(exchange, pair, timeframe, limit):
    Signal = "Non-Signal"
    try:
        df_ohlcv = exchange.fetch_ohlcv(pair ,timeframe=timeframe, limit=limit)
        df_ohlcv = pd.DataFrame(df_ohlcv, columns =['datetime', 'open','high','low','close','volume'])
        df_ohlcv['datetime'] = pd.to_datetime(df_ohlcv['datetime'], unit='ms')

        macd = df_ohlcv.ta.macd()
        rsi = df_ohlcv.ta.rsi()

        df_ohlcv = pd.concat([df_ohlcv, macd, rsi], axis=1)

        count = len(df_ohlcv)

        macd_a = df_ohlcv['MACD_12_26_9'][count-2]
        macd_b = df_ohlcv['MACD_12_26_9'][count-3]

        rsi_a = df_ohlcv['RSI_14'][count-2]
        rsi_b = df_ohlcv['RSI_14'][count-3]

        macdh_a = df_ohlcv['MACDh_12_26_9'][count-2]
        macdh_b = df_ohlcv['MACDh_12_26_9'][count-3]
        macdh_c = df_ohlcv['MACDh_12_26_9'][count-4]
        macdh_d = df_ohlcv['MACDh_12_26_9'][count-5]
        macdh_e = df_ohlcv['MACDh_12_26_9'][count-6]
        macdh_f = df_ohlcv['MACDh_12_26_9'][count-7]
        macdh_g = df_ohlcv['MACDh_12_26_9'][count-8]
    except:
        return Signal

    if macd_a > 0 and macd_b < 0:
        print("MACD WILL UP TREND")
        if (macdh_a > 0 and macdh_b < 0 and macdh_b > macdh_c) or \
        (macdh_b > 0 and macdh_c < 0 and macdh_c > macdh_d) or \
        (macdh_c > 0 and macdh_d < 0 and macdh_d > macdh_e) or \
        (macdh_d > 0 and macdh_e < 0 and macdh_e > macdh_f) or \
        (macdh_e > 0 and macdh_f < 0 and macdh_f > macdh_g):
            print("MACD HAS NEARLY CROSS UP")
            if rsi_a > 50 and rsi_a < 70:
                print("RSI IS IN NORMAL RANGE")
                if (rsi_a - rsi_b) > 1:
                    print("RSI IS UP")
                    Signal = "Buy_Signal"
    elif macd_a < 0 and macd_b > 0:
        print("MACD WILL DOWN TREND")
        if (macdh_a < 0 and macdh_b > 0 and macd_b < macdh_c) or \
        (macdh_b < 0 and macdh_c > 0 and macdh_c < macdh_d) or \
        (macdh_c < 0 and macdh_d > 0 and macdh_d < macdh_e) or \
        (macdh_d < 0 and macdh_e > 0 and macdh_e < macdh_f) or \
        (macdh_e < 0 and macdh_f > 0 and macdh_f < macdh_g):
            print("MACD HAS NEARLY CROSS DOWN")
            if rsi_a > 30 and rsi_a < 50:
                print("RSI IS IN NORMAL RANGE")
                if (rsi_b - rsi_a) > 1:
                    print("RSI IS DOWN")
                    Signal = "Sell_Signal"
    else:
        print("MACD ALREADY HAS TREND")

    return Signal

def find_signal_ema_sign(exchange, pair, timeframe, limit):
    Signal = "Non-Signal"

    try:
        df_ohlcv = exchange.fetch_ohlcv(pair ,timeframe=timeframe, limit=limit)
        df_ohlcv = pd.DataFrame(df_ohlcv, columns =['datetime', 'open','high','low','close','volume'])
        df_ohlcv['datetime'] = pd.to_datetime(df_ohlcv['datetime'], unit='ms')
    
        ema_12 = df_ohlcv.ta.ema(close=df_ohlcv.ta.ohlc4(), length=12)
        ema_26 = df_ohlcv.ta.ema(close=df_ohlcv.ta.ohlc4(), length=26)
        macd = df_ohlcv.ta.macd()
        rsi = df_ohlcv.ta.rsi()
    
        df_ohlcv = pd.concat([df_ohlcv, ema_12, ema_26, macd, rsi], axis=1)
    
        count = len(df_ohlcv)
    
        ema_fast_a = df_ohlcv['EMA_12'][count-2]
        ema_slow_a = df_ohlcv['EMA_26'][count-2]

        ema_fast_b = df_ohlcv['EMA_12'][count-3] 
        ema_slow_b = df_ohlcv['EMA_26'][count-3]

        rsi_a = round(df_ohlcv['RSI_14'][count-2], 1)

        macd_a = df_ohlcv['MACDh_12_26_9'][count-2]
        macd_b = df_ohlcv['MACDh_12_26_9'][count-3]
        macd_c = df_ohlcv['MACDh_12_26_9'][count-4]
        macd_d = df_ohlcv['MACDh_12_26_9'][count-5]    
    except:
        return Signal

    if ema_fast_a < ema_slow_a and ema_fast_b > ema_slow_b:
        print("EMA CROSS UP")
        if rsi_a > 35 and rsi_a < 65:
            print("RSI RANGE NORMAL")
            if (macd_d < 0 and macd_c > 0) or (macd_c < 0 and macd_b > 0) or (macd_b < 0 and macd_a > 0):
                print("ALREADY CROSS UP NEARLY")
                Signal = "Buy_Signal"
    elif ema_fast_a > ema_slow_a and ema_fast_b < ema_slow_b:
        print("EMA CROSS DOWN")
        if rsi_a > 35 and rsi_a < 65:
            print("RSI RANGE NORMAL")
            if (macd_d > 0 and macd_c < 0) or (macd_c > 0 and macd_b < 0) or (macd_b > 0 and macd_a < 0):
                print("ALREADY CROSS DOWN NEARLY")
                Signal = "Sell_Signal"
 
    return Signal
