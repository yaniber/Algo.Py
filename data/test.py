from gather import gather_ohlcv_binance, gather_ohlcv_indian_equity
from datetime import datetime, timedelta

if __name__=='__main__':
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5)
    gather_ohlcv_indian_equity(timeframe='15m', start_date=start_date)
    gather_ohlcv_binance(timeframe='15m', start_date=start_date)