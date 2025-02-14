# TODO : Add deploy option , call strategy deployment dashboard with query parameter : https://docs.streamlit.io/develop/api-reference/caching-and-state/st.query_params
import streamlit as st
import pandas as pd
import json
from pathlib import Path
import plotly.graph_objects as go
import vectorbtpro as vbt
from datetime import datetime

# Configure page
st.set_page_config(page_title="Backtest Archive", layout="wide", page_icon="📊")
st.title("🔍 Backtest Analysis Hub")

def load_backtests():
    """Load all backtests with error handling"""
    backtests = []
    bt_dir = Path("backtest_results")
    
    for bt_path in bt_dir.glob("*"):
        if not bt_path.is_dir():
            continue
            
        try:
            with open(bt_path / "params.json") as f:
                data = json.load(f)
            data["path"] = str(bt_path)
            backtests.append(data)
        except:
            continue
            
    return pd.DataFrame(backtests)

# Load data with status
with st.spinner("🔄 Loading backtests from archive..."):
    df = load_backtests()

if df.empty:
    st.success("🎉 No backtests found - ready for your first analysis!")
    st.stop()

# ======================
# MAIN DISPLAY - GRID VIEW
# ======================
st.header("📚 Backtest Library")

# Create responsive grid
cols = st.columns(3)
for idx, row in df.iterrows():
    with cols[idx % 3]:
        with st.container(border=True):
            # Header section
            st.markdown(f"### {row.get('strategy_name', 'Unnamed Strategy')}")
            st.caption(f"🕒 Created: {datetime.fromisoformat(row['created_at']).strftime('%b %d, %Y %H:%M')}")
            
            # Key metrics
            m1, m2, m3 = st.columns(3)
            performance_row = row.get('performance')
            m1.metric("Return", f"{performance_row.get('returns', 0):.2%}")
            m2.metric("Sharpe", f"{performance_row.get('sharpe_ratio', 0):.2f}")
            m3.metric("Drawdown", f"{abs(performance_row.get('max_drawdown', 0)):.2%}", delta_color="inverse")
            
            # Strategy info
            with st.expander("🔍 Quick View"):
                st.write(f"**Market**: {row.get('market_name', 'N/A')}")
                st.write(f"**Symbols**: {', '.join(row.get('symbol_list', []))}")
                st.write(f"**Timeframe**: {row.get('timeframe', 'N/A')}")
                st.write(f"**Duration**: {performance_row.get('duration_days', 0)} days")
                st.write(f"**Duration**: {performance_row.get('duration_days', 0)} days")
                
            # Detail trigger
            if st.button("📈 Deep Analysis", key=f"btn_{idx}"):
                st.session_state.selected_backtest = row

# ======================
# DETAILED ANALYSIS VIEW
# ======================
if "selected_backtest" in st.session_state:
    st.divider()
    selected = st.session_state.selected_backtest
    
    with st.spinner(f"📊 Unpacking {selected['strategy_name']} analysis..."):

        pf = vbt.Portfolio.load(Path(selected["path"]) / "portfolio.pkl")
        
        # === Core Metrics ===
        st.header(f"🧮 {selected['strategy_name']} Performance Deep Dive")
        
        # Metrics Grid
        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        mcol1.metric("Total Return", f"{pf.total_return:.2%}")
        mcol2.metric("Sharpe Ratio", f"{pf.sharpe_ratio:.2f}")
        mcol3.metric("Max Drawdown", f"{pf.max_drawdown:.2%}", delta_color="inverse")

        # === Visualization Tabs ===
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Equity Curve", "📉 Drawdown Analysis", "📋 Trade History", "⚙️ Configuration"])

        with tab1:
            # Interactive equity plot
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=pf.value.index,
                y=pf.value,
                mode='lines',
                name='Portfolio Value',
                line=dict(color='#4CAF50', width=2)
            ))
            fig.update_layout(
                title="🤑 Portfolio Value Evolution",
                yaxis_title="Value",
                xaxis_title="Date",
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            # Drawdown analysis
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=pf.drawdown.index,
                y=pf.drawdown,
                fill='tozeroy',
                line=dict(color='#FF5252'),
                name='Drawdown'
            ))
            fig.update_layout(
                title="😰 Drawdown Periods",
                yaxis_title="Drawdown %",
                xaxis_title="Date",
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab3:
            # Trade history table
            trades = pf.trades.records_readable
            st.dataframe(
                trades.style.format({
                    'PnL': '${:.2f}',
                    'Return': '{:.2%}',
                    'Position Value': '${:.2f}'
                }),
                use_container_width=True,
                height=400
            )

        with tab4:
            # Configuration details
            config_col1, config_col2 = st.columns(2)
            
            with config_col1:
                st.subheader("⚙️ Strategy Settings")
                st.json(selected.get('strategy_params', {}))
                
            with config_col2:
                st.subheader("⚡ Execution Parameters")
                st.write(f"**Initial Capital**: ${selected.get('init_cash', 0):,.2f}")
                st.write(f"**Fees**: {selected.get('fees', 0):.4%} per trade")
                st.write(f"**Slippage**: {selected.get('slippage', 0):.4%}")
                st.write(f"**Position Size**: {selected.get('size', 0):.2%} of capital")


    if st.button("◀️ Back to Overview"):
        del st.session_state.selected_backtest