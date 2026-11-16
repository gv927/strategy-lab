#!/usr/bin/env python3
"""
ARES — Chief Market Structure & Condition Analyst
HERMES PRIME Trading System
Cycle 1 Market Regime Analysis: 2021-2025
"""

import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = "/home/ubuntu/Desktop/data-download/historical_data"
OUTPUT_PATH = "/home/ubuntu/Desktop/pz4/.obsidian/HERMES_PRIME/Analysis/ARES_Cycle1_2025-06-02.md"

# ============================================================
# CONFIGURATION
# ============================================================
INSTRUMENTS = {
    "EUR/USD": {
        "tf5": "eurusd_5min_master.csv",
        "tf1h": "eurusd_1h_master.csv",
        "tf4h": "eurusd_4h_master.csv",
        "pip_size": 0.0001,
        "pip_name": "pips",
        "category": "Major FX",
    },
    "XAU/USD": {
        "tf5": "xauusd_5min_master.csv",
        "tf1h": "xauusd_1h_master.csv",
        "tf4h": "xauusd_4h_master.csv",
        "pip_size": 0.01,
        "pip_name": "pips",
        "category": "Commodity",
    },
    "US30": {
        "tf5": "usa30idxusd_5min_master.csv",
        "tf1h": "usa30idxusd_1h_master.csv",
        "tf4h": "usa30idxusd_4h_master.csv",
        "pip_size": 1.0,
        "pip_name": "points",
        "category": "Index",
    },
    "GBP/JPY": {
        "tf5": "gbpjpy_5min_master.csv",
        "tf1h": "gbpjpy_1h_master.csv",
        "tf4h": "gbpjpy_4h_master.csv",
        "pip_size": 0.01,
        "pip_name": "pips",
        "category": "Cross FX",
    },
}

YEARS = [2021, 2022, 2023, 2024, 2025]

# Session definitions (UTC hours)
SESSIONS = {
    "Asian": (0, 8),
    "London": (7, 16),
    "NY": (12, 21),
    "London/NY Overlap": (12, 16),
    "Asian/London Overlap": (7, 9),
}

# ============================================================
# DATA LOADING
# ============================================================
def load_csv(filepath):
    """Load a single CSV file with standard column names."""
    df = pd.read_csv(filepath, parse_dates=["Timestamp"])
    df.rename(columns={"Timestamp": "datetime"}, inplace=True)
    df.sort_values("datetime", inplace=True)
    df.reset_index(drop=True, inplace=True)
    # Standardize column names
    for col in ["open", "high", "low", "close", "volume"]:
        if col not in df.columns:
            df[col] = np.nan
    return df

def load_instrument(config):
    """Load all timeframes for an instrument."""
    data = {}
    for tf_key, fname in [("5m", config["tf5"]), ("1h", config["tf1h"]), ("4h", config["tf4h"])]:
        path = os.path.join(DATA_DIR, fname)
        if os.path.exists(path):
            data[tf_key] = load_csv(path)
        else:
            print(f"  WARNING: Missing {path}")
            data[tf_key] = pd.DataFrame()
    return data

# ============================================================
# TECHNICAL INDICATORS
# ============================================================
def compute_atr(df, period=14):
    """Compute Average True Range."""
    high = df["high"]
    low = df["low"]
    close = df["close"]
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    return atr, tr

def compute_adx(df, period=14):
    """Compute ADX, +DI, -DI."""
    high = df["high"]
    low = df["low"]
    close = df["close"]
    
    plus_dm = high.diff()
    minus_dm = -low.diff()
    
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0.0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0.0)
    
    atr, tr = compute_atr(df, period)
    
    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
    
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(period).mean()
    
    return adx, plus_di, minus_di

def compute_daily_stats(df_1h, pip_size):
    """Compute daily OHLC from hourly data."""
    df = df_1h.copy()
    df["date"] = df["datetime"].dt.date
    daily = df.groupby("date").agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
    ).reset_index()
    daily["range"] = (daily["high"] - daily["low"]) / pip_size
    daily["body"] = abs(daily["close"] - daily["open"]) / pip_size
    daily["change_pct"] = daily["close"].pct_change() * 100
    daily["direction"] = np.where(daily["close"] > daily["open"], "UP", 
                           np.where(daily["close"] < daily["open"], "DOWN", "FLAT"))
    return daily

# ============================================================
# REGIME CLASSIFICATION
# ============================================================
def classify_regime(avg_adx, avg_atr_norm, vol_of_vol, trend_consistency):
    """
    Classify market regime based on multiple indicators.
    
    TRENDING: High ADX (>25), moderate volatility, high directional consistency
    RANGING: Low ADX (<20), low volatility, low directional consistency
    VOLATILE: High ATR, high vol-of-vol regardless of ADX
    CHOPPY: Moderate ADX but high vol-of-vol, low trend consistency (whipsaw)
    """
    # Score-based classification
    trend_score = 0
    range_score = 0
    volatile_score = 0
    choppy_score = 0
    
    # ADX scoring
    if avg_adx >= 35:
        trend_score += 3
    elif avg_adx >= 25:
        trend_score += 2
    elif avg_adx >= 20:
        trend_score += 1
        range_score += 1
    elif avg_adx >= 15:
        range_score += 2
    else:
        range_score += 3
    
    # Volatility scoring
    if avg_atr_norm > 1.5:
        volatile_score += 3
        choppy_score += 1
    elif avg_atr_norm > 1.0:
        volatile_score += 1
        choppy_score += 1
    elif avg_atr_norm < 0.6:
        range_score += 2
    else:
        range_score += 1
    
    # Vol-of-vol scoring
    if vol_of_vol > 0.6:
        volatile_score += 2
        choppy_score += 2
    elif vol_of_vol > 0.4:
        choppy_score += 1
    else:
        range_score += 1
    
    # Trend consistency scoring
    if trend_consistency > 0.65:
        trend_score += 2
    elif trend_consistency > 0.5:
        trend_score += 1
    else:
        choppy_score += 2
        range_score += 1
    
    scores = {
        "TRENDING": trend_score,
        "RANGING": range_score,
        "VOLATILE": volatile_score,
        "CHOPPY": choppy_score,
    }
    
    regime = max(scores, key=scores.get)
    
    # Override: if volatility is extreme, always volatile
    if avg_atr_norm > 2.0:
        regime = "VOLATILE"
    
    return regime, scores

def best_strategy(regime):
    """Return best strategy type for a given regime."""
    strategies = {
        "TRENDING": "Trend-following (breakout entries, trailing stops, pyramid on pullbacks)",
        "RANGING": "Mean-reversion (support/resistance bounces, fade extremes, tight targets)",
        "VOLATILE": "Reduced position size + wide stops (breakout with confirmation, avoid counter-trend)",
        "CHOPPY": "Avoid or minimal size (wait for clarity, no trend-following, no mean-reversion, scalp only)",
    }
    return strategies.get(regime, "N/A")

# ============================================================
# YEAR-BY-YEAR ANALYSIS
# ============================================================
def analyze_year(df_4h, df_1h, df_5m, year, pip_size, pip_name):
    """Analyze a single year for a single instrument."""
    # Filter by year
    df4h = df_4h[df_4h["datetime"].dt.year == year].copy()
    df1h = df_1h[df_1h["datetime"].dt.year == year].copy()
    df5m = df_5m[df_5m["datetime"].dt.year == year].copy()
    
    if len(df4h) < 50 or len(df1h) < 100:
        return None
    
    # --- ATR on 4H ---
    atr_4h, tr_4h = compute_atr(df4h, 14)
    avg_atr_4h = atr_4h.mean()
    
    # --- ADX on 4H ---
    adx_4h, plus_di, minus_di = compute_adx(df4h, 14)
    avg_adx = adx_4h.mean()
    avg_plus_di = plus_di.mean()
    avg_minus_di = minus_di.mean()
    
    # --- Daily stats from 1H ---
    daily = compute_daily_stats(df1h, pip_size)
    daily["year"] = pd.to_datetime(daily["date"]).dt.year
    daily_yr = daily[daily["year"] == year].copy()
    
    if len(daily_yr) < 10:
        return None
    
    avg_daily_range = daily_yr["range"].mean()
    median_daily_range = daily_yr["range"].median()
    max_daily_range = daily_yr["range"].max()
    
    # ATR normalised: compare this year's ATR to multi-year average (computed later)
    # For now, store raw
    atr_in_pips = avg_atr_4h / pip_size
    
    # Vol-of-vol: standard deviation of daily range / mean of daily range
    vol_of_vol = daily_yr["range"].std() / daily_yr["range"].mean() if daily_yr["range"].mean() > 0 else 0
    
    # Trend consistency: % of days where direction was same as previous day
    daily_yr["dir_change"] = (daily_yr["direction"] != daily_yr["direction"].shift(1)).astype(int)
    trend_consistency = 1 - daily_yr["dir_change"].mean()
    
    # Trend days vs range days
    # Trend day: daily range > 1.5x ATR and close near high/low
    daily_atr = daily_yr["range"].rolling(14).mean()
    daily_yr["is_trend_day"] = (
        (daily_yr["range"] > daily_atr * 1.3) & 
        (daily_yr["body"] / daily_yr["range"].replace(0, np.nan) > 0.5)
    ).astype(int)
    n_trend_days = daily_yr["is_trend_day"].sum()
    n_range_days = len(daily_yr) - n_trend_days
    total_days = len(daily_yr)
    
    # Regime classification
    # Normalize ATR across years (will do after)
    regime, scores = classify_regime(avg_adx, 1.0, vol_of_vol, trend_consistency)
    
    # Key events: top 5 volatility spikes (by daily range)
    top_events = daily_yr.nlargest(5, "range")[["date", "range", "direction"]].values
    
    # Dangerous periods: extreme volatility (daily range > 3x average)
    danger_threshold = avg_daily_range * 3
    dangerous = daily_yr[daily_yr["range"] > danger_threshold][["date", "range"]].values
    
    # Session analysis from 1H data
    session_stats = {}
    for session_name, (start_h, end_h) in SESSIONS.items():
        mask = (df1h["datetime"].dt.hour >= start_h) & (df1h["datetime"].dt.hour < end_h)
        sess = df1h[mask].copy()
        if len(sess) < 10:
            session_stats[session_name] = {"avg_range_pips": 0, "avg_atr_pips": 0, "quality_score": 0}
            continue
        sess["bar_range"] = (sess["high"] - sess["low"]) / pip_size
        sess_atr, _ = compute_atr(sess, 14)
        avg_sess_range = sess["bar_range"].mean()
        avg_sess_atr = sess_atr.mean() / pip_size if not np.isnan(sess_atr.mean()) else 0
        # Quality score: higher ATR/range ratio = more directional = better
        quality = min(avg_sess_atr / avg_sess_range, 1.0) * 100 if avg_sess_range > 0 else 0
        session_stats[session_name] = {
            "avg_range_pips": round(avg_sess_range, 2),
            "avg_atr_pips": round(avg_sess_atr, 2),
            "quality_score": round(quality, 1),
        }
    
    return {
        "year": year,
        "avg_adx": round(avg_adx, 2),
        "avg_plus_di": round(avg_plus_di, 2),
        "avg_minus_di": round(avg_minus_di, 2),
        "avg_atr_4h_pips": round(atr_in_pips, 2),
        "avg_daily_range": round(avg_daily_range, 2),
        "median_daily_range": round(median_daily_range, 2),
        "max_daily_range": round(max_daily_range, 2),
        "vol_of_vol": round(vol_of_vol, 3),
        "trend_consistency": round(trend_consistency, 3),
        "n_trend_days": int(n_trend_days),
        "n_range_days": int(n_range_days),
        "total_days": total_days,
        "regime": regime,
        "regime_scores": scores,
        "best_strategy": best_strategy(regime),
        "top_events": top_events,
        "dangerous_periods": dangerous,
        "session_stats": session_stats,
    }

# ============================================================
# CROSS-INSTRUMENT CORRELATION
# ============================================================
def compute_correlations(all_1h_data, year):
    """Compute correlation matrix between instruments for a given year."""
    returns = {}
    for inst_name, df_1h in all_1h_data.items():
        yr = df_1h[df_1h["datetime"].dt.year == year].copy()
        if len(yr) < 50:
            continue
        yr["return"] = yr["close"].pct_change()
        yr = yr.set_index("datetime")
        returns[inst_name] = yr["return"]
    
    ret_df = pd.DataFrame(returns)
    ret_df = ret_df.dropna()
    if len(ret_df) < 10:
        return None
    
    return ret_df.corr()

# ============================================================
# MAIN ANALYSIS
# ============================================================
def run_analysis():
    print("=" * 60)
    print("ARES — HERMES PRIME Market Regime Analysis")
    print("=" * 60)
    
    # Load all data
    all_data = {}
    all_1h = {}
    all_4h = {}
    
    for inst_name, config in INSTRUMENTS.items():
        print(f"\nLoading {inst_name}...")
        data = load_instrument(config)
        all_data[inst_name] = data
        all_1h[inst_name] = data["1h"]
        all_4h[inst_name] = data["4h"]
        for tf, df in data.items():
            print(f"  {tf}: {len(df)} rows, {df['datetime'].min()} → {df['datetime'].max()}")
    
    # Analyze each instrument per year
    results = {}
    for inst_name, config in INSTRUMENTS.items():
        print(f"\nAnalyzing {inst_name}...")
        inst_results = []
        raw_atrs = []
        
        # First pass: collect raw ATRs for normalization
        for year in YEARS:
            r = analyze_year(
                all_data[inst_name]["4h"],
                all_data[inst_name]["1h"],
                all_data[inst_name]["5m"],
                year, config["pip_size"], config["pip_name"]
            )
            if r:
                raw_atrs.append(r["avg_atr_4h_pips"])
                inst_results.append(r)
        
        # Normalize ATR across years
        if raw_atrs:
            mean_atr = np.mean(raw_atrs)
            std_atr = np.std(raw_atrs) if len(raw_atrs) > 1 else 0.1
            for r in inst_results:
                r["atr_normalized"] = round((r["avg_atr_4h_pips"] - mean_atr) / max(std_atr, 0.01) + 1.0, 2)
                # Re-classify with normalized ATR
                r["regime"], r["regime_scores"] = classify_regime(
                    r["avg_adx"], r["atr_normalized"], r["vol_of_vol"], r["trend_consistency"]
                )
                r["best_strategy"] = best_strategy(r["regime"])
        
        results[inst_name] = inst_results
    
    # Compute correlations per year
    correlations = {}
    for year in YEARS:
        corr = compute_correlations(all_1h, year)
        if corr is not None:
            correlations[year] = corr
    
    # ============================================================
    # BUILD REPORT
    # ============================================================
    report = []
    report.append("# ARES Market Analysis Report — Cycle 1")
    report.append(f"**Date**: 2025-06-02  ")
    report.append(f"**Agent**: ARES (Agent 04) — Chief Market Structure & Condition Analyst  ")
    report.append(f"**System**: HERMES PRIME  ")
    report.append(f"**Classification**: UNCLASSIFIED // HERMES INTERNAL  ")
    report.append("")
    report.append("---")
    report.append("")
    
    # EXECUTIVE SUMMARY
    report.append("## Executive Summary")
    report.append("")
    
    # Summarize regimes
    regime_summary = {}
    for inst_name, inst_results in results.items():
        for r in inst_results:
            regime = r["regime"]
            if regime not in regime_summary:
                regime_summary[regime] = []
            regime_summary[regime].append(f"{inst_name} {r['year']}")
    
    report.append("### Regime Distribution Overview")
    report.append("")
    for regime, occurrences in sorted(regime_summary.items()):
        report.append(f"- **{regime}**: {len(occurrences)} instrument-year combinations — {', '.join(occurrences[:6])}{'...' if len(occurrences) > 6 else ''}")
    report.append("")
    
    # Key findings
    report.append("### Key Findings")
    report.append("")
    
    # Find most trending and most ranging
    all_regime_results = []
    for inst_name, inst_results in results.items():
        for r in inst_results:
            all_regime_results.append((inst_name, r))
    
    trending_items = [x for x in all_regime_results if x[1]["regime"] == "TRENDING"]
    ranging_items = [x for x in all_regime_results if x[1]["regime"] == "RANGING"]
    volatile_items = [x for x in all_regime_results if x[1]["regime"] == "VOLATILE"]
    choppy_items = [x for x in all_regime_results if x[1]["regime"] == "CHOPPY"]
    
    # Highest ADX periods
    top_adx = sorted(all_regime_results, key=lambda x: x[1]["avg_adx"], reverse=True)[:3]
    # Lowest ADX periods
    low_adx = sorted(all_regime_results, key=lambda x: x[1]["avg_adx"])[:3]
    # Highest volatility periods
    top_vol = sorted(all_regime_results, key=lambda x: x[1]["avg_daily_range"], reverse=True)[:3]
    
    report.append(f"- **Strongest Trend Periods**: {', '.join([f'{x[0]} {x[1][\"year\"]} (ADX={x[1][\"avg_adx\"]})' for x in top_adx])}")
    report.append(f"- **Weakest/Rangiest Periods**: {', '.join([f'{x[0]} {x[1][\"year\"]} (ADX={x[1][\"avg_adx\"]})' for x in low_adx])}")
    report.append(f"- **Highest Volatility Periods**: {', '.join([f'{x[0]} {x[1][\"year\"]} (Range={x[1][\"avg_daily_range\"]:.1f} {INSTRUMENTS[x[0]][\"pip_name\"]})' for x in top_vol])}")
    report.append("")
    
    # Strategy adaptation recommendations
    report.append("### Strategy Adaptation Recommendations")
    report.append("")
    report.append("1. **TRENDING Regimes**: Deploy trend-following strategies with breakout entries. Use 4H ADX > 25 as filter. Pyramid on pullbacks to 20 EMA. Trailing stops at 2x ATR.")
    report.append("2. **RANGING Regimes**: Switch to mean-reversion. Trade support/resistance bounces. Tight targets at 1.5x risk. Avoid breakout systems.")
    report.append("3. **VOLATILE Regimes**: Reduce position size by 50%. Widen stops to 3x ATR. Trade only with confirmed direction. Avoid news spikes.")
    report.append("4. **CHOPPY Regimes**: Stand aside or scalp only. No directional bias. Reduce frequency. Wait for regime transition confirmed by ADX crossing 25.")
    report.append("")
    report.append("### Correlation Warnings")
    report.append("")
    for year, corr_df in correlations.items():
        # Find high correlations
        high_corr_pairs = []
        for i in range(len(corr_df.columns)):
            for j in range(i+1, len(corr_df.columns)):
                val = corr_df.iloc[i, j]
                if abs(val) > 0.5:
                    high_corr_pairs.append((corr_df.columns[i], corr_df.columns[j], val))
        if high_corr_pairs:
            report.append(f"**{year}**: " + ", ".join([f"{p[0]}/{p[1]} = {p[2]:.2f}" for p in sorted(high_corr_pairs, key=lambda x: abs(x[2]), reverse=True)]))
    report.append("")
    
    report.append("---")
    report.append("")
    
    # ============================================================
    # PER-INSTRUMENT SECTIONS
    # ============================================================
    for inst_name, config in INSTRUMENTS.items():
        inst_results = results.get(inst_name, [])
        if not inst_results:
            continue
        
        report.append(f"## {inst_name} — Detailed Analysis")
        report.append("")
        report.append(f"**Category**: {config['category']}  ")
        report.append(f"**Pip Size**: {config['pip_size']} ({config['pip_name']})  ")
        report.append("")
        
        # Year-by-year table
        report.append("### Year-by-Year Regime Classification")
        report.append("")
        
        # Build table rows
        for r in inst_results:
            report.append(f"**{r['year']}**")
            report.append(f"- Regime: **{r['regime']}**")
            report.append(f"- ADX: {r['avg_adx']} | +DI: {r['avg_plus_di']} | -DI: {r['avg_minus_di']}")
            report.append(f"- ATR (4H): {r['avg_atr_4h_pips']} {config['pip_name']} | ATR Normalized: {r['atr_normalized']}")
            report.append(f"- Avg Daily Range: {r['avg_daily_range']:.1f} {config['pip_name']} | Median: {r['median_daily_range']:.1f} | Max: {r['max_daily_range']:.1f}")
            report.append(f"- Vol-of-Vol: {r['vol_of_vol']} | Trend Consistency: {r['trend_consistency']}")
            report.append(f"- Trend Days: {r['n_trend_days']} | Range Days: {r['n_range_days']} | Total: {r['total_days']}")
            report.append(f"- Best Strategy: {r['best_strategy']}")
            
            # Key events
            if len(r['top_events']) > 0:
                report.append("- Key Volatility Events:")
                for evt in r['top_events']:
                    report.append(f"  - {evt[0]}: {evt[1]:.1f} {config['pip_name']} range ({evt[2]})")
            
            # Dangerous periods
            if len(r['dangerous_periods']) > 0:
                report.append(f"- ⚠️ Dangerous Periods: {len(r['dangerous_periods'])} days with range > 3x average")
                for dp in r['dangerous_periods'][:5]:
                    report.append(f"  - {dp[0]}: {dp[1]:.1f} {config['pip_name']}")
            
            report.append("")
        
        # Session analysis
        report.append(f"### {inst_name} — Session Analysis")
        report.append("")
        report.append("Session quality across all years (aggregated):")
        report.append("")
        
        # Aggregate session stats across years
        agg_sessions = {}
        for r in inst_results:
            for sess_name, stats in r["session_stats"].items():
                if sess_name not in agg_sessions:
                    agg_sessions[sess_name] = {"ranges": [], "atrs": [], "qualities": []}
                agg_sessions[sess_name]["ranges"].append(stats["avg_range_pips"])
                agg_sessions[sess_name]["atrs"].append(stats["avg_atr_pips"])
                agg_sessions[sess_name]["qualities"].append(stats["quality_score"])
        
        for sess_name in ["Asian", "London", "NY", "London/NY Overlap", "Asian/London Overlap"]:
            if sess_name in agg_sessions:
                s = agg_sessions[sess_name]
                avg_q = np.mean(s["qualities"]) if s["qualities"] else 0
                avg_r = np.mean(s["ranges"]) if s["ranges"] else 0
                avg_a = np.mean(s["atrs"]) if s["atrs"] else 0
                report.append(f"- **{sess_name}**: Avg Range={avg_r:.2f} {config['pip_name']}, Avg ATR={avg_a:.2f}, Quality Score={avg_q:.1f}/100")
        
        report.append("")
        report.append("---")
        report.append("")
    
    # ============================================================
    # CORRELATION MATRICES
    # ============================================================
    report.append("## Cross-Instrument Correlations")
    report.append("")
    report.append("Correlation of hourly returns between instruments, by year:")
    report.append("")
    
    for year in YEARS:
        if year in correlations:
            corr_df = correlations[year]
            report.append(f"### {year}")
            report.append("")
            for i, col in enumerate(corr_df.columns):
                row_vals = []
                for j in range(len(corr_df.columns)):
                    val = corr_df.iloc[i, j]
                    row_vals.append(f"{val:.2f}")
                report.append(f"- **{col}**: {', '.join(row_vals)}")
            report.append("")
    
    report.append("---")
    report.append("")
    
    # ============================================================
    # DANGEROUS PERIODS COMPILATION
    # ============================================================
    report.append("## ⚠️ Dangerous Periods — Master List")
    report.append("")
    report.append("Extreme volatility events across all instruments. Avoid trading or reduce position to 25% normal size during similar conditions.")
    report.append("")
    
    for inst_name, inst_results in results.items():
        all_danger = []
        for r in inst_results:
            for dp in r['dangerous_periods']:
                all_danger.append((r['year'], dp[0], dp[1]))
        if all_danger:
            report.append(f"### {inst_name}")
            report.append("")
            for d in sorted(all_danger, key=lambda x: x[2], reverse=True)[:10]:
                report.append(f"- {d[1]}: **{d[2]:.1f} {INSTRUMENTS[inst_name]['pip_name']}** range (3x+ normal)")
            report.append("")
    
    # ============================================================
    # OPTIMAL TRADING WINDOWS
    # ============================================================
    report.append("## Optimal Trading Windows")
    report.append("")
    report.append("Best trading sessions ranked by quality score per instrument:")
    report.append("")
    
    for inst_name, inst_results in results.items():
        agg_sessions = {}
        for r in inst_results:
            for sess_name, stats in r["session_stats"].items():
                if sess_name not in agg_sessions:
                    agg_sessions[sess_name] = {"qualities": []}
                agg_sessions[sess_name]["qualities"].append(stats["quality_score"])
        
        ranked = []
        for sess_name, s in agg_sessions.items():
            avg_q = np.mean(s["qualities"]) if s["qualities"] else 0
            ranked.append((sess_name, avg_q))
        ranked.sort(key=lambda x: x[1], reverse=True)
        
        report.append(f"**{inst_name}**:")
        for rank, (sess_name, quality) in enumerate(ranked, 1):
            grade = "A" if quality >= 70 else "B" if quality >= 50 else "C" if quality >= 30 else "D"
            report.append(f"  {rank}. {sess_name}: Quality={quality:.0f}/100 (Grade {grade})")
        report.append("")
    
    report.append("---")
    report.append("")
    
    # ============================================================
    # METHODOLOGY
    # ============================================================
    report.append("## Methodology")
    report.append("")
    report.append("- **Data Source**: 5min, 1H, 4H OHLCV CSV files from broker historical data")
    report.append("- **Time Period**: 2021–2025 (5 full years)")
    report.append("- **ATR**: 14-period Average True Range computed on 4H candles")
    report.append("- **ADX**: 14-period Average Directional Index computed on 4H candles")
    report.append("- **Daily Stats**: Aggregated from 1H candles (UTC daily boundary)")
    report.append("- **Trend Day**: Daily range > 1.3x rolling 14-day ATR AND body > 50% of range")
    report.append("- **Regime Classification**: Multi-factor scoring using ADX, normalized ATR, volatility-of-volatility, and trend consistency")
    report.append("- **Session Definitions**: Asian (00-08 UTC), London (07-16 UTC), NY (12-21 UTC), Overlaps as intersection")
    report.append("- **Quality Score**: min(ATR/Range, 1.0) × 100 — measures how directional a session is")
    report.append("- **Correlation**: Pearson correlation of hourly log-returns")
    report.append("")
    
    report.append("---")
    report.append("")
    report.append("*Report generated by ARES — Agent 04 of HERMES PRIME*  ")
    report.append("*Cycle 1 — 2025-06-02*  ")
    report.append("*Feed: ARCHITECT (strategy design), AEGIS (risk assessment)*")
    
    # Write report
    report_text = "\n".join(report)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        f.write(report_text)
    
    print(f"\n{'='*60}")
    print(f"Report saved to: {OUTPUT_PATH}")
    print(f"Report length: {len(report_text)} characters, {len(report)} lines")
    print(f"{'='*60}")
    
    return results, correlations

if __name__ == "__main__":
    results, correlations = run_analysis()
