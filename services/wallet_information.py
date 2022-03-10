import pprint36 as pprint

def get_position_size(balance, risk_of_ruin, stop_loss, leverage):
    return balance * risk_of_ruin / stop_loss / leverage

def get_usdt_balance_in_future_wallet(exchange):
    balance = exchange.fetch_balance()
    total_balance = balance.get('info').get('totalWalletBalance') 
    return float(total_balance) 

def get_positions_list(exchange):
    try:
        balance = exchange.fetch_balance()
        positions = balance['info']['positions']
        filtered_positions = filter(lambda x: float(x.get('positionAmt')) > 0, positions)
        return list(filtered_positions)
    except:
        return list([])

def get_unit_of_symbol(exchange, coin, fiat):
    balance = exchange.fetch_balance()
    total_coin = balance.get(coin).get('total')
    total_fiat = balance.get(fiat).get('total')
    return total_coin, total_fiat 
