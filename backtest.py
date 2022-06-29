import ccxt
import settings as ENV
import moment
import math
import pymongo
from services.markets import get_market_list
from services.request import push_notify_message
from services.signal import get_df_ohlcv, find_signal_macd_updown_rf_sign

API_READING_KEY = ENV.API_READING_KEY
SECRET_READING_KEY = ENV.SECRET_READING_KEY
TF_DURATION = ENV.TF_DURATION
TF_UNIT = ENV.TF_UNIT
BACK_TEST_LIMIT = ENV.BACK_TEST_LIMIT
SL_PERCENTAGE = ENV.SL_PERCENTAGE
TP_PERCENTAGE = ENV.TP_PERCENTAGE
LEVERAGE = ENV.LEVERAGE
FUTURE_POSITION_SIZE = ENV.FUTURE_POSITION_SIZE
LINE_NOTIFY_TOKEN = ENV.LINE_NOTIFY_TOKEN
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
my_trades = client.binance.my_trades


def schedule_backtest():
    db_markets = symbol_backtest_stat.aggregate(
        [{"$sort": {"win_rate_percentage": -1, "total_win": -1, "total_position": -1}}])
    markets = list(db_markets)

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
            total, success, fail, orders_inform_list, avg_close_candle, _, _ = backtest_symbol(
                market.get('symbol'), BACK_TEST_LIMIT)
        except:
            total, success, fail, orders_inform_list, avg_close_candle = 0, 0, 0, [], 0

        summary_total += total
        summary_success += success
        summary_fail += fail
        orders_date_list += list(
            map(lambda order_inform: order_inform.get("datetime"), orders_inform_list))
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
        orders_date_list = list(map(lambda order_d: moment.utc(
            order_d).format("YYYY-MM-DD"), orders_date_list))
        orders_date_dict = {i: orders_date_list.count(
            i) for i in orders_date_list}

        high_same_day_orders = 0
        for date in orders_date_dict.keys():
            if orders_date_dict[date] > high_same_day_orders:
                high_same_day_orders = orders_date_dict[date]

        if avg_success_candle > 0:
            avg_success_candle = math.ceil(
                avg_success_candle / count_success_position)
        if avg_fault_candle > 0:
            avg_fault_candle = math.ceil(
                avg_fault_candle / count_fail_position)
        if avg_all_symbol_close_candle > 0:
            avg_all_symbol_close_candle = math.ceil(
                avg_all_symbol_close_candle / count_has_position_symbol)

        notify_message = "\n""### Backtest Schedule ###"
        notify_message += "\n""Take Profit Percentage " + str(TP_PERCENTAGE)
        notify_message += "\n""Stop Loss Percentage " + str(SL_PERCENTAGE)
        notify_message += "\n""Start Order At " + str(orders_date_list[0])
        notify_message += "\n""Maximum Number of Positions " + \
            str(high_same_day_orders) + "\n"
        notify_message += "\n""Total Signal " + str(summary_total)
        notify_message += "\n""Success Signal " + str(summary_success)
        notify_message += "\n""Fault Signal " + str(summary_fail)
        notify_message += "\n""Avg. Success Candle " + str(avg_success_candle)
        notify_message += "\n""Avg. Fault Candle " + str(avg_fault_candle)
        notify_message += "\n""Avg. Close Position Candle " + \
            str(avg_all_symbol_close_candle)
        try:
            win_rate = (summary_success / summary_total) * 100
        except:
            win_rate = 0
        notify_message += "\n""Win Rate " + str(win_rate) + "%"

        try:
            summary_profit = ((TP_PERCENTAGE * summary_success) -
                              (SL_PERCENTAGE * summary_fail)) * LEVERAGE
            realized_pnl = (summary_profit / 100) * FUTURE_POSITION_SIZE
        except:
            summary_profit = 0
            realized_pnl = 0
        notify_message += "\n""Summary Profit Percentage " + \
            str(summary_profit) + "%"
        notify_message += "\n""Realized PNL " + str(realized_pnl) + "USDT"

        try:
            start_time = exchange.parse8601(
                str(orders_date_list[0]) + "T00:00:00")
            my_trades_list = my_trades.aggregate([{"$sort": {"datetime": -1}}])
            my_trades_list = list(filter(lambda x: x.get(
                'time') >= start_time, my_trades_list))
            reality_pnl = 0

            for my_trade in my_trades_list:
                reality_pnl += float(my_trade.get('realizedPnl'))
        except:
            reality_pnl = 0
        reality_pnl = round(reality_pnl)
        notify_message += "\n""Reality PNL " + str(reality_pnl) + "USDT"
        notify_message += "\n""#####################"

    if notify_message != None:
        push_notify_message(LINE_NOTIFY_TOKEN, notify_message)


def schedule_backtest_month():
    db_markets = symbol_backtest_stat.aggregate(
        [{"$sort": {"win_rate_percentage": -1, "total_win": -1, "total_position": -1}}])
    markets = list(db_markets)

    summary_total = 0
    summary_success = 0
    orders_date_list = []

    count_30_days_success_position = 0
    count_30_days_fail_position = 0
    month_ago = exchange.parse8601(str(moment.utcnow().subtract(month=1).zero))

    for market in markets:
        try:
            total, success, _, orders_inform_list, _, _, _ = backtest_symbol(
                market.get('symbol'), BACK_TEST_LIMIT)
        except:
            total, success, orders_inform_list = 0, 0, []

        summary_total += total
        summary_success += success

        orders_date_list += list(
            map(lambda order_inform: order_inform.get("end_datetime"), orders_inform_list))
        if total > 0:
            for order_inform in orders_inform_list:
                st = order_inform.get("state")
                order_time = exchange.parse8601(
                    str(order_inform.get("end_datetime")) + "T00:00:00")

                if order_time > month_ago:
                    if st == "S":
                        count_30_days_success_position += 1
                    else:
                        count_30_days_fail_position += 1

    notify_message = None
    if summary_total > 0 and summary_success > 0:
        orders_date_list.sort()
        orders_date_list = list(map(lambda order_d: moment.utc(
            order_d).format("YYYY-MM-DD"), orders_date_list))

        notify_message = "\n""### Month Schedule Backtest ###"
        notify_message += "\n""Take Profit Percentage " + str(TP_PERCENTAGE)
        notify_message += "\n""Stop Loss Percentage " + str(SL_PERCENTAGE)

        try:
            summary_profit_month_ago = ((TP_PERCENTAGE * count_30_days_success_position) - (
                SL_PERCENTAGE * count_30_days_fail_position)) * LEVERAGE
            realized_pnl_month_ago = (
                summary_profit_month_ago / 100) * FUTURE_POSITION_SIZE
        except:
            summary_profit_month_ago = 0
            realized_pnl_month_ago = 0

        try:
            start_time = exchange.parse8601(
                str(orders_date_list[0]) + "T00:00:00")
            my_trades_list = my_trades.aggregate([{"$sort": {"datetime": -1}}])
            my_trades_list = list(filter(lambda x: x.get(
                'time') >= start_time, my_trades_list))
            reality_pnl_month_ago = 0

            for my_trade in my_trades_list:
                if my_trade.get('time') >= month_ago:
                    reality_pnl_month_ago += float(my_trade.get('realizedPnl'))
        except:
            reality_pnl_month_ago = 0

        notify_message += "\n""Success Signal(30 Days) " + \
            str(count_30_days_success_position)
        notify_message += "\n""Fault Signal(30 Days) " + \
            str(count_30_days_fail_position)
        notify_message += "\n""Summary Profit Pct.(30 Days) " + str(
            summary_profit_month_ago) + "%"
        notify_message += "\n""Realized PNL(30 Days) " + \
            str(realized_pnl_month_ago) + "USDT"
        reality_pnl_month_ago = round(reality_pnl_month_ago)
        notify_message += "\n""Reality PNL(30 Days) " + \
            str(reality_pnl_month_ago) + "USDT"

        notify_message += "\n""#####################"

    if notify_message != None:
        push_notify_message(LINE_NOTIFY_TOKEN, notify_message)


def schedule_backtest_week():
    db_markets = symbol_backtest_stat.aggregate(
        [{"$sort": {"win_rate_percentage": -1, "total_win": -1, "total_position": -1}}])
    markets = list(db_markets)

    summary_total = 0
    summary_success = 0
    orders_date_list = []

    count_7_days_success_position = 0
    count_7_days_fail_position = 0
    week_ago = exchange.parse8601(str(moment.utcnow().subtract(day=7).zero))

    for market in markets:
        try:
            total, success, _, orders_inform_list, _, _, _ = backtest_symbol(
                market.get('symbol'), BACK_TEST_LIMIT)
        except:
            total, success, orders_inform_list = 0, 0, []

        summary_total += total
        summary_success += success

        orders_date_list += list(
            map(lambda order_inform: order_inform.get("end_datetime"), orders_inform_list))
        if total > 0:
            for order_inform in orders_inform_list:
                st = order_inform.get("state")
                order_time = exchange.parse8601(
                    str(order_inform.get("end_datetime")) + "T00:00:00")

                if order_time > week_ago:
                    if st == "S":
                        count_7_days_success_position += 1
                    else:
                        count_7_days_fail_position += 1

    notify_message = None
    if summary_total > 0 and summary_success > 0:
        orders_date_list.sort()
        orders_date_list = list(map(lambda order_d: moment.utc(
            order_d).format("YYYY-MM-DD"), orders_date_list))

        notify_message = "\n""### Week Schedule Backtest ###"
        notify_message += "\n""Take Profit Percentage " + str(TP_PERCENTAGE)
        notify_message += "\n""Stop Loss Percentage " + str(SL_PERCENTAGE)

        try:
            summary_profit_week_ago = ((TP_PERCENTAGE * count_7_days_success_position) - (
                SL_PERCENTAGE * count_7_days_fail_position)) * LEVERAGE
            realized_pnl_week_ago = (
                summary_profit_week_ago / 100) * FUTURE_POSITION_SIZE
        except:
            summary_profit_week_ago = 0
            realized_pnl_week_ago = 0

        try:
            start_time = exchange.parse8601(
                str(orders_date_list[0]) + "T00:00:00")
            my_trades_list = my_trades.aggregate([{"$sort": {"datetime": -1}}])
            my_trades_list = list(filter(lambda x: x.get(
                'time') >= start_time, my_trades_list))
            reality_pnl_week_ago = 0

            for my_trade in my_trades_list:
                if my_trade.get('time') >= week_ago:
                    reality_pnl_week_ago += float(my_trade.get('realizedPnl'))
        except:
            reality_pnl_week_ago = 0

        notify_message += "\n""Success Signal(7 Days) " + \
            str(count_7_days_success_position)
        notify_message += "\n""Fault Signal(7 Days) " + \
            str(count_7_days_fail_position)
        notify_message += "\n""Summary Profit Pct.(7 Days) " + str(
            summary_profit_week_ago) + "%"
        notify_message += "\n""Realized PNL(7 Days) " + \
            str(realized_pnl_week_ago) + "USDT"
        reality_pnl_week_ago = round(reality_pnl_week_ago)
        notify_message += "\n""Reality PNL(7 Days) " + \
            str(reality_pnl_week_ago) + "USDT"

        notify_message += "\n""#####################"

    if notify_message != None:
        push_notify_message(LINE_NOTIFY_TOKEN, notify_message)


def schedule_backtest_daily():
    db_markets = symbol_backtest_stat.aggregate(
        [{"$sort": {"win_rate_percentage": -1, "total_win": -1, "total_position": -1}}])
    markets = list(db_markets)

    summary_total = 0
    summary_success = 0
    orders_date_list = []

    count_1_days_success_position = 0
    count_1_days_fail_position = 0
    daily_ago = exchange.parse8601(str(moment.utcnow().subtract(day=1).zero))

    for market in markets:
        try:
            total, success, _, orders_inform_list, _, _, _ = backtest_symbol(
                market.get('symbol'), BACK_TEST_LIMIT)
        except:
            total, success, orders_inform_list = 0, 0, []

        summary_total += total
        summary_success += success

        orders_date_list += list(
            map(lambda order_inform: order_inform.get("end_datetime"), orders_inform_list))
        if total > 0:
            for order_inform in orders_inform_list:
                st = order_inform.get("state")
                order_time = exchange.parse8601(
                    str(order_inform.get("end_datetime")) + "T00:00:00")

                if order_time > daily_ago:
                    if st == "S":
                        count_1_days_success_position += 1
                    else:
                        count_1_days_fail_position += 1

    notify_message = None
    if summary_total > 0 and summary_success > 0:
        orders_date_list.sort()
        orders_date_list = list(map(lambda order_d: moment.utc(
            order_d).format("YYYY-MM-DD"), orders_date_list))

        notify_message = "\n""### Daily Schedule Backtest ###"
        notify_message += "\n""Take Profit Percentage " + str(TP_PERCENTAGE)
        notify_message += "\n""Stop Loss Percentage " + str(SL_PERCENTAGE)

        try:
            summary_profit_daily_ago = ((TP_PERCENTAGE * count_1_days_success_position) - (
                SL_PERCENTAGE * count_1_days_fail_position)) * LEVERAGE
            realized_pnl_daily_ago = (
                summary_profit_daily_ago / 100) * FUTURE_POSITION_SIZE
        except:
            summary_profit_daily_ago = 0
            realized_pnl_daily_ago = 0

        try:
            start_time = exchange.parse8601(
                str(orders_date_list[0]) + "T00:00:00")
            my_trades_list = my_trades.aggregate([{"$sort": {"datetime": -1}}])
            my_trades_list = list(filter(lambda x: x.get(
                'time') >= start_time, my_trades_list))
            reality_pnl_daily_ago = 0

            for my_trade in my_trades_list:
                if my_trade.get('time') >= daily_ago:
                    reality_pnl_daily_ago += float(my_trade.get('realizedPnl'))
        except:
            reality_pnl_daily_ago = 0

        notify_message += "\n""Success Signal(1 Days) " + \
            str(count_1_days_success_position)
        notify_message += "\n""Fault Signal(1 Days) " + \
            str(count_1_days_fail_position)
        notify_message += "\n""Summary Profit Pct.(1 Days) " + str(
            summary_profit_daily_ago) + "%"
        notify_message += "\n""Realized PNL(1 Days) " + \
            str(realized_pnl_daily_ago) + "USDT"
        reality_pnl_daily_ago = round(reality_pnl_daily_ago)
        notify_message += "\n""Reality PNL(1 Days) " + \
            str(reality_pnl_daily_ago) + "USDT"

        notify_message += "\n""#####################"

    if notify_message != None:
        push_notify_message(LINE_NOTIFY_TOKEN, notify_message)


def position_backtest_symbol(symbol, notify):
    total, success, fail, orders_inform_list, avg_close_candle, current_order_position_date, current_order_position_number = backtest_symbol(
        symbol, BACK_TEST_LIMIT)

    count_success_position = 0
    count_fail_position = 0
    avg_success_candle = 0
    avg_fault_candle = 0
    win_rate = 0

    if current_order_position_date != None:
        current_order_position_date = moment.utc(
            current_order_position_date).format("YYYY-MM-DD HH:mm:ss")

    notify_message = None
    if total > 0:
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
                notify_message += "\n" + \
                    moment.utc(dt).format("YYYY-MM-DD HH:mm:ss") + \
                    " (" + str(cd) + ")" + "[" + st + "]"
                if st == "S":
                    count_success_position += 1
                    avg_success_candle += cd
                else:
                    count_fail_position += 1
                    avg_fault_candle += cd
            if avg_success_candle > 0:
                avg_success_candle = math.ceil(
                    avg_success_candle / count_success_position)
            if avg_fault_candle > 0:
                avg_fault_candle = math.ceil(
                    avg_fault_candle / count_fail_position)

        notify_message += "\n""Total Signal " + str(total)
        notify_message += "\n""Success Signal " + str(success)
        notify_message += "\n""Fault Signal " + str(fail)
        notify_message += "\n""Avg. Success Candle " + str(avg_success_candle)
        notify_message += "\n""Avg. Fault Candle " + str(avg_fault_candle)
        notify_message += "\n""Avg. Close Position Length " + \
            str(avg_close_candle)

        win_rate = (success / total) * 100
        notify_message += "\n""Win Rate " + str(win_rate) + "%"

        try:
            summary_profit = ((TP_PERCENTAGE * success) -
                              (SL_PERCENTAGE * fail)) * LEVERAGE
        except:
            summary_profit = 0
        notify_message += "\n""Summary Profit Percentage " + \
            str(summary_profit) + "%"

        notify_message += "\n""###########################"

    if notify_message != None and notify == True:
        push_notify_message(LINE_NOTIFY_TOKEN, notify_message)

    return total, success, fail, win_rate, avg_success_candle, avg_fault_candle, avg_close_candle, current_order_position_date, current_order_position_number


def backtest_symbol(symbol, back_test_limit):
    timeframe = TF_DURATION + TF_UNIT
    limit = back_test_limit

    df_ohlcv = get_df_ohlcv(exchange, symbol, timeframe, limit)

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
            s = find_signal_macd_updown_rf_sign(df_ohlcv_range)
            if s == "Buy_Signal" or s == "Sell_Signal":
                datetime = df_ohlcv['datetime'][index-1]
                end_datetime = df_ohlcv['datetime'][index-1]
                position_price = df_ohlcv['open'][index-1]
                count_candle_each_position = 1
                avg_close_candle += 1
                signal = s

                current_order_position_date = datetime
                current_order_position_number = 1

                last_candle_high = df_ohlcv['high'][index]
                last_candle_low = df_ohlcv['low'][index]
                if s == "Buy_Signal":
                    sl_price = (position_price * (1 - (SL_PERCENTAGE / 100)))
                    tp_price = (position_price * ((TP_PERCENTAGE / 100) + 1))
                    if last_candle_low <= sl_price:
                        fail_signal += 1
                        total_signal += 1
                        signal = None
                        print("Position at", datetime, "(" +
                              str(count_candle_each_position) + ")", "[F]")
                        orders_inform_list.append({
                            "datetime": datetime,
                            "end_datetime": end_datetime,
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
                        print("Position at", datetime, "(" +
                              str(count_candle_each_position) + ")", "[S]")
                        orders_inform_list.append({
                            "datetime": datetime,
                            "end_datetime": end_datetime,
                            "candle": count_candle_each_position,
                            "state": "S"
                        })
                        current_order_position_date = None
                        current_order_position_number = 0
                elif s == "Sell_Signal":
                    sl_price = (position_price * ((SL_PERCENTAGE / 100) + 1))
                    tp_price = (position_price * (1 - (TP_PERCENTAGE / 100)))
                    if last_candle_high >= sl_price:
                        fail_signal += 1
                        total_signal += 1
                        signal = None
                        count_has_position_symbol += 1
                        print("Position at", datetime, "(" +
                              str(count_candle_each_position) + ")", "[F]")
                        orders_inform_list.append({
                            "datetime": datetime,
                            "end_datetime": end_datetime,
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
                        print("Position at", datetime, "(" +
                              str(count_candle_each_position) + ")", "[S]")
                        orders_inform_list.append({
                            "datetime": datetime,
                            "end_datetime": end_datetime,
                            "candle": count_candle_each_position,
                            "state": "S"
                        })
                        current_order_position_date = None
                        current_order_position_number = 0

        elif signal != None:
            last_candle_high = df_ohlcv['high'][index]
            last_candle_low = df_ohlcv['low'][index]
            current_order_position_number += 1
            end_datetime = df_ohlcv['datetime'][index-1]

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
                    print("Position at", datetime,
                          "(" + str(count_candle_each_position) + ")", "[F]")
                    orders_inform_list.append({
                        "datetime": datetime,
                        "end_datetime": end_datetime,
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
                    print("Position at", datetime,
                          "(" + str(count_candle_each_position) + ")", "[S]")
                    orders_inform_list.append({
                        "datetime": datetime,
                        "end_datetime": end_datetime,
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
                    print("Position at", datetime,
                          "(" + str(count_candle_each_position) + ")", "[F]")
                    orders_inform_list.append({
                        "datetime": datetime,
                        "end_datetime": end_datetime,
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
                    print("Position at", datetime,
                          "(" + str(count_candle_each_position) + ")", "[S]")
                    orders_inform_list.append({
                        "datetime": datetime,
                        "end_datetime": end_datetime,
                        "candle": count_candle_each_position,
                        "state": "S"
                    })
                    current_order_position_date = None
                    current_order_position_number = 0

        index += 1

    try:
        avg_close_candle = avg_close_candle - current_order_position_number
        avg_close_candle = math.ceil(
            avg_close_candle/count_has_position_symbol)
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


def retreive_my_trades():
    markets = get_market_list(exchange, 'future', 'USDT')
    # markets = [{'symbol': 'BTC/USDT'}]

    all_trades = []
    for market in markets:
        print('------------------------------------------------------------------')
        print(market.get('symbol'))
        day = 24 * 60 * 60 * 1000
        # start_time = exchange.parse8601 ('2022-05-30T00:00:00')
        start_time = exchange.parse8601(
            str(moment.utcnow().subtract(day=1).zero))
        now = exchange.milliseconds()

        while start_time < now:

            print('Fetching trades from', exchange.iso8601(start_time))
            end_time = start_time + day

            trades = exchange.fetch_my_trades(market.get('symbol'), start_time, None, {
                'endTime': end_time,
            })
            if len(trades):
                last_trade = trades[len(trades) - 1]
                start_time = last_trade['timestamp'] + 1
                trades = list(map(lambda x: {
                    'id': x.get('id'),
                    'order': x.get('order'),
                    'symbol': market.get('symbol'),
                    'side': x.get('info').get('side'),
                    'price': x.get('price'),
                    'commission': x.get('info').get('commission'),
                    'realizedPnl': x.get('info').get('realizedPnl'),
                    'time': int(x.get('info').get('time')),
                    'datetime': moment.date(x.get('info').get('time')).timezone("Asia/Bangkok").format('YYYY-MM-DD hh:mm:ss')
                }, trades))
                all_trades = all_trades + trades
            else:
                start_time = end_time

    olds_data = my_trades.aggregate([{"$sort": {"datetime": -1}}])
    olds_data = list(
        sorted(olds_data, key=lambda x: (x['time']), reverse=True))

    if len(all_trades):
        try:
            all_trades = list(
                sorted(all_trades, key=lambda x: (x['time']), reverse=True))
            my_trades.drop()
            all_trades = all_trades + olds_data
            my_trades.insert_many(all_trades)
            print("Update My Trades")
        except:
            print("Insert My Trades Error")


if __name__ == "__main__":
    print("\n""####### Run Back Test #####")

    try:
        schedule_backtest()
    except (KeyboardInterrupt, SystemExit):
        pass
