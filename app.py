from datetime import date
from html import escape

import pandas as pd
import plotly.express as px
import streamlit as st
import yfinance as yf

from portfolio_analysis import analyze_portfolio

st.set_page_config(
    page_title="Portfolio Risk Dashboard | Finance Lab",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# EASY SETTINGS: change these values to restyle the whole dashboard
# ---------------------------------------------------------------------------
FONT_NAME = "Poppins"   # try: Inter, DM Sans, Manrope, Plus Jakarta Sans, Outfit, Nunito, Lora

BG, CARD = "#F1F4EE", "#FFFFFF"   # page background, card background
TEXT, MUTED = "#121A14", "#6B766D"
LIME, LIME_SOFT, FOREST = "#B8F26B", "#E6F8CF", "#17381A"   # main accent colors
BAD = "#E5484D"                                            # "total is not 100%" warning
INPUT_BG, INPUT_BORDER = "#E6F8CF", "#CFE9A8"   # color and outline of the ticker, date and allocation boxes

# Chart colors (flat, no gradients)
CHART_PRIMARY, CHART_SECONDARY = "#2E9F5B", "#F59E5B"      # Portfolio line, S&P 500 line
PIE_COLORS = ["#B8F26B", "#F8E08A", "#9FD6F5", "#D3C6F7", "#F9B9A0",
              "#8FDDB0", "#F4B6D3", "#C9E0A0", "#F2C879", "#B6C8F0"]

# Pastel fill for each of the six metric cards, in order:
# Return, Volatility, Beta, Sharpe, Drawdown, S&P difference
METRIC_COLORS = ["#CDF59A", "#F8E8A0", "#CFE5F8", "#DCD5F6", "#FAD5BC", "#CDEFD9"]

GRID = "rgba(20,40,25,0.07)"
FONT = f"'{FONT_NAME}', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"

ROOT_CSS = (
    ":root{"
    f"--bg:{BG};--card:{CARD};--text:{TEXT};--muted:{MUTED};"
    f"--lime:{LIME};--lime-soft:{LIME_SOFT};--forest:{FOREST};--bad:{BAD};"
    f"--input-bg:{INPUT_BG};--input-border:{INPUT_BORDER};"
    "--line:rgba(23,56,26,.09);}"
)
METRIC_CSS = "".join(
    f'.st-key-metric_grid [data-testid="stElementContainer"]:nth-child({i}) [data-testid="stMetric"]{{background:{c};}}'
    for i, c in enumerate(METRIC_COLORS, 1)
)

CSS = """
.stApp,.stApp p,.stApp label,.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp li,.stApp button,.stApp input,.stApp textarea{font-family:'__FONT__',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;}
[data-testid="stMetricLabel"],[data-testid="stMetricLabel"] *,[data-testid="stMetricValue"],[data-testid="stMetricValue"] *{font-family:'__FONT__',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;}
.stApp{background:var(--bg);color:var(--text);}
header[data-testid="stHeader"]{background:transparent;}
#MainMenu,footer{visibility:hidden;}
.block-container{max-width:1200px;padding:2rem 2rem 3rem;}

/* Header */
.fl-hero{margin:.4rem 0 1.2rem;}
.fl-badge{display:inline-flex;align-items:center;gap:.5rem;padding:.4rem .95rem;border-radius:999px;
background:var(--lime);color:var(--forest);font-size:.72rem;font-weight:700;letter-spacing:.12em;vertical-align:middle;}
.fl-logo{width:12px;height:12px;border-radius:4px;display:inline-block;background:var(--forest);}
.fl-byline{margin-left:.8rem;color:var(--muted);font-size:.85rem;font-weight:500;vertical-align:middle;}
.stApp .fl-hero h1{font-size:clamp(1.8rem,3.6vw,2.6rem);font-weight:700;letter-spacing:-.025em;line-height:1.12;
margin:.9rem 0 .4rem;padding:0;color:var(--text);}
.fl-hero p{color:var(--muted);font-size:1.02rem;max-width:720px;margin:0;line-height:1.6;}
.fl-note{display:flex;align-items:center;gap:.7rem;margin:0 0 1rem;padding:.85rem 1.1rem;border-radius:16px;
background:var(--lime-soft);color:var(--forest);font-size:.92rem;line-height:1.5;}
.fl-note i{font-style:normal;flex:none;width:22px;height:22px;border-radius:50%;background:var(--forest);color:var(--lime);
display:inline-flex;align-items:center;justify-content:center;font-size:.75rem;font-weight:700;}

/* Headings */
.fl-section{margin:2rem 0 .9rem;}
.stApp .fl-section h2{font-size:1.35rem;font-weight:700;letter-spacing:-.01em;margin:0;padding:0;color:var(--text);}
.fl-section p{color:var(--muted);margin:.3rem 0 0;font-size:.95rem;line-height:1.55;max-width:760px;}
.stApp .fl-card-head h3{font-size:1.1rem;font-weight:700;letter-spacing:-.01em;margin:0;padding:0;color:var(--text);}
.fl-card-head p{color:var(--muted);margin:.25rem 0 .5rem;font-size:.85rem;line-height:1.5;}

/* White cards: any block that starts with a card heading */
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] > [data-testid="stMarkdown"] .fl-card-marker){
background:var(--card);border:1px solid var(--line);border-radius:24px;padding:1.2rem 1.3rem;
box-shadow:0 1px 2px rgba(20,40,25,.05),0 10px 28px -18px rgba(20,40,25,.22);}

/* Metric cards: 3 columns on desktop, 2 on tablet and mobile */
.st-key-metric_grid[data-testid="stVerticalBlock"],.st-key-metric_grid>[data-testid="stVerticalBlock"]{
display:grid !important;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem;}
.st-key-metric_grid [data-testid="stElementContainer"]{width:auto !important;min-width:0;}
[data-testid="stMetric"]{position:relative;overflow:hidden;height:100%;background:var(--card);border-radius:24px;
padding:1.2rem 1.35rem;border:0;box-shadow:0 1px 2px rgba(20,40,25,.05);}
[data-testid="stMetric"]::after{content:"";position:absolute;right:-26px;top:-26px;width:104px;height:104px;
border-radius:50%;background:rgba(18,26,20,.06);pointer-events:none;}
[data-testid="stMetric"]>*{position:relative;z-index:1;}
[data-testid="stMetricLabel"]{color:rgba(18,26,20,.66);font-size:.88rem;font-weight:500;}
[data-testid="stMetricValue"]{color:#101712;font-size:2rem;font-weight:700;letter-spacing:-.02em;}

/* Tables, alerts, expanders */
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:16px;overflow:hidden;}
[data-testid="stAlert"]{border-radius:16px;}
[data-testid="stExpander"]{border:1px solid var(--line);border-radius:20px;background:var(--card);}
hr{border-color:var(--line);}

/* Inputs card */
[data-baseweb="input"],[data-baseweb="base-input"]{border-radius:12px !important;background-color:var(--input-bg) !important;}
[data-baseweb="input"]{border:1px solid var(--input-border) !important;}
[data-baseweb="input"]:focus-within{border-color:var(--forest) !important;}
[data-baseweb="input"] input,[data-baseweb="base-input"] input,[data-baseweb="input"] button{background-color:transparent !important;}
.fl-sub{margin:.8rem 0 .5rem;}
.fl-sub b{font-size:.95rem;font-weight:600;color:var(--text);}
.fl-sub p{margin:.15rem 0 0;color:var(--muted);font-size:.82rem;}
.fl-total{margin:.2rem 0 0;}
.fl-total div.row{display:flex;justify-content:space-between;font-size:.88rem;color:var(--muted);margin-bottom:.4rem;}
.fl-total div.row b{color:var(--forest);}
.fl-total.bad div.row b{color:var(--bad);}
.fl-bar{height:8px;border-radius:8px;background:rgba(23,56,26,.1);overflow:hidden;}
.fl-bar div{height:100%;border-radius:8px;background:#A6E85C;}
.fl-total.bad .fl-bar div{background:var(--bad);}
.stButton{width:100%;}
.stButton>button[kind="primary"],.stButton>button[data-testid="stBaseButton-primary"]{width:100%;min-height:2.9rem;border:0;border-radius:999px;
padding:.7rem 1rem;font-weight:700;background:var(--lime);box-shadow:none;transition:background .15s ease,transform .15s ease;}
.stButton>button[kind="primary"] *,.stButton>button[data-testid="stBaseButton-primary"] *{color:var(--forest) !important;}
.stButton>button[kind="primary"]:hover,.stButton>button[data-testid="stBaseButton-primary"]:hover{background:#A6E85C;transform:translateY(-1px);}

/* Empty state and footer */
.fl-empty{border:1px dashed rgba(23,56,26,.25);border-radius:24px;padding:2rem;margin-top:1.2rem;background:var(--card);}
.fl-empty h3{margin:0 0 .4rem;font-size:1.25rem;padding:0;color:var(--text);}
.fl-empty p{color:var(--muted);margin:0 0 1rem;}
.fl-empty ol{margin:0;padding-left:1.2rem;color:var(--text);line-height:1.9;}
.fl-footer{margin-top:3.5rem;padding-top:1.4rem;border-top:1px solid var(--line);color:var(--muted);
font-size:.8rem;line-height:1.7;text-align:center;}
.fl-footer .fl-brandline{display:inline-flex;align-items:center;gap:.5rem;color:var(--text);font-weight:600;margin-bottom:.4rem;}
.fl-footer .fl-logo{width:11px;height:11px;border-radius:4px;}

@media (max-width:900px){.st-key-metric_grid[data-testid="stVerticalBlock"],
.st-key-metric_grid>[data-testid="stVerticalBlock"]{grid-template-columns:repeat(2,minmax(0,1fr));}}
@media (max-width:640px){.block-container{padding:1.2rem 1rem 2rem;}
[data-testid="stMetric"]{padding:.9rem 1rem;border-radius:18px;}
[data-testid="stMetricValue"]{font-size:1.5rem;}
[data-testid="stMetricLabel"]{font-size:.75rem;}
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] > [data-testid="stMarkdown"] .fl-card-marker){padding:1rem;border-radius:20px;}
.fl-hero p{font-size:.98rem;}.fl-empty{padding:1.3rem;}}
"""


def html(markup):
    """Render HTML on one line so Markdown never treats indentation as code."""
    st.markdown(" ".join(line.strip() for line in markup.splitlines()), unsafe_allow_html=True)


def section(title, blurb):
    html(f'<div class="fl-section"><h2>{title}</h2><p>{blurb}</p></div>')


def card_head(title, blurb):
    """Heading at the top of a white card (the marker makes CSS turn its block into a card)."""
    html(f'<div class="fl-card-head"><span class="fl-card-marker"></span><h3>{title}</h3><p>{blurb}</p></div>')


def sub_head(title, hint):
    html(f'<div class="fl-sub"><b>{title}</b><p>{hint}</p></div>')


def style_fig(fig, grid=True):
    """Apply one consistent look to every Plotly chart."""
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=MUTED, size=13),
        title=dict(font=dict(size=13, color=MUTED), x=0.01, xanchor="left"),
        margin=dict(l=8, r=8, t=48, b=8),
        height=380,
        hoverlabel=dict(bgcolor=FOREST, bordercolor=FOREST, font=dict(color="#FFFFFF")),
        legend=dict(orientation="h", y=1.1, x=1, xanchor="right", bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(showgrid=grid, gridcolor=GRID, zeroline=False, linecolor="rgba(0,0,0,0)")
    fig.update_yaxes(showgrid=grid, gridcolor=GRID, zeroline=False, linecolor="rgba(0,0,0,0)")
    return fig


def show_chart(fig):
    """Display a Plotly figure full-width across Streamlit versions."""
    try:
        st.plotly_chart(fig, use_container_width=True, theme=None)
    except Exception:
        st.plotly_chart(fig, width="stretch", theme=None)


# The font @import must come first in the stylesheet or browsers ignore it
FONT_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2?family="
    + FONT_NAME.replace(" ", "+") + ":wght@400;500;600;700&display=swap');"
)
CSS = FONT_IMPORT + ROOT_CSS + METRIC_CSS + CSS.replace("__FONT__", FONT_NAME)
st.markdown("<style>" + "\n".join(l for l in CSS.splitlines() if l.strip()) + "</style>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
html(f"""
<div class="fl-hero">
<span class="fl-badge"><span class="fl-logo"></span>FINANCE LAB | BY: SIMRAN SUTARIA | 2026</span><span class="fl-byline"></span><h1>Portfolio Risk Dashboard</h1>
<p>Explore historical portfolio performance, risk, and diversification using real market data.</p>
</div>
""")
html("""
<div class="fl-note"><i>i</i><span>This dashboard is an educational tool. It does not provide investment recommendations.</span></div>
""")

# Remember allocations when ticker symbols change
if "previous_tickers" not in st.session_state:
    st.session_state.previous_tickers = []

if "saved_allocations" not in st.session_state:
    st.session_state.saved_allocations = []

# ---------------------------------------------------------------------------
# Portfolio inputs (main page)
# ---------------------------------------------------------------------------
with st.container():
    card_head("Build your portfolio",
              "Enter 2–10 tickers, set weights that total 100%, then choose a date range. "
              "The S&amp;P 500 is added automatically as the benchmark.")

    col_tickers, col_start, col_end = st.columns([2, 1, 1])
    with col_tickers:
        ticker_input = st.text_input(
            "Stock Tickers", value="AAPL, NKE, DIS",
            help="Enter 2–10 stock symbols separated by commas."
        )
        tickers = [ticker.strip().upper() for ticker in ticker_input.split(",") if ticker.strip()]
    with col_start:
        start_date = st.date_input("Start Date", value=date(2025, 1, 1))
    with col_end:
        end_date = st.date_input("End Date", value=date(2026, 1, 1))

    sub_head("Portfolio Allocations", "Set each stock's weight so the total equals 100%.")

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
    unique_tickers = list(dict.fromkeys(tickers))

    for row_start in range(0, len(unique_tickers), 5):
        row_tickers = unique_tickers[row_start:row_start + 5]
        weight_columns = st.columns(5)
        for column, ticker in zip(weight_columns, row_tickers):
            with column:
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
    total_ok = abs(total_weight - 100) <= 0.05

    col_total, col_button = st.columns([3, 1])
    with col_total:
        html(f"""
        <div class="fl-total {'ok' if total_ok else 'bad'}">
        <div class="row"><span>Total Allocation</span><b>{total_weight:.2f}%</b></div>
        <div class="fl-bar"><div style="width:{min(total_weight, 100):.2f}%"></div></div></div>
        """)
    with col_button:
        analyze_button = st.button("Analyze Portfolio", type="primary")

# ---------------------------------------------------------------------------
# Input validation (same rules as before, friendlier wording)
# ---------------------------------------------------------------------------
valid_inputs = True
if not 2 <= len(tickers) <= 10:
    st.error("Please enter between 2 and 10 stock tickers, separated by commas.", icon="⚠️")
    valid_inputs = False
if len(tickers) != len(set(tickers)):
    st.error("Duplicate tickers found. Please remove any repeated symbols.", icon="⚠️")
    valid_inputs = False
if abs(total_weight - 100) > 0.05:
    st.error(
        f"Portfolio allocations must add up to 100%. They currently total {total_weight:.2f}%.",
        icon="⚠️",
    )
    valid_inputs = False
if start_date >= end_date:
    st.error("Start date must be before the end date.", icon="⚠️")
    valid_inputs = False
if end_date > date.today():
    st.error("End date cannot be in the future.", icon="⚠️")
    valid_inputs = False

if not analyze_button:
    html("""
    <div class="fl-empty"><h3>Ready when you are</h3>
    <p>Build a portfolio in the sidebar and see how it has behaved historically.</p>
    <ol><li>Enter 2–10 stock tickers.</li><li>Set allocations that total 100%.</li>
    <li>Pick a date range, then click <b>Analyze Portfolio</b>.</li></ol></div>
    """)

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
                st.error(
                    "Missing historical data for: " + ", ".join(missing_tickers)
                    + ". Check the ticker spelling or try a different date range.",
                    icon="⚠️",
                )
            else:
                close_prices = close_prices.dropna()
                if len(close_prices) < 3:
                    st.error("Not enough historical data. Try a longer date range.", icon="⚠️")
                else:
                    results = analyze_portfolio(close_prices, weights)
                    st.success("Historical market data loaded!")

                    section(
                        "Portfolio Analysis Results",
                        "Six headline numbers summarizing return, risk, and how your portfolio compared with the market. "
                        "Hover the ⓘ icons for a quick definition.",
                    )
                    try:
                        metric_grid = st.container(key="metric_grid")
                    except TypeError:  # older Streamlit without container keys
                        metric_grid = st.container()
                    with metric_grid:
                        st.metric("Annualized Return", f"{results['Annualized Return']:.2%}",
                                  help="Annualized historical portfolio growth.")
                        st.metric("Annualized Volatility", f"{results['Annualized Volatility']:.2%}",
                                  help="Historical return variability, scaled to a year.")
                        st.metric("Beta", f"{results['Beta']:.3f}",
                                  help="Historical sensitivity to S&P 500 daily movements.")
                        st.metric("Sharpe Ratio", f"{results['Sharpe Ratio']:.3f}",
                                  help="Historical risk-adjusted return using an illustrative 4% annual risk-free rate.")
                        st.metric("Maximum Drawdown", f"{results['Maximum Drawdown']:.2%}",
                                  help="Largest historical decline from a previous peak.")
                        st.metric("S&P 500 Difference", f"{results['Benchmark Difference'] * 100:+.2f} pp",
                                  help="Difference in cumulative returns, in percentage points.")

                    st.write("")
                    with st.expander("What do these metrics mean?"):
                        st.write("**Annualized Return:** Annualized historical portfolio growth.")
                        st.write("**Annualized Volatility:** Historical return variability, scaled to a year.")
                        st.write("**Beta:** Historical sensitivity to S&P 500 daily movements.")
                        st.write("**Sharpe Ratio:** Historical risk-adjusted return using an illustrative 4% annual risk-free rate.")
                        st.write("**Maximum Drawdown:** Largest historical decline from a previous peak.")
                        st.write("**S&P 500 Difference:** Difference in cumulative returns, in percentage points.")

                    # Chart data (same calculations as before)
                    portfolio_returns = results["Portfolio Daily Returns"]
                    portfolio_growth = (1 + portfolio_returns).cumprod() * 100
                    portfolio_growth = pd.concat([
                        pd.Series([100.0], index=[close_prices.index[0]]),
                        portfolio_growth
                    ])
                    market_returns = results["Market Daily Returns"]
                    market_growth = (1 + market_returns).cumprod() * 100
                    market_growth = pd.concat([
                        pd.Series([100.0], index=[close_prices.index[0]]),
                        market_growth
                    ])

                    section("Charts", "Interactive charts: hover to see exact values.")
                    top_left, top_right = st.columns([2, 1])
                    bottom_left, bottom_right = st.columns(2)

                    # Chart 1: portfolio performance
                    with top_left:
                        card_head("Portfolio Performance",
                                  "How $100 invested at the start would have grown with your chosen weights.")
                        fig_performance = px.line(
                            x=portfolio_growth.index, y=portfolio_growth.values,
                            title="Historical Growth of $100",
                            labels={"x": "Date", "y": "Portfolio Value ($)"}
                        )
                        fig_performance.update_layout(showlegend=False, hovermode="x unified")
                        fig_performance.update_traces(line=dict(color=CHART_PRIMARY, width=3))
                        fig_performance.add_hline(y=100, line_dash="dot", line_color="rgba(20,40,25,.3)")
                        show_chart(style_fig(fig_performance))

                    # Chart 3: portfolio allocation
                    with top_right:
                        card_head("Portfolio Allocation",
                                  "How your money is split. Concentrated portfolios tend to be riskier.")
                        allocation_df = pd.DataFrame({
                            "Stock": list(weights.keys()),
                            "Allocation": list(weights.values())
                        })
                        fig_allocation = px.pie(
                            allocation_df, names="Stock", values="Allocation",
                            hole=0.62, title="Portfolio Allocation Breakdown",
                            color_discrete_sequence=PIE_COLORS,
                        )
                        fig_allocation.update_traces(
                            textinfo="label+percent",
                            textfont=dict(color=TEXT),
                            marker=dict(line=dict(color=CARD, width=3)),
                        )
                        fig_allocation.update_layout(showlegend=False)
                        show_chart(style_fig(fig_allocation))

                    # Chart 2: portfolio versus benchmark
                    with bottom_left:
                        card_head("Portfolio vs. S&amp;P 500",
                                  "The same $100 compared with the S&amp;P 500. The higher line grew more.")
                        comparison_df = pd.DataFrame({
                            "Portfolio": portfolio_growth,
                            "S&P 500": market_growth
                        })
                        fig_comparison = px.line(
                            comparison_df, title="Portfolio vs. S&P 500: Growth of $100",
                            labels={"index": "Date", "value": "Value ($)", "variable": "Series"},
                            color_discrete_map={"Portfolio": CHART_PRIMARY, "S&P 500": CHART_SECONDARY},
                        )
                        fig_comparison.update_layout(hovermode="x unified", legend_title_text="")
                        fig_comparison.update_traces(line=dict(width=2.8))
                        show_chart(style_fig(fig_comparison))

                    # Chart 4: correlation heatmap
                    with bottom_right:
                        card_head("Stock Correlation Heatmap",
                                  "Near +1: stocks move together. Near 0: independent. Lower usually means better diversification.")
                        correlation_matrix = results["Correlation Matrix"]
                        fig_correlation = px.imshow(
                            correlation_matrix, text_auto=".2f", zmin=-1, zmax=1,
                            color_continuous_scale=[[0, "#F2A98B"], [0.5, "#FFFFFF"], [1, "#5CBF86"]],
                            title="Correlation Between Stock Daily Returns"
                        )
                        fig_correlation.update_layout(
                            coloraxis_colorbar=dict(thickness=10, outlinewidth=0, tickfont=dict(color=MUTED))
                        )
                        show_chart(style_fig(fig_correlation, grid=False))

                    st.write("")
                    with st.container():
                        card_head("Historical Closing Prices", "The ten most recent trading days in your selected period.")
                        st.dataframe(close_prices.tail(10))

        except Exception as error:
            st.error(
                f"Unable to analyze portfolio: {error}\n\n"
                "Please check your tickers and dates, then try again. "
                "Market data can occasionally be unavailable.",
                icon="⚠️",
            )

html("""
<div class="fl-footer">
<div class="fl-brandline"><span class="fl-logo"></span>Finance Lab &middot; Portfolio Risk Dashboard</div><br>
Historical results do not guarantee future performance.
Calculations assume daily rebalancing, no fees or taxes,
and an illustrative 4% annual risk-free rate.<br>
Market data via Yahoo Finance (yfinance). For education only, not investment advice.
</div>
""")