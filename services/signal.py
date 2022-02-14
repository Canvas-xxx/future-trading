import pandas as pd
import pandas_ta as ta

def detect_signal_sign(exchange, pair, timeframe, limit):
    df_ohlcv = exchange.fetch_ohlcv(pair ,timeframe=timeframe, limit=limit)
    df_ohlcv = pd.DataFrame(df_ohlcv, columns =['datetime', 'open','high','low','close','volume'])
    df_ohlcv['datetime'] = pd.to_datetime(df_ohlcv['datetime'], unit='ms')

    # EMA 12, 26 
    EMA_12 = df_ohlcv.ta.ema(close=df_ohlcv.ta.ohlc4(), length=12)
    EMA_26 = df_ohlcv.ta.ema(close=df_ohlcv.ta.ohlc4(), length=26)

    df_ohlcv = pd.concat([df_ohlcv, EMA_12, EMA_26], axis=1)

    #EMA Cross
    count = len(df_ohlcv)

    EMA_fast_A = df_ohlcv['EMA_12'][count-2]
    EMA_fast_B = df_ohlcv['EMA_12'][count-3]
    
    EMA_slow_A = df_ohlcv['EMA_26'][count-2]
    EMA_slow_B = df_ohlcv['EMA_26'][count-3]

    # Signal and Trend
    Signal = "HOLD_POSITION"

    if EMA_fast_A < EMA_slow_A and EMA_fast_B > EMA_slow_B:
        Signal = "Sell_POSITION"
    elif EMA_fast_A > EMA_slow_A and EMA_fast_B < EMA_slow_B:
        Signal = "Buy_POSITION"
    else:
        Signal = "HOLD_POSITION"

    return Signal

def find_signal_ema_sign(exchange, pair, timeframe, limit):
    # เรียก ข้อมูล จาก  exchange
    df_ohlcv = exchange.fetch_ohlcv(pair ,timeframe=timeframe, limit=limit)

    # เรียงให้เป็น ตาราง + เอามาจัดเรียง ใส่หัวข้อ
    df_ohlcv = pd.DataFrame(df_ohlcv, columns =['datetime', 'open','high','low','close','volume'])

    # แปลงรูปแบบ ของเวลา ด้วย Pandas
    df_ohlcv['datetime'] = pd.to_datetime(df_ohlcv['datetime'], unit='ms')
    
    # EMA 12, 26 
    EMA_12 = df_ohlcv.ta.ema(close=df_ohlcv.ta.ohlc4(), length=12)
    EMA_26 = df_ohlcv.ta.ema(close=df_ohlcv.ta.ohlc4(), length=26)

    # MACD 12, 26
    macd = df_ohlcv.ta.macd(close=df_ohlcv.ta.ohlc4())
    
    # รวมข้อมูล
    df_ohlcv = pd.concat([df_ohlcv, EMA_12, EMA_26, macd], axis=1)
    # print("\n""Concat Data Frame" "\n",df_ohlcv)
    
    #EMA Cross
    count = len(df_ohlcv)
    
    EMA_fast_A = df_ohlcv['EMA_12'][count-2]
    EMA_slow_A = df_ohlcv['EMA_26'][count-2]
    PRICE_high_A = df_ohlcv['high'][count-2]
    PRICE_low_A = df_ohlcv['low'][count-2]
    MACD_A = df_ohlcv['MACD_12_26_9'][count-2]

    EMA_fast_B = df_ohlcv['EMA_12'][count-3] 
    EMA_slow_B = df_ohlcv['EMA_26'][count-3]
    PRICE_high_B = df_ohlcv['high'][count-3]
    PRICE_low_B = df_ohlcv['low'][count-3]
    MACD_B = df_ohlcv['MACD_12_26_9'][count-3]
    
    # Signal and Trend
    Signal = "Non-Signal"

    if EMA_fast_A > EMA_slow_A:
        if PRICE_high_B > EMA_fast_B and PRICE_low_B < EMA_slow_B and (MACD_B / MACD_A) >= 1.25:
            if PRICE_high_A < EMA_slow_A and (PRICE_high_B / PRICE_low_B) < 1.05:
                Signal = "Sell_Signal"
        else:
            if EMA_fast_B < EMA_slow_B and (PRICE_high_B / PRICE_low_B) < 1.05:
                Signal = "Buy_Signal"
    elif EMA_fast_A < EMA_slow_A:
        if PRICE_high_B > EMA_slow_B and PRICE_low_B < EMA_fast_B and (MACD_B / MACD_A) >= 1.25:
            if PRICE_low_A > EMA_slow_A and (PRICE_high_B / PRICE_low_B) < 1.05:
                Signal = "Buy_Signal"
        else:
            if EMA_fast_B > EMA_slow_B and (PRICE_high_B / PRICE_low_B) < 1.05:
                Signal = "Sell_Signal"
 
    return Signal

def find_signal_macd_rsi_sign(exchange, pair, timeframe, limit):
    df_ohlcv = exchange.fetch_ohlcv(pair ,timeframe=timeframe, limit=limit)
    df_ohlcv = pd.DataFrame(df_ohlcv, columns =['datetime', 'open','high','low','close','volume'])
    df_ohlcv['datetime'] = pd.to_datetime(df_ohlcv['datetime'], unit='ms')

    macd = df_ohlcv.ta.macd(close=df_ohlcv.ta.ohlc4())
    rsi = df_ohlcv.ta.rsi(close=df_ohlcv.ta.ohlc4())

    df_ohlcv = pd.concat([df_ohlcv, macd, rsi], axis=1)

    count = len(df_ohlcv)
    macd_blue_a = df_ohlcv['MACD_12_26_9'][count-2]
    macd_orange_a = df_ohlcv['MACDs_12_26_9'][count-2]
    rsi_a = round(df_ohlcv['RSI_14'][count-2], 1)

    macd_blue_b = df_ohlcv['MACD_12_26_9'][count-3]
    macd_orange_b = df_ohlcv['MACDs_12_26_9'][count-3]
    rsi_b = round(df_ohlcv['RSI_14'][count-3], 1)

    Signal = "Non-Signal"

    if macd_blue_a < 0 and macd_orange_a < 0:
        print("MACD LOWER MIDDLE")
        if macd_blue_a < macd_orange_a:
            if macd_blue_a > macd_blue_b and macd_orange_a < macd_orange_b:
                print("MACD WILL CROSS UP TREND")
                if rsi_a > rsi_b and rsi_b > 60 and rsi_b < 65 and rsi_a > 50 and rsi_a < 55:
                    print("RSI UP")
                    Signal = "Buy_Signal"
        else:
            print("MACD ALREADY CROSS UP TREND")
    elif macd_blue_a > 0 and macd_orange_a > 0:
        print("MACD HIGHER MIDDLE")
        if macd_blue_a > macd_orange_a:
            if macd_blue_a < macd_blue_b and macd_orange_a > macd_orange_b:
                print("MACD WILL CROSS DOWN TREND")
                if rsi_a < rsi_b and rsi_b > 35 and rsi_b < 40 and rsi_a > 45 and rsi_a < 50:
                    print("RSI DOWN")
                    Signal = "Sell_Signal"
        else:
            print("MACD ALREADY CROSS DOWN TREND")
    return Signal
