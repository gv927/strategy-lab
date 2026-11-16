#!/usr/bin/env python3
"""TITAN Data Validator - Optimized for large CSV files."""

import pandas as pd
import os
import subprocess
from datetime import datetime, timedelta

DATA_DIR = "/home/ubuntu/Desktop/data-download/historical_data/"

INSTRUMENTS = [
    "eurusd", "gbpjpy", "xauusd", "usa30idxusd", "usa500idxusd",
    "usatechidxusd", "eurjpy", "usdjpy", "usdchf", "usdcad",
    "audchf", "chfjpy", "gbpusd", "gbpnzd", "brentcmdusd",
    "deuidxeur", "gbridxgbp", "xagusd"
]

TIMEFRAMES = ["5min", "15min", "30min", "1h"]
EXPECTED_HEADERS = ["Timestamp", "open", "high", "low", "close"]
TF_MINUTES = {"5min": 5, "15min": 15, "30min": 30, "1h": 60}

def quick_file_check(filepath):
    """Get line count, header, first/last rows using shell commands."""
    if not os.path.exists(filepath):
        return None
    
    file_size = os.path.getsize(filepath)
    if file_size == 0:
        return {"size": 0, "lines": 0}
    
    # Count lines
    result = subprocess.run(["wc", "-l", filepath], capture_output=True, text=True)
    lines = int(result.stdout.strip().split()[0])
    
    # Get header
    result = subprocess.run(["head", "-1", filepath], capture_output=True, text=True)
    header = result.stdout.strip()
    
    # Get first data row
    result = subprocess.run(["sed", "-n", "2p", filepath], capture_output=True, text=True)
    first_row = result.stdout.strip()
    
    # Get last data row
    result = subprocess.run(["tail", "-1", filepath], capture_output=True, text=True)
    last_row = result.stdout.strip()
    
    return {
        "size": file_size,
        "lines": lines,
        "header": header,
        "first_row": first_row,
        "last_row": last_row
    }


def validate_file(pair, tf):
    filename = f"{pair}_{tf}_master.csv"
    filepath = os.path.join(DATA_DIR, filename)
    issues = []
    
    # 1. File exists and non-empty
    if not os.path.exists(filepath):
        return {"pair": pair, "tf": tf, "verdict": "NO-GO", "issues": ["FILE MISSING"], "rows": 0, "range": "N/A"}
    
    file_size = os.path.getsize(filepath)
    if file_size == 0:
        return {"pair": pair, "tf": tf, "verdict": "NO-GO", "issues": ["FILE EMPTY (0 bytes)"], "rows": 0, "range": "N/A"}
    
    quick = quick_file_check(filepath)
    data_rows = quick["lines"] - 1 if quick["lines"] > 0 else 0  # subtract header
    
    if data_rows == 0:
        return {"pair": pair, "tf": tf, "verdict": "NO-GO", "issues": ["0 data rows"], "rows": 0, "range": "N/A"}
    
    # 2. Headers check
    actual_header = quick["header"]
    header_fields = [h.strip() for h in actual_header.split(",")]
    if header_fields != EXPECTED_HEADERS:
        issues.append(f"HEADERS MISMATCH: got {header_fields}")
    
    # Parse first and last timestamps
    try:
        first_ts = pd.to_datetime(quick["first_row"].split(",")[0].strip(), utc=True)
        last_ts = pd.to_datetime(quick["last_row"].split(",")[0].strip(), utc=True)
    except Exception as e:
        issues.append(f"TIMESTAMP PARSE ERROR on boundary: {e}")
        return {"pair": pair, "tf": tf, "verdict": "NO-GO", "issues": issues, "rows": data_rows, "range": "parse error"}
    
    # Now read full file but only the columns we need, and use efficient parsing
    # For large 5min files, read in chunks for NaN/duplicate/gap check
    try:
        # Read only Timestamp + OHLC
        df = pd.read_csv(filepath, parse_dates=["Timestamp"], 
                         dtype={"open": "float64", "high": "float64", "low": "float64", "close": "float64"})
    except Exception as e:
        issues.append(f"READ ERROR: {e}")
        return {"pair": pair, "tf": tf, "verdict": "NO-GO", "issues": issues, "rows": data_rows, "range": "read error"}
    
    actual_rows = len(df)
    
    # 4. NaN/null values in OHLC
    for col in ["open", "high", "low", "close"]:
        nan_count = df[col].isna().sum()
        if nan_count > 0:
            issues.append(f"NaN in {col}: {nan_count} rows")
    
    # Also check NaN in Timestamp
    ts_nan = df["Timestamp"].isna().sum()
    if ts_nan > 0:
        issues.append(f"NaN Timestamps: {ts_nan} rows")
    
    # Drop NaT timestamps for further checks
    df = df.dropna(subset=["Timestamp"]).sort_values("Timestamp").reset_index(drop=True)
    
    # 6. Duplicate timestamps
    dup_count = df["Timestamp"].duplicated().sum()
    if dup_count > 0:
        issues.append(f"DUPLICATE TIMESTAMPS: {dup_count}")
    
    # 7. Data covers 2021-2025
    min_ts = df["Timestamp"].min()
    max_ts = df["Timestamp"].max()
    
    years_present = sorted(df["Timestamp"].dt.year.unique())
    expected_years = {2021, 2022, 2023, 2024, 2025}
    missing_years = expected_years - set(years_present)
    
    coverage_issues = []
    if missing_years:
        coverage_issues.append(f"Missing years: {sorted(missing_years)}")
    if min_ts > pd.Timestamp("2021-02-01", tz="utc"):
        coverage_issues.append(f"Late start: {min_ts.strftime('%Y-%m-%d')}")
    if max_ts < pd.Timestamp("2025-01-01", tz="utc"):
        coverage_issues.append(f"Early end: {max_ts.strftime('%Y-%m-%d')}")
    
    if coverage_issues:
        issues.append(f"PERIOD: {'; '.join(coverage_issues)}")
    
    # 3. Gap analysis - compute diffs
    diffs = df["Timestamp"].diff().dropna()
    
    # Count large gaps (>72h)
    large_gap_count = 0
    large_gap_examples = []
    intra_week_gap_count = 0
    
    expected_delta = timedelta(minutes=TF_MINUTES[tf])
    
    for idx in diffs.index[::max(1, len(diffs)//500)]:  # Sample for speed
        diff = diffs[idx]
        if pd.isna(diff):
            continue
        diff_td = diff if isinstance(diff, timedelta) else diff.to_pytimedelta()
        
        if diff_td > timedelta(hours=72):
            large_gap_count += 1
            if len(large_gap_examples) < 2:
                ts = df.loc[idx, "Timestamp"]
                large_gap_examples.append(f"{diff_td} at {ts.strftime('%Y-%m-%d')}")
        
        elif diff_td > expected_delta * 3:
            ts = df.loc[idx, "Timestamp"]
            dow = ts.dayofweek
            if dow not in [0, 6]:  # Not Monday/Sunday (weekend boundary)
                intra_week_gap_count += 1
    
    # For full accuracy, let's count properly
    # Count all large gaps
    large_gaps_full = (diffs > pd.Timedelta(hours=72)).sum()
    intra_week_full = 0
    
    # Sample intra-week gaps more carefully
    if len(diffs) > 10000:
        # Sample every Nth row
        sample_step = max(1, len(diffs) // 2000)
        sampled = diffs.iloc[::sample_step]
        for idx in sampled.index:
            diff = sampled[idx]
            if pd.isna(diff):
                continue
            diff_td = diff if isinstance(diff, timedelta) else diff.to_pytimedelta()
            if timedelta(hours=3) < diff_td <= timedelta(hours=72):
                try:
                    ts = df.loc[idx, "Timestamp"]
                    if ts.dayofweek not in [0, 6]:
                        intra_week_full += 1
                except:
                    pass
        # Scale up
        intra_week_full = int(intra_week_full * (len(diffs) / max(1, len(sampled))))
    else:
        for idx in diffs.index:
            diff = diffs[idx]
            if pd.isna(diff):
                continue
            diff_td = diff if isinstance(diff, timedelta) else diff.to_pytimedelta()
            if diff_td > expected_delta * 3 and diff_td <= timedelta(hours=72):
                try:
                    ts = df.loc[idx, "Timestamp"]
                    if ts.dayofweek not in [0, 6]:
                        intra_week_full += 1
                except:
                    pass
    
    if large_gaps_full > 5:
        issues.append(f"LARGE GAPS (>72h): {large_gaps_full} found")
    
    if intra_week_full > 50:
        issues.append(f"INTRA-WEEK GAPS: ~{intra_week_full} gaps >3x delta on weekdays")
    
    # 5. OHLC consistency
    high = df["high"]
    low = df["low"]
    open_ = df["open"]
    close = df["close"]
    
    h_lt_l = int((high < low).sum())
    h_lt_o = int((high < open_).sum())
    h_lt_c = int((high < close_).sum()) if (close_ := close) is not None else 0
    l_gt_o = int((low > open_).sum())
    l_gt_c = int((low > close_).sum())
    h_lt_c = int((high < close).sum())
    
    ohlc_issues = []
    if h_lt_l > 0: ohlc_issues.append(f"High<Low:{h_lt_l}")
    if h_lt_o > 0: ohlc_issues.append(f"High<Open:{h_lt_o}")
    if h_lt_c > 0: ohlc_issues.append(f"High<Close:{h_lt_c}")
    if l_gt_o > 0: ohlc_issues.append(f"Low>Open:{l_gt_o}")
    if l_gt_c > 0: ohlc_issues.append(f"Low>Close:{l_gt_c}")
    
    if ohlc_issues:
        issues.append(f"OHLC VIOLATIONS: {', '.join(ohlc_issues)}")
    
    # Determine verdict
    has_critical = any(kw in " ".join(issues) for kw in 
                       ["FILE MISSING", "FILE EMPTY", "0 data rows", "READ ERROR", 
                        "TIMESTAMP PARSE", "HEADERS MISMATCH", "NaN in", "OHLC VIOLATIONS",
                        "DUPLICATE TIMESTAMPS"])
    
    if has_critical:
        verdict = "NO-GO"
    else:
        verdict = "GO" if not issues else "GO*"
    
    return {
        "pair": pair, "tf": tf, "verdict": verdict, "issues": issues,
        "rows": actual_rows, "range": f"{min_ts.strftime('%Y-%m-%d')} -> {max_ts.strftime('%Y-%m-%d')}",
        "size_mb": round(file_size / (1024*1024), 1)
    }


# Run validation
print("=" * 95)
print("TITAN DATA VALIDATOR - HERMES PRIME v3 Scalping System")
print("=" * 95)
print()

all_results = []
for i, pair in enumerate(INSTRUMENTS):
    for tf in TIMEFRAMES:
        result = validate_file(pair, tf)
        all_results.append(result)
        v = result["verdict"]
        tag = f"[{v:>5}]"
        label = f"{pair}_{tf}"
        extra = f"rows={result['rows']:,} | {result['range']}"
        if result["issues"]:
            extra += f" | {'; '.join(result['issues'])}"
        print(f"  {tag} {label:<25} {extra}")

print()
print("=" * 95)
print("SUMMARY TABLE")
print("=" * 95)
print(f"{'Instrument':<18} {'5min':<10} {'15min':<10} {'30min':<10} {'1h':<10}")
print("-" * 48)

for pair in INSTRUMENTS:
    row = f"{pair:<18}"
    for tf in TIMEFRAMES:
        result = next(r for r in all_results if r["pair"] == pair and r["tf"] == tf)
        v = result["verdict"]
        row += f" {v:<10}"
    print(row)

print()
print("=" * 95)
print("FINAL STATISTICS")
print("=" * 95)

total = len(all_results)
go_count = sum(1 for r in all_results if r["verdict"] == "GO")
go_star_count = sum(1 for r in all_results if r["verdict"] == "GO*")
nogo_count = sum(1 for r in all_results if r["verdict"] == "NO-GO")

print(f"  Total files checked:  {total}")
print(f"  GO (clean):           {go_count}")
print(f"  GO* (with warnings):  {go_star_count}")
print(f"  NO-GO (blocked):      {nogo_count}")
print()

if nogo_count > 0:
    print("CRITICAL BLOCKERS:")
    for r in all_results:
        if r["verdict"] == "NO-GO":
            print(f"  - {r['pair']}_{r['tf']}: {'; '.join(r['issues'])}")
    print()

if go_star_count > 0:
    print("WARNINGS (GO* files):")
    for r in all_results:
        if r["verdict"] == "GO*":
            print(f"  - {r['pair']}_{r['tf']}: {'; '.join(r['issues'])}")
    print()

print("VERDICT: " + ("ALL CLEAR - Backtesting can proceed" if nogo_count == 0 else 
      f"BLOCKED - {nogo_count} file(s) need attention before backtesting"))
