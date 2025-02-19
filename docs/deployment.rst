
One-Click Deployment
====================

Algo.Py provides a streamlined one-click deployment feature, allowing you to transition from backtesting to live trading with minimal effort. This is achieved through a tight integration of the backtesting engine, strategy configuration, and order management system (OMS).

Deployment Workflow
-------------------

1.  **Backtest and Save:**  Develop and thoroughly backtest your strategy.  Once you're satisfied with the performance, save the backtest.  This creates a snapshot of the strategy, its parameters, and the backtest results.

2.  **Navigate to Deployment Dashboard:** Go to the "Strategy Deployment" page in the Streamlit application.

3.  **Load Backtest (Optional):** Click the "Load Backtest" button and select the saved backtest you want to deploy.  This automatically populates the deployment configuration with the backtest settings, including:

    *   Strategy
    *   Parameters
    *   Market
    *   Timeframe
    *   Asset Universe
    *   Initial cash (optional).
    *   Size (optional).

4.  **Configure Deployment Settings:**

    *   **Scheduler:** Choose how often the strategy should run.
        *   `Fixed Interval`: Specify an interval in minutes (e.g., run every 60 minutes).
        *   `Specific Time`:  Set a specific time of day for execution (e.g., run daily at 9:30 AM).
        *   Set the start and end time of the simulation.
    *   **OMS (Order Management System):** Select your preferred broker/exchange integration (e.g., Telegram, Zerodha, Binance). You'll need to configure the API keys and other credentials for your chosen OMS in the `config/.env` file.
    *  Additional deployment settings can be configured as well.

5.  **Deploy:** Click the "Deploy Strategy" button.

Behind the Scenes
------------------

When you click "Deploy Strategy," the following steps occur:

1.  **Process Creation:** A new, independent process is spawned for the deployment. This ensures that the live trading strategy runs in isolation and doesn't interfere with the Streamlit dashboard or other deployments.
2.  **Configuration Loading:** The deployment process loads the saved strategy configuration (either from the loaded backtest or from the manually configured settings).
3.  **OMS Initialization:** The selected OMS (e.g., `Binance`, `Zerodha`, `Telegram`) is initialized with the provided credentials.
4.  **Scheduler Setup:** A scheduler is set up based on your chosen configuration (fixed interval or specific time).
5.  **Data Fetching:** At each scheduled run, the strategy fetches the latest market data from FinStore.
6.  **Signal Generation:** The strategy's `run` method is executed, generating entry and exit signals.
7.  **Order Execution:** The generated signals are translated into orders and sent to the OMS for execution.
8.  **Monitoring:** The deployment manager keeps track of the running process, its status, and logs.
9. **Data Gap Handling:** The `fill_gap` utility function is invoked to ensure that any missing data points are handled.

Deployment Management
---------------------

The "Strategy Deployment" dashboard also provides tools for managing your active deployments:

*   **Status Monitoring:** A table displays the status of all deployments, including a unique ID, PID, start time, associated strategy, and current status (running, stopped, error).
*   **Log Viewing:** You can view real-time logs for each deployment, providing insights into the strategy's operation and any potential issues.
*   **Stopping Deployments:** A "Stop" button allows you to terminate a running deployment.
*   **Clearing Deployments:** You can easily clear all stopped deployments.

This one-click deployment system significantly simplifies the process of moving from strategy development and backtesting to live trading, providing a robust and user-friendly experience.