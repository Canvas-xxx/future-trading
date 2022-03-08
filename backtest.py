import ccxt
import settings as ENV
import pandas as pd
import pandas_ta as ta
from services.markets import get_market_list
from services.request import push_notify_message

API_KEY = ENV.API_KEY
SECRET_KEY = ENV.SECRET_KEY
TF_DURATION = ENV.TF_DURATION
TF_UNIT = ENV.TF_UNIT
BACK_TEST_LIMIT = ENV.BACK_TEST_LIMIT
SL_PERCENTAGE = ENV.SL_PERCENTAGE
TP_PERCENTAGE = ENV.TP_PERCENTAGE
LEVERAGE = ENV.LEVERAGE
LINE_NOTIFY_TOKEN = ENV.LINE_NOTIFY_TOKEN

exchange = ccxt.binanceusdm({
    'apiKey': API_KEY, 
    'secret': SECRET_KEY,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    }
})

def schedule_backtest():
    markets = get_market_list(exchange, 'future', 'USDT')
    markets = markets[0:15]

    index = 1
    summary_total = 0
    summary_success = 0
    summary_fail = 0

    for market in markets:
        total, success, fail = run_test(market.get('symbol'), index)
        summary_total += total
        summary_success += success
        summary_fail += fail
        index += 1

    if summary_total > 0 and summary_success > 0:
        notify_message = "### Backtest Schedule ###"
        notify_message += "\n""Take Profit Percentage " + str(TP_PERCENTAGE)
        notify_message += "\n""Stop Loss Percentage " + str(SL_PERCENTAGE)
        notify_message += "\n""Total Signal " + str(summary_total)
        notify_message += "\n""Success Signal " + str(summary_success)
        notify_message += "\n""Fault Signal " + str(summary_fail)
        try:
            win_rate = (summary_success / summary_total) * 100
        except:
            win_rate = 0
        notify_message += "\n""Win Rate " + str(win_rate) + "%"

        try:
            summary_profit = ((TP_PERCENTAGE * summary_success) - (SL_PERCENTAGE * summary_fail)) * LEVERAGE
        except:
            summary_profit = 0
        notify_message += "\n""Summary Profit Percentage " + str(summary_profit) + "%"

        notify_message += "\n""#########################"

    if notify_message != None:
        push_notify_message(LINE_NOTIFY_TOKEN, notify_message)

def run_test(symbol, i):
    timeframe = TF_DURATION + TF_UNIT
    limit = BACK_TEST_LIMIT

    df_ohlcv = exchange.fetch_ohlcv(symbol ,timeframe=timeframe, limit=limit)
    df_ohlcv = pd.DataFrame(df_ohlcv, columns =['datetime', 'open','high','low','close','volume'])
    df_ohlcv['datetime'] = pd.to_datetime(df_ohlcv['datetime'], unit='ms')

    total_signal = 0
    success_signal = 0
    fail_signal = 0
    signal = None
    position_price = 0

    count = len(df_ohlcv)
    index = 50

    print("Symbol", symbol)
    print("TP PERCENTAGE", TP_PERCENTAGE)
    print("SL PERCENTAGE", SL_PERCENTAGE)

    while index < count:
        df_ohlcv_range = df_ohlcv[0:index]
        if signal == None:
            s = find_signal_macd_4c_sign(exchange, df_ohlcv_range, symbol)
            if s == "Buy_Signal" or s == "Sell_Signal":
                if total_signal == 0:
                    datetime = df_ohlcv['datetime'][index]
                    print("Start at", datetime)
                position_price = df_ohlcv['open'][index-1]
                signal = s
        elif signal != None:
            last_candle_high = df_ohlcv['high'][index]
            last_candle_low = df_ohlcv['low'][index]

            if signal == "Buy_Signal":
                sl_price = (position_price * (1 - (SL_PERCENTAGE / 100))) 
                tp_price = (position_price * ((TP_PERCENTAGE / 100) + 1)) 
                if last_candle_low <= sl_price:
                    fail_signal += 1
                    total_signal += 1
                    signal = None
                    position_price = 0
                elif last_candle_high >= tp_price: 
                    success_signal += 1
                    total_signal += 1
                    signal = None
                    position_price = 0
            elif signal == "Sell_Signal":
                sl_price = (position_price * ((SL_PERCENTAGE / 100) + 1)) 
                tp_price = (position_price * (1 - (TP_PERCENTAGE / 100))) 
                if last_candle_high >= sl_price:
                    fail_signal += 1
                    total_signal += 1
                    signal = None
                    position_price = 0
                elif last_candle_low <= tp_price:
                    success_signal += 1
                    total_signal += 1
                    signal = None
                    position_price = 0
        index += 1

    print("Total Signal", total_signal)
    print("Success Signal", success_signal)
    print("Fail Signal", fail_signal)
    try:
        print("Win rate", str((success_signal / total_signal) * 100) + "%")
    except:
        print("Win rate", "0%")

    print("##################################")
    return total_signal, success_signal, fail_signal

def find_signal_macd_4c_sign(exchange, df_ohlcv, pair):
    Signal = "Non-Signal"
    try:
        macd = df_ohlcv.ta.macd()
        rsi = df_ohlcv.ta.rsi()

        df_ohlcv = pd.concat([df_ohlcv, macd, rsi], axis=1)

        count = len(df_ohlcv)

        macd_a = df_ohlcv['MACD_12_26_9'][count-2]
        macd_b = df_ohlcv['MACD_12_26_9'][count-3]

        macdh_a = df_ohlcv['MACDh_12_26_9'][count-2]
        macdh_b = df_ohlcv['MACDh_12_26_9'][count-3]
        macdh_c = df_ohlcv['MACDh_12_26_9'][count-4]
        macdh_d = df_ohlcv['MACDh_12_26_9'][count-5]
        macdh_e = df_ohlcv['MACDh_12_26_9'][count-6]
        macdh_f = df_ohlcv['MACDh_12_26_9'][count-7]
        macdh_g = df_ohlcv['MACDh_12_26_9'][count-8]

        rsi_a = df_ohlcv['RSI_14'][count-2]
        rsi_b = df_ohlcv['RSI_14'][count-3]
    except:
        return Signal

    if macd_a > 0 and macd_b < 0:
        if (macdh_a > 0 and macdh_b < 0 and macdh_b > macdh_c) or (macdh_b > 0 and macdh_c < 0 and macdh_c > macdh_d) or (macdh_c > 0 and macdh_d < 0 and macdh_d > macdh_e) or (macdh_d > 0 and macdh_e < 0 and macdh_e > macdh_f) or (macdh_e > 0 and macdh_f < 0 and macdh_f > macdh_g):
            if rsi_a > 50 and rsi_a < 70:
                if (rsi_a - rsi_b) > 1:
                    Signal = "Buy_Signal"
    elif macd_a < 0 and macd_b > 0:
        if (macdh_a < 0 and macdh_b > 0 and macd_b < macdh_c) or (macdh_b < 0 and macdh_c > 0 and macdh_c < macdh_d) or (macdh_c < 0 and macdh_d > 0 and macdh_d < macdh_e) or (macdh_d < 0 and macdh_e > 0 and macdh_e < macdh_f) or (macdh_e < 0 and macdh_f > 0 and macdh_f < macdh_g):
            if rsi_a > 30 and rsi_a < 50:
                if (rsi_b - rsi_a) > 1:
                    Signal = "Sell_Signal"

    return Signal

if __name__ == "__main__":
    print("\n""####### Run Back Test #####")

    try:
        schedule_backtest()
    except (KeyboardInterrupt, SystemExit):
        pass
