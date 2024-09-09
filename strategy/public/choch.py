import pandas as pd
import pandas_ta as ta
import numpy as np
import plotly.graph_objects as go
from scipy import stats

import os
os.chdir('C:\\Users\\Himanshu\\Desktop\\QuantiPy')
print(os.getcwd())
from utils.db.fetch import fetch_entries

class PatternDetector:
    def __init__(self, market_name='indian_equity', asset_name='^NSEI', timeframe='1d', window=5, backcandles=40, pivot_window=6, volume_filter=True):
        self.market_name = market_name
        self.asset_name = asset_name
        self.timeframe = timeframe
        self.window = window
        self.backcandles = backcandles
        self.pivot_window = pivot_window
        self.volume_filter = volume_filter
        self.df = self.load_data()
        self.df['isPivot'] = self.df.apply(lambda x: self.isPivot(x.name), axis=1)
        self.df['pointpos'] = self.df.apply(lambda row: self.pointpos(row), axis=1)
        self.df['pattern_detected'] = self.df.index.map(lambda x: self.detect_structure(x))

    def load_data(self):
        df = fetch_entries(market_name=self.market_name, timeframe=self.timeframe, all_entries=True)
        df = df[self.asset_name]
        if self.volume_filter:
            df = df[df['volume'] != 0]
        df.reset_index(drop=True, inplace=True)
        return df

    def isPivot(self, candle):
        if candle - self.window < 0 or candle + self.window >= len(self.df):
            return 0

        pivotHigh = 1
        pivotLow = 2
        for i in range(candle - self.window, candle + self.window + 1):
            if self.df.iloc[candle].low > self.df.iloc[i].low:
                pivotLow = 0
            if self.df.iloc[candle].high < self.df.iloc[i].high:
                pivotHigh = 0
        if pivotHigh and pivotLow:
            return 3
        elif pivotHigh:
            return pivotHigh
        elif pivotLow:
            return pivotLow
        else:
            return 0

    def pointpos(self, x):
        if x['isPivot'] == 2:
            return x['low'] - 1e-3
        elif x['isPivot'] == 1:
            return x['high'] + 1e-3
        else:
            return np.nan

    def detect_structure(self, candle):
        localdf = self.df[candle - self.backcandles - self.pivot_window:candle - self.pivot_window]
        highs = localdf[localdf['isPivot'] == 1].high.tail(3).values
        idxhighs = localdf[localdf['isPivot'] == 1].high.tail(3).index
        lows = localdf[localdf['isPivot'] == 2].low.tail(3).values
        idxlows = localdf[localdf['isPivot'] == 2].low.tail(3).index

        pattern_detected = False
        msb_high = None
        last_lower_low = None

        if len(highs) == 3 and len(lows) == 3:
            order_condition = (idxlows[0] < idxhighs[0] < idxlows[1] < idxhighs[1] < idxlows[2] < idxhighs[2])
            pattern_condition = (lows[0] < highs[0] and
                                 lows[1] < lows[0] and
                                 highs[1] < highs[0] and
                                 lows[2] < lows[1] and
                                 highs[2] > highs[1])

            if order_condition and pattern_condition:
                pattern_detected = True
                msb_high = highs[2]
                last_lower_low = lows[2]

        if pattern_detected:
            self.draw_fibonacci(last_lower_low, msb_high, candle)

        return 1 if pattern_detected else 0

    def draw_fibonacci(self, low, high, candle):
        fib_levels = [0.618, 0.65, 0.786]
        golden_zone = [low + (high - low) * level for level in fib_levels]
        buy_zone = (golden_zone[0], golden_zone[1])
        sell_zone = (golden_zone[1], golden_zone[2])
        stop_loss = (golden_zone[0] + golden_zone[1]) / 2

        print(f"Buy Zone: {buy_zone}, Sell Zone: {sell_zone}, Stop Loss: {stop_loss}")

        # Define the range to plot around the detected candle
        start = max(0, candle - 50)
        end = min(len(self.df), candle + 50)
        dfpl = self.df[start:end]

        # Plotting the Fibonacci levels on the chart
        fig = go.Figure(data=[go.Candlestick(x=dfpl.index,
                                             open=dfpl['open'],
                                             high=dfpl['high'],
                                             low=dfpl['low'],
                                             close=dfpl['close'])])

        # Add horizontal lines for Fibonacci levels
        for level, name, color in zip(golden_zone, ["Buy Zone Start", "Buy Zone End", "Sell Zone End"], ['green', 'green', 'red']):
            fig.add_hline(y=level, line=dict(color=color), annotation_text=name, annotation_position="top right")

        fig.add_hline(y=stop_loss, line=dict(color='blue'), annotation_text="Stop Loss", annotation_position="top right")

        fig.update_layout(xaxis_rangeslider_visible=False)
        fig.show()

    def get_detected_patterns(self):
        return self.df[self.df['pattern_detected'] != 0]

    def plot_detected_patterns(self):
        detected_patterns = self.get_detected_patterns()
        for idx in detected_patterns.index:
            start = max(0, idx - 70)
            end = min(len(self.df), idx + 30)
            dfpl = self.df[start:end]
            fig = go.Figure(data=[go.Candlestick(x=dfpl.index,
                                                 open=dfpl['open'],
                                                 high=dfpl['high'],
                                                 low=dfpl['low'],
                                                 close=dfpl['close'])])
            fig.add_scatter(x=dfpl.index, y=dfpl['pointpos'], mode="markers",
                            marker=dict(size=15, color="MediumPurple"),
                            name="pivot")
            fig.update_layout(xaxis_rangeslider_visible=False)
            fig.show()

# Example usage:
detector = PatternDetector()
detector.plot_detected_patterns()
