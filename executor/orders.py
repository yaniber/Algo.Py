from strategy.private.stocks_on_the_move import stocks_on_the_move
import vectorbt as vbt


def get_latest_orders(open_positions, portfolio):
    
    buy_orders = []
    sell_orders = []
    trade_history = portfolio.trade_history  
    # Ensure 'Creation Index' does not contain NaT values
    trade_history = trade_history.dropna(subset=['Creation Index'])
    
    if trade_history.empty:
        return buy_orders, sell_orders
    
    # Filter trades for the current date
    todays_trades = trade_history[trade_history['Creation Index'].max()]
        
    for _, trade in todays_trades.iterrows():
            order = {
                'Order Id': trade['Order Id'],
                'Creation Index': trade['Creation Index'],
                'Column': trade['Column'],
                'Size': trade['Size'],
                'Price': trade['Price'],
                'Fees': trade['Fees'],
                'PnL': trade['PnL'],
                'Return': trade['Return'],
                'Direction': trade['Direction'],
                'Status': trade['Status'],
                'Entry Trade Id': trade['Entry Trade Id'],
                'Exit Trade Id': trade['Exit Trade Id'],
                'Position Id': trade['Position Id']
            }
            
            symbol = trade['Column']
            
            if trade['Side'] == 'Buy' and trade['Status'] == 'Open':
                if symbol not in open_positions:
                    buy_orders.append(order)
                    open_positions[symbol] = order
                    print(f"Queued Buy Order: {order}")
            elif trade['Side'] == 'Sell' and trade['Status'] == 'Closed':
                if symbol in open_positions:
                    sell_orders.append(order)
                    open_positions.pop(symbol)
                    print(f"Queued Sell Order: {order}")

    # Output the queued orders
    print("Buy Orders:", buy_orders)
    print("Sell Orders:", sell_orders)
    return buy_orders, sell_orders