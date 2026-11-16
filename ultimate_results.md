# Ultimate Combined Strategy — Test Results

## Strategy Composition
- **Regime Filter**: STRAT-003 (EMA200 trend + slope)
- **Entry**: STRAT-001 (Multi-EMA pullback to EMA21 + VWAP confirm)
- **Exit**: STRAT-014 (EMA9 exit) + Partial profits (1R/2R) + Daily loss limit
- **Risk**: ATR-based sizing, ADX regime filter (skip chop)

## Test Results (Base Parameters)

| Pair | TF | Trades | WR | PF | Max DD | Notes |
|------|----|--------|----|-----|--------|-------|
| XAUUSD | M15 | 824 | 59.3% | 1.19 | 64.1% | PF < 1.3 |
| US30 | H1 | 889 | 61.1% | **2.47** | 85.6% | Best PF, DD too high |
| USDCAD | H4 | 397 | 59.2% | **2.23** | 238.3% | Good PF, DD high |

## Comparison vs Components

| Strategy | US30 H1 PF | US30 H1 DD | XAUUSD M15 PF | XAUUSD M15 DD |
|----------|------------|------------|---------------|---------------|
| STRAT-001 (base) | 2.43 | 50.5% | 3.13 | 149.6% |
| STRAT-003 (base) | N/A | N/A | **2.37** | **19.6%** ✓ |
| STRAT-014 (base) | 1.28 | catastrophic | 1.76 | 31.5% |
| **ULTIMATE** | **2.47** | 85.6% | 1.19 | 64.1% |

## Findings

1. **US30 improved**: PF 2.47 (vs 2.43) but DD worsened (85.6% vs 50.5%)
2. **XAUUSD degraded**: PF dropped from 3.13 to 1.19 — ADX filter kills too many trades in ranging gold
3. **USDCAD decent**: PF 2.23 but DD 238% — needs 4H-specific tuning

## Root Cause
- **ADX filter** (threshold 25) filters out too many valid trend entries on Gold
- **EMA9 exit** too slow in strong trends — gets whipped in chop
- **Partial profits** help but don't solve core DD issue
- **Daily loss limit** rarely triggered (DD comes from many small losses in chop)

## Next Iterations Needed

1. **Asset-specific ADX thresholds**: Gold needs lower (15-20), Indices higher (25-30)
2. **Volatility-adjusted stops**: ATR × vol_regime (wider in high vol, tighter in low)
3. **Faster exit in chop**: Add RSI/Bollinger confirmation for EMA9 exit
4. **Session filter**: Only trade London/NY overlap for Gold, cash session for indices
5. **Regime-aware trailing**: EMA21 trail in trend, EMA9 in chop

## Files
- `ultimate_strategy.py` — Full implementation
- `backtest_engine.py` — Core engine (updated with ULTIMATE runner)

## Next Steps
- [ ] Asset-specific parameter sets
- [ ] Volatility-adjusted ATR multiplier
- [ ] Session/time filters
- [ ] Walk-forward optimization on 70/30 split
- [ ] Monte Carlo validation (10k reshuffles)

