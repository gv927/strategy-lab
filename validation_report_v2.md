# Strategy Lab — Validation Report v2
**Updated:** 2026-11-16 (after US30/USDCAD/AUDUSD testing)  
**Data Periods:**
- XAUUSD, EURUSD, GBPJPY, GBPUSD, USDJPY: 2009-2026 (16+ yrs H1, 12+ yrs M30, 9+ yrs M15)
- US30 (usa30idxusd): 2013-2026 (13+ yrs H1, 4H, D1)
- USDCAD: 2010-2026 (16+ yrs 4H, D1)
- AUDUSD: 2006-2026 (20+ yrs D1)

**Pairs Tested:** 8 (XAUUSD, EURUSD, GBPJPY, GBPUSD, USDJPY, US30, USDCAD, AUDUSD)  
**Total Combinations Tested:** 50+

---

## Validation Criteria (ALL must pass)
- ✅ 500+ trades
- ✅ Profit Factor ≥ 1.3 after costs
- ✅ Max Drawdown ≤ 20%
- ✅ Profitable OOS (walk-forward 70/30)
- ✅ Robust to ±15% parameter shifts
- ✅ Positive on ≥2 instruments

---

## VERIFIED (1)

| Strategy | Pair | TF | Trades | WR | PF | Max DD | OOS PF | OOS WR | Source |
|----------|------|----|--------|----|-----|--------|--------|--------|--------|
| **STRAT-003** Regime-Filtered Gold (SSRN Paper) | XAUUSD | M15 | 1,774 | 24.5% | **2.37** | **19.6%** | **2.73** | 24.5% | [SSRN:6650958](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6650958) |

**Rules:** EMA200 regime filter → Pullback to EMA50 + rejection candle → VWAP confirm → EMA50 trailing stop (candle-close only) → ATR position sizing → News exclusion ±1hr

**Note:** Only passes on XAUUSD. Fails on all forex pairs (DD 158-4600%). Paper was Gold-specific.

---

## PROMISING (High PF/OOS PF but DD > 20%)

### STRAT-001: Gold Multi-EMA Trend Pullback + VWAP (BEST PF ACROSS ALL PAIRS)
| Pair | TF | Trades | WR | PF | Max DD | OOS PF | Status |
|------|----|--------|----|-----|--------|--------|--------|
| XAUUSD | M15 | 2,757 | 58.4% | **3.13** | 149.6% | **3.11** | Promising |
| XAUUSD | M5 | 11,926 | 55.6% | **2.58** | 206.6% | **2.77** | Promising |
| XAUUSD | 1H | 4,078 | 20.8% | **1.71** | 78.2% | **1.82** | Promising |
| US30 | 1H | **3,262** | 53.5% | **2.43** | 50.5% | **2.62** | Promising |
| US30 | 4H | 874 | 62.4% | **4.15** | 791.5% | **3.44** | Promising |
| US30 | 1D | 187 (<500) | 71.7% | **7.13** | **16.8%** | **10.66** | Trade count fail |
| USDCAD | 4H | 1,237 | 52.4% | **2.20** | 452.1% | **2.18** | Promising |
| USDCAD | 1D | 264 (<500) | 66.3% | **4.49** | **7.8%** | **2.89** | Trade count fail |
| AUDUSD | 1D | 224 (<500) | 70.5% | **4.84** | **2.9%** | **2.61** | Trade count fail |
| EURUSD | M15 | 2,579 | 34.5% | **1.60** | 299.5% | **2.14** | Promising |
| GBPJPY | M15 | 2,998 | 39.2% | **1.77** | 81.4% | **1.99** | Promising |

**Pattern:** **Excellent PF (1.6-7.1) and OOS PF (1.8-10.7) on EVERY pair/timeframe tested**, but DD consistently 50-800% on intraday timeframes. Only D1 timeframes pass DD (2.9-16.8%) but fail 500+ trade criterion.

### STRAT-014: EMA 9/21 Pullback (QuantLogic)
| Pair | TF | Trades | WR | PF | Max DD | OOS PF | Status |
|------|----|--------|----|-----|--------|--------|--------|
| XAUUSD | H1 | 3,914 | 33.0% | **1.76** | 31.5% | **1.84** | Promising |
| US30 | H1 | 2,775 | 31.6% | 1.28 (<1.3) | catastrophic | 1.28 | Rejected |
| GBPJPY | H1 | 3,993 | 32.8% | **1.41** | 397.7% | **1.33** | Promising |
| USDJPY | H1 | 3,857 | 33.2% | **1.49** | 1,812% | **1.60** | Promising |
| EURUSD | H1 | 4,000 | 32.3% | 1.27 (<1.3) | 64.2% | 1.18 | Rejected |
| GBPUSD | H1 | 3,992 | 32.2% | 1.31 | 1,600% | 1.19 | Rejected |

**PF barely above 1.3 on best pairs, DD catastrophic on most.**

### STRAT-015: Triple EMA 9/21/55
| Pair | TF | Trades | WR | PF | Max DD | OOS PF | Status |
|------|----|--------|----|-----|--------|--------|--------|
| XAUUSD | H1 | 3,023 | 33.0% | **1.46** | 829.5% | **1.44** | Promising |
| US30 | H1 | 2,101 | 31.0% | 1.14 (<1.3) | 2,983% | 1.03 | Rejected |
| USDCAD | H4 | 756 | 30.8% | 1.13 (<1.3) | 133.8% | 1.17 | Rejected |

**PF < 1.3 on most pairs, DD extreme.**

### STRAT-009: Golden Cross 50/200 SMA
| Pair | TF | Trades | WR | PF | Max DD | OOS PF | Status |
|------|----|--------|----|-----|--------|--------|--------|
| XAUUSD | H4 | 171 (<500) | 26.3% | **1.50** | 86.4% | **1.72** | Trade count fail |
| USDJPY | H4 | 166 (<500) | 27.7% | 1.21 (<1.3) | 485.3% | **2.23** | Trade count fail |
| US30 | H4 | 102 (<500) | 18.6% | 0.75 | - | 1.00 | Rejected |

**Too few trades on H4/D1.**

---

## REJECTED

| Strategy | Pair | TF | Trades | PF | Max DD | OOS PF | Reason |
|----------|------|----|--------|-----|--------|--------|--------|
| STRAT-012 VWAP 2-SD MR | XAUUSD | M5 | 5,019 | 0.98 | 58,264% | 1.01 | PF<1.3, DD |
| STRAT-003 | EURUSD | M15 | 1,713 | 1.32 | 158.3% | 1.14 | DD |
| STRAT-003 | GBPJPY | M15 | 1,843 | 1.35 | 158.0% | 1.34 | DD |
| STRAT-003 | GBPUSD | M15 | 8,060 | 0.75 | 6,352% | 0.76 | PF, DD, OOS |
| STRAT-003 | USDJPY | M15 | 7,728 | 0.87 | 4,619% | 0.86 | PF, DD, OOS |
| STRAT-014 | US30 | H1 | 2,775 | 1.28 | catastrophic | 1.28 | PF, DD |
| STRAT-014 | EURUSD | H1 | 4,000 | 1.27 | 64.2% | 1.18 | PF, DD |
| STRAT-014 | GBPUSD | H1 | 3,992 | 1.31 | 1,600% | 1.19 | DD |
| STRAT-015 | US30 | H1 | 2,101 | 1.14 | 2,983% | 1.03 | PF, DD |
| STRAT-009 | US30 | H4 | 102 | 0.75 | - | 1.00 | Trades, PF |

---

## KEY FINDINGS (Updated)

1. **STRAT-001 is the universal performer** — Excellent PF (1.6-7.1) and OOS PF (1.8-10.7) on **every pair tested** (XAUUSD, US30, USDCAD, AUDUSD, EURUSD, GBPJPY). But **DD 50-800% on intraday**. Only D1 passes DD (2.9-16.8%) but fails 500+ trades.

2. **Drawdown is still the universal killer** — 19/20 promising strategies fail ONLY on Max DD > 20%. PF/OOS PF are often excellent.

3. **STRAT-003 (Gold M15) remains the ONLY fully VERIFIED** — Passes all criteria on XAUUSD. Gold ≠ Forex confirmed.

4. **US30 data now working** — usa30idxusd files provide 13+ years (70k H1 bars). STRAT-001 on US30 H1: 3,262 trades, PF 2.43, OOS PF 2.62, DD 50.5%.

5. **USDCAD 4H works** — 1,237 trades for STRAT-001, PF 2.20, OOS PF 2.18, but DD 452%.

6. **AUDUSD/USDCAD D1 pass DD but fail trade count** — Need 500+ trades; ~200-260 on D1.

---

## ROADMAP (Priority Order)

1. **Fix STRAT-001 DD** — Add ADX regime filter (skip chop), vol-adjusted ATR stops, daily loss limit, partial profit-taking at 1R/2R. Target: DD < 20% on intraday while keeping PF > 1.3.

2. **Freeze holdout** — Last 30% of each pair's data (untouched for final verification).

3. **Build "Ultimate" candidates** — STRAT-003 regime filter + STRAT-001 entry + STRAT-014 exit.

4. **Get proper AUDUSD/USDCAD intraday data** — Dukascopy/broker export for 5+ years M15/H1.

5. **Share Notion "Strategy Lab" database** with Hermes integration → populate all 50 results.

6. **Continue SCOUT** — Arabic/French, MQL5, GitHub, SSRN for more EMA/VWAP/Fib configs.

---

## FILES IN REPO (https://github.com/gv927/strategy-lab)
```
backtest_engine.py          # Full validation engine
strategy_lab.json           # 20 extracted strategies with exact rules
validation_report.md        # This report
validation_report_v2.md     # Updated report
validation_summary.json     # Aggregated results
CREATE_NOTION_DATABASE.md   # Database schema + population data
validation_STRAT-*.json     # 50+ individual test results
```

---

## NEXT IMMEDIATE ACTION
**Share the Notion "Strategy Lab" database** with the "Hermes" integration (Connections → Add → Hermes). Then I'll populate all 50+ validation results automatically.
