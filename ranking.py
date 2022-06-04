import ccxt
import settings as ENV
import pymongo
from services.markets import get_market_list
from services.request import push_notify_message
from backtest import backtest_symbol 

API_READING_KEY = ENV.API_READING_KEY
SECRET_READING_KEY = ENV.SECRET_READING_KEY
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

def schedule_ranking():
    markets = get_market_list(exchange, 'future', 'USDT')
    db_markets = symbol_backtest_stat.aggregate([{ "$sort": {  "win_rate_percentage": -1, "total_win": -1, "total_position": -1  } }])
    markets = markets

    ranking_list = []

    for market in markets:
        total, success, fail, _, _, _, _ = backtest_symbol(market.get('symbol'), 1500)

        try:
            win_rate = (success / total) * 100
        except:
            win_rate = 0

        ranking_list.append({
            'number': 0,
            'symbol': market.get('symbol'),
            'precision': market.get('precision'),
            'total_position': total,
            'total_win': success,
            'total_lose': fail,
            'win_rate_percentage': win_rate
        })

    filter_none_win_out_list = filter(lambda x: x['win_rate_percentage'] > 35 and x['total_position'] > 1, ranking_list)
    order_ranking_list = sorted(filter_none_win_out_list, key = lambda x: (x['win_rate_percentage'], x['total_position']), reverse=True)

    notify_message = "\n""### Current Market Ranking ###"
    i = 0
    for symbol in order_ranking_list:
        symbol['number'] = i + 1

        previous_symbol = list(filter(lambda x: x['symbol'] == symbol['symbol'], db_markets)) 
        diff_symbol = ""
        diff_number = "-"
        if len(previous_symbol) > 0:
            try:
                previous_number = previous_symbol[0]["number"]
            except:
                previous_number = 0

            if previous_number > 0:
                diff_number = previous_number - symbol['number']
                if diff_number < 0:
                    diff_symbol = "⬇︎" 
                if diff_number > 0:
                    diff_symbol = "⬆︎"

        notify_message += "\nNo. " + str(symbol["number"]) + "(" + diff_symbol + str(diff_number) + ") " + symbol["symbol"]

        if (i + 1) % 20 == 0:
            if notify_message != None:
                push_notify_message(LINE_NOTIFY_TOKEN, notify_message)
                notify_message = ""

        i += 1

    if notify_message != None:
        push_notify_message(LINE_NOTIFY_TOKEN, notify_message)

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
