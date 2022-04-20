import ccxt
import settings as ENV
import pprint36 as pprint
import pandas as pd
import pandas_ta as ta
import moment
import math
import pymongo
from services.markets import get_market_list
from services.request import push_notify_message
from services.signal import range_filter_signal
from backtest import backtest_symbol 

API_READING_KEY = ENV.API_READING_KEY
SECRET_READING_KEY = ENV.SECRET_READING_KEY
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

def schedule_ranking():
    markets = get_market_list(exchange, 'future', 'USDT')
    markets = markets

    ranking_list = []

    for market in markets:
        total, success, fail, _, _ = backtest_symbol(market.get('symbol'), 1500)

        try:
            win_rate = (success / total) * 100
        except:
            win_rate = 0

        ranking_list.append({
            'symbol': market.get('symbol'),
            'precision': market.get('precision'),
            'total_position': total,
            'total_win': success,
            'total_lose': fail,
            'win_rate_percentage': win_rate
        })

    filter_none_win_out_list = filter(lambda x: x['win_rate_percentage'] > 30 and x['total_win'] > 0, ranking_list)
    order_ranking_list = sorted(filter_none_win_out_list, key = lambda x: (x['win_rate_percentage'], x['total_position']), reverse=True)

    try:
        symbol_backtest_stat.drop()
        symbol_backtest_stat.insert_many(order_ranking_list)
        print("Update Symbol Stat")
    except:
        print("Insert Stat Error")

if __name__ == "__main__":
    print("\n""####### Run Ranking Symbol #######")

    try:
        schedule_ranking() 
        pass
    except (KeyboardInterrupt, SystemExit):
        pass
