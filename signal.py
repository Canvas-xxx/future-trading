import pandas as pd
import pandas_ta as ta

def detect_signal_sign(exchange, pair, timeframe, limit):
    df_ohlcv = exchange.fetch_ohlcv(pair ,timeframe=timeframe, limit=limit)
    df_ohlcv = pd.DataFrame(df_ohlcv, columns =['datetime', 'open','high','low','close','volume'])
    df_ohlcv['datetime'] = pd.to_datetime(df_ohlcv['datetime'], unit='ms')

    # EMA 12, 26 
    EMA_12 = df_ohlcv.ta.ema(12)
    EMA_26 = df_ohlcv.ta.ema(26)

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

def find_signal_sign(exchange, pair, timeframe, limit):
    # เรียก ข้อมูล จาก  exchange
    df_ohlcv = exchange.fetch_ohlcv(pair ,timeframe=timeframe, limit=limit)

    # เรียงให้เป็น ตาราง + เอามาจัดเรียง ใส่หัวข้อ
    df_ohlcv = pd.DataFrame(df_ohlcv, columns =['datetime', 'open','high','low','close','volume'])

    # แปลงรูปแบบ ของเวลา ด้วย Pandas
    df_ohlcv['datetime'] = pd.to_datetime(df_ohlcv['datetime'], unit='ms')
    
    # EMA 12, 26 
    EMA_12 = df_ohlcv.ta.ema(12)
    EMA_26 = df_ohlcv.ta.ema(26)

    # MACD 12, 26
    macd = df_ohlcv.ta.macd()
    
    # รวมข้อมูล
    df_ohlcv = pd.concat([df_ohlcv, EMA_12, EMA_26, macd], axis=1)
    # print("\n""Concat Data Frame" "\n",df_ohlcv)
    
    #EMA Cross
    count = len(df_ohlcv)
    
    EMA_fast_A = df_ohlcv['EMA_12'][count-2]
    EMA_fast_B = df_ohlcv['EMA_12'][count-3]
    
    EMA_slow_A = df_ohlcv['EMA_26'][count-2]
    EMA_slow_B = df_ohlcv['EMA_26'][count-3]

    PRICE_high_A = df_ohlcv['high'][count-2]
    PRICE_high_B = df_ohlcv['high'][count-3]

    PRICE_low_A = df_ohlcv['low'][count-2]
    PRICE_low_B = df_ohlcv['low'][count-3]

    MACD_A = df_ohlcv['MACD_12_26_9'][count-2]
    MACD_B = df_ohlcv['MACD_12_26_9'][count-3]
    
    # Signal and Trend
    Signal = "Non-Signal"
    Trend = "Non-Trend"
    
    if EMA_fast_A > EMA_slow_A :
        if (MACD_B/MACD_A) >= 4 and PRICE_high_A < EMA_fast_A and PRICE_high_A < EMA_slow_A:
            Trend = "Down_trend"
            if PRICE_high_B < EMA_fast_B and PRICE_high_B > EMA_slow_B:
                Signal = "Sell_Signal"
        else:
            Trend = "Up_trend"
            if EMA_fast_A > EMA_slow_A and EMA_fast_B < EMA_slow_B:
                Signal = "Buy_Signal"
    elif EMA_fast_A < EMA_slow_A :
        if (MACD_B/MACD_A) >= 4 and PRICE_low_A > EMA_fast_A and PRICE_low_A > EMA_slow_A:
            Trend = "Up_trend"
            if PRICE_low_B > EMA_fast_B and PRICE_low_B < EMA_slow_B:
                Signal = "Buy_Signal"
        else:
            Trend = "Down_trend"
            if EMA_fast_A < EMA_slow_A and EMA_fast_B > EMA_slow_B:
                Signal = "Sell_Signal"
 
    return Trend, Signal
