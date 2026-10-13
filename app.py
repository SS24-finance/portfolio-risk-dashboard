
import streamlit as st

# Configure the website
st.set_page_config(
    page_title="Portfolio Risk Dashboard",
    page_icon="📊",
    layout="wide"
)

# Main heading
st.title("Portfolio Risk Dashboard")

st.write(
    "Explore historical portfolio performance, "
    "risk, and diversification using real market data."
)

st.info(
    "This dashboard is an educational tool. "
    "It does not provide investment recommendations."
)

# Sidebar
with st.sidebar:
    st.header("Portfolio Settings")
    st.write("Portfolio inputs will go here.")
    st.write("Coming next: tickers, allocations, and dates.")

# Portfolio overview
st.header("Portfolio Overview")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Annualized Return", "—")

with col2:
    st.metric("Annualized Volatility", "—")

with col3:
    st.metric("Beta", "—")

col4, col5, col6 = st.columns(3)

with col4:
    st.metric("Sharpe Ratio", "—")

with col5:
    st.metric("Maximum Drawdown", "—")

with col6:
    st.metric("S&P 500 Comparison", "—")

# Charts
st.header("Portfolio Performance")
st.info("Portfolio performance chart coming soon.")

st.header("Portfolio vs. S&P 500")
st.info("Benchmark comparison chart coming soon.")

st.header("Portfolio Allocation")
st.info("Allocation chart coming soon.")

st.header("Correlation Heatmap")
st.info("Correlation heatmap coming soon.")

# Footer
st.divider()
st.caption(
    "Historical results do not guarantee future performance."
)
