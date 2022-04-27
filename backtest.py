import ccxt
import settings as ENV
import pandas as pd
import pandas_ta as ta
import moment
import math
import pymongo
# from services.markets import get_market_list
from services.request import push_notify_message
from services.signal import range_filter_signal

API_READING_KEY = ENV.API_READING_KEY
SECRET_READING_KEY = ENV.SECRET_READING_KEY
TF_DURATION = ENV.TF_DURATION
TF_UNIT = ENV.TF_UNIT
BACK_TEST_LIMIT = ENV.BACK_TEST_LIMIT
SL_PERCENTAGE = ENV.SL_PERCENTAGE
TP_PERCENTAGE = ENV.TP_PERCENTAGE
LEVERAGE = ENV.LEVERAGE
LINE_NOTIFY_TOKEN = ENV.LINE_NOTIFY_TOKEN
# LIMIT_SYMBOLS = ENV.LIMIT_SYMBOLS
DATABASE_URL = ENV.DATABASE_URL

exchange = ccxt.binanceusdm({
    'apiKey': API_READING_KEY, 
    'secret': SECRET_READING_KEY,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    }
})

client = pymongo.MongoClient(DATABASE_URL)
symbol_backtest_stat = client.binance.symbol_backtest_stat

def schedule_backtest():
    db_markets = symbol_backtest_stat.aggregate([{ "$sort": {  "win_rate_percentage": -1, "total_win": -1, "total_position": -1  } }])
    markets = list(db_markets)
    # markets = get_market_list(exchange, 'future', 'USDT')
    # markets = markets[0:LIMIT_SYMBOLS]

    summary_total = 0
    summary_success = 0
    summary_fail = 0
    orders_date_list = []
    orders_date_dict = {}
    count_success_position = 0
    count_fail_position = 0
    count_has_position_symbol = 0
    avg_success_candle = 0
    avg_fault_candle = 0
    avg_all_symbol_close_candle = 0

    for market in markets:
        try:
            total, success, fail, orders_inform_list, avg_close_candle, _, _ = backtest_symbol(market.get('symbol'), BACK_TEST_LIMIT)
        except:
            total, success, fail, orders_inform_list, avg_close_candle = 0, 0, 0, [], 0

        summary_total += total
        summary_success += success
        summary_fail += fail
        orders_date_list += list(map(lambda order_inform: order_inform.get("datetime"), orders_inform_list))
        if total > 0:
            count_has_position_symbol += 1
            avg_all_symbol_close_candle += avg_close_candle
            for order_inform in orders_inform_list:
                st = order_inform.get("state")
                cd = order_inform.get("candle")
                if st == "S":
                    count_success_position += 1
                    avg_success_candle += cd
                else:
                    count_fail_position += 1
                    avg_fault_candle += cd 

    notify_message = None
    if summary_total > 0 and summary_success > 0:
        orders_date_list.sort()
        orders_date_list = list(map(lambda order_d: moment.utc(order_d).format("YYYY-MM-DD"), orders_date_list))
        orders_date_dict = {i:orders_date_list.count(i) for i in orders_date_list}

        high_same_day_orders = 0
        for date in orders_date_dict.keys():
            if orders_date_dict[date] > high_same_day_orders:
                high_same_day_orders = orders_date_dict[date]

        if avg_success_candle > 0:
            avg_success_candle = math.ceil(avg_success_candle / count_success_position)
        if avg_fault_candle > 0:
            avg_fault_candle = math.ceil(avg_fault_candle / count_fail_position)
        if avg_all_symbol_close_candle > 0: 
            avg_all_symbol_close_candle = math.ceil(avg_all_symbol_close_candle / count_has_position_symbol)

        notify_message = "\n""### Backtest Schedule ###"
        notify_message += "\n""Take Profit Percentage " + str(TP_PERCENTAGE)
        notify_message += "\n""Stop Loss Percentage " + str(SL_PERCENTAGE)
        notify_message += "\n""Start Order At " + str(orders_date_list[0])
        notify_message += "\n""Maximum Number of Positions " + str(high_same_day_orders)
        notify_message += "\n""Total Signal " + str(summary_total)
        notify_message += "\n""Success Signal " + str(summary_success)
        notify_message += "\n""Fault Signal " + str(summary_fail)
        notify_message += "\n""Avg. Success Candle " + str(avg_success_candle)
        notify_message += "\n""Avg. Fault Candle " + str(avg_fault_candle)
        notify_message += "\n""Avg. Close Position Candle " + str(avg_all_symbol_close_candle)
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

        notify_message += "\n""#####################"

    if notify_message != None:
        push_notify_message(LINE_NOTIFY_TOKEN, notify_message)

def position_backtest_symbol(symbol, notify):
    total, success, fail, orders_inform_list, avg_close_candle, current_order_position_date, current_order_position_number = backtest_symbol(symbol, BACK_TEST_LIMIT)

    count_success_position = 0
    count_fail_position = 0
    avg_success_candle = 0
    avg_fault_candle = 0

    if current_order_position_date != None:
        current_order_position_date = moment.utc(current_order_position_date).format("YYYY-MM-DD HH:mm:ss")

    notify_message = None
    if total > 0 and success> 0:
        notify_message = "\n""### Current Position Backtest ###"
        notify_message += "\n""Take Profit Percentage " + str(TP_PERCENTAGE)
        notify_message += "\n""Stop Loss Percentage " + str(SL_PERCENTAGE)
        notify_message += "\n""Symbol " + str(symbol)
        if len(orders_inform_list) > 0:
            notify_message += "\n""Positions At"
            for order_inform in orders_inform_list:
                dt = order_inform.get("datetime")
                cd = order_inform.get("candle")
                st = order_inform.get("state")
                notify_message += "\n" + moment.utc(dt).format("YYYY-MM-DD HH:mm:ss") + " (" + str(cd) + ")" + "[" + st + "]"
                if st == "S":
                    count_success_position += 1
                    avg_success_candle += cd
                else:
                    count_fail_position += 1
                    avg_fault_candle += cd
            if avg_success_candle > 0:
                avg_success_candle = math.ceil(avg_success_candle / count_success_position)
            if avg_fault_candle > 0:
                avg_fault_candle = math.ceil(avg_fault_candle / count_fail_position)

        notify_message += "\n""Total Signal " + str(total)
        notify_message += "\n""Success Signal " + str(success)
        notify_message += "\n""Fault Signal " + str(fail)
        notify_message += "\n""Avg. Success Candle " + str(avg_success_candle)
        notify_message += "\n""Avg. Fault Candle " + str(avg_fault_candle)
        notify_message += "\n""Avg. Close Position Length " + str(avg_close_candle)

        try:
            win_rate = (success / total) * 100
        except:
            win_rate = 0
        notify_message += "\n""Win Rate " + str(win_rate) + "%"

        try:
            summary_profit = ((TP_PERCENTAGE * success) - (SL_PERCENTAGE * fail)) * LEVERAGE
        except:
            summary_profit = 0
        notify_message += "\n""Summary Profit Percentage " + str(summary_profit) + "%"

        notify_message += "\n""###########################"

    if notify_message != None and notify == True:
        push_notify_message(LINE_NOTIFY_TOKEN, notify_message)

    return  total, success, fail, win_rate, avg_success_candle, avg_fault_candle, avg_close_candle, current_order_position_date, current_order_position_number

def backtest_symbol(symbol, back_test_limit):
    timeframe = TF_DURATION + TF_UNIT
    limit = back_test_limit 

    df_ohlcv = exchange.fetch_ohlcv(symbol ,timeframe=timeframe, limit=limit)
    df_ohlcv = pd.DataFrame(df_ohlcv, columns =['datetime', 'open','high','low','close','volume'])
    df_ohlcv['datetime'] = pd.to_datetime(df_ohlcv['datetime'], unit='ms')

    total_signal = 0
    success_signal = 0
    fail_signal = 0
    datetime = None

    count_has_position_symbol = 0
    count_candle_each_position = 0
    avg_close_candle = 0

    orders_inform_list = []

    signal = None
    position_price = 0

    current_order_position_date = None
    current_order_position_number = 0

    count = len(df_ohlcv)
    index = 0

    print("Symbol", symbol)
    print("TP PERCENTAGE", TP_PERCENTAGE)
    print("SL PERCENTAGE", SL_PERCENTAGE)

    while index < count:
        df_ohlcv_range = df_ohlcv[0:index]

        if signal == None:
            s = find_signal_macd_4c_sign(exchange, df_ohlcv_range, symbol)
            if s == "Buy_Signal" or s == "Sell_Signal":
                datetime = df_ohlcv['datetime'][index-1]
                current_order_position_date = datetime
                current_order_position_number = 0
                position_price = df_ohlcv['open'][index-1]
                count_candle_each_position = 0
                signal = s
        elif signal != None:
            last_candle_high = df_ohlcv['high'][index]
            last_candle_low = df_ohlcv['low'][index]
            current_order_position_number += 1

            if signal == "Buy_Signal":
                avg_close_candle += 1
                count_candle_each_position += 1
                sl_price = (position_price * (1 - (SL_PERCENTAGE / 100))) 
                tp_price = (position_price * ((TP_PERCENTAGE / 100) + 1)) 

                if last_candle_low <= sl_price:
                    fail_signal += 1
                    total_signal += 1
                    signal = None
                    count_has_position_symbol += 1
                    print("Position at", datetime, "(" + str(count_candle_each_position) + ")", "[F]")
                    orders_inform_list.append({
                        "datetime": datetime,
                        "candle": count_candle_each_position,
                        "state": "F"
                    })
                    current_order_position_date = None
                    current_order_position_number = 0
                elif last_candle_high >= tp_price: 
                    success_signal += 1
                    total_signal += 1
                    signal = None
                    count_has_position_symbol += 1
                    print("Position at", datetime, "(" + str(count_candle_each_position) + ")", "[S]")
                    orders_inform_list.append({
                        "datetime": datetime,
                        "candle": count_candle_each_position,
                        "state": "S"
                    })
                    current_order_position_date = None
                    current_order_position_number = 0
            elif signal == "Sell_Signal":
                avg_close_candle += 1
                count_candle_each_position += 1
                sl_price = (position_price * ((SL_PERCENTAGE / 100) + 1)) 
                tp_price = (position_price * (1 - (TP_PERCENTAGE / 100))) 

                if last_candle_high >= sl_price:
                    fail_signal += 1
                    total_signal += 1
                    signal = None
                    count_has_position_symbol += 1
                    print("Position at", datetime, "(" + str(count_candle_each_position) + ")", "[F]")
                    orders_inform_list.append({
                        "datetime": datetime,
                        "candle": count_candle_each_position,
                        "state": "F"
                    })
                    current_order_position_date = None
                    current_order_position_number = 0
                elif last_candle_low <= tp_price:
                    success_signal += 1
                    total_signal += 1
                    signal = None
                    count_has_position_symbol += 1
                    print("Position at", datetime, "(" + str(count_candle_each_position) + ")", "[S]")
                    orders_inform_list.append({
                        "datetime": datetime,
                        "candle": count_candle_each_position,
                        "state": "S"
                    })
                    current_order_position_date = None
                    current_order_position_number = 0

        index += 1

    try:
        avg_close_candle = avg_close_candle - current_order_position_number
        avg_close_candle = math.ceil(avg_close_candle/count_has_position_symbol)
    except:
        avg_close_candle = 0

    print("Total Signal", total_signal)
    print("Success Signal", success_signal)
    print("Fail Signal", fail_signal)
    print("Avg. Close Position Candle ", avg_close_candle)
    try:
        print("Win rate", str((success_signal / total_signal) * 100) + "%")
    except:
        print("Win rate", "0%")

    print("##################################")
    return total_signal, success_signal, fail_signal, orders_inform_list, avg_close_candle, current_order_position_date, current_order_position_number

def find_signal_macd_4c_sign(exchange, df_ohlcv, pair):
    Signal = "Non-Signal"
    try:
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
        
        _, upward, downward = range_filter_signal(df_ohlcv, 100, 4)
    except:
        return Signal

    len_ward = len(upward)
    if macd_a > 0 and macd_b < 0:
        if (macdh_a > 0 and macdh_b < 0 and macdh_b > macdh_c) or \
        (macdh_b > 0 and macdh_c < 0 and macdh_c > macdh_d) or \
        (macdh_c > 0 and macdh_d < 0 and macdh_d > macdh_e) or \
        (macdh_d > 0 and macdh_e < 0 and macdh_e > macdh_f) or \
        (macdh_e > 0 and macdh_f < 0 and macdh_f > macdh_g):
            if rsi_a > 50 and rsi_a < 70 and (rsi_a - rsi_b) > 1:
                if upward[len_ward-1] > 0 and upward[len_ward-1] < 10:
                    Signal = "Buy_Signal"
    elif macd_a < 0 and macd_b > 0:
        if (macdh_a < 0 and macdh_b > 0 and macdh_b < macdh_c) or \
        (macdh_b < 0 and macdh_c > 0 and macdh_c < macdh_d) or \
        (macdh_c < 0 and macdh_d > 0 and macdh_d < macdh_e) or \
        (macdh_d < 0 and macdh_e > 0 and macdh_e < macdh_f) or \
        (macdh_e < 0 and macdh_f > 0 and macdh_f < macdh_g):
            if rsi_a > 30 and rsi_a < 50 and (rsi_b - rsi_a) > 1:
                if downward[len_ward-1] > 0 and downward[len_ward-1] < 10:
                    Signal = "Sell_Signal"

    return Signal

if __name__ == "__main__":
    print("\n""####### Run Back Test #####")

    try:
        schedule_backtest()
    except (KeyboardInterrupt, SystemExit):
        pass
