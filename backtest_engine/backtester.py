import pandas as pd
from finstore.finstore import Finstore
from data.store.crypto_binance import store_crypto_binance
from data.store.indian_equity import store_indian_equity


class Backtester():
    
    def __init__(self,
                 market_name, 
                 symbol_list, 
                 pair,
                 timeframe, 
                 strategy_object, 
                 strategy_type,
                 start_date, 
                 end_date, 
                 init_cash, 
                 fees, 
                 slippage, 
                 size, 
                 cash_sharing,
                 allow_partial,
                 progress_callback
                 ) -> None:
        
        '''
        market_name : crypto_binance, indian_equity, str
        symbol_list : list of symbols to backtest for
        pair : optional , USDT , BTC only for crypto
        timeframe : 1y, 1m, 1d, 1h, 4h, etc
        strategy_object : initialized with strategy params
        strategy_type : single asset, multiple asset
        start_date, end_date : pd timestamp
        progress_callback : function with progress int, status text
        '''
        self.backtest()

    def backtest(self):

        ohlcv_data = self.data_fetch()
        entries, exits, close_data, open_data = self.strategy_object.run(ohlcv_data)
        import vectorbtpro as vbt
        pf = vbt.Portfolio.from_signals(
                close=close_data,
                open=open_data,
                entries=entries,
                exits=exits,
                direction='longonly',
                init_cash=self.init_cash,
                cash_sharing=True,
                size=0.01,  # Adjust the allocation per trade as needed
                size_type="valuepercent",
                fees=self.fees,
                slippage=self.slippage,
                allow_partial=self.allow_partial,
                sim_start=pd.Timestamp(self.start_date)
            )
        
        self.save_backtest(pf)
        
        return pf

    def data_fetch(self):
        finstore = Finstore(market_name=self.market_name, timeframe=self.timeframe, pair=self.pair)
        try:
            ohlcv_data = finstore.read.symbol_list(self.symbol_list)
            # TODO : check if ohlcv_data has data between start_date and end_date
            # Log how many symbols have data and how many don't , if no symbol has data then call fetch_new_data()
        except Exception as e: 
            print(f'Error with fetching ohlcv_data : {e}')
            ohlcv_data = self.fetch_new_data()
        
        return ohlcv_data
    
    def fetch_new_data(self):
        # TODO : calculate data points back using start date , end date and timeframe.
        if self.market_name == 'crypto_binance':
            store_crypto_binance(timeframe=self.timeframe, data_points_back=data_points, suffix=self.pair)
        elif self.market_name == 'indian_equity':
            store_indian_equity(timeframe=self.timeframe, data_points_back=data_points, complete_list=False)
        pass

    def save_backtest(self, pf):
        # TODO : save this potfolio object (it's not serializable so pickle or parquet the pf trade history or returns and other details)
        # save strategy params, and all other params that this backtester was initialized with (except for progress_callback, strategy_object input params)
        pass



if __name__ == '__main__':
    def dummy(progress_int, progress_status):
        print(f'Progress done : {progress_int}%')
        print(f'Progress status : {progress_status}')
    #Example usage
    Backtester(market_name='crypto_binance',
               symbol_list=['ETH/BTC'],
               pair='BTC',
               timeframe='1d',
               strategy_type='multi',
               start_date=pd.Timestamp.now() - pd.Timedelta(days=6),
               end_date=pd.Timestamp.now(),
               init_cash=10000,
               fees=0.00001,
               slippage=0.0002,
               size=0.1,
               cash_sharing=True,
               allow_partial=True,
               progress_callback=dummy)


