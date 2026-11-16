#!/usr/bin/env python3
"""
ARES — Market Condition Analyst
Session Intelligence Tables for HERMES PRIME v3
Computes ATR(14) per session block for XAU/USD, EUR/USD, GBP/USD, GBP/JPY, USD/JPY
"""

import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = "/home/ubuntu/Desktop/data-download/historical_data"

# Key instruments
INSTRUMENTS = {
    'xauusd': {'name': 'XAU/USD', 'pip_size': 0.01, 'ref_spread': 0.25, 'category': 'GOLD'},
    'eurusd': {'name': 'EUR/USD', 'pip_size': 0.0001, 'ref_spread': 0.08, 'category': 'MAJOR'},
    'gbpusd': {'name': 'GBP/USD', 'pip_size': 0.0001, 'ref_spread': 0.10, 'category': 'MAJOR'},
    'gbpjpy': {'name': 'GBP/JPY', 'pip_size': 0.01, 'ref_spread': 0.20, 'category': 'CROSS'},
    'usdjpy': {'name': 'USD/JPY', 'pip_size': 0.01, 'ref_spread': 0.08, 'category': 'MAJOR'},
}

# Session blocks (UTC hours)
SESSIONS = {
    'Asian':          (21, 6),   # 21:00-06:00 (overnight wrap)
    'Pre-London':     (6, 8),    # 06:00-08:00
    'London Open':    (8, 12),   # 08:00-12:00
    'London+NY':      (12, 15),  # 12:00-15:00
    'NY Open':        (13, 17),  # 13:30-17:00 (we'll use 13:00-17:00 for simplicity with bar alignment)
    'NY Afternoon':   (17, 21),  # 17:00-21:00
}

def assign_session(hour):
    """Assign a UTC hour to a session block. Asian wraps midnight."""
    if hour >= 21 or hour < 6:
        return 'Asian'
    elif 6 <= hour < 8:
        return 'Pre-London'
    elif 8 <= hour < 12:
        return 'London Open'
    elif 12 <= hour < 15:
        return 'London+NY'
    elif 13 <= hour < 17:
        return 'NY Open'  # Note: overlaps with London+NY at 13-15
    elif 17 <= hour < 21:
        return 'NY Afternoon'
    else:
        return 'Unknown'

def assign_session_priority(hour):
    """
    Assign session with priority handling for overlaps.
    London+NY and NY Open overlap at 13-15 UTC.
    Priority: London+NY gets 12-15, NY Open gets 15-17.
    Asian: 21-06, Pre-London: 06-08, London Open: 08-12,
    London+NY: 12-15, NY Open: 15-17, NY Afternoon: 17-21
    """
    if hour >= 21 or hour < 6:
        return 'Asian'
    elif 6 <= hour < 8:
        return 'Pre-London'
    elif 8 <= hour < 12:
        return 'London Open'
    elif 12 <= hour < 15:
        return 'London+NY'
    elif 15 <= hour < 17:
        return 'NY Open'
    elif 17 <= hour < 21:
        return 'NY Afternoon'
    else:
        return 'Unknown'

def compute_atr(df, period=14):
    """Compute ATR(14) on a dataframe with high, low, close columns."""
    df = df.copy()
    df['H-L'] = df['high'] - df['low']
    df['H-C'] = np.abs(df['high'] - df['close'].shift(1))
    df['L-C'] = np.abs(df['low'] - df['close'].shift(1))
    df['TR'] = df[['H-L', 'H-C', 'L-C']].max(axis=1)
    df['ATR'] = df['TR'].rolling(window=period).mean()
    return df

def load_and_process(symbol, tf='5min'):
    """Load CSV, compute ATR, assign session."""
    filepath = os.path.join(DATA_DIR, f"{symbol}_{tf}_master.csv")
    print(f"  Loading {filepath}...")
    df = pd.read_csv(filepath, parse_dates=['Timestamp'])
    df = df.sort_values('Timestamp').reset_index(drop=True)
    
    # Compute ATR(14)
    df = compute_atr(df, period=14)
    
    # Extract hour from Timestamp (UTC)
    df['hour'] = df['Timestamp'].dt.hour
    
    # Assign session using priority-based method
    df['session'] = df['hour'].apply(assign_session_priority)
    
    return df

# ============================================================
# MAIN ANALYSIS
# ============================================================

print("=" * 80)
print("ARES — Session Intelligence Analysis for HERMES PRIME v3")
print("=" * 80)

# Store results for all instruments
all_results = {}

for symbol, info in INSTRUMENTS.items():
    print(f"\n>>> Processing {info['name']} ({symbol})...")
    
    # Try 5min first (more granular for session analysis)
    try:
        df = load_and_process(symbol, '5min')
        tf_used = '5min'
    except Exception as e:
        print(f"  5min failed: {e}, trying 15min...")
        df = load_and_process(symbol, '15min')
        tf_used = '15min'
    
    print(f"  Using {tf_used} data. Rows: {len(df)}, Date range: {df['Timestamp'].min()} to {df['Timestamp'].max()}")
    
    # Compute average ATR per session (exclude NaN ATR rows)
    valid_df = df.dropna(subset=['ATR'])
    
    session_stats = {}
    session_order = ['Asian', 'Pre-London', 'London Open', 'London+NY', 'NY Open', 'NY Afternoon']
    
    for session in session_order:
        sdf = valid_df[valid_df['session'] == session]
        if len(sdf) == 0:
            session_stats[session] = {
                'avg_atr_raw': 0, 'median_atr_raw': 0, 'std_atr_raw': 0,
                'avg_atr_pips': 0, 'count': 0, 'avg_range_raw': 0, 'avg_range_pips': 0,
            }
            continue
        
        avg_atr = sdf['ATR'].mean()
        median_atr = sdf['ATR'].median()
        std_atr = sdf['ATR'].std()
        avg_range = (sdf['high'] - sdf['low']).mean()
        
        pip_size = info['pip_size']
        session_stats[session] = {
            'avg_atr_raw': avg_atr,
            'median_atr_raw': median_atr,
            'std_atr_raw': std_atr,
            'avg_atr_pips': avg_atr / pip_size,
            'avg_range_raw': avg_range,
            'avg_range_pips': avg_range / pip_size,
            'count': len(sdf),
        }
    
    all_results[symbol] = session_stats

# ============================================================
# Compute relative metrics: ATR as % of daily range, and spread/ATR ratio
# ============================================================

print("\n" + "=" * 80)
print("SESSION ATR SUMMARY (Raw values)")
print("=" * 80)

for symbol, info in INSTRUMENTS.items():
    print(f"\n--- {info['name']} ---")
    for session in session_order:
        st = all_results[symbol][session]
        print(f"  {session:15s}: ATR={st['avg_atr_raw']:.5f}  ATR_pips={st['avg_atr_pips']:.1f}  Range_pips={st['avg_range_pips']:.1f}  Bars={st['count']}")

# ============================================================
# QUALITY RATING ASSIGNMENT
# ============================================================
# Logic: 
#   - Compute each session's ATR as a fraction of the instrument's max-session ATR
#   - Also compute spread/ATR ratio (lower is better for scalping)
#   - PRIME:  ATR relative >= 0.70 AND spread/ATR <= threshold
#   - REDUCE: ATR relative >= 0.40 OR mixed signal
#   - AVOID:  ATR relative < 0.40 (dead zone — not enough movement for scalping)

def assign_quality(atr_relative, spread_atr_ratio, category):
    """
    Assign quality rating based on ATR relative strength and spread impact.
    For GOLD (category='GOLD'), thresholds are adjusted due to higher volatility.
    """
    if category == 'GOLD':
        if atr_relative >= 0.65 and spread_atr_ratio < 0.15:
            return 'PRIME'
        elif atr_relative >= 0.40:
            return 'REDUCE'
        else:
            return 'AVOID'
    else:
        # Forex pairs
        if atr_relative >= 0.70 and spread_atr_ratio < 0.20:
            return 'PRIME'
        elif atr_relative >= 0.40:
            return 'REDUCE'
        else:
            return 'AVOID'

# Compute quality ratings
quality_ratings = {}
session_atr_relative = {}
spread_atr_ratios = {}

for symbol, info in INSTRUMENTS.items():
    # Find max ATR across sessions for this instrument
    max_atr = max(all_results[symbol][s]['avg_atr_raw'] for s in session_order)
    if max_atr == 0:
        max_atr = 1  # avoid div by zero
    
    quality_ratings[symbol] = {}
    session_atr_relative[symbol] = {}
    spread_atr_ratios[symbol] = {}
    
    for session in session_order:
        st = all_results[symbol][session]
        atr_rel = st['avg_atr_raw'] / max_atr if max_atr > 0 else 0
        
        # Spread/ATR ratio: reference spread / avg range per bar (as proxy for per-bar ATR)
        # Lower spread/ATR = better for scalping
        ref_spread = info['ref_spread']
        avg_range = st['avg_range_raw']
        spread_atr = ref_spread / avg_range if avg_range > 0 else 999
        
        session_atr_relative[symbol][session] = atr_rel
        spread_atr_ratios[symbol][session] = spread_atr
        
        quality_ratings[symbol][session] = assign_quality(atr_rel, spread_atr, info['category'])

# ============================================================
# OUTPUT TABLE 1: GOLD SESSION TABLE
# ============================================================

print("\n" + "=" * 80)
print("TABLE 1: GOLD SESSION INTELLIGENCE TABLE (XAU/USD)")
print("=" * 80)

symbol = 'xauusd'
info = INSTRUMENTS[symbol]
print(f"\n{'Session':<15} {'Avg ATR($)':<12} {'ATR(pips)':<12} {'Rel ATR%':<10} {'Spread/ATR':<12} {'Quality':<10}")
print("-" * 71)
for session in session_order:
    st = all_results[symbol][session]
    rel = session_atr_relative[symbol][session] * 100
    spr = spread_atr_ratios[symbol][session]
    q = quality_ratings[symbol][session]
    print(f"{session:<15} ${st['avg_atr_raw']:<11.3f} {st['avg_atr_pips']:<12.1f} {rel:<10.1f} {spr:<12.4f} {q:<10}")

# ============================================================
# OUTPUT TABLE 2: FOREX SESSION MAP
# ============================================================

print("\n" + "=" * 80)
print("TABLE 2: FOREX SESSION MAP")
print("=" * 80)

forex_symbols = ['eurusd', 'gbpusd', 'gbpjpy', 'usdjpy']

print(f"\n{'Session':<15}", end='')
for sym in forex_symbols:
    print(f" {INSTRUMENTS[sym]['name']:<14}", end='')
print()
print(f"{'':15}", end='')
for sym in forex_symbols:
    print(f" {'ATR/Quality':<14}", end='')
print()
print("-" * 75)

for session in session_order:
    print(f"{session:<15}", end='')
    for sym in forex_symbols:
        st = all_results[sym][session]
        q = quality_ratings[sym][session]
        atr_pips = st['avg_atr_pips']
        print(f" {atr_pips:>6.1f}/{q:<7}", end='')
    print()

# ============================================================
# DETAILED NUMERICAL TABLES FOR REFERENCE
# ============================================================

print("\n" + "=" * 80)
print("DETAILED: ATR(14) in PIPS per Session per Instrument (5min bars)")
print("=" * 80)

print(f"\n{'Session':<15}", end='')
for sym in ['xauusd', 'eurusd', 'gbpusd', 'gbpjpy', 'usdjpy']:
    print(f" {INSTRUMENTS[sym]['name']:>10}", end='')
print()
print("-" * 65)

for session in session_order:
    print(f"{session:<15}", end='')
    for sym in ['xauusd', 'eurusd', 'gbpusd', 'gbpjpy', 'usdjpy']:
        st = all_results[sym][session]
        print(f" {st['avg_atr_pips']:>10.1f}", end='')
    print()

print(f"\n{'Session':<15}", end='')
for sym in ['xauusd', 'eurusd', 'gbpusd', 'gbpjpy', 'usdjpy']:
    print(f" {INSTRUMENTS[sym]['name']:>10}", end='')
print("  (Relative ATR %)")
print("-" * 80)

for session in session_order:
    print(f"{session:<15}", end='')
    for sym in ['xauusd', 'eurusd', 'gbpusd', 'gbpjpy', 'usdjpy']:
        rel = session_atr_relative[sym][session] * 100
        print(f" {rel:>9.1f}%", end='')
    print()

# ============================================================
# QUALITY RATING MAP
# ============================================================

print("\n" + "=" * 80)
print("QUALITY RATING MAP")
print("=" * 80)

print(f"\n{'Session':<15}", end='')
for sym in ['xauusd', 'eurusd', 'gbpusd', 'gbpjpy', 'usdjpy']:
    print(f" {INSTRUMENTS[sym]['name']:>10}", end='')
print()
print("-" * 65)

for session in session_order:
    print(f"{session:<15}", end='')
    for sym in ['xauusd', 'eurusd', 'gbpusd', 'gbpjpy', 'usdjpy']:
        q = quality_ratings[sym][session]
        print(f" {q:>10}", end='')
    print()

# ============================================================
# SPREAD/ATR RATIO TABLE
# ============================================================

print("\n" + "=" * 80)
print("SPREAD IMPACT ANALYSIS (Reference Spread / Avg Bar Range)")
print("=" * 80)

print(f"\n{'Session':<15}", end='')
for sym in ['xauusd', 'eurusd', 'gbpusd', 'gbpjpy', 'usdjpy']:
    print(f" {INSTRUMENTS[sym]['name']:>10}", end='')
print()
print("-" * 65)

for session in session_order:
    print(f"{session:<15}", end='')
    for sym in ['xauusd', 'eurusd', 'gbpusd', 'gbpjpy', 'usdjpy']:
        spr = spread_atr_ratios[sym][session]
        print(f" {spr:>10.4f}", end='')
    print()

print(f"\nReference Spreads used:")
for sym in ['xauusd', 'eurusd', 'gbpusd', 'gbpjpy', 'usdjpy']:
    info = INSTRUMENTS[sym]
    print(f"  {info['name']:>10}: {info['ref_spread']} (in price units)")

# ============================================================
# ASIAN SESSION SUB-ANALYSIS (split at midnight)
# ============================================================

print("\n" + "=" * 80)
print("ASIAN SESSION DEEP DIVE (21:00-06:00 UTC)")
print("=" * 80)

asian_subblocks = {
    '21-00 (Pre-midnight)': (21, 24),
    '00-03 (Early Asian)':  (0, 3),
    '03-06 (Late Asian)':   (3, 6),
}

print(f"\n{'Sub-block':<25}", end='')
for sym in ['xauusd', 'eurusd', 'gbpusd', 'gbpjpy', 'usdjpy']:
    print(f" {INSTRUMENTS[sym]['name']:>10}", end='')
print()
print("-" * 75)

for subname, (h_start, h_end) in asian_subblocks.items():
    print(f"{subname:<25}", end='')
    for sym in ['xauusd', 'eurusd', 'gbpusd', 'gbpjpy', 'usdjpy']:
        filepath = os.path.join(DATA_DIR, f"{sym}_5min_master.csv")
        df = pd.read_csv(filepath, parse_dates=['Timestamp'])
        df = df.sort_values('Timestamp').reset_index(drop=True)
        df = compute_atr(df, period=14)
        df['hour'] = df['Timestamp'].dt.hour
        
        if h_end == 24:
            mask = (df['hour'] >= h_start)
        else:
            mask = (df['hour'] >= h_start) & (df['hour'] < h_end)
        
        valid = df[mask].dropna(subset=['ATR'])
        if len(valid) > 0:
            atr_pips = valid['ATR'].mean() / INSTRUMENTS[sym]['pip_size']
        else:
            atr_pips = 0
        print(f" {atr_pips:>10.1f}", end='')
    print()

# ============================================================
# VOLATILITY RANKING PER SESSION
# ============================================================

print("\n" + "=" * 80)
print("VOLATILITY RANKING PER SESSION (by ATR pips, highest first)")
print("=" * 80)

for session in session_order:
    pairs = []
    for sym in ['xauusd', 'eurusd', 'gbpusd', 'gbpjpy', 'usdjpy']:
        atr_pips = all_results[sym][session]['avg_atr_pips']
        pairs.append((INSTRUMENTS[sym]['name'], atr_pips))
    pairs.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\n  {session}:")
    for i, (name, atr) in enumerate(pairs, 1):
        print(f"    {i}. {name:<10} {atr:.1f} pips ATR(14)")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
