# index.py
import streamlit as st


# Custom CSS styling
st.markdown("""
<style>
    /* Main container styling */
    .main {
        background-color: #0E1117;
    }
    
    /* Card styling */
    .card {
        background-color: #1a1d24;
        border-radius: 10px;
        padding: 25px;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
    }
    
    .card:hover {
        transform: translateY(-5px);
        background-color: #23272f;
    }
    
    /* Link styling */
    a {
        color: #00f3ff !important;
        text-decoration: none !important;
    }
    
    a:hover {
        color: #00c4cf !important;
    }
    
    /* Title styling */
    h1 {
        color: #00f3ff !important;
        border-bottom: 2px solid #2d343f;
        padding-bottom: 10px;
    }
    
    /* Section headers */
    h3 {
        color: #ffffff !important;
        margin-bottom: 20px !important;
    }
</style>
""", unsafe_allow_html=True)

# Introduction
st.markdown("""
<div style="color: #7e8a9a; margin-bottom: 30px;">
    Advanced trading platform with integrated modules for instant backtest and deployments
</div>
""", unsafe_allow_html=True)

# Create columns for modules
col1, col2, col3 = st.columns(3)

# Strategy Management Card
with col1:
    st.markdown("""
    <div class="card">
        <h3>📈 Strategy Management</h3>
        <ul style="list-style-type: none; padding-left: 0;">
            <li><a href="/strategy_backtest" target="_self">→ Strategy Backtest</a></li>
            <li><a href="/strategy_deployment" target="_self">→ Strategy Deployment</a></li>
            <li><a href="/strategy_monitor" target="_self">→ Strategy Monitor</a></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# Order Management Card
with col2:
    st.markdown("""
    <div class="card">
        <h3>📋 Order Management</h3>
        <ul style="list-style-type: none; padding-left: 0;">
            <li><a href="/ai_order_manager" target="_self">→ AI Order Manager</a></li>
            <li><a href="/order_management_system" target="_self">→ Order Management System</a></li>
            <li><a href="/risk_management_system" target="_self">→ Risk Management System</a></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# Market Data Card
with col3:
    st.markdown("""
    <div class="card">
        <h3>🌐 Market Data</h3>
        <ul style="list-style-type: none; padding-left: 0;">
            <li><a href="/live_dom_chart" target="_self">→ Live DOM Chart</a></li>
            <li><a href="/static_dom_chart" target="_self">→ Static DOM Chart</a></li>
            <li><a href="/footprint_chart" target="_self">→ Footprint Chart</a></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# Data Utilities Section
st.markdown("""
<div class="card" style="margin-top: 20px;">
    <h3>🔧 Data Utilities</h3>
    <ul style="list-style-type: none; padding-left: 0;">
        <li><a href="/data_utils" target="_self">→ Data Utilities Module</a></li>
    </ul>
</div>
""", unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align: center; color: #7e8a9a; margin-top: 40px;">
    <hr style="border-color: #2d343f;">
    Algo.py © 2025 | Secure Professional Trading Platform
</div>
""", unsafe_allow_html=True)