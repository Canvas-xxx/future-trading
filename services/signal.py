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
    
    #EMA Cross
    count = len(df_ohlcv)
    
    EMA_fast_A = df_ohlcv['EMA_12'][count-2]
    EMA_slow_A = df_ohlcv['EMA_26'][count-2]

    EMA_fast_B = df_ohlcv['EMA_12'][count-3] 
    EMA_slow_B = df_ohlcv['EMA_26'][count-3]

    RSI_B = round(df_ohlcv['RSI_14'][count-3], 1)
    
    # Signal and Trend
    Signal = "Non-Signal"

    if EMA_fast_A < EMA_slow_A and EMA_fast_B > EMA_slow_B:
        print("EMA CROSS UP")
        if RSI_B > 35 and RSI_B < 65:
            print("RSI RANGE NORMAL")
            Signal = "Buy_Signal"
    elif EMA_fast_A > EMA_slow_A and EMA_fast_B < EMA_slow_B:
        print("EMA CROSS DOWN")
        if RSI_B > 35 and RSI_B < 65:
            print("RSI RANGE NORMAL")
            Signal = "Sell_Signal"
 
    return Signal

def find_signal_macd_rsi_sign(exchange, pair, timeframe, limit):
    Signal = "Non-Signal"

    df_ohlcv = exchange.fetch_ohlcv(pair ,timeframe=timeframe, limit=limit)
    df_ohlcv = pd.DataFrame(df_ohlcv, columns =['datetime', 'open','high','low','close','volume'])
    df_ohlcv['datetime'] = pd.to_datetime(df_ohlcv['datetime'], unit='ms')

    macd = df_ohlcv.ta.macd(close=df_ohlcv.ta.ohlc4())
    rsi = df_ohlcv.ta.rsi(close=df_ohlcv.ta.ohlc4())

    df_ohlcv = pd.concat([df_ohlcv, macd, rsi], axis=1)

    try:
        count = len(df_ohlcv)
        macd_blue_a = df_ohlcv['MACD_12_26_9'][count-2]
        macd_orange_a = df_ohlcv['MACDs_12_26_9'][count-2]
        rsi_a = round(df_ohlcv['RSI_14'][count-2], 1)

        macd_blue_b = df_ohlcv['MACD_12_26_9'][count-3]
        macd_orange_b = df_ohlcv['MACDs_12_26_9'][count-3]
        rsi_b = round(df_ohlcv['RSI_14'][count-3], 1)

        rsi_c = round(df_ohlcv['RSI_14'][count-4], 1)
    except:
        return Signal


    if macd_blue_a < 0 and macd_orange_a < 0:
        print("MACD LOWER MIDDLE")
        if macd_blue_a < macd_orange_a:
            if macd_blue_a > macd_blue_b and macd_orange_a < macd_orange_b:
                print("MACD WILL CROSS UP TREND")
                if rsi_a > rsi_b and rsi_b > rsi_c:
                    if (rsi_a - rsi_b) > 1 and rsi_a > 42 and rsi_a < 50 and ((rsi_b > 35 and rsi_b < 40) or (rsi_c > 35 and rsi_c < 40)):
                        print("RSI UP")
                        Signal = "Buy_Signal"
        else:
            print("MACD ALREADY CROSS UP TREND")
    elif macd_blue_a > 0 and macd_orange_a > 0:
        print("MACD HIGHER MIDDLE")
        if macd_blue_a > macd_orange_a:
            if macd_blue_a < macd_blue_b and macd_orange_a > macd_orange_b:
                print("MACD WILL CROSS DOWN TREND")
                if rsi_a < rsi_b and rsi_b < rsi_c:
                    if (rsi_b - rsi_a) > 1 and rsi_a > 50 and rsi_a < 58 and ((rsi_b > 60 and rsi_b < 65) or (rsi_c > 60 and rsi_c < 65)):
                        print("RSI DOWN")
                        Signal = "Sell_Signal"
        else:
            print("MACD ALREADY CROSS DOWN TREND")
    return Signal
