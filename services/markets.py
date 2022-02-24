import pandas as pd
import pandas_ta as ta
import pprint36 as pprint

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

    df_markets = pd.DataFrame(available_expiry_markets, columns=["symbol"])
    raws_tickers = exchange.fetch_tickers() 
    tickers = []

    for market in df_markets.values:
        tickers.append(raws_tickers[market[0]].get('quoteVolume'))

    tickers = pd.DataFrame(tickers, columns=["volume"])
    df_markets = pd.concat([df_markets, tickers], axis=1) 
        
    sorted_markets = df_markets.sort_values(by="volume", ascending=False)
    
    return sorted_markets.to_dict('records')[0:80]

def set_pair_leverage(exchange, pair, leverage):
    exchange.set_leverage(leverage, pair)

def get_amount_from_quote(exchange, symbol, position_size):
    ticker = exchange.fetch_ticker(symbol)
    price = ticker.get('close')
    return position_size / price

def create_stop_loss_order(exchange, symbol, side, position_size, stop_loss, tp, leverage):
    print("\n""####### Create Order ########")
    print("Symbol", symbol)
    print("Side", side)
    print("Position Size", position_size, "USDT")
    print("Leverage", leverage)

    leverage_position_size = position_size * leverage
    print("Leverage Position Size", leverage_position_size)

    quote_amount = get_amount_from_quote(exchange, symbol, leverage_position_size)
    print("Quota Amount", quote_amount, "Coin")

    try:
        order = exchange.create_order(symbol, 'market', side, quote_amount)
        order_price = order['price']

        if order_price is None:
            order_price = order['average']
        if order_price is None:
            cumulative_quote = float(order['info']['cumQuote'])
            executed_quantity = float(order['info']['executedQty'])
            order_price = cumulative_quote / executed_quantity

        print("Entry Price", order['price'])
    except:
        print("Balance insufficient")
    
    try:
        stop_loss_percentage = 0
        tp_percentage = 0

        if side == "buy":
            stop_loss_percentage = 1 - (stop_loss / 100)
            tp_percentage = 1 + (tp / 100)
            tp_sl_side = "sell"
        else:
            stop_loss_percentage = 1 + (stop_loss / 100)
            tp_percentage = 1 - (tp / 100)
            tp_sl_side = "buy"
        stop_loss_params = {'stopPrice': order_price * stop_loss_percentage} 
        stop_order = exchange.create_order(symbol, 'stop_market', tp_sl_side, quote_amount, None, stop_loss_params)

        print("Stop Loss Price", stop_order['stopPrice'])
    except:
        print("Stop Loss Error")

    try:
        tp_params = {'stopPrice': order_price * tp_percentage}
        tp_order = exchange.create_order(symbol, 'take_profit_market', tp_sl_side, quote_amount, None, tp_params)

        print("Take Profit Price", tp_order['stopPrice'])
    except:
        print("Take Profit Error")

    print("##########################")
    
def cancel_unused_order(exchange, positions, type, quote_asset):
    print("\n""####### Cancel Orders #####")

    markets = get_market_list(exchange, type, quote_asset)

    positions_symbol = list(map(lambda position: position.get('symbol'), positions)) 
    markets_symbol = list(map(lambda market: market.get('symbol'), markets))
    exclude_symbol = list(filter(lambda sym: sym not in positions_symbol, markets_symbol))
    for sym in exclude_symbol:
        orders = exchange.fetch_orders(sym)
        if len(orders) > 0:
            print("Cancel", sym)
            exchange.cancel_all_orders(sym)

    print("##########################")

def get_average_price_by_symbol(exchange, symbol):
    ticker = exchange.fetch_ticker(symbol)
    average_price = (ticker.get('ask') + ticker.get('bid')) / 2
    return average_price

def adjust_trailing_stop_position(exchange, positions, stop_loss_percentage):
    print("\n""####### Adjust Stop Positions #####")
    for position in positions:
        symbol = position.get('symbol')
        real_percentage = position.get('percentage') / int(position.get('info').get('leverage'))
        real_percentage_diff = real_percentage - stop_loss_percentage
        if real_percentage_diff > 0:
            position_amount = position.get('info').get('positionAmt')
            orders = exchange.fetch_orders(symbol)
            if len(orders) > 0:
                stop_loss_orders = list(filter(lambda order: order.get('type') == 'stop_market', orders)) 
                if len(stop_loss_orders) > 0:
                    entry_price = position.get('entryPrice')
                    if position.get('side') == 'long' or position.get('side') == 'buy':
                        side = 'buy'
                        sl_side = 'sell'
                        stop_loss_percentage = 1 + (real_percentage_diff / 100)
                    else:
                        side = 'sell'
                        sl_side = 'buy'
                        stop_loss_percentage = 1 - (real_percentage_diff / 100)

                    max_value_stop_loss = entry_price * stop_loss_percentage

                    for stop_loss_order in stop_loss_orders:
                        try:
                            exchange.cancel_order(stop_loss_order.get('id'), stop_loss_order.get('symbol'))
                            stop_price = stop_loss_order.get('stopPrice')
                        except:
                            stop_price = None
                            print(symbol, "Missing Order Number")

                        if stop_price is not None:
                            if side == 'buy':
                                if max_value_stop_loss < stop_price:
                                    max_value_stop_loss = stop_price
                            else:
                                if max_value_stop_loss > stop_price:
                                    max_value_stop_loss = stop_price

                    stop_loss_params = {'stopPrice': max_value_stop_loss} 
                    try:
                        stop_order = exchange.create_order(symbol, 'stop_market', sl_side, position_amount, None, stop_loss_params)
                        print(symbol, "Update Stop Price To", stop_order['stopPrice'], "Current Profit Percentage", real_percentage, "%")
                    except:
                        print(symbol, "Cant Create Stop Loss order")
            else:
                print(symbol, "No Positions")
        else:
            print(symbol, "Not Profit Positions")

    print("##########################")
