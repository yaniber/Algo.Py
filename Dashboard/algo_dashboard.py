import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time

# Import shared data from WebSocket script
from fake_websocket import symbol_trade_data  # Make sure it's the correct import path

# ------------------------------------
# 1. Fetch the latest R2P scores
# ------------------------------------
def get_latest_r2p_scores():
    results = {}
    for pair, time_dict in symbol_trade_data.items():
        if not time_dict:
            continue
        latest_timestamp = max(time_dict.keys())
        latest_data = time_dict[latest_timestamp]
        if "r2p_score" in latest_data:
            results[pair] = latest_data["r2p_score"]
    return results

# ------------------------------------
# 2. Auto-refresh using JavaScript (every 60 seconds)
# ------------------------------------
REFRESH_SEC = 60

refresh_script = f"""
<script>
    setTimeout(function() {{
        window.location.reload(1);
    }}, {REFRESH_SEC * 1000});
</script>
"""
st.markdown(refresh_script, unsafe_allow_html=True)

# ------------------------------------
# 3. Streamlit Dashboard
# ------------------------------------
st.title("Strategy Monitor")

latest_scores = get_latest_r2p_scores()
if not latest_scores:
    st.write("No R2P data available yet.")
else:
    df = pd.DataFrame(
        [(symbol, score) for symbol, score in latest_scores.items()],
        columns=["symbol", "r2p_score"]
    )
    
    # Treemap (Heatmap Alternative)
    df["abs_r2p"] = df["r2p_score"].abs()

    fig_treemap = px.treemap(
        df,
        path=["symbol"],
        values="abs_r2p",
        color="r2p_score",
        color_continuous_scale="RdYlGn",
        title="R2P Scores Treemap (Latest)"
    )
    st.plotly_chart(fig_treemap, use_container_width=True)

    # Top 5
    top5_df = df.sort_values("r2p_score", ascending=False).head(5)
    st.subheader("Top 5 R2P Scores")
    st.table(top5_df)

# ------------------------------------
# 4. Live Line Charts for Top 5 Symbols
# ------------------------------------
st.subheader("Live Charts for Top 5 Symbols")

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
            title=f"Live R2P Score for {symbol}",
            xaxis_title="Timestamp",
            yaxis_title="R2P Score",
            xaxis=dict(showline=True, showgrid=False),
            yaxis=dict(showline=True, showgrid=True),
        )

        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.write(f"No historical data available for {symbol}.")
