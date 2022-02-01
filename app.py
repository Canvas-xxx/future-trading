import ccxt
import time
import moment
import pprint36 as pprint
import settings as ENV
from signal import detect_signal_sign, find_signal_sign
from wallet_information import get_position_size, get_usdt_balance, get_positions_list
from markets import get_market_list, set_pair_leverage, create_stop_loss_order, cancel_unused_order

API_KEY = ENV.API_KEY
SECRET_KEY = ENV.SECRET_KEY

exchange = ccxt.binanceusdm({
    'apiKey': API_KEY, 
    'secret': SECRET_KEY,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    }
})

# กำหนดตัวแปร ที่ต้องใช้
timeframe = "4h" # ช่วงเวลาของกราฟที่จะดึงข้อมูล 1m 5m 1h 4h 1d
limit = 100 # ให้ดึงข้อมูลมากี่แถว ย้อนหลังกี่แทง
leverage = 3
risk_of_ruin = 2
stop_loss_percentage = 2

def run_ordinary_task():
    balance = get_usdt_balance(exchange) 
    print("\n""####### Balance #####")
    pprint.pprint(balance)
    print("\n""##########################")

    position_size = get_position_size(balance, risk_of_ruin, stop_loss_percentage, leverage)
    print("\n""####### Position Size #####")
    print(position_size)
    print("\n""##########################")

    positions = get_positions_list(exchange)
    print("\n""####### Positions List #####")
    positions_symbol = list(map(lambda position: position.get('symbol'), positions)) 
    pprint.pprint(positions_symbol)
    print("\n""##########################")

    markets = get_market_list(exchange)
    none_position_market = list(filter(lambda market: market.get('symbol') not in positions_symbol, markets))

    print("\n""####### Trade Status #####")
    for market in none_position_market:
        Trend, Signal = find_signal_sign(exchange, market.get('symbol'), timeframe, limit)

        set_pair_leverage(exchange, market.get('symbol'), leverage)
        print("\n""Symbol", market.get('symbol'))
        print("\n", Trend)
        if Signal  == "Buy_Signal":
            print("BUY-Trade")
            create_stop_loss_order(exchange, market.get('symbol'), 'buy', position_size, stop_loss_percentage)
          
        elif Signal  == "Sell_Signal":
            print("SELL-Trade")
            create_stop_loss_order(exchange, market.get('symbol'), 'sell', position_size, stop_loss_percentage)
    
        else:
            print("Non-Trade")
    print("\n""##########################")

    print("\n""####### Positions Stop Loss #####")
    for position in positions:
        detect_signal = detect_signal_sign(exchange, position.get('symbol'), timeframe, limit)
        if position.get('side') == "long" and detect_signal == "SELL_POSITION":
            print("Stop-Loss-Position-Long")
            exchange.create_order(position.get('symbol'), 'market', 'sell', position.get('contracts'))
        elif position.get('side') == "short" and detect_signal == "BUY_POSITION":
            print("Stop-Loss-Position-Short")
            exchange.create_order(position.get('symbol'), 'market', 'buy', position.get('contracts'))
        else:
            print("HOLD-Position", position.get('symbol'))
    print("\n""##########################")


    print("\n""####### Cancel Orders #####")
    new_positions = get_positions_list(exchange)
    new_positions_symbol = list(map(lambda position: position.get('symbol'), new_positions)) 
    pprint.pprint(new_positions_symbol)
    for position in positions_symbol:
        if position not in new_positions_symbol:
            cancel_unused_order(exchange, position)
    print("\n""##########################")

if __name__ == "__main__":
    print("############ Schedule ############")
    utc = moment.utcnow().zero.date
    now = moment.utcnow().format("HH-mm")
    now_hh = int(now.split('-')[0])
    now_mm = int(now.split('-')[1])
    
    times = 0
    circle = 6
    not_yet = True
    
    while not_yet:
        t = moment.date(utc).add(hour=(times*4)).format("HH-mm")
        t_hh = int(t.split('-')[0])
        t_mm = int(t.split('-')[1])
        
        if now_hh == t_hh and now_mm < 1:
            run_ordinary_task()
            not_yet = False
        else:
            times = times + 1
            if times >= circle:
                not_yet = False
    print("\n""############ End Schedule ############")


# while True: 
#     print("############ Looping ############")
#     utc = moment.utcnow().zero.date
#     now = moment.utcnow().format("HH-mm")
#     now_hh = int(now.split('-')[0])
#     now_mm = int(now.split('-')[1])
    
#     times = 0
#     circle = 6
#     not_yet = True
    
#     while not_yet:
#         t = moment.date(utc).add(hour=(times*4)).format("HH-mm")
#         t_hh = int(t.split('-')[0])
#         t_mm = int(t.split('-')[1])
        
#         if now_hh == t_hh and now_mm < 1:
#             run_ordinary_task()
#             not_yet = False
#         else:
#             times = times + 1
#             if times >= circle:
#                 not_yet = False
    
#     sleep = 60
#     print("\n""Sleep",sleep,"sec.")
#     time.sleep(sleep) # Delay for 1 minute (60 seconds).
#     print("\n""############ End Looping ############")
