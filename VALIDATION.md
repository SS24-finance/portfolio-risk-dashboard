# V1.1 verification and deployment handoff

Verified locally on November 17, 2026. No push, merge, or deployment performed.

## Checkpoint and repository

Before editing, the source files were saved in
`checkpoints/before-v1.1-fixes-20261117-190529.zip`. Archive integrity passed.
This checkpoint also preserves the pre-existing uncommitted edits in `app.py`;
they were not reverted. Git's HEAD differs from that original working copy.

- Repository: https://github.com/SS24-finance/portfolio-risk-dashboard
- Current branch: `ui-redesign`.
- Local HEAD: `35a312a` (`Update app.py`).
- Local tracking reference: `origin/ui-redesign`, at the same commit when inspected.
- Local `main` / `origin/main`: `964cdcc`.
- Remote references were inspected locally, not refreshed from GitHub.
- No existing tracked Cloud workflow or theme configuration was present.
  README mentioned a theme file that was absent; a light theme file now exists.
- System `/usr/bin/git` cannot run without Apple's developer tools. GitHub
  Desktop's bundled Git works and was used for status, history, and diff checks:
  `/Applications/GitHub Desktop.app/Contents/Resources/app/git/bin/git`.

## Checks passed

- 24 automated unittest/AppTest tests passed.
- Syntax compilation passed for both application files and both test files.
- `pip check`: no broken dependency requirements.
- `git diff --check`: no whitespace errors.
- Streamlit started successfully on http://127.0.0.1:8501.
- Browser inspection confirmed the green/cream/white layout, readable controls,
  and the pastel-green beginner button with dark-green text.
- Clicking the beginner button populated AAPL/MSFT at 50% each and the dates
  January 1, 2025 to January 1, 2026.
- Live Yahoo analysis succeeded over January 2 through December 31, 2025:
  six headline metrics, two drawdown comparison cards, four Plotly charts,
  the historical-price table, and assumptions appeared without an app error.
- Live example smoke-check values: annualized return 15.60%, volatility 24.55%,
  beta 1.105, Sharpe 0.551, maximum drawdown -23.91%, benchmark difference
  -1.24 percentage points. These are observations, not immutable test fixtures;
  provider adjustments can change historical prices.
- Browser testing initially found a Yahoo cache `database is locked` error.
  Downloads now run sequentially (`threads=False`), and the repeat live test
  succeeded. Conflicting widget defaults were also removed.

Automated coverage includes known financial answers, initial losses, flat
prices, weight order and rounding, invalid weights/prices, missing benchmark or
ticker data, interior gaps, trimmed edges, insufficient history, duplicate
symbols, ticker count limits, empty inputs, invalid dates, simulated network
failure, saved allocations after reorder/remove/re-add, custom dates, beginner
reset, N/A ratios, and creation of every chart and metric.

## Limits and remaining deployment checks

The Cloud management page opened to a sign-in screen. The existing website's
URL, deployed branch, Python version, build logs, and remote production behavior
could not be verified. No Cloud settings were changed.

Local tests used Python 3.14.10 on macOS. The pinned versions of Streamlit,
pandas, NumPy, yfinance, and Plotly were installed and tested locally. NumPy's
pinned version requires Python >=3.12. The Linux Cloud build has not been run.

The missing-price safeguard detects holes in returned price rows. It does not
independently detect trading sessions omitted entirely by the provider. Yahoo
availability and rate limits remain external dependencies.

## Exact next step for the existing website

1. Sign into https://share.streamlit.io/ and inspect the existing app's settings.
   Confirm its repository is `SS24-finance/portfolio-risk-dashboard`, its
   entrypoint is `app.py`, its deployed branch, and a compatible Python version
   (at least 3.12; local testing used 3.14).
2. Before publication, verify the remote branch state and review these local
   changes, including the pre-existing `app.py` edits preserved in the checkpoint.
3. With explicit user approval, commit the reviewed files and update the branch
   already connected to the existing app. If it is `ui-redesign`, push that
   branch. If it is `main`, review and approve the merge into `main` first; do
   not assume pushing `ui-redesign` updates a site connected to `main`.
4. Community Cloud automatically updates from its connected branch. Dependency
   changes trigger a rebuild. Review the build logs, then run the beginner
   example on the existing public URL. Do not create a replacement repository
   or app, and do not delete the existing site to resolve configuration issues.

Source: https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app
Python environment rules:
https://docs.streamlit.io/deploy/streamlit-community-cloud/status
