"""Validated daily-rebalanced portfolio calculations."""

import numpy as np
import pandas as pd

TRADING_DAYS = 252
RISK_FREE_RATE = 0.04
BENCHMARK = "^GSPC"


def prepare_close_prices(close_prices, tickers):
    """Trim unavailable edges, but never bridge missing prices within the period.

    Dates supplied by the provider are treated as trading sessions. Weekends and
    holidays need no filling; an exchange calendar is not inferred here.
    """
    if not isinstance(close_prices, pd.DataFrame):
        raise ValueError("Historical prices must be a table.")
    columns = list(dict.fromkeys([*tickers, BENCHMARK]))
    if not close_prices.columns.is_unique:
        raise ValueError("Historical prices contain duplicate ticker columns.")
    missing = [ticker for ticker in columns if ticker not in close_prices.columns]
    if missing:
        raise ValueError("Missing historical data for: " + ", ".join(missing))
    prices = close_prices.loc[:, columns].copy()
    if not prices.index.is_unique or not prices.index.is_monotonic_increasing:
        raise ValueError("Historical dates must be unique and in chronological order.")
    try:
        prices = prices.astype(float)
    except (TypeError, ValueError) as exc:
        raise ValueError("Historical prices must be numeric.") from exc
    missing = [ticker for ticker in columns if prices[ticker].dropna().empty]
    if missing:
        raise ValueError("Missing historical data for: " + ", ".join(missing)
                         + ". Check the symbols or choose another date range.")
    values = prices.to_numpy()
    if np.isinf(values).any() or (values <= 0).any():
        raise ValueError("Historical prices must be finite and greater than zero.")
    complete = prices.notna().all(axis=1).to_numpy()
    positions = np.flatnonzero(complete)
    if len(positions) < 3:
        raise ValueError("Not enough overlapping historical data. At least three complete price dates are required.")
    prices = prices.iloc[positions[0]:positions[-1] + 1]
    if prices.isna().any().any():
        affected = prices.columns[prices.isna().any()].tolist()
        raise ValueError("Missing prices within the analysis period for: "
                         + ", ".join(affected)
                         + ". Choose a date range without gaps or try again later; missing dates cannot safely be treated as daily returns.")
    return prices


def analyze_portfolio(close_prices, weights):
    """Return metrics for target percentage weights, rebalanced each session."""
    if not isinstance(weights, dict) or not weights:
        raise ValueError("Provide at least one ticker and its allocation.")
    try:
        weight_series = pd.Series(weights, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("Allocations must be numeric percentages.") from exc
    if not np.isfinite(weight_series.to_numpy()).all() or (weight_series < 0).any() or (weight_series > 100).any():
        raise ValueError("Allocations must be finite percentages between 0 and 100.")
    if abs(weight_series.sum() - 100) > 0.05:
        raise ValueError("Portfolio allocations must add up to 100%.")
    # Normalize accepted rounding differences (e.g. three weights of 33.33%).
    weight_series = weight_series / weight_series.sum()
    tickers = list(weights)
    close_prices = prepare_close_prices(close_prices, tickers)
    daily_returns = close_prices.pct_change(fill_method=None).iloc[1:]
    if len(daily_returns) < 2 or not np.isfinite(daily_returns.to_numpy()).all():
        raise ValueError("At least two finite daily returns are required for risk calculations.")
    stock_returns = daily_returns[tickers]
    market_returns = daily_returns[BENCHMARK]
    portfolio_returns = stock_returns.dot(weight_series)

    cumulative_return = (1 + portfolio_returns).prod() - 1
    annualized_return = (1 + cumulative_return) ** (TRADING_DAYS / len(portfolio_returns)) - 1
    daily_volatility = portfolio_returns.std(ddof=1)
    annualized_volatility = daily_volatility * np.sqrt(TRADING_DAYS)
    market_variance = market_returns.var(ddof=1)
    beta = (portfolio_returns.cov(market_returns) / market_variance
            if market_variance > 0 else np.nan)

    daily_risk_free_rate = (1 + RISK_FREE_RATE) ** (1 / TRADING_DAYS) - 1
    annualized_mean_excess_return = (portfolio_returns - daily_risk_free_rate).mean() * TRADING_DAYS
    sharpe_ratio = (annualized_mean_excess_return / annualized_volatility
                    if annualized_volatility > 0 else np.nan)

    portfolio_growth = (1 + portfolio_returns).cumprod()
    growth_with_start = np.insert(portfolio_growth.to_numpy(), 0, 1.0)
    running_peak = np.maximum.accumulate(growth_with_start)
    max_drawdown = (growth_with_start / running_peak - 1).min()
    market_cumulative_return = (1 + market_returns).prod() - 1

    return {
        "Cumulative Return": cumulative_return,
        "Annualized Return": annualized_return,
        "Annualized Volatility": annualized_volatility,
        "Beta": beta,
        "Sharpe Ratio": sharpe_ratio,
        "Maximum Drawdown": max_drawdown,
        "Benchmark Difference": cumulative_return - market_cumulative_return,
        "Correlation Matrix": stock_returns.corr(),
        "Portfolio Daily Returns": portfolio_returns,
        "Market Daily Returns": market_returns,
    }
