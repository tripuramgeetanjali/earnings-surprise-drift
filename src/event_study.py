import argparse, os
import pandas as pd, numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def load_prices(tickers, start, end, source='yfinance', sample_prices=None):
    if source == 'sample':
        if sample_prices is None:
            raise ValueError('sample_prices path required for source=sample')
        df = pd.read_csv(sample_prices, parse_dates=['Date']).set_index('Date')
        # ensure all requested tickers exist; fill if missing
        missing = [t for t in tickers if t not in df.columns]
        for m in missing:
            df[m] = df.iloc[:,0].values  # duplicate first as placeholder
        return df[tickers].dropna(how='all')
    else:
        import yfinance as yf
        data = yf.download(tickers, start=start, end=end, progress=False)['Adj Close']
        if isinstance(data, pd.Series):
            data = data.to_frame()
        data = data.dropna(how='all')
        data.columns = [c if isinstance(c, str) else c[1] for c in data.columns]
        return data

def compute_surprise(row):
    cons = row['ConsensusEPS']
    rep = row['ReportedEPS']
    if cons == 0 or pd.isna(cons) or pd.isna(rep):
        return np.nan
    return (rep - cons) / abs(cons)

def bucket_surprise(s):
    if pd.isna(s):
        return 'NA'
    if s > 0.05:
        return 'Positive (>+5%)'
    elif s < -0.05:
        return 'Negative (<-5%)'
    else:
        return 'Neutral (-5%..+5%)'

def forward_returns(prices, event_date, ticker, horizons=(1,5,20,60)):
    if ticker not in prices.columns:
        return {f'+{h}d': np.nan for h in horizons}
    series = prices[ticker].dropna()
    if event_date not in series.index:
        # pick next available trading day
        idx = series.index.searchsorted(event_date)
        if idx >= len(series):
            return {f'+{h}d': np.nan for h in horizons}
        event_date = series.index[idx]
    base = series.loc[event_date]
    out = {}
    for h in horizons:
        idx = series.index.searchsorted(event_date) + h
        if idx < len(series):
            fwd = series.iloc[idx] / base - 1.0
        else:
            fwd = np.nan
        out[f'+{h}d'] = fwd
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--earnings_csv', type=str, required=True)
    ap.add_argument('--tickers_csv', type=str, required=True)
    ap.add_argument('--start', type=str, default='2023-01-01')
    ap.add_argument('--end', type=str, default=datetime.today().strftime('%Y-%m-%d'))
    ap.add_argument('--prices_source', type=str, choices=['yfinance','sample'], default='sample')
    ap.add_argument('--sample_prices', type=str, default='data/sample_prices.csv')
    ap.add_argument('--window', type=int, default=60)
    ap.add_argument('--outdir', type=str, default='outputs')
    args = ap.parse_args()

    earnings = pd.read_csv(args.earnings_csv, parse_dates=['Date'])
    tickers = pd.read_csv(args.tickers_csv)['Ticker'].dropna().astype(str).tolist()
    unique_tickers = sorted(set(tickers) | set(earnings['Ticker'].dropna().astype(str).tolist()))

    # Price window: include window days after max earnings date
    start = args.start
    end = args.end
    prices = load_prices(unique_tickers, start, end, source=args.prices_source, sample_prices=args.sample_prices)

    earnings['Surprise'] = earnings.apply(compute_surprise, axis=1)
    earnings['Bucket'] = earnings['Surprise'].apply(bucket_surprise)

    horizons = (1,5,20,60)
    fwd_rows = []
    for _, row in earnings.iterrows():
        fwd = forward_returns(prices, row['Date'], row['Ticker'], horizons=horizons)
        fwd_rows.append(fwd)
    fwd_df = pd.DataFrame(fwd_rows)
    result = pd.concat([earnings, fwd_df], axis=1)

    os.makedirs(args.outdir, exist_ok=True)
    result.to_csv(os.path.join(args.outdir, 'event_metrics.csv'), index=False)

    # Plot average cumulative returns by bucket
    agg = result.groupby('Bucket')[[f'+{h}d' for h in horizons]].mean().T
    agg.index = [int(s.strip('+d')) for s in agg.index.str.replace('+','').str.replace('d','')]

    plt.figure()
    for bucket in ['Positive (>+5%)','Neutral (-5%..+5%)','Negative (<-5%)']:
        if bucket in agg.columns:
            agg[bucket].sort_index().plot(label=bucket)
    plt.legend()
    plt.title('Average Post-Earnings Drift by Surprise Bucket')
    plt.xlabel('Days after earnings'); plt.ylabel('Average return')
    plt.tight_layout()
    plt.savefig(os.path.join(args.outdir, 'drift_plot.png'))
    plt.close()

    print('Wrote:', os.path.join(args.outdir, 'event_metrics.csv'))
    print('Wrote:', os.path.join(args.outdir, 'drift_plot.png'))

if __name__ == '__main__':
    main()
