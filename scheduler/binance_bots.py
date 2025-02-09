'''
This is the main file for the Indian Equity pipeline.
Run as a module to start the pipeline.
python -m scheduler.binance_bots
'''

from data.update.crypto_binance import fill_gap
from utils.db.fetch import fetch_entries
import pandas as pd
import schedule
import time
from utils.notifier.telegram import send_telegram_message
from strategy.private.crypto_sotm import CryptoSOTM
import pytz
from datetime import datetime, timedelta
import os
import threading

def run_in_thread(job_func):
    job_thread = threading.Thread(target=job_func)
    job_thread.start()

def _4h_momentum_bot():
    print("4h momentum bot started")
    
    #fill_gap(market_name='crypto_binance', timeframe='4h', pair='BTC')
    try: 
        ohlcv_data = fetch_entries(market_name='crypto_binance', timeframe='4h', all_entries=True, pair='BTC')
        print(ohlcv_data['ETH/BTC']['timestamp'].max())
        crypto_sotm = CryptoSOTM()
        top_n_rising_symbols = crypto_sotm.get_top_n_symbols(ohlcv_data, n=10, r2_period=90)
        print(top_n_rising_symbols)
        telegram_message_rising = crypto_sotm.get_top_n_pairs_message(top_n_rising_symbols, n=10)

        top_n_symbols = crypto_sotm.get_top_n_symbols(ohlcv_data, n=10, r2_period=90)
        print(top_n_symbols)
        telegram_message = crypto_sotm.get_top_n_pairs_message(top_n_symbols, n=10)

        import json
        from dotenv import load_dotenv
        load_dotenv(dotenv_path='config/.env')
        dict_string = os.getenv("TELEGRAM_BOT_CHANNELS")
        my_dict = json.loads(dict_string)
        send_telegram_message(telegram_message, chat_id=my_dict['4h_altbtc_momentum'])
        send_telegram_message(telegram_message_rising, chat_id=my_dict['4h_altbtc_momentum'])
    except Exception as e:
        print(e)

def _15m_momentum_bot():
    print("15m momentum bot started")
    
    fill_gap(market_name='crypto_binance', timeframe='15m', pair='BTC')
    try: 
        ohlcv_data = fetch_entries(market_name='crypto_binance', timeframe='15m', all_entries=True, pair='BTC')
        print(ohlcv_data['ETH/BTC']['timestamp'].max())
        crypto_sotm = CryptoSOTM()
        top_n_symbols_rising = crypto_sotm.get_top_n_symbols(ohlcv_data, n=10, r2_period=90, rising_only=True)
        print(top_n_symbols_rising)
        telegram_message_rising = crypto_sotm.get_top_n_pairs_message(top_n_symbols_rising, n=10, rising=True)

        top_n_symbols = crypto_sotm.get_top_n_symbols(ohlcv_data, n=10, r2_period=90, rising_only=False)
        print(top_n_symbols)
        telegram_message = crypto_sotm.get_top_n_pairs_message(top_n_symbols, n=10, rising=False)

        import json
        from dotenv import load_dotenv
        load_dotenv(dotenv_path='config/.env')
        dict_string = os.getenv("TELEGRAM_BOT_CHANNELS")
        my_dict = json.loads(dict_string)
        send_telegram_message(telegram_message, chat_id=my_dict['15m_altbtc_momentum'])
        send_telegram_message(telegram_message_rising, chat_id=my_dict['15m_altbtc_momentum'])
    except Exception as e:
        print(e)

def _1m_momentum_bot():
    print("1m momentum bot started")
    
    #fill_gap(market_name='crypto_binance', timeframe='1m', pair='BTC')
    try: 
        ohlcv_data = fetch_entries(market_name='crypto_binance', timeframe='1m', all_entries=True, pair='BTC')
        print(ohlcv_data['ETH/BTC']['timestamp'].max())
        crypto_sotm = CryptoSOTM()
        top_n_symbols_rising = crypto_sotm.get_top_n_symbols(ohlcv_data, n=10, r2_period=90, rising_only=True)
        print(top_n_symbols_rising)
        telegram_message_rising = crypto_sotm.get_top_n_pairs_message(top_n_symbols_rising, n=10, rising=True)

        top_n_symbols = crypto_sotm.get_top_n_symbols(ohlcv_data, n=10, r2_period=90, rising_only=False)
        print(top_n_symbols)
        telegram_message = crypto_sotm.get_top_n_pairs_message(top_n_symbols, n=10, rising=False)

        import json
        from dotenv import load_dotenv
        load_dotenv(dotenv_path='config/.env')
        dict_string = os.getenv("TELEGRAM_BOT_CHANNELS")
        my_dict = json.loads(dict_string)
        send_telegram_message(telegram_message, chat_id=my_dict['1m_altbtc_momentum'])
        send_telegram_message(telegram_message_rising, chat_id=my_dict['1m_altbtc_momentum'])
    except Exception as e:
        print(e)

def _5m_momentum_bot():
    print("5m momentum bot started")
    
    fill_gap(market_name='crypto_binance', timeframe='5m', pair='BTC')
    try: 
        ohlcv_data = fetch_entries(market_name='crypto_binance', timeframe='5m', all_entries=True, pair='BTC')
        print(ohlcv_data['ETH/BTC']['timestamp'].max())
        crypto_sotm = CryptoSOTM()
        top_n_symbols_rising = crypto_sotm.get_top_n_symbols(ohlcv_data, n=10, r2_period=90, rising_only=True)
        print(top_n_symbols_rising)
        telegram_message_rising = crypto_sotm.get_top_n_pairs_message(top_n_symbols_rising, n=10, rising=True)

        top_n_symbols = crypto_sotm.get_top_n_symbols(ohlcv_data, n=10, r2_period=90, rising_only=False)
        print(top_n_symbols)
        telegram_message = crypto_sotm.get_top_n_pairs_message(top_n_symbols, n=10, rising=False)

        import json
        from dotenv import load_dotenv
        load_dotenv(dotenv_path='config/.env')
        dict_string = os.getenv("TELEGRAM_BOT_CHANNELS")
        my_dict = json.loads(dict_string)
        send_telegram_message(telegram_message, chat_id=my_dict['5m_altbtc_momentum'])
        send_telegram_message(telegram_message_rising, chat_id=my_dict['5m_altbtc_momentum'])
    except Exception as e:
        print(e)

def Scheduler():
    '''
    Scheduler function that runs the pipeline every day at 6 pm IST to get fresh orders and sells from pipeline.
    '''
    ist = pytz.timezone('Asia/Kolkata')
    utc = pytz.UTC

    # Schedule pipeline at 9 AM IST
    target_time_ist_pipeline = datetime.now(ist).replace(hour=23, minute=0, second=0, microsecond=0)
    target_time_utc_pipeline = target_time_ist_pipeline.astimezone(utc).time()
    schedule.every().day.at(target_time_utc_pipeline.strftime('%H:%M')).do(_4h_momentum_bot)

    # Schedule pipeline for every 2 hours for 15m momentum bot
    schedule.every(2).hours.do(_15m_momentum_bot)

    #schedule.every(1).minutes.do(_1m_momentum_bot)

    schedule.every(40).minutes.do(_5m_momentum_bot)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    #sim_start = pd.Timestamp.now() - pd.Timedelta(days=6)
    Scheduler()
    #pipeline()
    #_5m_momentum_bot()
    #_4h_momentum_bot()
    #_15m_momentum_bot()