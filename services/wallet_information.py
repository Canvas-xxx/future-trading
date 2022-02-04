def get_position_size(balance, risk_of_ruin, stop_loss, leverage):
    return round(balance * risk_of_ruin / stop_loss / leverage)

def get_usdt_balance(exchange):
    balance = exchange.fetch_balance()
    total_balance = balance.get('info').get('totalWalletBalance') 
    return float(total_balance) 


def get_positions_list(exchange):
    positions = exchange.fetch_positions()
    filtered_positions = filter(lambda x: x.get('side') != None, positions)
    return list(filtered_positions)
