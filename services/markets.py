import pandas as pd
import pandas_ta as ta
import pprint36 as pprint
import math
import re

def get_market_list(exchange, type, quote_asset):
    markets = exchange.fetch_markets()
    if type == 'future':
        available_expiry_markets = list(
            filter(
                lambda market: market.get('expiry') == None and market.get('future') and market.get('info').get('quoteAsset') == quote_asset, markets
            )
        )
    elif type == 'spot':
        available_expiry_markets = list(
            filter(
                lambda market: market.get('expiry') == None and market.get('spot') and market.get('info').get('quoteAsset') == quote_asset, markets
            )
        )
    else:
        available_expiry_markets = list(filter(lambda market: market.get('expiry') == None, markets))

    df_markets = pd.DataFrame(available_expiry_markets, columns=["symbol", "precision"])
    raws_tickers = exchange.fetch_tickers() 
    tickers = []

    for market in df_markets.values:
        try:
            tickers.append(raws_tickers[market[0]].get('quoteVolume'))
        except:
            print("No market quoteVolume")

    tickers = pd.DataFrame(tickers, columns=["volume"])
    df_markets = pd.concat([df_markets, tickers], axis=1) 
        
    sorted_markets = df_markets.sort_values(by="volume", ascending=False)
    
    return sorted_markets.to_dict('records')

def set_pair_leverage(binance, pair, leverage):
    try:
        binance.change_leverage(symbol=re.sub('/', '', pair), leverage = leverage)
    except Exception as e:
        print("Leverage Error", e)

    try:
        binance.change_margin_type(symbol=re.sub('/', '', pair), marginType="ISOLATED")
    except Exception as e:
        print("Margin Type Error", e)

def get_amount_from_quote(exchange, symbol, position_size):
    ticker = exchange.fetch_ticker(symbol)
    price = ticker.get('close')
    return position_size / price

def create_stop_loss_order(exchange, binance, symbol, precision, side, position_size, stop_loss, tp, leverage):
    print("\n""####### Create Order ########")
    print("Symbol", symbol)
    print("Side", side)
    print("Position Size", position_size, "USDT")
    print("Leverage", leverage)

    notify_message = "\n""### Create Order ####"
    notify_message += "\n" + str(side).upper() + " " + symbol
    notify_message += "\n""Position Size " + str(position_size) + "USDT"

    leverage_position_size = position_size * leverage
    print("Leverage Position Size", leverage_position_size)

    quote_amount = get_amount_from_quote(exchange, symbol, leverage_position_size)
    quote_amount = float(round(quote_amount, precision['amount']))
    print("Quota Amount", quote_amount, "Coin")

    try:
        order = binance.new_order(symbol=re.sub('/', '', symbol), side = side, type= "MARKET", quantity= quote_amount, newOrderRespType="RESULT")
        order_price = order['price']

        if order_price is not None:
            order_price = float(order_price)

        if order_price is None or order_price == 0:
            order_price = float(order['avgPrice'])
        if order_price is None or order_price == 0:
            cumulative_quote = float(order['info']['cumQuote'])
            executed_quantity = float(order['info']['executedQty'])
            order_price = float(cumulative_quote / executed_quantity)

        print("Entry Price", order_price)
        notify_message += "\n""Entry Price " + str(order_price)
    except:
        print("Balance insufficient")
        notify_message += "\n""Balance insufficient"
        return notify_message
    
    try:
        stop_loss_percentage = 0
        tp_percentage = 0

        if side == "BUY":
            stop_loss_percentage = 1 - (stop_loss / 100)
            tp_percentage = 1 + (tp / 100)
            tp_sl_side = "SELL"
        else:
            stop_loss_percentage = 1 + (stop_loss / 100)
            tp_percentage = 1 - (tp / 100)
            tp_sl_side = "BUY"

        stop_price = round((order_price * stop_loss_percentage), precision['price']) 
        binance.new_order(symbol=re.sub('/', '', symbol), side=tp_sl_side, type= "STOP_MARKET", quantity= quote_amount, stopPrice=stop_price)

        print("Stop Loss Price", stop_price)
        notify_message += "\n""Stop Loss Price " + str(stop_price)
    except:
        print("Stop Loss Error")
        notify_message += "\n""Stop Loss Error"

    try:
        tp_price = round((order_price * tp_percentage), precision['price']) 
        binance.new_order(symbol=re.sub('/', '', symbol), side=tp_sl_side, type= "TAKE_PROFIT_MARKET", quantity= quote_amount, stopPrice=tp_price)

        print("Take Profit Price", tp_price)
        notify_message += "\n""Take Profit Price " + str(tp_price)
    except:
        print("Take Profit Error")
        notify_message += "\n""Take Profit Error"

    print("##########################")
    notify_message += "\n""#####################"
    return notify_message
    
def cancel_unused_order(exchange, binance, positions, type, quote_asset):
    print("\n""####### Cancel Orders #####")

    markets = get_market_list(exchange, type, quote_asset)

    positions_symbol = list(map(lambda position: position.get('symbol'), positions)) 
    markets_symbol = list(map(lambda market: market.get('symbol'), markets))
    exclude_symbol = list(filter(lambda sym: sym not in positions_symbol, markets_symbol))
    for sym in exclude_symbol:
        try:
            orders = exchange.fetch_orders(sym)
            for order in orders:
                if order.get('type') == 'take_profit_market' or order.get('type') == 'stop_market':
                    try:
                        binance.cancel_order(symbol= re.sub('/', '', order.get('symbol')), orderId=order.get('id'))
                        print("Cancel", sym)
                    except:
                        print(sym, "Missing Order Number")
        except Exception as e:
            print(e)
    print("##########################")

def get_average_price_by_symbol(exchange, symbol):
    ticker = exchange.fetch_ticker(symbol)
    average_price = (ticker.get('ask') + ticker.get('bid')) / 2
    return average_price
