import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
from datetime import datetime

# Import the shared data dictionary from the WebSocket script
from fake_websocket import symbol_trade_data  # Ensure this is correctly imported

# ------------------------------------
# 1. Set Up Live Updates Without Full Page Refresh
# ------------------------------------
st.set_page_config(page_title="Live Strategy Monitor", layout="wide")

# Initialize session state for live updates
if "latest_scores" not in st.session_state:
    st.session_state["latest_scores"] = {}

st.title("Live Strategy Monitor 📈")

# ------------------------------------
# 2. Fetch the Latest R2P Scores from WebSocket
# ------------------------------------
def get_latest_r2p_scores():
    results = {}
    for pair, time_dict in symbol_trade_data.items():
        if not time_dict:
            continue
        latest_timestamp = max(time_dict.keys())  # Get the latest timestamp
        latest_data = time_dict[latest_timestamp]
        if "r2p_score" in latest_data:
            results[pair] = latest_data["r2p_score"]
    return results

# ------------------------------------
# 3. Live Data Updating Every Second
# ------------------------------------
placeholder = st.empty()  # Create a placeholder for dynamic updates

while True:
    latest_scores = get_latest_r2p_scores()
    st.session_state["latest_scores"] = latest_scores  # Store the latest scores

    with placeholder.container():
        if not latest_scores:
            st.write("No R2P data available yet.")
        else:
            df = pd.DataFrame(
                [(symbol, score) for symbol, score in latest_scores.items()],
                columns=["symbol", "r2p_score"]
            )

            # Treemap Visualization (Live Heatmap)
            df["abs_r2p"] = df["r2p_score"].abs()
            fig_treemap = px.treemap(
                df,
                path=["symbol"],
                values="abs_r2p",
                color="r2p_score",
                color_continuous_scale="RdYlGn",
                title="Live R2P Scores Heatmap"
            )
            st.plotly_chart(fig_treemap, use_container_width=True)

            # Top 5 R2P Scores
            top5_df = df.sort_values("r2p_score", ascending=False).head(5)
            st.subheader("Top 5 R2P Scores 🔥")
            st.table(top5_df)

            # ------------------------------------
            # 4. Live Charts for Top 5 Symbols (Dynamic Updates)
            # ------------------------------------
            st.subheader("📊 Live R2P Score Charts (Updated Every Second)")

            chart_placeholder = st.empty()  # Placeholder for live charts

            with chart_placeholder.container():
                for symbol in top5_df["symbol"]:
                    historical_data = symbol_trade_data.get(symbol, {})

                    if historical_data:
                        timestamps = sorted(historical_data.keys())  # Sorted timestamps
                        r2p_values = [historical_data[t]["r2p_score"] for t in timestamps]

                        fig_line = go.Figure()
                        fig_line.add_trace(go.Scatter(
                            x=[pd.to_datetime(t, unit='ms') for t in timestamps],
                            y=r2p_values,
                            mode='lines+markers',
                            name=symbol
                        ))

                        fig_line.update_layout(
                            title=f"📈 Live R2P Score for {symbol}",
                            xaxis_title="Timestamp",
                            yaxis_title="R2P Score",
                            xaxis=dict(showline=True, showgrid=False),
                            yaxis=dict(showline=True, showgrid=True),
                        )

                        st.plotly_chart(fig_line, use_container_width=True)
                    else:
                        st.write(f"No historical data available for {symbol}.")

    time.sleep(1)  # Update every second
