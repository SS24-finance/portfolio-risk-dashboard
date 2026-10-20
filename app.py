from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st
import yfinance as yf

from portfolio_analysis import analyze_portfolio

st.set_page_config(page_title="Portfolio Risk Dashboard", page_icon="📊", layout="wide")
st.title("Portfolio Risk Dashboard")
st.write("Explore historical portfolio performance, risk, and diversification using real market data.")
st.info("This dashboard is an educational tool. It does not provide investment recommendations.")

# Remember allocations when ticker symbols change
if "previous_tickers" not in st.session_state:
    st.session_state.previous_tickers = []

if "saved_allocations" not in st.session_state:
    st.session_state.saved_allocations = []
with st.sidebar:
    st.header("Portfolio Settings")
    ticker_input = st.text_input(
        "Stock Tickers", value="AAPL, NKE, DIS",
        help="Enter 2–10 stock symbols separated by commas."
    )
    tickers = [ticker.strip().upper() for ticker in ticker_input.split(",") if ticker.strip()]
   
    st.subheader("Portfolio Allocations")

    # Detect when the ticker list changes
    if tickers != st.session_state.previous_tickers:
        previous_allocations = st.session_state.saved_allocations

        for i, ticker in enumerate(tickers):
            if i < len(previous_allocations):
                allocation = previous_allocations[i]
            else:
                allocation = round(100.0 / len(tickers), 2)

            st.session_state[f"weight_{ticker}"] = allocation

        st.session_state.previous_tickers = tickers.copy()

    weights = {}

    for ticker in dict.fromkeys(tickers):
        weights[ticker] = st.number_input(
            f"{ticker} Allocation (%)",
            min_value=0.0,
            max_value=100.0,
            step=1.0,
            key=f"weight_{ticker}"
        )

    # Save allocations for the next ticker change
    st.session_state.saved_allocations = [
        weights[ticker] for ticker in tickers
    ]

    total_weight = sum(weights.values())
    st.write(f"Total Allocation: {total_weight:.2f}%")

    st.subheader("Historical Period")
    start_date = st.date_input("Start Date", value=date(2025, 1, 1))
    end_date = st.date_input("End Date", value=date(2026, 1, 1))
    analyze_button = st.button("Analyze Portfolio", type="primary")

valid_inputs = True
if not 2 <= len(tickers) <= 10:
    st.error("Please enter between 2 and 10 stocks.")
    valid_inputs = False
if len(tickers) != len(set(tickers)):
    st.error("Please remove duplicate stock tickers.")
    valid_inputs = False
if abs(total_weight - 100) > 0.05:
    st.error("Portfolio allocations must add up to 100%.")
    valid_inputs = False
if start_date >= end_date:
    st.error("Start date must be before end date.")
    valid_inputs = False
if end_date > date.today():
    st.error("End date cannot be in the future.")
    valid_inputs = False

if analyze_button and valid_inputs:
    with st.spinner("Analyzing portfolio..."):
        try:
            all_tickers = tickers + ["^GSPC"]
            data = yf.download(
                all_tickers, start=start_date, end=end_date,
                auto_adjust=True, progress=False
            )
            close_prices = data["Close"]
            missing_tickers = [
                ticker for ticker in all_tickers
                if ticker not in close_prices.columns
                or close_prices[ticker].dropna().empty
            ]
            if missing_tickers:
                st.error("Missing historical data for: " + ", ".join(missing_tickers))
            else:
                close_prices = close_prices.dropna()
                if len(close_prices) < 3:
                    st.error("Not enough historical data. Try a longer date range.")
                else:
                    results = analyze_portfolio(close_prices, weights)
                    st.success("Historical market data loaded!")
                    st.header("Portfolio Analysis Results")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Annualized Return", f"{results['Annualized Return']:.2%}")
                    with col2:
                        st.metric("Annualized Volatility", f"{results['Annualized Volatility']:.2%}")
                    with col3:
                        st.metric("Beta", f"{results['Beta']:.3f}")
                    col4, col5, col6 = st.columns(3)
                    with col4:
                        st.metric("Sharpe Ratio", f"{results['Sharpe Ratio']:.3f}")
                    with col5:
                        st.metric("Maximum Drawdown", f"{results['Maximum Drawdown']:.2%}")
                    with col6:
                        st.metric("S&P 500 Difference", f"{results['Benchmark Difference'] * 100:+.2f} pp")

                    with st.expander("What do these metrics mean?"):
                        st.write("**Annualized Return:** Annualized historical portfolio growth.")
                        st.write("**Annualized Volatility:** Historical return variability, scaled to a year.")
                        st.write("**Beta:** Historical sensitivity to S&P 500 daily movements.")
                        st.write("**Sharpe Ratio:** Historical risk-adjusted return using an illustrative 4% annual risk-free rate.")
                        st.write("**Maximum Drawdown:** Largest historical decline from a previous peak.")
                        st.write("**S&P 500 Difference:** Difference in cumulative returns, in percentage points.")

                    st.subheader("Historical Closing Prices")
                    st.dataframe(close_prices.tail(10))

                    # Chart 1: portfolio performance
                    st.header("Portfolio Performance")
                    portfolio_returns = results["Portfolio Daily Returns"]
                    portfolio_growth = (1 + portfolio_returns).cumprod() * 100
                    portfolio_growth = pd.concat([
                        pd.Series([100.0], index=[close_prices.index[0]]),
                        portfolio_growth
                    ])
                    fig_performance = px.line(
                        x=portfolio_growth.index, y=portfolio_growth.values,
                        title="Historical Growth of $100",
                        labels={"x": "Date", "y": "Portfolio Value ($)"}
                    )
                    fig_performance.update_layout(showlegend=False, hovermode="x unified")
                    st.plotly_chart(fig_performance, use_container_width=True)

                    # Chart 2: portfolio versus benchmark
                    st.header("Portfolio vs. S&P 500")
                    market_returns = results["Market Daily Returns"]
                    market_growth = (1 + market_returns).cumprod() * 100
                    market_growth = pd.concat([
                        pd.Series([100.0], index=[close_prices.index[0]]),
                        market_growth
                    ])
                    comparison_df = pd.DataFrame({
                        "Portfolio": portfolio_growth,
                        "S&P 500": market_growth
                    })
                    fig_comparison = px.line(
                        comparison_df, title="Portfolio vs. S&P 500: Growth of $100",
                        labels={"index": "Date", "value": "Value ($)", "variable": "Series"}
                    )
                    fig_comparison.update_layout(hovermode="x unified")
                    st.plotly_chart(fig_comparison, use_container_width=True)

                    # Chart 3: portfolio allocation
                    st.header("Portfolio Allocation")
                    allocation_df = pd.DataFrame({
                        "Stock": list(weights.keys()),
                        "Allocation": list(weights.values())
                    })
                    fig_allocation = px.pie(
                        allocation_df, names="Stock", values="Allocation",
                        hole=0.5, title="Portfolio Allocation Breakdown"
                    )
                    fig_allocation.update_traces(textinfo="label+percent")
                    st.plotly_chart(fig_allocation, use_container_width=True)

                    # Chart 4: correlation heatmap
                    st.header("Stock Correlation Heatmap")
                    correlation_matrix = results["Correlation Matrix"]
                    fig_correlation = px.imshow(
                        correlation_matrix, text_auto=".2f", zmin=-1, zmax=1,
                        color_continuous_scale="RdBu_r",
                        title="Correlation Between Stock Daily Returns"
                    )
                    st.plotly_chart(fig_correlation, use_container_width=True)

        except Exception as error:
            st.error(f"Unable to analyze portfolio: {error}")

st.divider()
st.caption(
    "Historical results do not guarantee future performance. "
    "Calculations assume daily rebalancing, no fees or taxes, "
    "and an illustrative 4% annual risk-free rate."
)
