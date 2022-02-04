import pandas as pd
import pandas_ta as ta
import pprint36 as pprint

def get_market_list(exchange):
    markets = exchange.fetch_markets()
    available_expiry_markets = list(filter(lambda market: market.get('expiry') == None and market.get('future') and market.get('info').get('quoteAsset') == "USDT", markets))
    df_markets = pd.DataFrame(available_expiry_markets, columns=["symbol"])
    raws_tickers = exchange.fetch_tickers() 
    tickers = []

    for market in df_markets.values:
        tickers.append(raws_tickers[market[0]].get('quoteVolume'))

    tickers = pd.DataFrame(tickers, columns=["volume"])
    df_markets = pd.concat([df_markets, tickers], axis=1) 
        
    sorted_markets = df_markets.sort_values(by="volume", ascending=False)
    
    return sorted_markets.to_dict('records')[0:100]

def set_pair_leverage(exchange, pair, leverage):
    exchange.set_leverage(leverage, pair)

def get_amount_from_quote(exchange, symbol, quote_amount):
    ticker = exchange.fetch_ticker(symbol)
    price = ticker.get('close')
    return quote_amount / price

def create_stop_loss_order(exchange, symbol, side, amount, stop_loss):
    quote_amount = get_amount_from_quote(exchange, symbol, amount)
    print("\n""####### Create Order ########")
    print("Symbol", symbol)
    print("Side", side)
    print("Amount", amount)
    print("Quota Amount", quote_amount)
    try:
        order = exchange.create_order(symbol, 'market', side, quote_amount)
        order_price = order['price']

        if order_price is None:
            order_price = order['average']
        if order_price is None:
            cumulative_quote = float(order['info']['cumQuote'])
            executed_quantity = float(order['info']['executedQty'])
            order_price = cumulative_quote / executed_quantity

        pprint.pprint(order)
        print('---------------------------')
    except:
        print("Balance insufficient")
        print('---------------------------')
    
    try:
        stop_loss_percentage = 0
        tp_percentage = 0

        if side == "buy":
            stop_loss_percentage = 1 - (stop_loss / 100)
            tp_percentage = 1 + ((stop_loss * 3) / 100)
            tp_sl_side = "sell"
        else:
            stop_loss_percentage = 1 + (stop_loss / 100)
            tp_percentage = 1 - ((stop_loss * 3) / 100)
            tp_sl_side = "buy"
        stop_loss_params = {'stopPrice': order_price * stop_loss_percentage} 
        stop_order = exchange.create_order(symbol, 'stop_market', tp_sl_side, quote_amount, None, stop_loss_params)

        pprint.pprint(stop_order)
        print('---------------------------')
    except:
        print("Stop Loss Error")
        print('---------------------------')

    try:
        tp_params = {'stopPrice': order_price * tp_percentage}
        tp_order = exchange.create_order(symbol, 'take_profit_market', tp_sl_side, quote_amount, None, tp_params)

        pprint.pprint(tp_order)
        print('---------------------------')
    except:
        print("Take Profit Error")
        print('---------------------------')

    print("\n""#######---------------########")
    
def cancel_unused_order(exchange, positions):
    print("\n""####### Cancel Orders #####")

    markets = get_market_list(exchange)

    positions_symbol = list(map(lambda position: position.get('symbol'), positions)) 
    markets_symbol = list(map(lambda market: market.get('symbol'), markets))
    exclude_symbol = list(filter(lambda sym: sym not in positions_symbol, markets_symbol))
    for sym in exclude_symbol:
        orders = exchange.fetch_orders(sym)
        if len(orders) > 0:
            print(sym)
            exchange.cancel_all_orders(sym)

    print("##########################")

