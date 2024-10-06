import pandas as pd
from executor.monitor import TradeMonitor
from executor.constructor import construct_portfolio
import os
from dotenv import load_dotenv
from utils.notifier.telegram import send_telegram_message

def get_fresh_trades(ohlcv_data: pd.DataFrame, 
                     symbol_list: list, 
                     trade_monitor: TradeMonitor, 
                     sim_start : pd.Timestamp, 
                     sim_end : pd.Timestamp, 
                     weekday : int = 2,
                     init_cash : float = 100000):
    """
    Gets fresh buys and sells from the portfolio's trade history by utilizing the TradeMonitor class.

    Parameters
    ----------
    ohlcv_data : pd.DataFrame
        A DataFrame containing OHLCV data.
    
    symbol_list : list
        List of symbols to create the portfolio for.
    
    sim_start : pd.Timestamp
        Start date of the simulation.
    
    sim_end : pd.Timestamp
        End date of the simulation.
    
    trade_monitor : TradeMonitor
        An instance of the TradeMonitor class.
    
    Returns
    -------
    tuple (pd.DataFrame, pd.DataFrame)
        A tuple containing two DataFrames:
        - fresh_buys: DataFrame of fresh "Buy" trades.
        - fresh_sells: DataFrame of fresh "Sell" trades.
    """
    # Create the portfolio using the provided OHLCV data and symbol list
    portfolio = construct_portfolio(ohlcv_data=ohlcv_data, symbol_list=symbol_list, sim_start=sim_start, sim_end=sim_end, weekday=weekday, init_cash=init_cash)

    trade_history = portfolio.trade_history
    
    # Use TradeMonitor to get fresh buys and sells from the trade history
    fresh_buys, fresh_sells = trade_monitor.monitor_fresh_trades(trade_history)

    return fresh_buys, fresh_sells

def execute_trades_telegram(trades: pd.DataFrame):
    """
    Execute the trades in the trades DataFrame.
    """

    load_dotenv(dotenv_path='config/.env')
    token = os.getenv('TELEGRAM_TOKEN')
    group_id = os.getenv('TELEGRAM_GROUP_ID')

    if not trades.empty:
        # Create a detailed message with symbol names, side, size, and price
        trade_details = []
        for _, row in trades.iterrows():
            symbol = row['Column']
            side = row['Side']
            size = row['Size']
            price = row['Price']
            trade_details.append(f"Symbol: {symbol}, Side: {side}, Size: {size}, Price: {price}")
        
        trade_message = "\n".join(trade_details)
        
        # Send the trade execution message
        full_message = f"Executing {trades.shape[0]} trades:\n{trade_message}"
        send_telegram_message(message=full_message, token=token, chat_id=group_id)
    else:
        full_message = f"No trades to execute"
        send_telegram_message(message=full_message, token=token, chat_id=group_id)

def execute_trades_zerodha(trades: pd.DataFrame) -> tuple[list, list]:
    """
    Execute the trade in the trades DataFrame.

    Args:
        trades (pd.DataFrame): A DataFrame containing the trades to be executed. usually generated from vbt.
    
    Returns:
        tuple (list, list) : A tuple containing two lists:
        - successful_trades: list of successful trade details in dict.
        - failed_trades: list of failed trade details in dict.
    """
    from jugaad_trader import Zerodha
    import pyotp
    import json

    load_dotenv(dotenv_path='config/.env')
    userid = os.getenv('USER_ID')
    password = os.getenv('PASSWORD')
    totp = os.getenv('TOTP_SECRET')

    otp_gen = pyotp.TOTP(totp)
    kite = Zerodha(user_id=userid, password=password, twofa=otp_gen.now())
    kite.login()

    if not trades.empty:
        failed_trades = []
        successful_trades = []
        for _, row in trades.iterrows():
            symbol = row['Column']
            if '.NS' in symbol:
                symbol = symbol.replace('.NS', '')
            side = row['Side']
            size = int(row['Size'])
            price = float(row['Price'])

            try:
                order_id = kite.place_order(tradingsymbol=symbol,
                                exchange=kite.EXCHANGE_NSE,
                                transaction_type=kite.TRANSACTION_TYPE_BUY if side == 'Buy' else kite.TRANSACTION_TYPE_SELL,
                                quantity=size,
                                order_type=kite.ORDER_TYPE_MARKET,
                                    product=kite.PRODUCT_CNC,
                                    variety=kite.VARIETY_REGULAR)
            except Exception as e:
                failed_trades.append({'symbol': symbol, 'side': side, 'size': size, 'price': price, 'status': 'REJECTED', 'error': str(e), 'order_id': None, 'orders_df': json.dumps({})})
                continue
            
            orders = pd.DataFrame(kite.orders())

            status = orders[orders['order_id'] == order_id]['status'].values[0]

            if status == 'REJECTED':
                errmsg = orders[orders['order_id'] == order_id]['status_message'].values[0]
                failed_trades.append({'symbol': symbol, 'side': side, 'size': size, 'price': price, 'status': status, 'error': errmsg, 'order_id': order_id, 'orders_df': orders.to_json()})
            elif status == 'COMPLETE':
                fill_price = orders[orders['order_id'] == order_id]['average_price'].values[0]
                fill_quantity = orders[orders['order_id'] == order_id]['filled_quantity'].values[0]
                successful_trades.append({'symbol': symbol, 'side': side, 'size': size, 'price': price, 'status': status, 'fill_price': fill_price, 'fill_quantity': fill_quantity, 'order_id': order_id, 'orders_df': orders.to_json()})
        return successful_trades, failed_trades
    else:
        return [], []

def pipeline(sim_start, sim_end):
    from utils.db.fetch import fetch_entries
    from data.fetch.indian_equity import fetch_symbol_list_indian_equity
    
    market_name = 'indian_equity'
    timeframe = '1d'
    
    ohlcv_data = fetch_entries(market_name=market_name, timeframe=timeframe, all_entries=True)
    symbol_list = fetch_symbol_list_indian_equity(complete_list=False)

    trade_monitor = TradeMonitor()

    fresh_buys, fresh_sells = get_fresh_trades(ohlcv_data, symbol_list, trade_monitor, sim_start, sim_end)

    execute_trades_telegram(fresh_buys, fresh_sells)
    successful_trades, failed_trades = execute_trades_zerodha(fresh_buys, fresh_sells)

    return successful_trades, failed_trades

if __name__ == "__main__":
    sim_start = pd.Timestamp('2024-01-01')
    sim_end = pd.Timestamp('2024-01-31')
    fresh_buys, fresh_sells = pipeline(sim_start, sim_end)
    print(fresh_buys)
    print(fresh_sells)

