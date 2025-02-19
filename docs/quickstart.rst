.. _quickstart:

Quickstart Guide
================

This guide provides step-by-step instructions on how to perform a backtest, deploy a strategy, and use the live trading dashboard.

Running a Backtest
-------------------

1.  **Start the Dashboard:**

    If you have docker installed, run : 

    .. code-block:: bash

        docker-compose up -d

    If you have python environment setup , follow steps in installation.

    From the project's root directory, start the Streamlit application:

    .. code-block:: bash

        streamlit run Dashboard/main_dash.py

    Open your web browser and go to the URL provided by Streamlit (usually `http://localhost:8501`).  Click on the "Strategy Backtest" link in the navigation.

2.  **Configure the Backtest:**

    *   **Timeframe:** Select the desired timeframe for the backtest (e.g., 1D, 4H, 1H).
    *   **Strategy Module:** Choose a strategy module (e.g., "EMA Crossover Strategy").
    *   **Asset Universe:** Select the assets you want to include in your backtest (e.g., Crypto, Equities).  You can search and select multiple assets.
    *   **Strategy Parameters:** Adjust the parameters specific to the selected strategy (e.g., EMA periods).
    *   **Backtest Settings:** Set the start and end dates, initial capital, trading fees, and slippage.

3.  **Run the Backtest:**

    Click the "🚀 Run Backtest" button.  A progress bar will show the backtesting progress. Once complete, detailed performance statistics, charts (equity curve, cumulative returns, trade history), and trade signals will be displayed.

4.  **Save the Backtest:**

    Enter a filename and click the "💾 Save Portfolio" button.  The backtest results and configuration will be saved for later use (e.g., for deployment).

Deploying a Strategy
---------------------

1.  **Start the Dashboard:**

    Start the streamlit dashboard as described above.

2.  **Navigate to the Deployment Dashboard:**

    Click on the "Strategy Deployment" link in the navigation.

3.  **Load a Backtest (Optional):**

    You can load a previously saved backtest by going to the "Strategy Backtest" page, navigating to the "Load Previous Backtest" section, and selecting the backtest you saved. This will automatically populate *most* of the deployment settings.  You will still need to select an `OMS Type` and configure its settings.

4.  **Configure Deployment Parameters:**

    The deployment dashboard allows you to configure the following:

    *   **Strategy:** Select the strategy you want to deploy.
    *   **Strategy Parameters:** Adjust any strategy-specific parameters.
    *   **Market Configuration:**  Select the market (e.g., `crypto_binance`, `indian_equity`) and timeframe.
    *   **Asset Universe:** Select the assets to trade.
    *   **Order Management (OMS):** Choose your order management system (Telegram, Zerodha, or Binance).
        *   **Telegram:** Provide your bot token and chat ID.
        *   **Zerodha:** Enter your User ID, Password, and TOTP secret.
        *   **Binance:** Enter your API key and secret.
    *   **Scheduler Configuration:** Select the schedule type:
        *   **Fixed Interval:**  Specify how often the strategy should run (in minutes).
        *   **Specific Time:**  Set a specific time of day (and timezone) for the strategy to run.
    *   **Additional Deployment Settings:** Configure:
        *   **Initial Cash:** The starting capital for the live deployment.
        *    **Start Date:** Set the start date for the deployment.
        *   **Size:** Set the size of each trade, can be changed in settings.
        *   **Cash Sharing:**  Enable or disable cash sharing between multiple assets.
        *   **Allow Partial:** Enable/Disable partial orders.

5.  **Deploy:**  Click the "Deploy Strategy" button.  A new deployment process will be launched, and its status will be displayed in the "Active Deployments" section of the dashboard.

Using the Live Trading Dashboard
--------------------------------

The live trading dashboard provides several pages for monitoring market data and strategy performance:

*   **Live DOM Chart:**  Displays a real-time depth-of-market (DOM) chart for BTC/USDT, with order book levels visualized as a heatmap and trade executions shown as bubbles.
*   **Static DOM Chart:** Shows the DOM.
*   **Footprint Chart:**  Provides a detailed view of order flow, including bid/ask volume at each price level.
*   **Strategy Monitor:** Tracks the live performance of a selected strategy, showing confidence scores and charts for the top-performing assets.
*   **AI Order Manager:**  An autonomous trading agent that uses AI to generate and execute trading signals.
*   **Order Management System:** A dashboard for manually placing orders, managing positions, and viewing account information (currently supports Binance).
*   **Risk Management System:** A dashboard for monitoring overall portfolio risk and setting emergency controls (e.g., a "kill switch" to close all positions).
*  **Data Utils:** Fetch, view and manage market data.

Each dashboard page has its own specific controls and settings, usually located in a sidebar.