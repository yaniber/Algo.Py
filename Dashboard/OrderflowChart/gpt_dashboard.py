import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import asyncio
import websockets
import datetime
import threading
import queue
import time
import json
import random
import string

###############################################
# 1) THE SAME "OrderFlowChart" CLASS AS YOURS
###############################################
class OrderFlowChart():
    def __init__(self, orderflow_data, ohlc_data, identifier_col=None, imbalance_col=None, **kwargs):
        if 'data' in kwargs:
            try:
                self.use_processed_data(kwargs['data'])
            except:
                raise Exception("Invalid data structure found. Please provide a valid processed data dictionary.")
        else:
            self.orderflow_data = orderflow_data
            self.ohlc_data = ohlc_data
            self.identifier_col = identifier_col
            self.imbalance_col = imbalance_col
            self.is_processed = False
            # Approximate "granularity" from the first two price rows
            # to replicate your existing code
            self.granularity = abs(
                self.orderflow_data.iloc[0]['price'] - 
                self.orderflow_data.iloc[1]['price']
            )

    def generate_random_string(self, length):
        letters = string.ascii_letters
        return ''.join(random.choice(letters) for _ in range(length))

    def create_identifier(self):
        # If no candle identifiers exist, create them
        identifier = [self.generate_random_string(5) for _ in range(self.ohlc_data.shape[0])]
        self.ohlc_data['identifier'] = identifier
        self.orderflow_data.loc[:, 'identifier'] = self.ohlc_data['identifier']
        
    def create_sequence(self):
        self.ohlc_data['sequence'] = self.ohlc_data[self.identifier_col].str.len()
        self.orderflow_data['sequence'] = self.orderflow_data[self.identifier_col].str.len()

    def calc_imbalance(self, df):
        df['sum'] = df['bid_size'] + df['ask_size']
        df['time'] = df.index.astype(str)
        bids, asks = [], []
        for b, a in zip(df['bid_size'].astype(int).astype(str),
                        df['ask_size'].astype(int).astype(str)):
            dif = 4 - len(a)
            a = a + (' ' * dif)
            dif = 4 - len(b)
            b = (' ' * dif) + b
            bids.append(b)
            asks.append(a)

        # Overwrite index with 'identifier'
        df['text'] = pd.Series(bids, index=df.index) + '  ' + pd.Series(asks, index=df.index)
        df.index = df['identifier']
        
        if self.imbalance_col is None:
            print("Calculating imbalance, as no imbalance column was provided.")
            df['size'] = (df['bid_size'] - df['ask_size'].shift().bfill()) / (
                df['bid_size'] + df['ask_size'].shift().bfill()
            )
            df['size'] = df['size'].ffill().bfill()
        else:
            print(f"Using imbalance column: {self.imbalance_col}")
            df['size'] = df[self.imbalance_col]
            df = df.drop([self.imbalance_col], axis=1)
        return df

    def annotate(self, df2):
        df2 = df2.drop(['size'], axis=1)
        df2['sum'] = df2['sum'] / df2.groupby(df2.index)['sum'].transform('max')
        df2['text'] = ''
        df2['time'] = df2['time'].astype(str)
        df2['text'] = ['█' * int(s * 10) for s in df2['sum']]
        df2['text'] = '                    ' + df2['text']
        df2['time'] = df2['time'].astype(str)
        return df2

    def range_proc(self, ohlc, type_='hl'):
        if type_ == 'hl':
            seq = pd.concat([ohlc['low'], ohlc['high']])
        elif type_ == 'oc':
            seq = pd.concat([ohlc['open'], ohlc['close']])
        id_seq = pd.concat([ohlc['identifier'], ohlc['identifier']])
        seq_hl = pd.concat([ohlc['sequence'], ohlc['sequence']])
        seq = pd.DataFrame(seq, columns=['price'])
        seq['identifier'] = id_seq
        seq['sequence'] = seq_hl
        seq['time'] = seq.index
        seq = seq.sort_index()
        seq = seq.set_index('identifier')
        return seq

    def candle_proc(self, df):
        df = df.sort_values(by=['time', 'sequence', 'price'])
        df = df.reset_index()
        df_dp = df.iloc[1::2].copy()
        df = pd.concat([df, df_dp])
        df = df.sort_index()
        df = df.set_index('identifier')
        df = df.sort_values(by=['time', 'sequence'])
        df[2::3] = np.nan
        return df

    def calc_params(self, of, ohlc):
        delta = of.groupby(of['identifier']).sum()['ask_size'] - \
            of.groupby(of['identifier']).sum()['bid_size']
        delta = delta[ohlc['identifier']]
        cum_delta = delta.rolling(10).sum()
        roc = (cum_delta.diff()/cum_delta.shift(1) * 100).fillna(0).round(2)
        volume = of.groupby(of['identifier']).sum()['ask_size'] + of.groupby(of['identifier']).sum()['bid_size']

        delta_df = pd.DataFrame(delta, columns=['value'])
        delta_df['type'] = 'delta'
        cum_delta_df = pd.DataFrame(cum_delta, columns=['value'])
        cum_delta_df['type'] = 'cum_delta'
        roc_df = pd.DataFrame(roc, columns=['value'])
        roc_df['type'] = 'roc'
        volume_df = pd.DataFrame(volume, columns=['value'])
        volume_df['type'] = 'volume'

        labels = pd.concat([delta_df, cum_delta_df, roc_df, volume_df])
        labels = labels.sort_index()
        labels['text'] = labels['value'].astype(str)
        labels['value'] = np.tanh(labels['value'])
        return labels

    def plot_ranges(self, ohlc):
        ymin = ohlc['high'][-1] + 1
        ymax = ymin - int(48*self.granularity)
        xmax = ohlc.shape[0]
        xmin = xmax - 9
        tickvals = list(ohlc['identifier'])
        ticktext = list(ohlc.index)
        return ymin, ymax, xmin, xmax, tickvals, ticktext

    def process_data(self):
        if self.identifier_col is None:
            self.identifier_col = 'identifier'
            self.create_identifier()

        self.create_sequence()
        self.df = self.calc_imbalance(self.orderflow_data)
        self.df2 = self.annotate(self.df.copy())

        self.green_id = self.ohlc_data.loc[self.ohlc_data['close'] >= self.ohlc_data['open']]['identifier']
        self.red_id = self.ohlc_data.loc[self.ohlc_data['close'] < self.ohlc_data['open']]['identifier']

        self.high_low = self.range_proc(self.ohlc_data, type_='hl')
        self.green_hl = self.high_low.loc[self.green_id]
        self.green_hl = self.candle_proc(self.green_hl)

        self.red_hl = self.high_low.loc[self.red_id]
        self.red_hl = self.candle_proc(self.red_hl)

        self.open_close = self.range_proc(self.ohlc_data, type_='oc')
        self.green_oc = self.open_close.loc[self.green_id]
        self.green_oc = self.candle_proc(self.green_oc)
        self.red_oc = self.open_close.loc[self.red_id]
        self.red_oc = self.candle_proc(self.red_oc)

        self.labels = self.calc_params(self.orderflow_data, self.ohlc_data)
        self.is_processed = True

    def plot(self, return_figure=False):
        if not self.is_processed:
            self.process_data()

        ymin, ymax, xmin, xmax, tickvals, ticktext = self.plot_ranges(self.ohlc_data)
        print("Total candles: ", self.ohlc_data.shape[0])

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                            vertical_spacing=0.0, row_heights=[9, 1])

        # 1) VolumeProfile / text blocks
        fig.add_trace(go.Scatter(
            x=self.df2['identifier'],
            y=self.df2['price'],
            text=self.df2['text'],
            name='VolumeProfile',
            textposition='middle right',
            textfont=dict(size=8, color='rgb(0, 0, 255, 0.0)'),
            hoverinfo='none',
            mode='text',
            showlegend=True
        ), row=1, col=1)

        # 2) Orderflow Heatmap
        fig.add_trace(
            go.Heatmap(
                x=self.df['identifier'],
                y=self.df['price'],
                z=self.df['size'],
                text=self.df['text'],
                colorscale='icefire_r',
                showscale=False,
                showlegend=True,
                name='BidAsk',
                texttemplate="%{text}",
                textfont={"size": 11, "family": "Courier New"},
                hovertemplate="Price: %{y}<br>Size: %{text}<br>Imbalance: %{z}<extra></extra>",
                xgap=60
            ),
            row=1, col=1)

        # 3) Candle lines
        fig.add_trace(
            go.Scatter(
                x=self.green_hl.index,
                y=self.green_hl['price'],
                name='Candle',
                legendgroup='group',
                showlegend=True,
                line=dict(color='green', width=1.5)
            ),
            row=1, col=1)

        fig.add_trace(
            go.Scatter(
                x=self.red_hl.index,
                y=self.red_hl['price'],
                name='Candle',
                legendgroup='group',
                showlegend=False,
                line=dict(color='red', width=1.5)
            ),
            row=1, col=1)

        # 4) Candle open/close thick lines
        fig.add_trace(
            go.Scatter(
                x=self.green_oc.index,
                y=self.green_oc['price'],
                name='Candle',
                legendgroup='group',
                showlegend=False,
                line=dict(color='green', width=6)
            ),
            row=1, col=1)

        fig.add_trace(
            go.Scatter(
                x=self.red_oc.index,
                y=self.red_oc['price'],
                name='Candle',
                legendgroup='group',
                showlegend=False,
                line=dict(color='red', width=6)
            ),
            row=1, col=1)

        # 5) Lower subplot: "Parameters" heatmap
        fig.add_trace(
            go.Heatmap(
                x=self.labels.index,
                y=self.labels['type'],
                z=self.labels['value'],
                colorscale='rdylgn',
                showscale=False,
                showlegend=True,
                name='Parameters',
                text=self.labels['text'],
                texttemplate="%{text}",
                textfont={"size": 10},
                hovertemplate="%{x}<br>%{text}<extra></extra>",
                xgap=4,
                ygap=4
            ),
            row=2, col=1)

        # Layout
        fig.update_layout(
            title='Order Book Chart (Live from Binance)',
            yaxis=dict(title='Price', showgrid=False, range=[ymax, ymin], tickformat='.2f'),
            yaxis2=dict(fixedrange=True, showgrid=False),
            xaxis2=dict(title='Time', showgrid=False),
            xaxis=dict(showgrid=False, range=[xmin, xmax]),
            height=600,
            template='plotly_dark',
            paper_bgcolor='#222',
            plot_bgcolor='#222',
            dragmode='pan',
            margin=dict(l=10, r=0, t=40, b=20)
        )
        fig.update_xaxes(
            showspikes=True,
            spikecolor="white",
            spikesnap="cursor",
            spikemode="across",
            spikethickness=0.25,
            tickmode='array',
            tickvals=tickvals,
            ticktext=ticktext
        )
        fig.update_yaxes(
            showspikes=True,
            spikecolor="white",
            spikesnap="cursor",
            spikemode="across",
            spikethickness=0.25
        )
        fig.update_layout(spikedistance=1000, hoverdistance=100)

        config = {
            'modeBarButtonsToRemove': ['zoomIn', 'zoomOut', 'zoom', 'autoScale'],
            'scrollZoom': True,
            'displaylogo': False,
            'modeBarButtonsToAdd': [
                'drawline','drawopenpath','drawclosedpath',
                'drawcircle','drawrect','eraseshape'
            ]
        }

        if return_figure:
            return fig

        # Non-Streamlit fallback
        fig.show(config=config)

###############################################
# 2) BINANCE LIVE DATA PART
###############################################

def is_sell_trade(is_maker: bool) -> bool:
    """
    On Binance:
      m=True => The buyer is the market maker => 
                Taker is a SELL => accumulate in 'bid_size'
      m=False => The seller is the maker =>
                 Taker is a BUY => accumulate in 'ask_size'
    """
    return is_maker  # True => SELL side

def get_minute_floor(timestamp_ms: int) -> datetime.datetime:
    """
    Convert Binance trade timestamp to a Python datetime minute.
    """
    dt = datetime.datetime.utcfromtimestamp(timestamp_ms / 1000.0)
    return dt.replace(second=0, microsecond=0)

# We'll store live data in memory for the last X minutes
# candle_map[minute_dt] = {
#    'open': float,
#    'high': float,
#    'low': float,
#    'close': float,
#    'bid_size': { price_level: volume },
#    'ask_size': { price_level: volume },
#    'identifier': str,   # e.g. "2023-06-14 14:01:00"
# }

def build_or_update_candle(candle, price, qty, is_sell_side):
    """
    Update a single candle dict with a trade.
    """
    if candle['open'] is None:
        candle['open'] = price
        candle['high'] = price
        candle['low']  = price
        candle['close'] = price
    else:
        candle['high'] = max(candle['high'], price)
        candle['low']  = min(candle['low'], price)
        candle['close'] = price

    # Accumulate volume by price
    # For a real footprint, we might store raw float prices, or you can do rounding.
    # Here we use the raw float price as the dictionary key (careful with too many levels).
    side_dict = candle['bid_size'] if is_sell_side else candle['ask_size']
    rounded_price = round(price, 1)  # or to the nearest 0.5, etc.
    side_dict[rounded_price] = side_dict.get(rounded_price, 0.0) + qty

def convert_to_ohlc_and_orderflow(candle_map):
    """
    Convert our in-memory 'candle_map' structure to the DataFrames
    that 'OrderFlowChart' expects:
      1) ohlc_df: columns = [open, high, low, close, identifier]
         with a DateTimeIndex
      2) orderflow_df: columns = [bid_size, price, ask_size, identifier]
         also with a DateTimeIndex
    """

    # Lists of records
    ohlc_records = []
    orderflow_records = []

    # Sort by minute
    for minute_dt in sorted(candle_map.keys()):
        c = candle_map[minute_dt]
        identifier = c['identifier']
        # OHLC record
        ohlc_records.append({
            'timestamp': minute_dt,
            'open':  c['open'],
            'high':  c['high'],
            'low':   c['low'],
            'close': c['close'],
            'identifier': identifier
        })

        # For each price in bid_size or ask_size
        all_prices = set(c['bid_size'].keys()) | set(c['ask_size'].keys())
        for p in sorted(all_prices):
            bid_sz = c['bid_size'].get(p, 0.0)
            ask_sz = c['ask_size'].get(p, 0.0)
            orderflow_records.append({
                'timestamp': minute_dt,
                'bid_size': bid_sz,
                'price': p,
                'ask_size': ask_sz,
                'identifier': identifier
            })

    # Build DataFrames
    ohlc_df = pd.DataFrame(ohlc_records).set_index('timestamp')
    orderflow_df = pd.DataFrame(orderflow_records).set_index('timestamp')

    return orderflow_df, ohlc_df


async def binance_trade_listener(trade_queue: queue.Queue):
    """
    Connect to Binance WebSocket for BTC/USDT trades and push them to trade_queue.
    """
    uri = "wss://stream.binance.com:9443/ws/btcusdt@trade"
    async with websockets.connect(uri) as websocket:
        while True:
            try:
                msg = await websocket.recv()
                trade_queue.put(msg)
            except Exception as ex:
                print("WebSocket error:", ex)
                await asyncio.sleep(5)
                break


def start_websocket_thread(trade_queue: queue.Queue):
    """
    Launch an asyncio event loop in a background thread to consume trades.
    """
    loop = asyncio.new_event_loop()

    def run_loop():
        asyncio.set_event_loop(loop)
        loop.run_until_complete(binance_trade_listener(trade_queue))

    t = threading.Thread(target=run_loop, daemon=True)
    t.start()


###############################################
# 3) STREAMLIT APP
###############################################
def main():
    st.set_page_config(page_title="Live Binance Footprint Chart", layout="wide")
    st.title("BTC/USDT Footprint Chart - Live from Binance")

    # Controls
    lookback_minutes = st.sidebar.slider("Lookback (minutes)", 5, 60, 15, 1)

    # Our in-memory candle map
    # candle_map[minute_dt] = { 'open', 'high', 'low', 'close',
    #                           'bid_size', 'ask_size', 'identifier' }
    if 'candle_map' not in st.session_state:
        st.session_state['candle_map'] = {}

    # The trade queue for asynchronous retrieval
    if 'trade_queue' not in st.session_state:
        st.session_state['trade_queue'] = queue.Queue()

    # Start the websocket thread if not started
    if 'websocket_started' not in st.session_state:
        start_websocket_thread(st.session_state['trade_queue'])
        st.session_state['websocket_started'] = True

    chart_placeholder = st.empty()

    # Real-time update loop
    while True:
        # 1. Pull trades from the queue
        while not st.session_state['trade_queue'].empty():
            raw_msg = st.session_state['trade_queue'].get()
            data = json.loads(raw_msg)
            # 'data' is a dict with keys: e, E, s, t, p, q, T, m, ...
            # We only proceed if e == "trade", s == "BTCUSDT", etc.
            if data.get("e") != "trade" or data.get("s") != "BTCUSDT":
                continue

            price = float(data["p"])
            qty   = float(data["q"])
            ts    = data["T"]
            m     = data["m"]  # True => SELL side from taker
            minute_dt = get_minute_floor(ts)

            # Insert / update candle in session state
            if minute_dt not in st.session_state['candle_map']:
                # Create a new candle dictionary
                st.session_state['candle_map'][minute_dt] = {
                    'open': None, 'high': None, 'low': None, 'close': None,
                    'bid_size': {},
                    'ask_size': {},
                    'identifier': minute_dt.strftime("%Y-%m-%d %H:%M:%S")
                }

            build_or_update_candle(
                st.session_state['candle_map'][minute_dt],
                price, qty, is_sell_side=is_sell_trade(m)
            )

        # 2. Prune old candles beyond the lookback
        now_utc = datetime.datetime.utcnow().replace(second=0, microsecond=0)
        cutoff = now_utc - datetime.timedelta(minutes=lookback_minutes)
        st.session_state['candle_map'] = {
            k: v for k, v in st.session_state['candle_map'].items() if k >= cutoff
        }

        # 3. Convert to DataFrames in the format that `OrderFlowChart` expects
        if st.session_state['candle_map']:
            orderflow_df, ohlc_df = convert_to_ohlc_and_orderflow(st.session_state['candle_map'])
            # Make sure we have at least 2 distinct price rows for `granularity` to work
            if len(orderflow_df) > 1:
                # 4. Instantiate & plot
                chart = OrderFlowChart(
                    orderflow_df,
                    ohlc_df,
                    identifier_col='identifier'
                )
                fig = chart.plot(return_figure=True)
                chart_placeholder.plotly_chart(fig, use_container_width=True, key=f'placehold_{time.time()}')
            else:
                chart_placeholder.warning("Not enough trade data yet to compute footprint.")
        else:
            chart_placeholder.warning("No trades accumulated. Waiting for data...")

        time.sleep(1)  # Slow down loop to reduce overhead


if __name__ == "__main__":
    main()
