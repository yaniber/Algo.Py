import ccxt
import pandas as pd

def fetch_ohlcv_binance(symbol, timeframe, since):
    exchange = ccxt.binance()
    all_ohlcv = []
    limit = 200  # Most exchanges allow a max of 500 entries per request
    while True:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
        if not ohlcv:
            break
        all_ohlcv.extend(ohlcv)
        since = ohlcv[-1][0] + 1  # Update since to get new data from the end of the last fetch
    df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    if 'timestamp' not in df.columns:
        print(f"Error: 'timestamp' column missing in data for {symbol}")
    return df

def fetch_symbol_list_binance(type='spot', suffix='USDT'):
    '''
    Fetches symbol list of all matching coins from binance.
    type: 'spot' or 'futures' ?
    suffix: 'USDT' or 'BTC'
    '''
    exchange = ccxt.binance()
    markets = exchange.load_markets()
    symbols = [market.split(':')[0] for market in markets if markets[market]['type'] == type and market.split(':')[0].endswith(f'/{suffix}')] 
    return symbols