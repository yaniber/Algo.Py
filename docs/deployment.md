<!-- File: deployment.md -->
# Deployment

**Algo.Py** offers an intuitive one‑click deployment system for live trading.

## One‑Click Deployment Workflow

1. **Backtest and Save:**  
   Run and save your backtest to capture the strategy’s configuration and performance metrics.

2. **Navigate to the Deployment Dashboard:**  
   Open the **Strategy Deployment** page in the Streamlit dashboard.

3. **Load a Backtest (Optional):**  
   Use the **Load Backtest** button to auto‑populate deployment settings from a saved backtest.

4. **Configure Deployment Settings:**

   - **Scheduler:**  
     - *Fixed Interval:* Set the run interval (in minutes).  
     - *Specific Time:* Choose an execution time (with timezone).

   - **OMS (Order Management System):**  
     Select your OMS (e.g., Telegram, Zerodha, or Binance) and provide the required credentials.
     
   - **Additional Settings:**  
     Set initial cash, start date, trade size, cash sharing, and partial order options.

5. **Deploy:**  
   Click the **Deploy Strategy** button. A new process is spawned to handle live execution, and you can monitor its status, logs, and performance via the dashboard.

## Behind the Scenes

- A dedicated process is launched for deployment.
- The saved configuration is loaded and the OMS is initialized.
- A scheduler triggers data fetching, signal generation, and order execution.
- Deployment status and logs are continuously updated.
