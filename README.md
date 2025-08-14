# FTSE 350 Earnings-Surprise Tracker & Post-Earnings Drift (Event Study)

This project builds an **event study** around UK earnings. It:
1) Computes **earnings surprises** (Reported EPS vs. Consensus EPS).
2) Groups stocks into **positive / neutral / negative** surprise buckets.
3) Tracks and plots **average cumulative returns** after the announcement (e.g., +1, +5, +20, +60 trading days).
4) Shows evidence (or lack) of **post-earnings announcement drift**.

> **Earnings surprise** = (ReportedEPS - ConsensusEPS) / |ConsensusEPS|

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Option A: Run the notebook
jupyter lab notebooks/earnings_event_study.ipynb

# Option B: Run from the CLI
python src/event_study.py --earnings_csv data/sample_earnings.csv --tickers_csv data/sample_ftse350.csv --prices_source sample --window 60
```

Use `--prices_source yfinance` to fetch live prices (internet required).  
London tickers typically end with `.L` (e.g., VOD.L).

## Data schema

- **earnings CSV** (`data/sample_earnings.csv`):  
  `Ticker,Date,ConsensusEPS,ReportedEPS` with dates in `YYYY-MM-DD`.

- **tickers CSV** (`data/sample_ftse350.csv`):  
  `Ticker` one per line.

## Method

1. Build an **event calendar** from the earnings file.
2. Calculate surprise %.
3. For each event, align forward returns over horizons (1,5,20,60d).
4. Average cumulative returns by surprise bucket and plot the drift curves.

## Outputs
- `outputs/drift_plot.png`: average cumulative return by bucket.
- `outputs/event_metrics.csv`: per-event surprises and forward returns.

