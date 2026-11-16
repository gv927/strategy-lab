#!/usr/bin/env python3
"""
TITAN — Chief Data Validation & Integrity Officer
HERMES PRIME Trading System — Historical Data Validation Script
Cycle 1: 2025-06-02
"""
import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = "/home/ubuntu/Desktop/data-download/historical_data"
REPORT_PATH = "/home/ubuntu/Desktop/pz4/.obsidian/HERMES_PRIME/Research/TITAN_Cycle1_2025-06-02.md"

INSTRUMENTS = {
    "EUR/USD": "eurusd",
    "XAU/USD": "xauusd",
    "US30": "usa30idxusd",
    "GBP/JPY": "gbpjpy",
}

TIMEFRAMES = {
    "3min": {"minutes": 3, "label": "3M"},
    "5min": {"minutes": 5, "label": "5M"},
    "15min": {"minutes": 15, "label": "15M"},
    "30min": {"minutes": 30, "label": "30M"},
    "1h": {"minutes": 60, "label": "1H"},
    "4h": {"minutes": 240, "label": "4H"},
}

# Minimum expected file sizes (bytes) — flag if smaller
MIN_FILE_SIZE = {
    "3min": 5_000_000,
    "5min": 3_000_000,
    "15min": 1_000_000,
    "30min": 500_000,
    "1h": 200_000,
    "4h": 100_000,
}

# Expected OHLCV columns (case-insensitive check)
EXPECTED_COLS = {"timestamp", "open", "high", "low", "close", "volume"}


def load_csv(filepath):
    """Load CSV with flexible timestamp parsing."""
    df = pd.read_csv(filepath)
    # Normalize column names
    df.columns = [c.strip().lower() for c in df.columns]
    # Parse timestamp
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], format="mixed", utc=False)
    elif "date" in df.columns:
        df["timestamp"] = pd.to_datetime(df["date"], format="mixed", utc=False)
        df.drop(columns=["date"], inplace=True)
    elif "time" in df.columns:
        df["timestamp"] = pd.to_datetime(df["time"], format="mixed", utc=False)
        df.drop(columns=["time"], inplace=True)
    else:
        # Try first column as timestamp
        first_col = df.columns[0]
        df["timestamp"] = pd.to_datetime(df[first_col], format="mixed", utc=False)
    return df


def validate_single_file(filepath, instrument_name, tf_key, tf_info):
    """Validate a single CSV file. Returns a dict of results."""
    result = {
        "instrument": instrument_name,
        "tf": tf_info["label"],
        "tf_key": tf_key,
        "filepath": filepath,
        "errors": [],
        "warnings": [],
        "anomalies": [],
    }
    
    # File size check
    file_size = os.path.getsize(filepath)
    result["file_size_mb"] = round(file_size / 1_048_576, 2)
    min_size = MIN_FILE_SIZE.get(tf_key, 0)
    if file_size < min_size:
        result["warnings"].append(
            f"File size {file_size:,} bytes is below expected minimum {min_size:,} bytes"
        )
    
    # Load data
    try:
        df = load_csv(filepath)
    except Exception as e:
        result["errors"].append(f"Failed to load CSV: {e}")
        return result
    
    result["candle_count"] = len(df)
    result["columns"] = list(df.columns)
    
    # Column validation
    actual_cols = set(df.columns) - {"timestamp"}
    missing_cols = EXPECTED_COLS - {"timestamp"} - actual_cols
    if missing_cols:
        result["errors"].append(f"Missing expected columns: {missing_cols}")
    
    # Data types
    result["dtypes"] = {col: str(df[col].dtype) for col in df.columns if col != "timestamp"}
    
    # Date range
    if len(df) == 0:
        result["errors"].append("File is EMPTY — zero candles")
        return result
    
    result["start"] = str(df["timestamp"].min())
    result["end"] = str(df["timestamp"].max())
    
    # Missing values per column
    result["missing_values"] = {}
    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            nan_count = df[col].isna().sum()
            null_count = df[col].isnull().sum()
            total_missing = nan_count + null_count
            if total_missing > 0:
                result["missing_values"][col] = int(total_missing)
                result["warnings"].append(f"{col}: {total_missing} missing values")
    
    # Duplicate timestamps
    dup_count = df["timestamp"].duplicated().sum()
    result["duplicate_timestamps"] = int(dup_count)
    if dup_count > 0:
        dups = df[df["timestamp"].duplicated(keep=False)]["timestamp"].unique()
        sample_dups = [str(t) for t in dups[:10]]
        result["warnings"].append(
            f"{dup_count} duplicate timestamps. Samples: {sample_dups}"
        )
    
    # Timestamp ordering
    is_sorted = df["timestamp"].is_monotonic_increasing
    result["timestamp_ordered"] = is_sorted
    if not is_sorted:
        result["errors"].append("Timestamps are NOT in chronological order")
    
    # Price anomalies
    price_anomalies = []
    for col in ["open", "high", "low", "close"]:
        if col in df.columns:
            zero_prices = df[df[col] == 0]
            if len(zero_prices) > 0:
                for idx in zero_prices.index[:5]:
                    price_anomalies.append(
                        f"Zero {col} at {df.loc[idx, 'timestamp']}"
                    )
            neg_prices = df[df[col] < 0]
            if len(neg_prices) > 0:
                for idx in neg_prices.index[:5]:
                    price_anomalies.append(
                        f"Negative {col} ({df.loc[idx, col]}) at {df.loc[idx, 'timestamp']}"
                    )
    
    # high < low
    if "high" in df.columns and "low" in df.columns:
        hl_violations = df[df["high"] < df["low"]]
        if len(hl_violations) > 0:
            for idx in hl_violations.index[:5]:
                price_anomalies.append(
                    f"High < Low at {df.loc[idx, 'timestamp']}: H={df.loc[idx, 'high']} L={df.loc[idx, 'low']}"
                )
    
    # close > high or close < low
    if "close" in df.columns and "high" in df.columns and "low" in df.columns:
        ch_violations = df[df["close"] > df["high"]]
        if len(ch_violations) > 0:
            for idx in ch_violations.index[:5]:
                price_anomalies.append(
                    f"Close > High at {df.loc[idx, 'timestamp']}: C={df.loc[idx, 'close']} H={df.loc[idx, 'high']}"
                )
        cl_violations = df[df["close"] < df["low"]]
        if len(cl_violations) > 0:
            for idx in cl_violations.index[:5]:
                price_anomalies.append(
                    f"Close < Low at {df.loc[idx, 'timestamp']}: C={df.loc[idx, 'close']} L={df.loc[idx, 'low']}"
                )
    
    result["price_anomalies"] = price_anomalies
    if price_anomalies:
        result["errors"].extend(price_anomalies[:3])  # Top 3 to errors
        if len(price_anomalies) > 3:
            result["anomalies"].extend(price_anomalies[3:])
    
    # Volume anomalies
    volume_anomalies = []
    if "volume" in df.columns:
        zero_vol = df[df["volume"] == 0]
        result["zero_volume_count"] = len(zero_vol)
        if len(zero_vol) > 0:
            # For XAU/USD, zero volume is common (metals data)
            if "xau" not in instrument_name.lower():
                pct = len(zero_vol) / len(df) * 100
                if pct > 50:
                    volume_anomalies.append(
                        f"{len(zero_vol)} zero-volume candles ({pct:.1f}% of total)"
                    )
                else:
                    result["warnings"].append(
                        f"{len(zero_vol)} zero-volume candles ({pct:.1f}%)"
                    )
            else:
                result["warnings"].append(
                    f"{len(zero_vol)} zero-volume candles (expected for metals)"
                )
        
        neg_vol = df[df["volume"] < 0]
        if len(neg_vol) > 0:
            for idx in neg_vol.index[:5]:
                volume_anomalies.append(
                    f"Negative volume ({df.loc[idx, 'volume']}) at {df.loc[idx, 'timestamp']}"
                )
    
    result["volume_anomalies"] = volume_anomalies
    if volume_anomalies:
        result["errors"].extend(volume_anomalies[:3])
    
    # Gap detection — compare actual vs expected candle count
    # We count only weekday candles (Mon-Fri) within trading hours
    # For forex: Sun 22:00 - Fri 22:00 UTC roughly
    # For indices: roughly Mon-Fri with session hours
    # Simple approach: count expected candles between start and end,
    # excluding weekends. We flag gaps only if they seem unusual.
    
    tf_minutes = tf_info["minutes"]
    start_ts = df["timestamp"].min()
    end_ts = df["timestamp"].max()
    total_range_minutes = (end_ts - start_ts).total_seconds() / 60
    
    # Expected candles: count only non-weekend minutes
    # Generate a full range and filter to weekdays
    date_range = pd.date_range(start=start_ts, end=end_ts, freq=f"{tf_minutes}min")
    # Weekday = 0-4 (Mon-Fri)
    weekday_mask = date_range.weekday < 5
    expected_weekday_candles = weekday_mask.sum()
    
    # For forex, also include Sunday evening (if data has it)
    # We'll just compare actual vs weekday-expected
    actual_candles = len(df)
    
    # Calculate gap ratio — significant undercounting indicates gaps
    if expected_weekday_candles > 0:
        coverage_ratio = actual_candles / expected_weekday_candles
    else:
        coverage_ratio = 1.0
    
    result["expected_weekday_candles"] = int(expected_weekday_candles)
    result["coverage_ratio"] = round(coverage_ratio, 3)
    
    # Detect actual gaps within the data (missing consecutive candles)
    # Look for time differences > 2x the expected interval within trading days
    sorted_ts = df["timestamp"].sort_values().reset_index(drop=True)
    gaps = []
    for i in range(1, len(sorted_ts)):
        diff = (sorted_ts[i] - sorted_ts[i-1]).total_seconds() / 60
        # If gap is more than 2x the timeframe AND it's within a weekday
        if diff > tf_minutes * 2:
            # Check if this is a weekend gap (Fri-Mon)
            day_of_week_prev = sorted_ts[i-1].weekday()
            day_of_week_curr = sorted_ts[i].weekday()
            
            if day_of_week_prev >= 5 and day_of_week_curr >= 5:
                continue  # Both on weekend, skip
            
            # Weekend gap: Fri to Mon is natural
            if day_of_week_prev == 4 and day_of_week_curr == 0:
                continue  # Fri-Mon, natural weekend
            
            # Check if it's a holiday-like gap (e.g., overnight for indices)
            # For now, flag gaps > 10x the timeframe as significant
            if diff > tf_minutes * 10:
                gaps.append({
                    "after": str(sorted_ts[i-1]),
                    "before": str(sorted_ts[i]),
                    "gap_minutes": diff,
                    "expected_minutes": tf_minutes,
                })
    
    result["significant_gaps"] = gaps
    if gaps:
        result["warnings"].append(
            f"{len(gaps)} significant gaps detected (>10x timeframe)"
        )
    
    # Count all gaps > 2x timeframe (including minor ones)
    minor_gap_count = 0
    for i in range(1, len(sorted_ts)):
        diff = (sorted_ts[i] - sorted_ts[i-1]).total_seconds() / 60
        if diff > tf_minutes * 2:
            day_prev = sorted_ts[i-1].weekday()
            day_curr = sorted_ts[i].weekday()
            if day_prev == 4 and day_curr == 0:
                continue
            if day_prev >= 5 and day_curr >= 5:
                continue
            minor_gap_count += 1
    
    result["gap_count"] = minor_gap_count
    
    # Determine status
    error_count = len(result["errors"])
    if error_count == 0:
        result["status"] = "✅ USABLE"
    elif error_count <= 2:
        result["status"] = "⚠️ PARTIAL"
    else:
        result["status"] = "❌ FAILED"
    
    return result


def cross_timeframe_validation(results_by_instrument):
    """Cross-timeframe consistency checks."""
    cross_results = {}
    
    for inst_name, tf_results in results_by_instrument.items():
        cross = {
            "date_range_consistent": True,
            "issues": [],
            "alignment_issues": [],
        }
        
        # Check that 5M covers same range as 1H and 4H
        if "5min" in tf_results and "1h" in tf_results:
            r5 = tf_results["5min"]
            r1 = tf_results["1h"]
            if "start" in r5 and "start" in r1:
                s5 = pd.Timestamp(r5["start"])
                e5 = pd.Timestamp(r5["end"])
                s1 = pd.Timestamp(r1["start"])
                e1 = pd.Timestamp(r1["end"])
                if s1 < s5:
                    cross["issues"].append(
                        f"1H start ({s1}) is before 5M start ({s5})"
                    )
                    cross["date_range_consistent"] = False
                if e1 > e5:
                    cross["issues"].append(
                        f"1H end ({e1}) is after 5M end ({e5})"
                    )
                    cross["date_range_consistent"] = False
        
        if "5min" in tf_results and "4h" in tf_results:
            r5 = tf_results["5min"]
            r4 = tf_results["4h"]
            if "start" in r5 and "start" in r4:
                s5 = pd.Timestamp(r5["start"])
                e5 = pd.Timestamp(r5["end"])
                s4 = pd.Timestamp(r4["start"])
                e4 = pd.Timestamp(r4["end"])
                if s4 < s5:
                    cross["issues"].append(
                        f"4H start ({s4}) is before 5M start ({s5})"
                    )
                    cross["date_range_consistent"] = False
                if e4 > e5:
                    cross["issues"].append(
                        f"4H end ({e4}) is after 5M end ({e5})"
                    )
                    cross["date_range_consistent"] = False
        
        # Candle alignment: 4H close should match last 5M close in that period
        if "5min" in tf_results and "4h" in tf_results:
            try:
                r5path = tf_results["5min"]["filepath"]
                r4path = tf_results["4h"]["filepath"]
                df5 = load_csv(r5path)
                df4 = load_csv(r4path)
                
                # Sample alignment check: check last 20 4H candles
                df4_sorted = df4.sort_values("timestamp").tail(20)
                misalign_count = 0
                misalign_samples = []
                
                for _, row4 in df4_sorted.iterrows():
                    ts4 = row4["timestamp"]
                    close4 = row4["close"]
                    
                    # Find 5M candles within this 4H period
                    period_start = ts4 - pd.Timedelta(minutes=240) + pd.Timedelta(minutes=5)
                    period_end = ts4
                    
                    mask = (df5["timestamp"] > period_start) & (df5["timestamp"] <= period_end)
                    period_5m = df5[mask]
                    
                    if len(period_5m) == 0:
                        continue
                    
                    last_5m_close = period_5m.iloc[-1]["close"]
                    
                    # Allow small floating point differences
                    if abs(close4 - last_5m_close) > close4 * 0.0001:  # 0.01% tolerance
                        misalign_count += 1
                        if len(misalign_samples) < 5:
                            misalign_samples.append(
                                f"4H close={close4} vs 5M close={last_5m_close} at {ts4}"
                            )
                
                if misalign_count > 0:
                    cross["alignment_issues"] = misalign_samples
                    cross["alignment_misalign_count"] = misalign_count
                    cross["alignment_checked"] = len(df4_sorted)
                    cross["issues"].append(
                        f"{misalign_count}/{len(df4_sorted)} 4H candles misaligned with 5M"
                    )
                else:
                    cross["alignment_misalign_count"] = 0
                    cross["alignment_checked"] = len(df4_sorted)
                    
            except Exception as e:
                cross["issues"].append(f"Alignment check failed: {e}")
        
        # Also check 1H alignment with 5M
        if "5min" in tf_results and "1h" in tf_results:
            try:
                r5path = tf_results["5min"]["filepath"]
                r1path = tf_results["1h"]["filepath"]
                df5 = load_csv(r5path)
                df1 = load_csv(r1path)
                
                df1_sorted = df1.sort_values("timestamp").tail(20)
                misalign_count = 0
                misalign_samples = []
                
                for _, row1 in df1_sorted.iterrows():
                    ts1 = row1["timestamp"]
                    close1 = row1["close"]
                    
                    period_start = ts1 - pd.Timedelta(minutes=60) + pd.Timedelta(minutes=5)
                    period_end = ts1
                    
                    mask = (df5["timestamp"] > period_start) & (df5["timestamp"] <= period_end)
                    period_5m = df5[mask]
                    
                    if len(period_5m) == 0:
                        continue
                    
                    last_5m_close = period_5m.iloc[-1]["close"]
                    
                    if abs(close1 - last_5m_close) > close1 * 0.0001:
                        misalign_count += 1
                        if len(misalign_samples) < 5:
                            misalign_samples.append(
                                f"1H close={close1} vs 5M close={last_5m_close} at {ts1}"
                            )
                
                if misalign_count > 0:
                    cross["alignment_issues_1h"] = misalign_samples
                    cross["alignment_misalign_1h"] = misalign_count
                    cross["alignment_checked_1h"] = len(df1_sorted)
                    cross["issues"].append(
                        f"{misalign_count}/{len(df1_sorted)} 1H candles misaligned with 5M"
                    )
                else:
                    cross["alignment_misalign_1h"] = 0
                    cross["alignment_checked_1h"] = len(df1_sorted)
                    
            except Exception as e:
                cross["issues"].append(f"1H alignment check failed: {e}")
        
        cross_results[inst_name] = cross
    
    return cross_results


def generate_report(all_results, cross_results):
    """Generate the TITAN Data Quality Report in Markdown."""
    lines = []
    lines.append("# 🔱 TITAN Data Quality Report — Cycle 1")
    lines.append(f"**Date:** 2025-06-02  ")
    lines.append("**Agent:** TITAN — Chief Data Validation & Integrity Officer  ")
    lines.append("**System:** HERMES PRIME Trading System  ")
    lines.append("**Mission:** Validate all historical data files for backtesting readiness  ")
    lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # Executive Summary
    total_files = sum(len(tfr) for tfr in all_results.values())
    usable = sum(1 for inst in all_results.values() for r in inst.values() if r.get("status") == "✅ USABLE")
    partial = sum(1 for inst in all_results.values() for r in inst.values() if r.get("status") == "⚠️ PARTIAL")
    failed = sum(1 for inst in all_results.values() for r in inst.values() if r.get("status") == "❌ FAILED")
    
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"- **Total files validated:** {total_files}")
    lines.append(f"- **✅ USABLE:** {usable}")
    lines.append(f"- **⚠️ PARTIAL:** {partial}")
    lines.append(f"- **❌ FAILED:** {failed}")
    lines.append(f"- **Validation pass rate:** {usable/total_files*100:.1f}%")
    lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # Summary Table
    lines.append("## Data Inventory & Status")
    lines.append("")
    lines.append("| Instrument | TF | Candles | Start | End | Gaps | Errors | Status |")
    lines.append("|---|---|---|---|---|---|---|---|")
    
    for inst_name, tf_results in all_results.items():
        for tf_key, r in tf_results.items():
            candles = r.get("candle_count", "N/A")
            start = r.get("start", "N/A")[:19] if r.get("start") else "N/A"
            end = r.get("end", "N/A")[:19] if r.get("end") else "N/A"
            gaps = r.get("gap_count", "N/A")
            errors = len(r.get("errors", []))
            status = r.get("status", "N/A")
            lines.append(f"| {inst_name} | {r['tf']} | {candles:,} | {start} | {end} | {gaps} | {errors} | {status} |")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # File Size Report
    lines.append("## File Size Report")
    lines.append("")
    lines.append("| Instrument | TF | Size (MB) |")
    lines.append("|---|---|---|")
    for inst_name, tf_results in all_results.items():
        for tf_key, r in tf_results.items():
            size_mb = r.get("file_size_mb", "N/A")
            lines.append(f"| {inst_name} | {r['tf']} | {size_mb} |")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Detailed Findings Per Instrument
    lines.append("## Detailed Findings Per Instrument")
    lines.append("")
    
    for inst_name, tf_results in all_results.items():
        lines.append(f"### {inst_name}")
        lines.append("")
        
        for tf_key, r in tf_results.items():
            lines.append(f"#### {r['tf']} ({tf_key})")
            lines.append("")
            lines.append(f"- **Candle count:** {r.get('candle_count', 'N/A'):,}" if isinstance(r.get('candle_count'), int) else f"- **Candle count:** N/A")
            lines.append(f"- **Date range:** {r.get('start', 'N/A')[:19]} → {r.get('end', 'N/A')[:19]}")
            lines.append(f"- **File size:** {r.get('file_size_mb', 'N/A')} MB")
            lines.append(f"- **Columns:** {', '.join(r.get('columns', []))}")
            lines.append(f"- **Duplicate timestamps:** {r.get('duplicate_timestamps', 0)}")
            lines.append(f"- **Chronologically ordered:** {'Yes' if r.get('timestamp_ordered') else 'NO'}")
            lines.append(f"- **Coverage ratio:** {r.get('coverage_ratio', 'N/A')} (actual/expected weekday candles)")
            lines.append(f"- **Gap count (>2x TF):** {r.get('gap_count', 'N/A')}")
            lines.append(f"- **Zero volume candles:** {r.get('zero_volume_count', 'N/A')}")
            
            if r.get("missing_values"):
                lines.append(f"- **Missing values:** {r['missing_values']}")
            
            if r.get("errors"):
                lines.append(f"- **🚨 Errors:**")
                for e in r["errors"]:
                    lines.append(f"  - {e}")
            
            if r.get("warnings"):
                lines.append(f"- **⚠️ Warnings:**")
                for w in r["warnings"]:
                    lines.append(f"  - {w}")
            
            if r.get("price_anomalies"):
                lines.append(f"- **Price anomalies:**")
                for a in r["price_anomalies"]:
                    lines.append(f"  - {a}")
            
            if r.get("volume_anomalies"):
                lines.append(f"- **Volume anomalies:**")
                for a in r["volume_anomalies"]:
                    lines.append(f"  - {a}")
            
            if r.get("significant_gaps"):
                lines.append(f"- **Significant gaps (>10x TF):**")
                for g in r["significant_gaps"][:10]:
                    lines.append(f"  - After {g['after']} → Before {g['before']} ({g['gap_minutes']:.0f} min gap, expected {g['expected_minutes']} min)")
            
            lines.append(f"- **Status:** {r.get('status', 'N/A')}")
            lines.append("")
        
        # Cross-timeframe results for this instrument
        if inst_name in cross_results:
            cr = cross_results[inst_name]
            lines.append(f"#### Cross-Timeframe Consistency — {inst_name}")
            lines.append("")
            lines.append(f"- **Date range consistent (5M ↔ 1H ↔ 4H):** {'✅ Yes' if cr['date_range_consistent'] else '❌ No'}")
            
            if cr.get("alignment_misalign_count") is not None:
                lines.append(f"- **4H↔5M alignment:** {cr['alignment_misalign_count']}/{cr.get('alignment_checked', '?')} misaligned")
            if cr.get("alignment_misalign_1h") is not None:
                lines.append(f"- **1H↔5M alignment:** {cr['alignment_misalign_1h']}/{cr.get('alignment_checked_1h', '?')} misaligned")
            
            if cr.get("alignment_issues"):
                lines.append(f"- **4H alignment samples:**")
                for a in cr["alignment_issues"]:
                    lines.append(f"  - {a}")
            if cr.get("alignment_issues_1h"):
                lines.append(f"- **1H alignment samples:**")
                for a in cr["alignment_issues_1h"]:
                    lines.append(f"  - {a}")
            
            if cr["issues"]:
                lines.append(f"- **Issues:**")
                for issue in cr["issues"]:
                    lines.append(f"  - {issue}")
            else:
                lines.append(f"- **No cross-timeframe issues detected** ✅")
            
            lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # Anomalies Summary
    lines.append("## Anomalies Found")
    lines.append("")
    has_anomalies = False
    for inst_name, tf_results in all_results.items():
        for tf_key, r in tf_results.items():
            anomalies = r.get("price_anomalies", []) + r.get("volume_anomalies", [])
            sig_gaps = r.get("significant_gaps", [])
            if anomalies or sig_gaps:
                has_anomalies = True
                lines.append(f"### {inst_name} — {r['tf']}")
                lines.append("")
                for a in anomalies:
                    lines.append(f"- {a}")
                for g in sig_gaps[:5]:
                    lines.append(f"- Gap: {g['after']} → {g['before']} ({g['gap_minutes']:.0f} min)")
                lines.append("")
    
    if not has_anomalies:
        lines.append("No significant anomalies found across all validated files. ✅")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # Cross-Timeframe Consistency Summary
    lines.append("## Cross-Timeframe Consistency Summary")
    lines.append("")
    lines.append("| Instrument | 5M↔1H Range | 5M↔4H Range | 4H↔5M Align | 1H↔5M Align | Verdict |")
    lines.append("|---|---|---|---|---|---|")
    
    for inst_name, cr in cross_results.items():
        range_ok = "✅" if cr["date_range_consistent"] else "❌"
        align_4h = f"{cr.get('alignment_misalign_count', 'N/A')}/{cr.get('alignment_checked', '?')}" if cr.get("alignment_misalign_count") is not None else "N/A"
        align_1h = f"{cr.get('alignment_misalign_1h', 'N/A')}/{cr.get('alignment_checked_1h', '?')}" if cr.get("alignment_misalign_1h") is not None else "N/A"
        
        if cr["date_range_consistent"] and (cr.get("alignment_misalign_count", 0) or 0) == 0 and (cr.get("alignment_misalign_1h", 0) or 0) == 0:
            verdict = "✅ CONSISTENT"
        elif cr["date_range_consistent"]:
            verdict = "⚠️ MINOR ISSUES"
        else:
            verdict = "❌ INCONSISTENT"
        
        lines.append(f"| {inst_name} | {range_ok} | {range_ok} | {align_4h} | {align_1h} | {verdict} |")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Final Verdict Per Instrument
    lines.append("## Final Verdict Per Instrument")
    lines.append("")
    
    instrument_verdicts = {}
    for inst_name, tf_results in all_results.items():
        statuses = [r.get("status") for r in tf_results.values()]
        critical_tfs = {"5min": tf_results.get("5min", {}), "1h": tf_results.get("1h", {}), "4h": tf_results.get("4h", {})}
        
        critical_ok = all(r.get("status") == "✅ USABLE" for r in critical_tfs.values() if r)
        bonus_ok = all(r.get("status") in ["✅ USABLE", "⚠️ PARTIAL"] for r in tf_results.values() if r)
        
        any_failed = any(r.get("status") == "❌ FAILED" for r in tf_results.values())
        
        if critical_ok and bonus_ok:
            verdict = "✅ USABLE"
            note = "All timeframes pass validation. Safe for backtesting."
        elif critical_ok:
            verdict = "✅ USABLE"
            note = "Critical timeframes (5M, 1H, 4H) pass. Some bonus TFs have issues."
        elif any_failed:
            # Check if critical TFs failed
            critical_failed = any(
                r.get("status") == "❌ FAILED" 
                for k, r in critical_tfs.items() 
                if k in tf_results
            )
            if critical_failed:
                verdict = "❌ FAILED"
                note = "One or more critical timeframes (5M, 1H, 4H) FAILED validation."
            else:
                verdict = "⚠️ PARTIAL"
                note = "Critical timeframes usable but with warnings. Non-critical TFs have issues."
        else:
            verdict = "⚠️ PARTIAL"
            note = "All timeframes have minor issues. Usable with caution."
        
        instrument_verdicts[inst_name] = verdict
        lines.append(f"### {inst_name}: {verdict}")
        lines.append("")
        lines.append(f"**{note}**")
        lines.append("")
        lines.append("- 5M (Entry): " + ("✅" if critical_tfs.get("5min", {}).get("status") == "✅ USABLE" else "⚠️" if critical_tfs.get("5min", {}).get("status") == "⚠️ PARTIAL" else "❌"))
        lines.append("- 1H (Bias): " + ("✅" if critical_tfs.get("1h", {}).get("status") == "✅ USABLE" else "⚠️" if critical_tfs.get("1h", {}).get("status") == "⚠️ PARTIAL" else "❌"))
        lines.append("- 4H (Macro): " + ("✅" if critical_tfs.get("4h", {}).get("status") == "✅ USABLE" else "⚠️" if critical_tfs.get("4h", {}).get("status") == "⚠️ PARTIAL" else "❌"))
        
        bonus_tfs = {k: v for k, v in tf_results.items() if k not in critical_tfs}
        if bonus_tfs:
            lines.append("- Bonus TFs:")
            for k, v in bonus_tfs.items():
                s = v.get("status", "N/A")
                lines.append(f"  - {v['tf']}: {s}")
        
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # Recommendation
    lines.append("## Recommendation for SIGMA (Backtesting)")
    lines.append("")
    usable_instruments = [inst for inst, v in instrument_verdicts.items() if "✅" in v]
    partial_instruments = [inst for inst, v in instrument_verdicts.items() if "⚠️" in v]
    failed_instruments = [inst for inst, v in instrument_verdicts.items() if "❌" in v]
    
    if usable_instruments:
        lines.append(f"**✅ SAFE FOR BACKTESTING:** {', '.join(usable_instruments)}")
        lines.append("")
        lines.append("These instruments have clean data across all critical timeframes (5M, 1H, 4H).")
        lines.append("SIGMA may proceed with backtesting these instruments immediately.")
        lines.append("")
    
    if partial_instruments:
        lines.append(f"**⚠️ USE WITH CAUTION:** {', '.join(partial_instruments)}")
        lines.append("")
        lines.append("These instruments have minor issues. Review warnings before proceeding.")
        lines.append("Backtesting is possible but results should be cross-verified.")
        lines.append("")
    
    if failed_instruments:
        lines.append(f"**❌ DO NOT USE:** {', '.join(failed_instruments)}")
        lines.append("")
        lines.append("These instruments have critical data quality issues.")
        lines.append("Re-download or repair data before backtesting.")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    lines.append("*Report generated by TITAN — Agent 09, HERMES PRIME*  ")
    lines.append(f"*Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    
    return "\n".join(lines)


def main():
    print("🔱 TITAN — Data Validation & Integrity Officer")
    print("=" * 60)
    print(f"Data directory: {DATA_DIR}")
    print("")
    
    all_results = {}  # { instrument_name: { tf_key: result_dict } }
    
    for inst_name, inst_prefix in INSTRUMENTS.items():
        print(f"\n📂 Validating {inst_name} ({inst_prefix})...")
        all_results[inst_name] = {}
        
        for tf_key, tf_info in TIMEFRAMES.items():
            filename = f"{inst_prefix}_{tf_key}_master.csv"
            filepath = os.path.join(DATA_DIR, filename)
            
            if not os.path.exists(filepath):
                print(f"  ❌ MISSING: {filename}")
                all_results[inst_name][tf_key] = {
                    "tf": tf_info["label"],
                    "errors": [f"File not found: {filepath}"],
                    "status": "❌ FAILED",
                    "warnings": [],
                    "anomalies": [],
                }
                continue
            
            print(f"  🔍 Validating {tf_info['label']} ({filename})...")
            result = validate_single_file(filepath, inst_name, tf_key, tf_info)
            all_results[inst_name][tf_key] = result
            
            candle_count = result.get("candle_count", "N/A")
            status = result.get("status", "N/A")
            error_count = len(result.get("errors", []))
            print(f"    → {candle_count:,} candles | {status} | {error_count} errors")
    
    # Cross-timeframe validation
    print("\n🔗 Cross-timeframe consistency checks...")
    cross_results = cross_timeframe_validation(all_results)
    
    for inst_name, cr in cross_results.items():
        print(f"  {inst_name}: {'Consistent ✅' if cr['date_range_consistent'] else 'INCONSISTENT ❌'}")
        if cr["issues"]:
            for issue in cr["issues"]:
                print(f"    → {issue}")
    
    # Generate report
    print("\n📝 Generating TITAN Data Quality Report...")
    report = generate_report(all_results, cross_results)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    
    with open(REPORT_PATH, "w") as f:
        f.write(report)
    
    print(f"\n✅ Report saved to: {REPORT_PATH}")
    print(f"   Size: {os.path.getsize(REPORT_PATH):,} bytes")
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for inst_name, tf_results in all_results.items():
        statuses = [r.get("status", "N/A") for r in tf_results.values()]
        critical = ["5min", "1h", "4h"]
        critical_ok = all(
            tf_results.get(k, {}).get("status") == "✅ USABLE" for k in critical
        )
        verdict = "✅ USABLE" if critical_ok else "⚠️ PARTIAL/FAILED"
        print(f"  {inst_name}: {verdict}")


if __name__ == "__main__":
    main()
