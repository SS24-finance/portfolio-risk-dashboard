# Portfolio Risk Dashboard V1.1

A Finance Lab educational dashboard for exploring historical portfolio returns,
risk, and diversification with Yahoo Finance data. The existing green, cream,
and white interface includes six headline metrics, four charts, a benchmark
maximum-drawdown comparison, explanations, and portfolio assumptions.

## Run locally

From this project folder:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

The prepared `.venv` uses Python 3.14.10. The pinned dependencies require Python
3.12 or newer. Check the existing Cloud app's Python version before publishing.

## Run checks

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall -q app.py portfolio_analysis.py tests
.venv/bin/python -m pip check
```

The tests use controlled prices and mocked downloads. They run without Yahoo
network access and cover calculation accuracy, invalid inputs, allocation
persistence, the beginner example, all metrics, and all chart creation paths.

## Calculation and data rules

- Holdings retain their allocations when tickers are reordered. Added holdings
  start at 0%; removed holdings remember their weights within the session.
  The beginner example explicitly resets AAPL and MSFT to 50% each.
- Weights must total 100%, with a tolerance of 0.05 percentage points for
  rounding. Accepted weights are normalized to exactly 100% for calculations.
- The portfolio rebalances daily, without transaction costs or taxes.
- Annualized return compounds historical daily portfolio returns over 252
  trading days per year.
- Sharpe uses mean daily excess return times 252, divided by daily sample
  standard deviation times the square root of 252. The daily risk-free rate
  is `1.04 ** (1 / 252) - 1`.
- Drawdowns include the initial investment, so an immediate decline counts.
- At least three complete price dates (two daily returns) are required. This
  prevents invalid sample statistics, but short samples remain unreliable.
- Missing edges are trimmed to the shared period with a visible warning.
  Missing prices inside that period stop analysis. No forward-filling or
  bridging gaps is performed. Entire sessions omitted by the provider cannot
  be detected without a separate exchange calendar; provider dates are assumed
  to be trading sessions.
- End dates are exclusive. Adjusted stocks include dividend/split adjustments;
  `^GSPC` is a price index, so the benchmark has different dividend treatment.
- Undefined beta/Sharpe values display as N/A. Flat-price stocks have undefined
  correlations.

## Files

- `app.py`: dashboard inputs, styling, charts, and explanations.
- `portfolio_analysis.py`: price validation and financial calculations.
- `.streamlit/config.toml`: light theme and readable control colors.
- `requirements.txt`: tested direct dependency versions.
- `tests/`: automated calculation and Streamlit AppTest checks.
- `VALIDATION.md`: verification results and deployment next steps.
- `checkpoints/`: ignored local source backups; not deployed.

This is an educational tool, not investment advice.
