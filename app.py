from apscheduler.schedulers.blocking import BlockingScheduler
import ccxt
import time
import moment
import pprint36 as pprint
import settings as ENV
from services.signal import detect_signal_sign, find_signal_macd_rsi_sign
from services.wallet_information import get_position_size, get_usdt_balance_in_future_wallet, get_positions_list, get_unit_of_symbol 
from services.markets import get_market_list, set_pair_leverage, create_stop_loss_order, cancel_unused_order, get_average_price_by_symbol 

API_KEY = ENV.API_KEY
SECRET_KEY = ENV.SECRET_KEY
TF_DURATION = ENV.TF_DURATION
TF_UNIT = ENV.TF_UNIT
CANDLE_LIMIT = ENV.CANDLE_LIMIT
RISK_OF_RUIN = ENV.RISK_OF_RUIN
LEVERAGE = ENV.LEVERAGE
SL_PERCENTAGE = ENV.SL_PERCENTAGE
TP_PERCENTAGE = ENV.TP_PERCENTAGE
REBALANCING_COIN = ENV.REBALANCING_COIN
REBALANCING_FAIT_COIN = ENV.REBALANCING_FAIT_COIN
REBALANCING_PERCENTAGE = ENV.REBALANCING_PERCENTAGE

exchange = ccxt.binanceusdm({
    'apiKey': API_KEY, 
    'secret': SECRET_KEY,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    }
})

exchange_spot = ccxt.binance({
    'apiKey': API_KEY, 
    'secret': SECRET_KEY,
    'enableRateLimit': True,
})

def cancle_close_positions():
    positions = get_positions_list(exchange)
    cancel_unused_order(exchange, positions, 'future', 'USDT')

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
    print("RISK_OF_RUIN", risk_of_ruin)
    print("STOP LOSS PERCENTAGE", stop_loss_percentage)
    print("TAKE PROFIT PERCENTAGE", tp_percentage)
    print("######################")

    print("\n""######################")
    balance = get_usdt_balance_in_future_wallet(exchange) 
    print("Balance", balance)
    print("######################")

    print("\n""##########################")
    position_size = get_position_size(balance, risk_of_ruin, stop_loss_percentage, leverage)
    print("Position Size", position_size)
    print("##########################")

    print("\n""####### Current Positions List #####")
    positions = get_positions_list(exchange)
    positions_symbol = list(map(lambda position: position.get('symbol'), positions)) 
    pprint.pprint(positions_symbol)
    print("##########################")

    cancle_close_positions()

    markets = get_market_list(exchange, 'future', 'USDT')
    none_position_market = list(filter(lambda market: market.get('symbol') not in positions_symbol, markets))

    print("\n""####### Trade Status #####")
    for market in none_position_market:
        set_pair_leverage(exchange, market.get('symbol'), leverage)

        print("$$$$$$$$$$$$$$$$$$$$$$$$$$")
        print("Symbol", market.get('symbol'))
        # Signal = find_signal_ema_sign(exchange, market.get('symbol'), timeframe, limit)
        Signal = find_signal_macd_rsi_sign(exchange, market.get('symbol'), timeframe, limit)
        if Signal  == "Buy_Signal":
            print("BUY-Trade")
            create_stop_loss_order(exchange, market.get('symbol'), 'buy', position_size, stop_loss_percentage, tp_percentage)
          
        elif Signal  == "Sell_Signal":
            print("SELL-Trade")
            create_stop_loss_order(exchange, market.get('symbol'), 'sell', position_size, stop_loss_percentage, tp_percentage)
    
        else:
            print("Non-Trade")
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$")
    print("##########################")

    print("\n""####### Positions Stop Loss #####")
    for position in positions:
        detect_signal = detect_signal_sign(exchange, position.get('symbol'), timeframe, limit)
        if position.get('side') == "long" and detect_signal == "SELL_POSITION":
            print("Stop-Loss-Position-Long", position.get('symbol'))
            exchange.create_order(position.get('symbol'), 'market', 'sell', float(position.get('contracts')))
        elif position.get('side') == "short" and detect_signal == "BUY_POSITION":
            print("Stop-Loss-Position-Short", position.get('symbol'))
            exchange.create_order(position.get('symbol'), 'market', 'buy', float(position.get('contracts')))
        else:
            print("HOLD-Position", position.get('symbol'))
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

    rebalance_mark = fiat_unit
    rebalance_percentage = REBALANCING_PERCENTAGE

    side = None
    diff_value = 0
    if coin_value > (rebalance_mark + (rebalance_mark * rebalance_percentage / 100)):
        side = 'sell'
        diff_value = coin_value - rebalance_mark
    elif coin_value < (rebalance_mark - (rebalance_mark * rebalance_percentage / 100)):
        side = 'buy'
        diff_value = rebalance_mark - coin_value

    if side != None and fiat_unit > 0:
        print(side, pair_trade, 'Amount', (diff_value / average))
        exchange_spot.create_order(pair_trade, 'market', side, (diff_value/average))

    print("##########################")

def wake_up_job():
    print('Tick! The time is: %s', moment.utcnow().timezone("Asia/Bangkok").format("YYYY-MM-DD HH:mm:ss"))

if __name__ == "__main__":
    print("\n""####### Run Scheduler #####")
    scheduler = BlockingScheduler()
    duration = int(TF_DURATION)

    # PING Server Schedule
    scheduler.add_job(wake_up_job, 'cron', hour='*/1', minute='59', second='45', timezone="Africa/Abidjan")

    # Futures Trading Schedule
    scheduler.add_job(cancle_close_positions, 'cron', minute='*/15', second='0', timezone="Africa/Abidjan")
    scheduler.add_job(future_schedule_job, 'cron', hour='*/' + str(duration), minute='0', second='5', timezone="Africa/Abidjan")

    # Spots Rebalancing Schedule
    scheduler.add_job(rebalacing_pair_of_symbol, 'cron', day='*/1', hour='0', minute='0', second='0', timezone="Africa/Abidjan")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
