import numpy as np
import json
from utils.db.lock import generic_lock
import asyncio
import time
import pandas as pd
import sys
sys.path.append('/app/data/stream')
import slope_r2_product

async def ema_handle_message(pair, message, symbol_trade_data, top_pairs_dict, finstore, time_received, binance_client):
    
    if top_pairs_dict == {}:
        top_pairs_dict['counter'] = -1
        top_pairs_dict['pnl'] = 0.0
        for i in range(1, 6):
            top_pairs_dict[f'pair{i}'] = {'symbol' : 'None', 'score': 0.0, 'close_price_buy': 0.0, 'keep_open' : False}
    
    running_trade = False
    for key, value in top_pairs_dict.items():
        if key in ['counter', 'pnl']:
            continue
        if value['symbol'] == pair:
            running_trade = True
            break



    try:
        if (symbol_trade_data.get(pair, None) != None) and (symbol_trade_data.get('BTCUSDT', None) != None):
        
            last_key = list(symbol_trade_data[pair].keys())[-1]
            previous_message = symbol_trade_data[pair][last_key]
            if ('T' in previous_message and 'T' in message):
                if message['T'] != previous_message['T']:

                    #print(f'New Received for : {pair} : {symbol_trade_data[pair]}')
                    data_dict = symbol_trade_data[pair]
                    data_dict_btc = symbol_trade_data['BTCUSDT']
                    btc_close_lookup = {timestamp: float(data['c']) for timestamp, data in data_dict_btc.items()}

                    # Compute synthetic pair close values
                    synthetic_close_values = []
                    alt_volumes = []
                    for timestamp, data in data_dict.items():
                        alt_close = float(data['c'])
                        alt_volume = float(data['v'])
                        alt_volumes.append(alt_volume)
                        if timestamp in btc_close_lookup:  # Ensure timestamp exists in BTCUSDT data
                            btc_close = btc_close_lookup[timestamp]
                            synthetic_close_values.append(alt_close / btc_close)
                    
                    #close_values = [float(value['c']) for value in data_dict.values()]
                    #close_values = close_values[-30:]
                    alt_volumes_15 = alt_volumes[-20:]
                    alt_volumes_5 = alt_volumes[-5:]
                    try:
                        volume_flag = True if (sum(alt_volumes_5) / len(alt_volumes_5)) > (sum(alt_volumes_15) / len(alt_volumes_15)) else False
                        #volume_flag = True
                    except Exception as e:
                        print(e)
                        volume_flag = True

                    
        else:
            symbol_trade_data[pair] = {}
    except Exception as e:
        print(e)
    
    symbol_trade_data[pair][message['T']] = message 

'''
symbol_trade_data : 
{ pair : {timestamp : {ohlcv, etc dict}}
}

need to return for dashboard : 
{pair : {timestamp : {ohlcv, r2p score}}

-> dashboard should do the calculation for top 5/10 wtv scores, 
-> plot them based on timestamps.
-> heatmap based on scores.


pair dict ::::::::::: {1738324319999: {'t': 1738324260000, 'T': 1738324319999, 's': 'DUSKUSDT', 'i': '1m', 'f': 187956825, 'L': 187956885, 'o': '0.16683', 'c': '0.16666', 'h': '0.16683', 'l': '0.16661', 'v': '5988', 'n': 61, 'x': True, 'q': '998.18311', 'V': '1476', 'Q': '246.08368', 'B': '0'}, 1738324379999: {'t': 1738324320000, 'T': 1738324379999, 's': 'DUSKUSDT', 'i': '1m', 'f': 187956886, 'L': 187956918, 'o': '0.16671', 'c': '0.16681', 'h': '0.16688', 'l': '0.16671', 'v': '4377', 'n': 33, 'x': True, 'q': '730.16035', 'V': '826', 'Q': '137.77232', 'B': '0'}, 1738324439999: {'t': 1738324380000, 'T': 1738324439999, 's': 'DUSKUSDT', 'i': '1m', 'f': 187956919, 'L': 187956947, 'o': '0.16681', 'c': '0.16690', 'h': '0.16694', 'l': '0.16673', 'v': '2381', 'n': 29, 'x': True, 'q': '397.27156', 'V': '1091', 'Q': '182.04626', 'B': '0'}, 1738324499999: {'t': 1738324440000, 'T': 1738324499999, 's': 'DUSKUSDT', 'i': '1m', 'f': 187956948, 'L': 187956985, 'o': '0.16689', 'c': '0.16678', 'h': '0.16699', 'l': '0.16678', 'v': '10732', 'n': 38, 'x': True, 'q': '1790.90551', 'V': '3196', 'Q': '533.29561', 'B': '0', 'r2p_score': -0.00046583746186962694}, 1738324559999: {'t': 1738324500000, 'T': 1738324559999, 's': 'DUSKUSDT', 'i': '1m', 'f': 187956986, 'L': 187957003, 'o': '0.16679', 'c': '0.16715', 'h': '0.16715', 'l': '0.16679', 'v': '2569', 'n': 18, 'x': True, 'q': '428.92492', 'V': '2514', 'Q': '419.73772', 'B': '0', 'r2p_score': 0.27296389866803744}, 1738324619999: {'t': 1738324560000, 'T': 1738324619999, 's': 'DUSKUSDT', 'i': '1m', 'f': 187957004, 'L': 187957058, 'o': '0.16715', 'c': '0.16735', 'h': '0.16739', 'l': '0.16702', 'v': '6190', 'n': 55, 'x': True, 'q': '1034.64966', 'V': '3187', 'Q': '532.72786', 'B': '0', 'r2p_score': 0.5891663918514245}, 1738324679999: {'t': 1738324620000, 'T': 1738324679999, 's': 'DUSKUSDT', 'i': '1m', 'f': 187957059, 'L': 187957213, 'o': '0.16737', 'c': '0.16761', 'h': '0.16784', 'l': '0.16731', 'v': '66431', 'n': 155, 'x': True, 'q': '11143.31603', 'V': '60167', 'Q': '10093.41820', 'B': '0', 'r2p_score': 0.6793751781646309}, 1738324739999: {'t': 1738324680000, 'T': 1738324739999, 's': 'DUSKUSDT', 'i': '1m', 'f': 187957214, 'L': 187957260, 'o': '0.16762', 'c': '0.16777', 'h': '0.16778', 'l': '0.16762', 'v': '18098', 'n': 47, 'x': True, 'q': '3035.14024', 'V': '4881', 'Q': '818.57298', 'B': '0', 'r2p_score': 0.7933412244969265}}
'''


async def kline_handle_message(pair, message, symbol_trade_data, top_pairs_dict, finstore, time_received, binance_client):   

    try:
        if (symbol_trade_data.get(pair, None) != None):
        
            last_key = list(symbol_trade_data[pair].keys())[-1]
            previous_message = symbol_trade_data[pair][last_key]
            if ('T' in previous_message and 'T' in message):
                if message['T'] != previous_message['T']:

                    #print(f'New Received for : {pair} : {symbol_trade_data[pair]}')
                    data_dict = symbol_trade_data[pair]
                    data_dict_btc = symbol_trade_data['BTCUSDT']
                    btc_close_lookup = {timestamp: float(data['c']) for timestamp, data in data_dict_btc.items()}

                    # Compute synthetic pair close values
                    synthetic_close_values = []
                    for timestamp, data in data_dict.items():
                        alt_close = float(data['c'])
                        if timestamp in btc_close_lookup:  # Ensure timestamp exists in BTCUSDT data
                            btc_close = btc_close_lookup[timestamp]
                            synthetic_close_values.append(alt_close / btc_close)
                    

                    synthetic_close_values = synthetic_close_values[-10:]
                    srp = slope_r2_product.SlopeR2Product(synthetic_close_values)
                    try:
                        r2p = srp.calc_slope_r2_product()
                        MIN_R2P = 0.75
                        '''
                        if (abs(r2p) >= MIN_R2P):
                            print(f'R 2 Product for pair : {pair} : {r2p} for timestamp : {message["T"]} for len : {len(synthetic_close_values)}')
                        '''
                        symbol_trade_data[pair][last_key]['r2p_score'] = r2p 
                        print(f"pair dict ::::::::::: {symbol_trade_data[pair]}")

                    except Exception as e:
                        import traceback
                        print(f'Error for pair : {pair} : {e} , close values : {synthetic_close_values[-10:]}')
                        print(traceback.print_exc())
        else:
            symbol_trade_data[pair] = {}
    except Exception as e:
        print(e)
    
    symbol_trade_data[pair][message['T']] = message 