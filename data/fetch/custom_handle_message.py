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

async def updated_handle_message(pair, message, symbol_trade_data, anomaly_dict, finstore, time_received):

    #print(f"Received for {pair}: {message}")
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