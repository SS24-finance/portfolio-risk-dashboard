
import numpy as np
import pandas as pd


def analyze_portfolio(close_prices, weights):
    # 1. Convert prices into daily returns
    daily_returns = close_prices.pct_change(
        fill_method=None
    ).dropna()

    # 2. Separate stocks and benchmark
    tickers = list(weights.keys())
    stock_returns = daily_returns[tickers]
    market_returns = daily_returns["^GSPC"]

    # Convert allocation percentages into decimals
    weight_series = pd.Series(weights) / 100

    # 3. Calculate portfolio daily returns
    portfolio_returns = stock_returns.dot(weight_series)

    # 4. Cumulative and annualized returns
    cumulative_return = (
        (1 + portfolio_returns).prod() - 1
    )

    trading_days = len(portfolio_returns)

    annualized_return = (
        (1 + cumulative_return) ** (252 / trading_days) - 1
    )

    # 5. Annualized volatility
    annualized_volatility = (
        portfolio_returns.std() * np.sqrt(252)
    )

    # 6. Portfolio beta
    market_variance = market_returns.var()

    beta = (
        portfolio_returns.cov(market_returns)
        / market_variance
        if market_variance > 0
        else np.nan
    )

    # 7. Sharpe ratio
    risk_free_rate = 0.04

    sharpe_ratio = (
        (annualized_return - risk_free_rate)
        / annualized_volatility
        if annualized_volatility > 0
        else np.nan
    )

    # 8. Maximum drawdown
    portfolio_growth = (
        1 + portfolio_returns
    ).cumprod()

    growth_with_start = np.insert(
        portfolio_growth.to_numpy(), 0, 1.0
    )

    running_peak = np.maximum.accumulate(
        growth_with_start
    )

    drawdowns = (
        growth_with_start / running_peak - 1
    )

    max_drawdown = drawdowns.min()

    # 9. S&P 500 comparison
    market_cumulative_return = (
        (1 + market_returns).prod() - 1
    )

    benchmark_difference = (
        cumulative_return - market_cumulative_return
    )

    # 10. Correlation matrix
    correlation_matrix = stock_returns.corr()

    return {
        "Cumulative Return": cumulative_return,
        "Annualized Return": annualized_return,
        "Annualized Volatility": annualized_volatility,
        "Beta": beta,
        "Sharpe Ratio": sharpe_ratio,
        "Maximum Drawdown": max_drawdown,
        "Benchmark Difference": benchmark_difference,
        "Correlation Matrix": correlation_matrix,
        "Portfolio Daily Returns": portfolio_returns,
        "Market Daily Returns": market_returns
    }
