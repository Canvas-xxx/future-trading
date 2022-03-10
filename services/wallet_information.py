import re

def get_position_size(balance, risk_of_ruin, stop_loss, leverage):
    return balance * risk_of_ruin / stop_loss / leverage

def get_usdt_balance_in_future_wallet(exchange):
    balance = exchange.fetch_balance()
    total_balance = balance.get('info').get('totalWalletBalance') 
    return float(total_balance) 

def get_positions_list(exchange, fiat):
    try:
        balance = exchange.fetch_balance()
        positions = balance['info']['positions']
        filtered_positions = list(filter(lambda x: float(x.get('entryPrice')) != 0, positions))
        filtered_positions = list(map(lambda x: { \
            'symbol': replace_symbol(x.get('symbol'), fiat), \
            'contracts': replace_position_amount(x.get('positionAmt')) \
        }, filtered_positions))
        return filtered_positions
    except:
        return []

def replace_symbol(symbol, fiat):
    return re.sub('\/?(' + fiat + ')$', '/' + fiat, symbol)

def replace_position_amount(amount):
    amt = float(amount)
    if amt >= 0:
        return amt
    else:
        return amt * -1

def get_unit_of_symbol(exchange, coin, fiat):
    balance = exchange.fetch_balance()
    total_coin = balance.get(coin).get('total')
    total_fiat = balance.get(fiat).get('total')
    return total_coin, total_fiat 
