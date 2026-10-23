Portfolio Risk Dashboard
A Finance Lab educational tool for exploring the historical performance, risk, and diversification of a stock portfolio using real market data from Yahoo Finance (via yfinance).
Metrics: annualized return, annualized volatility, beta, Sharpe ratio, maximum drawdown, and difference versus the S&P 500.
Charts: portfolio growth, portfolio vs. S&P 500, allocation breakdown, and correlation heatmap.
Run locally
pip install -r requirements.txt
streamlit run app.py
​
Project structure
app.py: Streamlit interface and styling
portfolio_analysis.py: all financial calculations
.streamlit/config.toml: dark theme and toolbar settings
This is an educational tool and does not provide investment recommendations.