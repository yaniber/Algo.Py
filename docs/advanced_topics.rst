.. _advanced_topics:

Advanced Topics
===============

This section delves into some of the more advanced features and concepts within the Algo.Py platform.

Footprint Charts
----------------

Footprint charts (also known as order flow charts) provide a detailed view of trading activity at each price level within a candlestick.  They visualize the *volume traded at each price*, distinguishing between buying and selling pressure. This gives traders a deeper understanding of market dynamics than traditional candlestick charts.

**Key Concepts:**

*   **Bid/Ask Volume:**  Footprint charts show the volume traded at the bid price (sellers hitting the bid) and the ask price (buyers lifting the offer).
*   **Imbalances:**  Significant differences between bid and ask volume at a particular price level can indicate strong buying or selling pressure.
*   **Point of Control (POC):** The price level with the highest traded volume within a candle.
*   **Volume Profile:** A histogram displayed alongside the footprint chart, showing the total volume traded at each price level.

**How to Use Footprint Charts in Algo.Py:**

1.  **Live Footprint Chart:** Navigate to the "Footprint Chart" page on the dashboard. This provides a live, updating view of the footprint for BTC/USDT on Binance.
2.  **Interpreting the Chart:**
    *   **Color Coding:** The heatmap uses a color scale (typically "icefire_r") to represent the balance between buying and selling.  "Redder" areas indicate more selling pressure, while "bluer" areas indicate more buying pressure.
    *   **Text Display:**  The chart displays the bid and ask volume at each price level.
    *   **Candlestick Lines:**  Traditional candlestick lines (open, high, low, close) are overlaid on the footprint for context.
    *   **Parameters Heatmap:**  A lower subplot displays a heatmap of various calculated parameters, such as delta, cumulative delta, and rate of change.

Depth of Market (DOM)
----------------------

The Depth of Market (DOM), also known as the order book, shows the list of outstanding buy and sell orders for a particular asset at different price levels.  It provides insights into market liquidity and potential price movements.

**Key Concepts:**

*   **Bid Orders:** Orders to buy the asset at a specific price or lower.
*   **Ask Orders:** Orders to sell the asset at a specific price or higher.
*   **Levels:**  The different price levels at which orders are placed.
*   **Liquidity:** The volume of orders available at each price level.  High liquidity generally indicates a tighter bid-ask spread and less price slippage.

**DOM Charts in Algo.Py:**

*   **Live DOM Chart:**  The "Live DOM Chart" page displays a real-time, updating DOM for BTC/USDT on Binance. It uses a heatmap visualization to highlight areas of high order volume, indicating potential support and resistance levels.
*   **Static DOM Chart**: The 'Static DOM Chart' displays a static version of DOM.

**How to use the DOM Chart:**

*   **Order Blocks:** The chart uses colored rectangles (order blocks) to represent the volume of orders at each price level.  The opacity of the rectangles indicates the relative strength of the order volume.
*   **Price Range:** You can adjust the price range displayed on the chart.
*   **Real-time Updates:** The chart updates automatically, reflecting changes in the order book.
*  **Trades:** The chart represents trades with bubbles, the size corresponds to trade volume and the color, direction.

Volume Bubbles
---------------

Volume bubbles are a visual representation of trade size, displayed on the chart alongside the price action. They appear in real time as trades are executed.

**Key Concepts:**

*   **Size:** The size of the bubble corresponds to the volume of the trade. Larger bubbles indicate larger trades.
*   **Color:**  Typically, green bubbles represent buy trades (market orders hitting the ask), and red bubbles represent sell trades (market orders hitting the bid).
*   **Real-time Updates:** Bubbles appear on the chart in real-time as trades occur.

**How to use Volume Bubbles:**

*   **Visualizing Trade Activity:** Bubbles provide a quick visual way to assess the size and direction of trades happening in the market.  Large bubbles can indicate significant buying or selling pressure.
* **Combining with DOM and Footprint:**  Volume bubbles are most effective when used in conjunction with the DOM and footprint charts, providing a comprehensive view of market activity.

Smart Order Execution (Limit Order Chaser)
-------------------------------------------

The Limit Order Chaser is a feature designed to improve the execution of limit orders, particularly in volatile markets. It dynamically adjusts the limit order price to increase the chances of getting filled, while still aiming to achieve a favorable price (i.e. acting as a 'maker').

**How it Works:**

1.  **Post-Only Orders:** The chaser uses "Post-Only" (maker-only) limit orders. These orders are only added to the order book and *never* take liquidity (i.e., they never execute at the market price). This helps avoid paying taker fees.

2.  **Price Adjustment:** The chaser starts by placing a limit order slightly better than the best bid (for sells) or best ask (for buys).

3.  **Monitoring and Cancellation:**  If the order doesn't get filled within a short interval, the chaser cancels the existing order.

4.  **Repricing:**  The chaser then places a *new* limit order, adjusting the price slightly closer to the market price (but still aiming to be a maker order).

5.  **Iteration:**  Steps 3 and 4 are repeated until the order is filled or a maximum number of retries is reached.

**Benefits:**

*   **Improved Fill Rate:** Increases the likelihood of getting your limit order filled, especially in fast-moving markets.
*   **Potential Price Improvement:** By starting with a more aggressive price and gradually adjusting, the chaser can potentially achieve a better execution price than a static limit order.
*   **Reduced Taker Fees:** By using Post-Only orders, the chaser helps minimize taker fees.

**Configuration:**

*   **`max_retries`:** The maximum number of times the chaser will attempt to adjust the order price.
*   **`interval`:** The time interval (in seconds) between each price adjustment attempt.
*   **`reduceOnly`:** (Used when closing positions) Ensures that the order can only reduce the size of an existing position, preventing accidental position increases.

The Limit Order Chaser is an advanced tool that can help optimize order execution, but it's important to understand its behavior and configure it appropriately for your trading strategy and risk tolerance.