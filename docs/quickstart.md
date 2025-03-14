<!-- File: quickstart.md -->
# Quickstart Guide

This guide provides step-by-step instructions for performing a backtest, deploying a strategy, and using the different trading dashboards.

## Running a Backtest

1. **Start the Dashboard:**

   - After installation, open a terminal and run:
     
     '''bash
     docker exec -it algopy_app bash
     '''
   
   - [Recommended] Alternatively, if you use VS Code, install the Docker extension, navigate to Containers, right-click on `algopy_app`, and select **Attach Visual Studio Code**. This opens a new window attached to the container, eliminating the need to manually export ports and providing a perfect environment (including running Jupyter notebooks seamlessly).

   - Once inside the container (starting from the `/app` directory), launch the Streamlit application:
     
     '''bash
     streamlit run Dashboard/main_dash.py
     '''

   Open your browser (typically at [http://localhost:8501](http://localhost:8501)) and click on the **Strategy Backtest** link in the navigation.

2. **Configure the Backtest:**

   - **Timeframe:** Choose the timeframe (e.g., 1D, 4H, 1H).
   - **Strategy Module:** Select a module (e.g., "EMA Crossover Strategy").
   - **Asset Universe:** Search for and select assets (Crypto, Equities, etc.).
   - **Strategy Parameters:** Adjust settings specific to the chosen strategy.
   - **Backtest Settings:** Set start/end dates, initial capital, fees, and slippage.

3. **Run the Backtest:**

   Click the **🚀 Run Backtest** button. A progress bar will indicate the process. Upon completion, you will see detailed performance statistics, interactive charts (including equity curve, cumulative returns, and trade history), and generated signals.

4. **Save the Backtest:**

   Enter a filename and click the **💾 Save Portfolio** button. The configuration and results will be saved for later deployment.

## Deploying a Strategy [Beta]

> **Warning:** This is an early-stage deployment feature. It is not recommended to use with real money. Instead, use it in a sandbox or low-capital environment to validate your strategy. **Algo.Py** is not responsible for any financial losses incurred.

1. **Navigate to the Deployment Dashboard:**

   From the Dashboard sidebar, go to the **Strategy Deployment** section.

2. **Load a Backtest (Optional):**

   On the **Strategy Backtest** page, use the **Load Previous Backtest** section to select a saved backtest. Most deployment settings will auto-populate, though you will still need to select an OMS type and configure its settings.

3. **Configure Deployment Parameters:**

   - **Strategy:** Select your strategy.
   - **Strategy Parameters:** Adjust as needed.
   - **Market Configuration:** Choose the market (e.g., `crypto_binance`, `indian_equity`) and the timeframe.
   - **Asset Universe:** Select the assets you wish to trade.
   - **Order Management (OMS):** Choose between Telegram, Zerodha, or Binance:
     - **Telegram:** Provide your bot token and chat ID.
     - **Zerodha:** Provide your User ID, Password, and TOTP secret.
     - **Binance:** Provide your API key and secret.
   - **Scheduler Configuration:** Choose one:
     - **Fixed Interval:** Define the interval (in minutes).
     - **Specific Time:** Set a daily execution time (with timezone).
   - **Additional Settings:** Configure initial cash, start date, trade size, cash sharing, and partial order settings.

4. **Deploy:**

   Click the **Deploy Strategy** button. The deployment process will start, and you can monitor its status in the **Active Deployments** section.

## Order Management System

Manage your positions in an advanced manner using the Order Management System (OMS). You can choose between Limit Orders and Market Orders.

### Limit Orders

- **Parameters:**
  - **Price:** Specify the order price.
  - **Quantity:** Define the amount.
  - **Quantity Type:** Choose between contracts (e.g., 0.001 BTC to represent 0.001 BTC) or USD (e.g., 100 USD worth of BTC).
  - **Order Side:** Select Buy or Sell.
  - **Leverage:** Set your desired leverage.
- Click **Place Order** to execute.

### Market Orders

- **Parameters:** Similar to Limit Orders, but without the price field.
- **Limit Order Chaser:** An additional feature that:
  - Places limit orders at the closest available price in the order book.
  - Continuously adjusts (“chases”) the market price until the order is filled.
  
  This is beneficial because platforms like Binance and Bybit often charge higher fees for market orders compared to limit orders. The Limit Order Chaser helps reduce fees by ensuring orders fill as limit orders.

## Orderbook Heatmap

This tool visualizes resting orders in the order book as yellow boxes. The darker the yellow, the higher the quantity at that price level. Additionally, executing orders are displayed as bubbles, where a larger bubble indicates a greater order size. Use this tool to identify iceberg orders or bot-driven orders.

## Footprint Chart

The Footprint Chart offers a detailed view of order flow, featuring:
- Deltas
- Volume point-of-control (POC)
- Volume bars for each candle
- Rate of Change (ROC)
  
This chart enables enhanced analysis of market order flow for more informed decision-making.
