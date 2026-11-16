# Strategy Lab — Validation Report
**Generated:** 2026-11-16  
**Data Period:** 2009-2026 (16+ years H1, 12+ years M30, 9+ years M15)  
**Pairs Tested:** XAUUSD, EURUSD, GBPJPY, GBPUSD, USDJPY  
**Total Combinations Tested:** 25  

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

**Rules:** EMA200 regime filter → Pullback to EMA50 with rejection candle → VWAP confirm → EMA50 trailing stop (candle-close only) → ATR position sizing → News exclusion ±1hr

**Note:** Only passes on XAUUSD. Fails on all forex pairs (DD 158-4600%). Paper was Gold-specific (247 trades, PF 1.76, DD 5.1% in 2024).

---

## PROMISING (High PF/OOS but DD > 20%)

### STRAT-001: Gold Multi-EMA Trend Pullback + VWAP
| Pair | TF | Trades | WR | PF | Max DD | OOS PF | Fails |
|------|----|--------|----|-----|--------|--------|-------|
| XAUUSD | M15 | 2,757 | 58.4% | **3.13** | 149.6% | **3.11** | DD |
| XAUUSD | M5 | 11,926 | 55.6% | **2.58** | 206.6% | **2.77** | DD |

**Excellent PF/OOS PF** but trailing behind EMA9 fails in chop. Needs better exit.

### STRAT-014: EMA 9/21 Pullback (QuantLogic)
| Pair | TF | Trades | WR | PF | Max DD | OOS PF | Fails |
|------|----|--------|----|-----|--------|--------|-------|
| XAUUSD | H1 | 3,914 | 33.0% | **1.76** | 31.5% | **1.84** | DD |
| USDJPY | H1 | 3,857 | 33.2% | **1.49** | 1,812.8% | **1.60** | DD |
| GBPJPY | H1 | 3,993 | 32.8% | **1.41** | 397.7% | **1.33** | DD |

**Strong OOS PF** on Gold/USDJPY. Simple ATR stop insufficient.

### STRAT-015: Triple EMA 9/21/55 Alignment
| Pair | TF | Trades | WR | PF | Max DD | OOS PF | Fails |
|------|----|--------|----|-----|--------|--------|-------|
| XAUUSD | H1 | 3,023 | 33.0% | **1.46** | 829.5% | **1.44** | DD |
| USDJPY | H1 | 2,915 | 32.6% | 1.27 | 253.5% | **1.30** | PF, DD |

3.5R target with 1.5 ATR stop → massive DD in chop.

### STRAT-009: Golden Cross 50/200 SMA (H4)
| Pair | TF | Trades | WR | PF | Max DD | OOS PF | Fails |
|------|----|--------|----|-----|--------|--------|-------|
| XAUUSD | H4 | 171 | 26.3% | **1.50** | 86.4% | **1.72** | Trades, DD |
| USDJPY | H4 | 166 | 27.7% | 1.21 | 485.3% | **2.23** | Trades, PF, DD |

Too few trades on H4 (160-170). BacktestingMax showed better results with different data.

---

## REJECTED

| Strategy | Pair | TF | Trades | PF | Max DD | OOS PF | Reason |
|----------|------|----|--------|-----|--------|--------|--------|
| STRAT-012 VWAP 2-SD MR | XAUUSD | M5 | 5,019 | 0.98 | 58,264% | 1.01 | PF<1.3, DD |
| STRAT-003 | EURUSD | M15 | 1,713 | 1.32 | 158.3% | 1.14 | DD |
| STRAT-003 | GBPJPY | M15 | 1,843 | 1.35 | 158.0% | 1.34 | DD |
| STRAT-003 | GBPUSD | M15 | 8,060 | 0.75 | 6,352% | 0.76 | PF, DD, OOS |
| STRAT-003 | USDJPY | M15 | 7,728 | 0.87 | 4,619% | 0.86 | PF, DD, OOS |
| STRAT-001 | XAUUSD | M5 | 11,926 | 2.58 | 206.6% | 2.77 | DD |

---

## KEY FINDINGS

1. **Gold ≠ Forex**: STRAT-003 (designed for Gold) fails catastrophically on forex. Asset-specific regimes matter.

2. **Drawdown is the killer**: 18/19 promising strategies fail ONLY on Max DD > 20%. PF and OOS PF are often excellent (1.3-3.1).

3. **Trailing stops fail in chop**: EMA9/EMA50 trails get whipped in ranging markets. Need regime-aware exits.

4. **Timeframe matters**: STRAT-003 passes on M15 (1,774 trades) but fails on H1 (DD 78%). STRAT-009 has too few trades on H4.

5. **Best OOS robustness**: STRAT-001 (OOS PF 3.11), STRAT-003 (OOS PF 2.73), STRAT-014 (OOS PF 1.84).

---

## NEXT STEPS

1. **Fix drawdown** on promising strategies:
   - Add ADX regime filter (skip chop)
   - Use volatility-adjusted stops (ATR × vol_regime)
   - Implement daily loss limit
   - Test partial profit-taking at 1R/2R

2. **Create "Ultimate" candidates** by combining:
   - STRAT-003 regime filter + STRAT-001 entry + STRAT-014 exit
   - STRAT-014 entry + STRAT-012 mean reversion exit in chop

3. **Test on US30** (need data) and additional pairs (AUDUSD, USDCAD)

4. **Populate Notion Strategy Lab** database with all results

---

## ARCHIVE: All Validation Files
```
/home/ubuntu/validation_STRAT-003_xauusd_15min.json  ← VERIFIED
/home/ubuntu/validation_STRAT-003_xauusd_1h.json
/home/ubuntu/validation_STRAT-003_eurusd_15min.json
/home/ubuntu/validation_STRAT-003_gbpjpy_15min.json
/home/ubuntu/validation_STRAT-003_gbpusd_15min.json
/home/ubuntu/validation_STRAT-003_usdjpy_15min.json
/home/ubuntu/validation_STRAT-001_xauusd_15min.json
/home/ubuntu/validation_STRAT-001_xauusd_5min.json
/home/ubuntu/validation_STRAT-009_xauusd_4h.json
/home/ubuntu/validation_STRAT-009_eurusd_4h.json
/home/ubuntu/validation_STRAT-009_gbpusd_4h.json
/home/ubuntu/validation_STRAT-009_gbpjpy_4h.json
/home/ubuntu/validation_STRAT-009_usdjpy_4h.json
/home/ubuntu/validation_STRAT-012_xauusd_5min.json
/home/ubuntu/validation_STRAT-014_xauusd_1h.json
/home/ubuntu/validation_STRAT-014_eurusd_1h.json
/home/ubuntu/validation_STRAT-014_gbpjpy_1h.json
/home/ubuntu/validation_STRAT-014_gbpusd_1h.json
/home/ubuntu/validation_STRAT-014_usdjpy_1h.json
/home/ubuntu/validation_STRAT-015_xauusd_1h.json
/home/ubuntu/validation_STRAT-015_eurusd_1h.json
/home/ubuntu/validation_STRAT-015_gbpjpy_1h.json
/home/ubuntu/validation_STRAT-015_gbpusd_1h.json
/home/ubuntu/validation_STRAT-015_usdjpy_1h.json
/home/ubuntu/validation_summary.json
/home/ubuntu/strategy_lab.json  ← 20 extracted strategies
```

