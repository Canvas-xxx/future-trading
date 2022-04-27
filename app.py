from apscheduler.schedulers.blocking import BlockingScheduler
import ccxt
import time
import moment
import pprint36 as pprint
import re
from pymongo import MongoClient 
import settings as ENV
from binance.futures import Futures as Client
from services.signal import detect_signal_sign, find_signal_macd_4c_sign
from services.wallet_information import get_position_size, get_usdt_balance_in_future_wallet, get_positions_list, get_unit_of_symbol 
from services.markets import get_market_list, set_pair_leverage, create_stop_loss_order, cancel_unused_order, get_average_price_by_symbol 
from services.request import push_notify_message
from backtest import schedule_backtest, position_backtest_symbol 
from ranking import schedule_ranking

API_KEY = ENV.API_KEY
SECRET_KEY = ENV.SECRET_KEY
API_READING_KEY = ENV.API_READING_KEY
SECRET_READING_KEY = ENV.SECRET_READING_KEY
TF_DURATION = ENV.TF_DURATION
TF_UNIT = ENV.TF_UNIT
CANDLE_LIMIT = ENV.CANDLE_LIMIT
RISK_OF_RUIN = ENV.RISK_OF_RUIN
LEVERAGE = ENV.LEVERAGE
SL_PERCENTAGE = ENV.SL_PERCENTAGE
TP_PERCENTAGE = ENV.TP_PERCENTAGE
FUTURE_POSITION_SIZE = ENV.FUTURE_POSITION_SIZE
REBALANCING_COIN = ENV.REBALANCING_COIN
REBALANCING_FAIT_COIN = ENV.REBALANCING_FAIT_COIN
REBALANCING_PERCENTAGE = ENV.REBALANCING_PERCENTAGE
LINE_NOTIFY_TOKEN = ENV.LINE_NOTIFY_TOKEN
# LIMIT_SYMBOLS = ENV.LIMIT_SYMBOLS
FIXIE_URL = ENV.FIXIE_URL
DATABASE_URL = ENV.DATABASE_URL

exchange = ccxt.binanceusdm({
    'apiKey': API_READING_KEY, 
    'secret': SECRET_READING_KEY,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    }
})

exchange_spot = ccxt.binance({
    'apiKey': API_READING_KEY, 
    'secret': SECRET_READING_KEY,
    'enableRateLimit': True
})

client = Client(API_KEY, SECRET_KEY, base_url="https://fapi.binance.com", proxies= {'http': FIXIE_URL, 'https': FIXIE_URL})

client_db = MongoClient(DATABASE_URL)
symbol_backtest_stat = client_db.binance.symbol_backtest_stat

def clearance_close_positions():
    print("############ Cancle Position Schedule(", moment.utcnow().timezone("Asia/Bangkok").format("YYYY-MM-DD HH:mm:ss"), ") ############")
    positions = get_positions_list(exchange, 'USDT')
    cancel_unused_order(exchange, client, positions, 'future', 'USDT')

def backtest_current_positions():
    positions = get_positions_list(exchange, 'USDT')
    notify_list = []
    for position in positions:
        try:
            symbol = position.get('symbol')
            total, _, _, win_rate, avg_success_candle, avg_fault_candle, avg_close_candle, current_order_position_date, current_order_position_number = position_backtest_symbol(symbol, False)
        except:
            total, win_rate, avg_success_candle, avg_fault_candle, avg_close_candle, current_order_position_date, current_order_position_number = 0, 0, 0, 0, 0, None, 0

        notify_list.append({
            'symbol': position.get('symbol'),
            'total': total,
            'win_rate': win_rate,
            'avg_success_candle': avg_success_candle,
            'avg_fault_candle': avg_fault_candle,
            'avg_close_candle': avg_close_candle,
            'current_order_position_date': current_order_position_date,
            'current_order_position_number': current_order_position_number
        })

    if len(notify_list) > 0:
        notify_message = "\n""### Current Position Backtest ###"
        notify_message += "\n""No. of Current Position " + str(len(positions))
        index = 0
        for pos in notify_list:
            notify_message += "\n""Symbol " + str(pos.get('symbol'))
            notify_message += "\n""Totals " + str(pos.get('total'))
            notify_message += "\n""Win Rate " + str(round(float(pos.get('win_rate')), 2)) + "%"
            notify_message += "\n""Avg. Success Candle " + str(pos.get('avg_success_candle'))
            notify_message += "\n""Avg. Fault Candle " + str(pos.get('avg_fault_candle'))
            notify_message += "\n""Avg. Close Candle " + str(pos.get('avg_close_candle'))
            notify_message += "\n""Current Position " + str(pos.get('current_order_position_date')) + ", " + str(pos.get('current_order_position_number'))
            notify_message += "\n""------"
            index += 1
            if (index % 5) == 0:
                push_notify_message(LINE_NOTIFY_TOKEN, notify_message)
                notify_message = ""

        if len(notify_message) > 0:
            push_notify_message(LINE_NOTIFY_TOKEN, notify_message)

def future_schedule_job():
    print("############ Schedule(",moment.utcnow().timezone("Asia/Bangkok").format("YYYY-MM-DD HH:mm:ss"),") ############")
    utc = moment.utcnow().zero.date
    now = moment.utcnow().format("HH-mm")
    now_hh = int(now.split('-')[0])
    now_mm = int(now.split('-')[1])
    
    times = 0
    duration = int(TF_DURATION)
    circle = round(24/duration)
    not_yet = True
    
    while not_yet:
        t = moment.date(utc).add(hour=(times*duration)).format("HH-mm")
        t_hh = int(t.split('-')[0])
        
        if now_hh == t_hh and now_mm < 2:
            run_ordinary_future_task()
            not_yet = False
        else:
            times = times + 1
            if times >= circle:
                not_yet = False

    print("\n""############ End Schedule ############")

def run_ordinary_future_task():
    timeframe = TF_DURATION + TF_UNIT
    limit = CANDLE_LIMIT
    leverage = LEVERAGE
    risk_of_ruin = RISK_OF_RUIN
    stop_loss_percentage = SL_PERCENTAGE
    tp_percentage = TP_PERCENTAGE
    print("\n""######## Configuration ##########")
    print("TIMEFRAME", timeframe)
    print("CANDLE_LIMIT", limit)
    print("LEVERAGE", leverage)
    print("STOP LOSS PERCENTAGE", stop_loss_percentage)
    print("TAKE PROFIT PERCENTAGE", tp_percentage)

    print("\n""######################")
    balance = get_usdt_balance_in_future_wallet(exchange) 
    print("Balance", balance)

    try:
        position_size = FUTURE_POSITION_SIZE
        if FUTURE_POSITION_SIZE == 0:
            position_size = get_position_size(balance, risk_of_ruin, stop_loss_percentage, leverage)
    except:
        position_size = get_position_size(balance, risk_of_ruin, stop_loss_percentage, leverage)
    print("Position Size", position_size)

    print("\n""##########################")

    print("\n""####### Current Positions List #####")
    positions = get_positions_list(exchange, 'USDT')
    positions_symbol = list(map(lambda position: position.get('symbol'), positions)) 
    pprint.pprint(positions_symbol)
    print("##########################")

    db_markets = symbol_backtest_stat.aggregate([{ "$sort": {  "win_rate_percentage": -1, "total_win": -1, "total_position": -1  } }])
    markets = list(db_markets)
    # markets = get_market_list(exchange, 'future', 'USDT')
    none_position_market = list(filter(lambda market: market.get('symbol') not in positions_symbol, markets))

    print("\n""####### Trade Status #####")
    index = 1
    for market in none_position_market:
        print("---------------------------------")
        set_pair_leverage(client, market.get('symbol'), leverage)

        # if index > LIMIT_SYMBOLS:
        #     return

        print("Symbol", index, market.get('symbol'))
        Signal = find_signal_macd_4c_sign(exchange, market.get('symbol'), timeframe, limit)
        message = None

        if Signal  == "Buy_Signal":
            print("BUY-Trade")
            message = create_stop_loss_order(exchange, client, market.get('symbol'), market.get('precision'), 'BUY', position_size, stop_loss_percentage, tp_percentage, LEVERAGE)
          
        elif Signal  == "Sell_Signal":
            print("SELL-Trade")
            message = create_stop_loss_order(exchange, client, market.get('symbol'), market.get('precision'), 'SELL', position_size, stop_loss_percentage, tp_percentage, LEVERAGE)
    
        else:
            print("Non-Trade")

        index = index + 1
        if message != None:
            push_notify_message(LINE_NOTIFY_TOKEN, message)
        print("---------------------------------")

    print("##########################")

def rebalacing_pair_of_symbol():
    print("\n""######## Rebalancing Schedule ##########")
    print("REBALANCING_COIN", REBALANCING_COIN)
    print("REBALANCING_FAIT_COIN", REBALANCING_FAIT_COIN)
    print("REBALANCING_PERCENTAGE", REBALANCING_PERCENTAGE)

    coin = REBALANCING_COIN
    fiat = REBALANCING_FAIT_COIN
    pair_trade = coin + '/' + fiat
    coin_unit, fiat_unit = get_unit_of_symbol(exchange_spot, coin, fiat)
    average = get_average_price_by_symbol(exchange_spot, pair_trade)
    coin_value = coin_unit * average

    print("Coin Unit", coin_unit)
    print("Fiat Unit", fiat_unit)
    print("Coin Value", coin_value)

    rebalance_mark = fiat_unit
    rebalance_percentage = REBALANCING_PERCENTAGE

    side = None
    diff_value = 0
    rebalance_mark_sell = rebalance_mark + (rebalance_mark * rebalance_percentage / 100)
    rebalance_mark_buy = rebalance_mark - (rebalance_mark * rebalance_percentage / 100)
    print("Rebalance Mark Sell", rebalance_mark_sell)
    print("Rebalance Mark Buy", rebalance_mark_buy)

    if coin_value > rebalance_mark_sell:
        side = 'sell'
        diff_value = coin_value - rebalance_mark
        diff_value = diff_value / 2
    elif coin_value < rebalance_mark_buy:
        side = 'buy'
        diff_value = rebalance_mark - coin_value
        diff_value = diff_value / 2


    if side != None and fiat_unit > 0:
        print(side, pair_trade, 'Amount', (diff_value / average))
        message = "\n""### Rebalancing Trigger ###" 
        message += "\n""Symbol " + pair_trade
        message += "\n""Coin Unit " + str(coin_unit)
        message += "\n""Fiat Unit " + str(fiat_unit)
        message += "\n""Coin Value " + str(coin_value)
        message += "\n""Rebalance Mark Sell " + str(rebalance_mark_sell)
        message += "\n""Rebalance Mark Buy " + str(rebalance_mark_buy) 

        try:
            exchange_spot.create_order(pair_trade, 'market', side, (diff_value/average))
            message += "\n" + str(side).upper() + " at " + str(average) + " for " + str(diff_value/average)
        except:
            print("Coin Less Than Min Limitation")
            message += "\n""Coin Less Than Min Limitation"

        message += "\n""#######################" 
        push_notify_message(LINE_NOTIFY_TOKEN, message)

    print("##########################")

if __name__ == "__main__":
    print("\n""####### Run Scheduler #####")
    scheduler = BlockingScheduler()
    duration = int(TF_DURATION)

    # Quater Backtest Stat Schedule
    scheduler.add_job(schedule_ranking, 'cron', day_of_week="6", hour='7', minute='10', second='0', timezone="Africa/Abidjan")

    # Backtest Futures Signal
    scheduler.add_job(schedule_backtest, 'cron', day='*/1', hour='0', minute='5', second='0', timezone="Africa/Abidjan")
    scheduler.add_job(backtest_current_positions, 'cron', hour='*/1', minute='5', second='0', timezone="Africa/Abidjan")

    # Futures Trading Schedule
    scheduler.add_job(future_schedule_job, 'cron', hour='*/' + str(duration), minute='0', second='0', timezone="Africa/Abidjan")
    scheduler.add_job(clearance_close_positions, 'cron', hour='*/1', minute='45', second='0', timezone="Africa/Abidjan")

    # Spots Rebalancing Schedule
    # scheduler.add_job(rebalacing_pair_of_symbol, 'cron', minute='*/30', second='0', timezone="Africa/Abidjan")

    print("Scheduler Jobs No.", len(scheduler.get_jobs()))

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
