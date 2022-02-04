from apscheduler.schedulers.blocking import BlockingScheduler
import ccxt
import time
import moment
import pprint36 as pprint
import settings as ENV
from services.signal import detect_signal_sign, find_signal_macd_rsi_sign
from services.wallet_information import get_position_size, get_usdt_balance, get_positions_list
from services.markets import get_market_list, set_pair_leverage, create_stop_loss_order, cancel_unused_order

API_KEY = ENV.API_KEY
SECRET_KEY = ENV.SECRET_KEY
TF_DURATION = ENV.TF_DURATION
TF_UNIT = ENV.TF_UNIT
CANDLE_LIMIT = ENV.CANDLE_LIMIT
RISK_OF_RUIN = ENV.RISK_OF_RUIN
LEVERAGE = ENV.LEVERAGE
SL_PERCENTAGE = ENV.SL_PERCENTAGE
TP_PERCENTAGE = ENV.TP_PERCENTAGE

exchange = ccxt.binanceusdm({
    'apiKey': API_KEY, 
    'secret': SECRET_KEY,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    }
})

def schedule_job():
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
            run_ordinary_task()
            not_yet = False
        else:
            times = times + 1
            if times >= circle:
                not_yet = False

    positions = get_positions_list(exchange)
    cancel_unused_order(exchange, positions)
    print("\n""############ End Schedule ############")

def run_ordinary_task():
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
    balance = get_usdt_balance(exchange) 
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

    markets = get_market_list(exchange)
    none_position_market = list(filter(lambda market: market.get('symbol') not in positions_symbol, markets))

    print("\n""####### Trade Status #####")
    for market in none_position_market:
        # Signal = find_signal_ema_sign(exchange, market.get('symbol'), timeframe, limit)
        Signal = find_signal_macd_rsi_sign(exchange, market.get('symbol'), timeframe, limit)

        set_pair_leverage(exchange, market.get('symbol'), leverage)
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$")
        print("Symbol", market.get('symbol'))
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

def wake_up_job():
    print('Tick! The time is: %s', moment.utcnow().timezone("Asia/Bangkok").format("YYYY-MM-DD HH:mm:ss"))

if __name__ == "__main__":
    print("\n""####### Run Scheduler #####")
    scheduler = BlockingScheduler()
    duration = int(TF_DURATION)
    wake_up_duration = 0
    if duration > 1:
        wake_up_duration = duration - 1
    else:
        wake_up_duration = duration
    scheduler.add_job(wake_up_job, 'cron', hour='*/' + str(wake_up_duration), minute='59', second='45', timezone="Africa/Abidjan")
    scheduler.add_job(schedule_job, 'cron', hour='*/' + str(duration), minute='0', second='5', timezone="Africa/Abidjan")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
