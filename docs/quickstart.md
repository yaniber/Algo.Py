<!-- File: quickstart.md -->
# Quickstart Guide

This guide provides step-by-step instructions to perform a backtest, deploy a strategy, and use the live trading dashboard.

## Running a Backtest

1. **Start the Dashboard:**

   - If you have Docker installed, run:

     ```bash
     docker-compose up -d
     ```

   - If you have a Python environment set up, use the installation steps. Then, from the project’s root directory, start the Streamlit application:

     ```bash
     streamlit run Dashboard/main_dash.py
     ```

   Open your browser (typically at [http://localhost:8501](http://localhost:8501)) and click on the **Strategy Backtest** link in the navigation.

2. **Configure the Backtest:**

   - **Timeframe:** Choose the timeframe (e.g., 1D, 4H, 1H).
   - **Strategy Module:** Select a module (e.g., "EMA Crossover Strategy").
   - **Asset Universe:** Search and select assets (Crypto, Equities, etc.).
   - **Strategy Parameters:** Adjust parameters specific to the strategy.
   - **Backtest Settings:** Set start/end dates, initial capital, fees, and slippage.

3. **Run the Backtest:**

   Click the **🚀 Run Backtest** button. A progress bar shows the process. When complete, detailed performance stats, interactive charts (equity curve, cumulative returns, trade history), and signals are displayed.

4. **Save the Backtest:**

   Enter a filename and click the **💾 Save Portfolio** button. The configuration and results are saved for later deployment.

## Deploying a Strategy

1. **Start the Dashboard:**

   Launch the Streamlit dashboard as above.

2. **Navigate to the Deployment Dashboard:**

   Click the **Strategy Deployment** link.

3. **Load a Backtest (Optional):**

   On the **Strategy Backtest** page, use the **Load Previous Backtest** section to select a saved backtest. Most deployment settings will auto-populate (you’ll still need to select an OMS type and configure its settings).

4. **Configure Deployment Parameters:**

   - **Strategy:** Select your strategy.
   - **Strategy Parameters:** Adjust as needed.
   - **Market Configuration:** Choose the market (e.g., `crypto_binance`, `indian_equity`) and timeframe.
   - **Asset Universe:** Select assets.
   - **Order Management (OMS):** Choose between Telegram, Zerodha, or Binance:
     - **Telegram:** Provide bot token and chat ID.
     - **Zerodha:** Provide User ID, Password, and TOTP secret.
     - **Binance:** Provide API key and secret.
   - **Scheduler Configuration:** Pick one:
     - **Fixed Interval:** Define the interval (in minutes).
     - **Specific Time:** Set a daily execution time (with timezone).
   - **Additional Settings:** Configure initial cash, start date, trade size, cash sharing, and partial orders.

5. **Deploy:**

   Click the **Deploy Strategy** button. The deployment process will start, and you can monitor its status in the **Active Deployments** section.
