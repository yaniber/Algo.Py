<!-- File: features.md -->
# Features Overview

**Algo.Py** is a comprehensive algorithmic trading platform that covers every stage from strategy development and backtesting to live deployment.

## Key Features

### Backtesting & Deployment
- **Vectorized Backtesting:** Uses the `vectorbtpro` library for fast historical testing.
- **Detailed Metrics:** Computes total return, Sharpe ratio, Sortino ratio, maximum drawdown, win rate, profit factor, and more.
- **Interactive Charts:** Displays interactive Plotly charts including equity curves and cumulative returns.
- **One‑Click Deployment:** Seamlessly transition from backtesting to live trading.

### Strategy Development
- **Modular Design:** Build strategies on a consistent structure.
- **Automatic Registration:** Strategies in the `strategy/public` directory are auto‑registered.
- **Parameter Exposure:** Strategy parameters are automatically made configurable in dashboards.
- **Built‑in Indicators:** Pre‑built indicators (EMA, Supertrend, RSI, etc.) plus support for custom indicators.
- **Multi‑Asset Support:** Run strategies on multiple assets simultaneously.

### Custom Data Layer (FinStore)
- **Organized Storage:** Data is categorized by market and timeframe.
- **Efficient Format:** Leverages Parquet for compact, fast data storage.
- **Incremental Updates:** Easily add new data without overwriting previous files.
- **Caching:** Uses integrated caching to boost performance.

### Multi‑Broker & Market Support
- **Market Versatility:** Supports both cryptocurrency (Binance) and Indian equities.
- **Extensible Architecture:** Easily integrate additional markets and data sources.
- **Timeframe Flexibility:** Operates across various timeframes (1m, 5m, 15m, 1h, 4h, 1d).

### Order and Risk Management
- **OMS Integration:** Connects with multiple order management systems (Telegram, Zerodha, Binance).
- **Automated Order Execution:** Executes trades automatically based on strategy signals.
- **Risk Tools:** Provides basic risk management features such as position sizing and cash sharing.

### Live Trading Dashboards
- **Streamlit Based:** User-friendly, real-time dashboards.
- **Visual Tools:** Features live DOM charts, footprint charts, and more.
- **AI Enhancements:** Upcoming features include an AI Trading Journal and AI backtesting agent.
