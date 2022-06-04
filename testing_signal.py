import ccxt
import settings as ENV
import moment
import pprint36 as pprint
from services.signal import get_df_ohlcv, find_signal_macd_updown_rf_sign, \
    find_ema_200_trend_st_macd_cross_sign, find_rf_sign, find_st_sign

API_READING_KEY = ENV.API_READING_KEY
SECRET_READING_KEY = ENV.SECRET_READING_KEY

exchange = ccxt.binanceusdm({
    'apiKey': API_READING_KEY, 
    'secret': SECRET_READING_KEY,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    }
})

def backtest_with_signal(df_ohlcv):
    strategy = 'st_signal'

    index = 600
    orders = []
    while index < len(df_ohlcv):
        locale_df = df_ohlcv[0:index]
        locale_count = len(locale_df)

        low = locale_df['low'][locale_count-2]
        high = locale_df['high'][locale_count-2]   
        close = locale_df['close'][locale_count-2]
        atr = locale_df['ATRr_14'][locale_count-2]

        datetime = locale_df['datetime'][locale_count-1]
        datetime = moment.date(datetime).timezone("Asia/Bangkok").format('YYYY-MM-DD HH:mm:ss')

        exit_signal = 'None-Signal'
        if strategy == 'rf_signal':
            exit_signal = find_rf_sign(locale_df)
        elif strategy == 'st_signal':
            exit_signal = find_st_sign(locale_df)

        last_order = None
        if len(orders) > 0:
            last_order = orders[len(orders) - 1]

        if last_order != None:
            if last_order.get('status') == None:
                if last_order.get('side') == "BUY":
                    if low <= last_order.get('stop_loss'):
                        orders[len(orders) - 1]['status'] = "LOSE"
                        orders[len(orders) - 1]['endtime'] = datetime
                        orders[len(orders) - 1]['endprice'] = last_order.get('stop_loss') 
                        pnl = ((100 * last_order.get('stop_loss')) / last_order.get('price')) - 100
                        orders[len(orders) - 1]['realizedPnl'] = pnl
                    elif exit_signal == "Sell_Signal":
                        pnl = ((100 * close) / last_order.get('price')) - 100
                        orders[len(orders) - 1]['realizedPnl'] = pnl
                        if pnl > 0:
                            orders[len(orders) - 1]['status'] = "WIN"
                            orders[len(orders) - 1]['endtime'] = datetime
                            orders[len(orders) - 1]['endprice'] = close 
                        else:
                            orders[len(orders) - 1]['status'] = "LOSE"
                            orders[len(orders) - 1]['endtime'] = datetime
                            orders[len(orders) - 1]['endprice'] = close 
                else:
                    if high >= last_order.get('stop_loss'):
                        orders[len(orders) - 1]['status'] = "LOSE"
                        orders[len(orders) - 1]['endtime'] = datetime
                        orders[len(orders) - 1]['endprice'] = last_order.get('stop_loss') 
                        pnl = 100 - ((100 * last_order.get('stop_loss')) / last_order.get('price'))
                        orders[len(orders) - 1]['realizedPnl'] = pnl
                    elif exit_signal == "Buy_Signal":
                        pnl = 100 - ((100 * close) / last_order.get('price'))
                        orders[len(orders) - 1]['realizedPnl'] = pnl
                        if pnl > 0:
                            orders[len(orders) - 1]['status'] = "WIN"
                            orders[len(orders) - 1]['endtime'] = datetime
                            orders[len(orders) - 1]['endprice'] = close 
                        else:
                            orders[len(orders) - 1]['status'] = "LOSE"
                            orders[len(orders) - 1]['endtime'] = datetime
                            orders[len(orders) - 1]['endprice'] = close 

        signal = None
        if strategy == 'rf_signal':
            signal = find_signal_macd_updown_rf_sign(locale_df)
        elif strategy == 'st_signal':
            signal = find_ema_200_trend_st_macd_cross_sign(locale_df)

        if signal != None:
            if len(orders) > 0:
                if orders[len(orders) - 1].get('status') == None:
                    signal = None

            if signal == "Buy_Signal":
                orders.append({ \
                    'datetime': datetime, \
                    'endtime': None, \
                    'status': None, \
                    'side': 'BUY', \
                    'price': close, \
                    'endprice': None, \
                    'stop_loss': low - atr, \
                    'realizedPnl': 0, \
                })
            elif signal == "Sell_Signal":
                orders.append({ \
                    'datetime': datetime, \
                    'endtime': None, \
                    'status': None, \
                    'side': 'SELL', \
                    'price': close, \
                    'endprice': None, \
                    'stop_loss': high + atr, \
                    'realizedPnl': 0, \
                })

        index += 1

    return orders

def backtest_symbol(symbol):
    timeframe = "30m"
    limit = 1500
    df_ohlcv = get_df_ohlcv(exchange, symbol, timeframe, limit)

    orders = backtest_with_signal(df_ohlcv)

    sum_realized = 0
    sum_win_count = 0
    sum_win_realized = 0
    sum_lose_count = 0
    sum_lose_realized = 0

    for order in orders:
        sum_realized += order.get('realizedPnl')

        if order.get('status') == "WIN":
            sum_win_count += 1
            sum_win_realized += order.get('realizedPnl')
        elif order.get('status') == "LOSE":
            sum_lose_count += 1
            sum_lose_realized += order.get('realizedPnl')
            
    return { \
        'symbol': symbol, \
        'sum_realized': sum_realized, \
        'sum_win_count': sum_win_count, \
        'sum_win_realized': sum_win_realized, \
        'sum_lose_count': sum_lose_count, \
        'sum_lose_realized': sum_lose_realized, \
        'orders': orders
    }


if __name__ == "__main__":
    try:
        symbols = ["BTC/USDT"]

        list_orders = []
        for symbol in symbols:
            orders = backtest_symbol(symbol)
            list_orders.append(orders)

        # list_orders = list(filter(lambda x: x.get('sum_realized') > 0, list_orders))
        for list_order in list_orders:
            orders = list_order.get('orders')
            print("###################", list_order.get('symbol'), "#######################")

            for order in orders:
                if order.get('side') == "BUY":
                    dep_side = "SELL"
                else:
                    dep_side = "BUY"
                print(order.get('side'), "price", order.get('price'), "at :", order.get('datetime'), \
                dep_side, "price", order.get('endprice'), "at :", order.get('endtime'), \
                ",", order.get('status'), ":", order.get('realizedPnl'))

            sum_realized = list_order.get('sum_realized')
            sum_win_count = list_order.get('sum_win_count')
            sum_win_realized = list_order.get('sum_win_realized')
            sum_lose_count = list_order.get('sum_lose_count')
            sum_lose_realized = list_order.get('sum_lose_realized')

            print("Summary", sum_realized)
            print("WIN :", sum_win_count, sum_win_realized)
            print("LOSE :", sum_lose_count, sum_lose_realized)

            print("##################################################")

        print("Total Symbols", len(symbols))
        print("Win Symbols", len(list_orders))
    except (KeyboardInterrupt, SystemExit):
        pass
