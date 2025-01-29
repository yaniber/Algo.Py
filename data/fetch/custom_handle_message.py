'''
what's different? newer function detects anomalies and also reports on missing data
Also introduced the locking function to prevent data corruption


Issues : 

- There's a pile up happening because the processing takes 2 seconds apparently for score calculation and some time to write data,
- There's almost a 20 minute gap sometimes between data being published and reaching this function which is unacceptable since we want instant anomaly detection.


Solution : 
- Finstore is the bloody bottleneck.

Score Calc : 
- Use market cap / 24h vol cap vs the anomaly volume / past few minutes volume ratio to see how much does it effect it. 
- Use buy - sell ratio wisely - change signs if sells become more dominant or buys become more dominant.
'''
import numpy as np
import json
from utils.db.lock import generic_lock
import asyncio
import time
import pandas as pd
import sys
sys.path.append('/app/data/fetch')
import slope_r2_product

async def updated_handle_message(pair, message, symbol_trade_data, anomaly_dict, finstore, time_received):

    print(f"Received for {pair}: {message}")
    calculate_bool = False
    
    #if (time.time() * 1000) - message['T'] > 300 * 1000:
        #print(f"Delayed for {pair}: {message}")

    if pair == '':
        print(f'len of symbol trade dict : {pair} : {len(symbol_trade_data[pair])}')
        print(f"{message['a']}")


    # Save the trade data for the past 10 minutes
    try:
        if symbol_trade_data[pair]:
            previous_message = symbol_trade_data[pair][-1]
            if 'a' in previous_message and 'a' in message:
                if message['a'] != previous_message['a'] + 1:
                    print(f"Warning: Missed trades for {pair}. Previous 'a': {previous_message['a']}, Current 'a': {message['a']}")

        symbol_trade_data[pair].append(message)

        # Calculate mean and standard deviation of quantities for the current pair
        quantities = [float(trade['q']) for trade in symbol_trade_data[pair]]
        mean_quantity = np.mean(quantities)
        std_quantity = np.std(quantities)

        # Determine the modulo rule based on the mean quantity
        if mean_quantity >= 10000:
            modulo_rule = 1000
        elif mean_quantity >= 1000:
            modulo_rule = 100
        elif mean_quantity >= 100:
            modulo_rule = 10
        else:
            modulo_rule = 5

        # Detect bot orders based on conditions
        current_quantity = float(message['q'])
        current_price = float(message['p'])
        order_type = "Buy" if message['m'] else "Sell"
        # if (abs(current_quantity - mean_quantity) > 3 * std_quantity) and (current_quantity % modulo_rule == 0):

        message_timestamp = message['T'] / 1000  # Convert to seconds
        current_time = time.time()  # Current time in seconds since the epoch

        time_elapsed = current_time - message_timestamp  # Time difference in seconds

        #if time_elapsed > 1.5:
            #print(f'Wayyyy too much time taken for anomaly detection : {time_elapsed}')
        
        if (abs(current_quantity - mean_quantity) > 10 * std_quantity):
            anomaly = {
                "symbol": pair,
                "timestamp": message['T'],
                "usdt_value": current_quantity * current_price,
                "order_type": order_type,
                "quantity": current_quantity,
                "mean_quantity": mean_quantity,
                "std_quantity": std_quantity,
                "modulo_rule": modulo_rule,
                "time_received" : time_received,
                "current_time" : current_time,
            }
            if pair not in anomaly_dict:
                anomaly_dict[pair] = []
            anomaly_dict[pair].append(anomaly)
            
            with open('anomaly_file.json', 'a') as file:
                file.write(json.dumps(anomaly) + '\n')

            if len(anomaly_dict[pair]) >= 3:
                #print(f"\nPotential bot order detected for {pair} in :{time_elapsed} seconds :\n")
                #for idx, a in enumerate(anomaly_dict[pair], start=1):
                #    print(f"  Anomaly {idx}: {a}")

                current_time = time.time()

                #asyncio.create_task(calculate_anomaly_score(pair , anomaly_dict, symbol_trade_data, current_price, message, current_time))
                calculate_bool = True
            else:
                calculate_bool = False


        # Save the trade data using finstore
        #with generic_lock:
        #    finstore.stream.save_trade_data(pair, message, preset='agg_trade')
        
        if calculate_bool:
            await calculate_anomaly_score(pair , anomaly_dict, symbol_trade_data, current_price, message, current_time)
    
    except Exception as e:
        import traceback
        print(f'Error in handle message : {traceback.print_exc()}')

async def calculate_anomaly_score(pair , anomaly_dict, symbol_trade_data, current_price, message, current_time):

    try:

        num_buys = sum(1 for a in anomaly_dict[pair] if a['order_type'] == "Buy")
        avg_buy_usdt = sum(a['usdt_value'] for a in anomaly_dict[pair] if a['order_type'] == "Buy") / max(num_buys, 1)

        num_sells = sum(1 for a in anomaly_dict[pair] if a['order_type'] == "Sell")
        avg_sell_usdt = sum(a['usdt_value'] for a in anomaly_dict[pair] if a['order_type'] == "Sell") / max(num_sells, 1)

        delta = sum(a['usdt_value'] for a in anomaly_dict[pair] if a['order_type'] == "Buy") - sum(a['usdt_value'] for a in anomaly_dict[pair] if a['order_type'] == "Sell")

        timestamps = [a['timestamp'] for a in anomaly_dict[pair]]
        order_rate = len(timestamps) / ((max(timestamps) - min(timestamps)) / 1000 + 1)

        time_diff = time.time() - current_time


        # Calculate scores for anomalies
        total_usdt_volume = sum(float(trade['q']) * float(trade['p']) for trade in symbol_trade_data[pair])
        delta_anomalies_usdt = sum(a['usdt_value'] for a in anomaly_dict[pair])
        delta_ratio = delta_anomalies_usdt / max(total_usdt_volume, 1)

        max_anomaly_rate = max(
            (len(anomaly_dict[s]) / ((max(a['timestamp'] for a in anomaly_dict[s]) - min(a['timestamp'] for a in anomaly_dict[s])) / 1000 + 1))
            for s in anomaly_dict if anomaly_dict[s]
        )

        rate_ratio = order_rate / max(max_anomaly_rate, 1)

        num_buys = sum(1 for a in anomaly_dict[pair] if a['order_type'] == "Buy")
        num_sells = sum(1 for a in anomaly_dict[pair] if a['order_type'] == "Sell")
        buy_sell_ratio = (num_buys - num_sells) / max(num_buys + num_sells, 1)

        # Calculate buy/sell ratio for all trades in the past hour
        num_buys_hour = sum(1 for trade in symbol_trade_data[pair] if not trade['m'])
        num_sells_hour = sum(1 for trade in symbol_trade_data[pair] if trade['m'])
        buy_sell_ratio_hour = (num_buys_hour - num_sells_hour) / max(num_buys_hour + num_sells_hour, 1)

        # Define weights for scoring
        w1, w2, w3 = 0.5, 0.2, 0.3
        #score = (w1 * delta_ratio + w2 * rate_ratio) + w3 * (buy_sell_ratio_hour * buy_sell_ratio)
        if buy_sell_ratio_hour * buy_sell_ratio > 0:
            sign = 1
        else:
            sign = -1
        
        max_anomaly_length = max(len(anomaly_dict[s]) for s in anomaly_dict if anomaly_dict[s])
        anomaly_len_ratio = len(anomaly_dict[pair]) / max_anomaly_length
        score = (0.5 * delta_ratio + 0.5 * anomaly_len_ratio) * sign
        

        score = {
            "symbol": pair,
            "timestamp": message['T'],
            "price": current_price,
            "score": score,
            "delta_ratio" : delta_ratio,
            "rate_ratio" : rate_ratio,
            "buy_sell_ratio" : buy_sell_ratio,
            "buy_sell_ratio_hour" : buy_sell_ratio_hour,
            "anomaly_len_ratio" : anomaly_len_ratio,
        }
        if abs(score['score']) >= 0.4: 
            print('*'*len(anomaly_dict[pair]))
            print(f"\nProcessing done for {pair}: time diff : {time_diff}\n")
            print(f"Number of buys: {num_buys}, Avg buy amount in USDT: {avg_buy_usdt:.2f}")
            print(f"Number of sells: {num_sells}, Avg sell amount in USDT: {avg_sell_usdt:.2f}")
            print(f"Order rate: {order_rate:.2f} orders per second")
            print(f'\nDelta :::::: {delta} :::::::::')
            print(f"Score: {score['score']:.3f}, Price: {current_price:.5f}, buy_sell_ratio: {buy_sell_ratio}, buy_sell_hour : {buy_sell_ratio_hour}")
        
        with open('score_file.json', 'a') as file:
            file.write(json.dumps(score) + '\n')
    
    except Exception as e:
        print(e)
                

async def notupdated_handle_message(pair, message, symbol_trade_data, finstore):
    #print(f"Received for {pair}: {message}")

    # Save the trade data for the past 10 minutes
    if symbol_trade_data[pair]:
        previous_message = symbol_trade_data[pair][-1]
        if 'a' in previous_message and 'a' in message:
            if message['a'] != previous_message['a'] + 1:
                print(f"Warning: Missed trades for {pair}. Previous 'a': {previous_message['a']}, Current 'a': {message['a']}")

    symbol_trade_data[pair].append(message)

    # Save the trade data using finstore
    finstore.stream.save_trade_data(pair, message, preset='agg_trade')

'''

- Need to decide between tradeoff of speed vs accuracy 
    - I.e= take trades at counter = 0 , or take top 10 trades at counter = 1

    
- Need to change counter logic since BTC might change counter after several symbols have already called handle message. 
    - Hence they shall be missed opportunities. 

- Short equal quantities of BTC for every position and long for every closing of position?
'''


async def kline_handle_message(pair, message, symbol_trade_data, top_pairs_dict, finstore, time_received, binance_client):
    
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

                    if pair == 'BTCUSDT':
                        top_pairs_dict['counter'] += 1
                        if top_pairs_dict['counter'] > 5:
                            top_pairs_dict['counter'] = 0
                        
                        print(f"Counter Value : {top_pairs_dict['counter']}")

                        if top_pairs_dict['counter'] == 1:
                            
                            queue_entries = binance_client.get_all_from_queue()
                            # Sort entries by absolute r2p scores in descending order and keep only the top 10
                            if queue_entries:

                                if len(queue_entries) < 20: 
                                
                                    top_5_entries = sorted(queue_entries, key=lambda x: abs(x['r2p_score']), reverse=True)[:5]

                                    print(f"Processing top 10 entries: {top_5_entries}")

                                    # Process each of the top 10 entries
                                    for entry in top_5_entries:
                                        symbol = entry['symbol']
                                        r2p_score = entry['r2p_score']
                                        close_price = entry['close_price']
                                        side = 'buy' if r2p_score > 0 else 'sell'  # Determine side based on r2p

                                        # Calculate the quantity
                                        quantity = 25.0 / close_price

                                        try:
                                            # Change leverage and place the futures order
                                            binance_client.change_leverage(symbol=symbol, leverage=10)
                                            #binance_client.place_futures_order(symbol=symbol, side=side, quantity=quantity)
                                            binance_client.limit_order_chaser_async(symbol=pair, side=side, size=quantity, max_retries=120, interval=2.0)
                                            print(f"Order placed for {symbol}: side={side}, quantity={quantity}, r2p_score={r2p_score}")

                                            
                                            #in case you want to trade pairs :
                                            #binance_client.change_leverage(symbol='BTCUSDT', leverage=20)
                                            #last_key = list(symbol_trade_data['BTCUSDT'].keys())[-1]
                                            #previous_message = symbol_trade_data['BTCUSDT'][last_key]
                                            #binance_client.place_futures_order(symbol='BTCUSDT', side='sell' if side == 'buy' else 'buy', quantity=50.0/float(previous_message['c']))
                                            

                                            # Add the symbol to an available slot in top_pairs_dict
                                            for key, value in top_pairs_dict.items():
                                                if key in ['counter', 'pnl']:
                                                    continue
                                                if value['symbol'] == 'None':  # Find the first empty slot
                                                    top_pairs_dict[key] = {
                                                        'symbol': symbol,
                                                        'score': r2p_score,
                                                        'close_price_buy': close_price,
                                                        'keep_open': False
                                                    }
                                                    print(f"Added {symbol} to top_pairs_dict: {top_pairs_dict[key]}")
                                                    break
                                        except Exception as e:
                                            print(f"Failed to execute order for {symbol}: {e}")

                                    # Clear the queue after processing the top 10 entries
                                    
                                    binance_client.clear_queue()
                                    
                                    #pass
                                else:
                                    print(f'Passing this iteration as more than 20 trades are present : {len(queue_entries)}')
                                    binance_client.clear_queue()
                            else:
                                print(f'queue entries : {queue_entries}')

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
                    # The lookback period is 10 : 
                    #earlier_values = synthetic_close_values[-60:]
                    #recent_values = synthetic_close_values[-10:]

                    #earlier_srp = slope_r2_product.SlopeR2Product(earlier_values)
                    #recent_srp = slope_r2_product.SlopeR2Product(recent_values)

                    synthetic_close_values = synthetic_close_values[-7:]
                    srp = slope_r2_product.SlopeR2Product(synthetic_close_values)
                    try:
                        #r2p_earlier = earlier_srp.calc_slope_r2_product()
                        #r2p_recent = recent_srp.calc_slope_r2_product()
                        #r2p = 0.4 * r2p_earlier + 0.6 * r2p_recent
                        r2p = srp.calc_slope_r2_product()
                        MIN_R2P = 0.75
                        if running_trade:
                            MIN_R2P = 0.5
                            volume_flag = True
                        if (abs(r2p) >= MIN_R2P) and volume_flag:
                            print(f'R 2 Product for pair : {pair} : {r2p} for timestamp : {message["T"]} for len : {len(synthetic_close_values)}')

                            if top_pairs_dict['counter'] == 0:

                                if len(symbol_trade_data[pair]) >= 5:
                                
                                    queue_entries = binance_client.get_all_from_queue()

                                    # Sort entries by absolute r2p scores in descending order and keep only the top 10
                                    if len(queue_entries) < 10000:

                                        binance_client.add_to_queue({
                                                        'symbol': pair,
                                                        'r2p_score': r2p,
                                                        'close_price': float(message['c'])  # Close price from the message
                                                    })
                                        
                                        side = 'buy' if r2p > 0 else 'sell'  # Determine side based on r2p

                                        '''
                                        # Calculate the quantity
                                        quantity = 30.0 / float(message['c'])

                                        try:
                                            # Change leverage and place the futures order
                                            binance_client.change_leverage(symbol=pair, leverage=10)
                                            #binance_client.place_futures_order(symbol=pair, side=side, quantity=quantity)
                                            binance_client.limit_order_chaser_async(symbol=pair, side=side, size=quantity, max_retries=120, interval=2.0)
                                            print(f"Order placed for {pair}: side={side}, quantity={quantity}, r2p_score={r2p}")

                                            # Add the symbol to an available slot in top_pairs_dict
                                            for key, value in top_pairs_dict.items():
                                                if key in ['counter', 'pnl']:
                                                    continue
                                                if value['symbol'] == 'None':  # Find the first empty slot
                                                    top_pairs_dict[key] = {
                                                        'symbol': pair,
                                                        'score': r2p,
                                                        'close_price_buy': float(message['c']),
                                                        'keep_open': False
                                                    }
                                                    print(f"Added {pair} to top_pairs_dict: {top_pairs_dict[key]}")
                                                    break
                                        except Exception as e:
                                            print(f"Failed to execute order for {pair}: {e}")
                                        '''
                                        


                            
                            if top_pairs_dict['counter'] == 100:
                                open_positions = sum(1 for value in top_pairs_dict.values() if value.get('symbol') != 'None')
                                if open_positions < 10:
                                    #print(f'Positions Opened : \n')
                                    for key, value in list(top_pairs_dict.items()): 
                                        if (key == 'counter') or (key == 'pnl'):
                                            continue

                                        quantity = 50.0 / float(data['c'])
                                        side = 'buy' if abs(r2p)/r2p > 0 else 'sell'
                                        if value.get('symbol', '') == pair:
                                            if len(symbol_trade_data[pair]) >= 10:
                                                binance_client.change_leverage(symbol=pair, leverage=10)
                                                binance_client.place_futures_order(symbol=pair, side=side, quantity=quantity)
                                            print(f"\n\n\n\------ \nSymbol : {value['symbol']}\nScore : {value['score']}\n")

                            
                            if top_pairs_dict['counter'] in [3,4,5]:
                                for key, value in list(top_pairs_dict.items()):  # Create a list to allow modification during iteration
                                    if (key == 'counter') or (key == 'pnl'):
                                        continue

                                    if value['symbol'] == pair:
                                        percent_change = ((float(message['c']) - value['close_price_buy']) /  value['close_price_buy'])*(100*(abs(r2p)/r2p))
                                        print(f'\n\n\n\nStill open position for : {pair}, percent_change : {percent_change}\n\n\n\n')
                                        side = 'buy' if abs(r2p)/r2p > 0 else 'sell'
                                        #binance_client.place_futures_order(symbol=pair, side=side, quantity=40, quantity_type='USD')
                                        top_pairs_dict[key]['keep_open'] = True
                        else:
                            if top_pairs_dict['counter'] in [5]:
                                for key, value in list(top_pairs_dict.items()):  # Create a list to allow modification during iteration
                                    if (key == 'counter') or (key == 'pnl'):
                                        continue
                                    if value['symbol'] == pair:
                                        percent_change = ((float(message['c']) - value['close_price_buy']) /  value['close_price_buy'])*(100*(abs(r2p)/r2p))
                                        print(f'\n\n\n\nClosing position for : {pair}, r2p : {r2p}, percent_change : {percent_change}\n\n\n\n')

                                        if len(symbol_trade_data[pair]) >= 5:
                                            binance_client.close_futures_positions(symbol=pair, use_chaser=True)
                                            if binance_client.get_all_from_queue():
                                                binance_client.execution_queue.pop()

                                        top_pairs_dict[key] = {'symbol' : 'None', 'score': 0, 'close_price_buy': 0, 'keep_open' : False}
                                        top_pairs_dict['pnl'] += (percent_change - 0.02) 
                                        print(f'\n\n\n\nPnL ::::::::: {top_pairs_dict["pnl"]}')


                    except Exception as e:
                        import traceback
                        print(f'Error for pair : {pair} : {e} , close values : {synthetic_close_values[-10:]}')
                        print(traceback.print_exc())
        else:
            symbol_trade_data[pair] = {}
    except Exception as e:
        print(e)
    
    symbol_trade_data[pair][message['T']] = message 




async def kline_handle_message_new(pair, message, symbol_trade_data, top_pairs_dict, finstore, time_received, binance_client):
    
    MAX_NUMBER_OF_PAIRS = 5 # Maximum number of positions at a time.
    MAX_COUNTER = 10 # Max counter - how many minutes to rotate in.  
    COUNTER_TAKE_TRADE = 1 # Counter in which to take trade. 
    QUANTITY_USD = 100.0 # quantity per dollar
    LOOKBACK_PERIOD = 19 # lookback for calculating Slope R2 Value.
    MIN_R2P = 0.75 # Minimum value of r2p to add it to queue. 
    ADD_SIZE = 100.0 # Size to add to open position. 


    if top_pairs_dict == {}:
        top_pairs_dict['counter'] = -1
        top_pairs_dict['pnl'] = 0.0
        for i in range(1, MAX_NUMBER_OF_PAIRS + 1):
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

                    if pair == 'BTCUSDT':
                        top_pairs_dict['counter'] += 1
                        if top_pairs_dict['counter'] > MAX_COUNTER:
                            top_pairs_dict['counter'] = 0
                        
                        print(f"Counter Value : {top_pairs_dict['counter']}")
                        
                        if top_pairs_dict['counter'] == COUNTER_TAKE_TRADE:
                            
                            queue_entries = binance_client.get_all_from_queue()
                            # Sort entries by absolute r2p scores in descending order and keep only the top 10
                            if queue_entries:
                                top_5_entries = sorted(queue_entries, key=lambda x: abs(x['r2p_score']), reverse=True)[:MAX_NUMBER_OF_PAIRS]

                                print(f"Processing top 5 entries: {top_5_entries}")

                                # Process each of the top 10 entries
                                for entry in top_5_entries:
                                    symbol = entry['symbol']
                                    r2p_score = entry['r2p_score']
                                    close_price = entry['close_price']
                                    side = 'buy' if r2p_score > 0 else 'sell'  # Determine side based on r2p

                                    # Calculate the quantity
                                    quantity = QUANTITY_USD / close_price

                                    try:
                                        # Add the symbol to an available slot in top_pairs_dict
                                        for key, value in top_pairs_dict.items():
                                            if key in ['counter', 'pnl']:
                                                continue
                                            if value['symbol'] == 'None':  # Find the first empty slot
                                                top_pairs_dict[key] = {
                                                    'symbol': symbol,
                                                    'score': r2p_score,
                                                    'close_price_buy': close_price,
                                                    'keep_open': False
                                                }
                                                print(f"Added {symbol} to top_pairs_dict: {top_pairs_dict[key]}")
                                                # Change leverage and place the futures order
                                                binance_client.change_leverage(symbol=symbol, leverage=10)
                                                binance_client.place_futures_order(symbol=symbol, side=side, quantity=quantity)
                                                print(f"Order placed for {symbol}: side={side}, quantity={quantity}, r2p_score={r2p_score}")
                                                break
                                    except Exception as e:
                                        print(f"Failed to execute order for {symbol}: {e}")

                                # Clear the queue after processing the top 10 entries
                                
                                binance_client.clear_queue()
                                #pass

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

                    # The lookback period is 10 : 
                    # Split synthetic close values

                    alt_volumes_40 = alt_volumes[-50:-10]
                    alt_volumes_10 = alt_volumes[-10:]
                    volume_flag = True if (sum(alt_volumes_10) / len(alt_volumes_10)) > (sum(alt_volumes_40) / len(alt_volumes_40)) else False
                    earlier_values = synthetic_close_values[-1*LOOKBACK_PERIOD:-5]
                    recent_values = synthetic_close_values[-5:]

                    if len(symbol_trade_data[pair]) >= LOOKBACK_PERIOD:
                        # Calculate R² product for each segment
                        earlier_srp = slope_r2_product.SlopeR2Product(earlier_values)
                        recent_srp = slope_r2_product.SlopeR2Product(recent_values)

                        try:
                            r2p_earlier = earlier_srp.calc_slope_r2_product()
                            r2p_recent = recent_srp.calc_slope_r2_product()
                            r2p = 0.4 * r2p_earlier + 0.6 * r2p_recent

                            if running_trade:
                                MIN_R2P = 0.68
                                volume_flag = True
                                print(f'\n\nCurrent R2P for : {pair} : {r2p}')
                            if (abs(r2p) >= MIN_R2P) and (volume_flag==True):
                                print(f'R 2 Product for pair : {pair} : {r2p} for timestamp : {message["T"]} for len : {len(earlier_values)}')

                                if top_pairs_dict['counter'] == COUNTER_TAKE_TRADE - 1:

                                    if len(symbol_trade_data[pair]) >= LOOKBACK_PERIOD:
                                    
                                        queue_entries = binance_client.get_all_from_queue()

                                        binance_client.add_to_queue({
                                                        'symbol': pair,
                                                        'r2p_score': r2p,
                                                        'close_price': float(message['c'])  # Close price from the message
                                                    })
                                            
                                if top_pairs_dict['counter'] in [MAX_COUNTER]:
                                    for key, value in list(top_pairs_dict.items()):  # Create a list to allow modification during iteration
                                        if (key == 'counter') or (key == 'pnl'):
                                            continue

                                        if value['symbol'] == pair:
                                            percent_change = ((float(message['c']) - value['close_price_buy']) /  value['close_price_buy'])*(100*(abs(r2p)/r2p))
                                            print(f'\n\n\n\nStill open position for : {pair}, percent_change : {percent_change}\n\n\n\n')
                                            side = 'buy' if abs(r2p)/r2p > 0 else 'sell'
                                            binance_client.place_futures_order(symbol=pair, side=side, quantity=ADD_SIZE, quantity_type='USD')
                                            top_pairs_dict[key]['keep_open'] = True
                            else:
                                if top_pairs_dict['counter'] in [MAX_COUNTER, MAX_COUNTER-1, MAX_COUNTER-2]:
                                    for key, value in list(top_pairs_dict.items()):  # Create a list to allow modification during iteration
                                        if (key == 'counter') or (key == 'pnl'):
                                            continue
                                        if value['symbol'] == pair:
                                            percent_change = ((float(message['c']) - value['close_price_buy']) /  value['close_price_buy'])*(100*(abs(r2p)/r2p))
                                            print(f'\n\n\n\nClosing position for : {pair}, percent_change : {percent_change}\n\n\n\n')

                                            if len(symbol_trade_data[pair]) >= LOOKBACK_PERIOD:
                                                binance_client.close_futures_positions(symbol=pair)

                                            top_pairs_dict[key] = {'symbol' : 'None', 'score': 0, 'close_price_buy': 0, 'keep_open' : False}
                                            top_pairs_dict['pnl'] += percent_change
                                            print(f'\n\n\n\nPnL ::::::::: {top_pairs_dict["pnl"]}')


                        except Exception as e:
                            import traceback
                            print(f'Error for pair : {pair} : {e} , close values : {synthetic_close_values[-10:]}')
                            print(traceback.print_exc())
        else:
            symbol_trade_data[pair] = {}
    except Exception as e:
        print(e)
    
    symbol_trade_data[pair][message['T']] = message 
