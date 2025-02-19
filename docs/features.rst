.. _features:

Features
========

Algo.Py is a comprehensive algorithmic trading platform with the following key features:

🚀 Backtesting & Deployment
--------------------------

*   **Vectorized Backtesting:**  Uses the `vectorbtpro` library for fast and efficient backtesting on historical data.
*   **Detailed Performance Metrics:** Calculates a wide range of performance metrics, including total return, Sharpe ratio, Sortino ratio, maximum drawdown, win rate, profit factor, and more.
*   **Interactive Charts:** Visualizes backtest results with interactive Plotly charts, including equity curves, cumulative returns, drawdowns, and trade history.
*   **One-Click Deployment:** Seamlessly deploy backtested strategies to live trading with a single click.  The platform handles scheduling, data fetching, signal generation, and order execution.
*   **Deployment Management:** Monitor and manage active deployments, view logs, and stop deployments as needed.

🧠 Algorithmic Strategy Development
----------------------------------

*   **Modular Strategy Design:** Create custom strategies by inheriting from the `StrategyBaseClass`, providing a consistent structure and simplifying development.
*   **Strategy Registry:** A built-in registry automatically discovers and makes available strategies in the `strategy/public` directory.
*   **Parameterization:**  Define strategy parameters within the `__init__` method. These parameters are automatically exposed in the backtesting and deployment dashboards for easy configuration.
*   **Technical Indicators:** Includes pre-built, optimized technical indicators (EMA, Supertrend, RSI, etc.).  Easily create custom indicators.
*   **Multi-Asset Support:** Strategies can operate on multiple assets simultaneously.

📊 Custom Data Layer (FinStore)
--------------------------------

*   **Organized Data Storage:**  Data is organized by market (e.g., `crypto_binance`, `indian_equity`) and timeframe (e.g., `1d`, `4h`), stored in the efficient Parquet format within the `database/finstore` directory.
*   **Data Fetching:** Provides functions for fetching historical data from various sources (currently Binance and Indian equity data).
*   **Data Gathering:** Includes utilities to gather OHLCV data.
*   **Data Updates:** Supports incremental updates to ensure data is up-to-date.
*   **Finstore API:** A simple and consistent API (`Finstore`) for reading and writing data.
*   **Caching**: Integrated caching using `diskcache`

🌍 Multi-Broker & Market Support
--------------------------------

*   **Multiple Markets:** Supports Cryptocurrency (Binance) and Indian Equities.
*   **Extensible:** Designed for easy extension to support additional markets and data sources.
*   **Multiple Timeframes:** Supports various timeframes (1m, 5m, 15m, 1h, 4h, 1d).

🤖 OMS (Order Management System) & RMS (Risk Management System)
--------------------------------------------------------------

*   **Pluggable OMS:** Integrates with multiple order management systems:
    *   **Telegram:** Send trade signals via Telegram.
    *   **Zerodha:** Full integration with the Zerodha trading platform.
    *   **Binance:** Support for spot and futures trading on Binance.
*   **Automated Order Execution:** Automatically executes trades based on generated signals.
*   **Basic Risk Management:** Includes features like position sizing and cash sharing.

📈 Live Trading Dashboards
--------------------------

*   **Streamlit Integration:** Provides a user-friendly web-based dashboard built with Streamlit.
*   **Multiple Dashboards:**
    *   **Strategy Backtest:** Configure and run backtests.
    *   **Strategy Deployment:** Deploy and manage live strategies.
    *   **Strategy Monitor:** Track live performance.
    *   **Live DOM Chart:** Real-time depth-of-market visualization.
    *   **Static DOM Chart:** Snapshot of the order book.
    *   **Footprint Chart:** Advanced order flow visualization.
    *   **AI Order Manager:** Autonomous trading agent.
    *   **Order Management System:** Manually place orders, manage positions.
    *   **Risk Management System:** Monitor portfolio risk.
    *   **Data Utilities:** Fetch, view, and manage data.
*   **Real-time Updates:** Dashboards update in real-time.