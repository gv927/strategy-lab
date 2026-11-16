"""
Ultimate Combined Strategy: STRAT-003 Regime + STRAT-001 Entry + STRAT-014 Exit
- Regime filter: EMA200 (from STRAT-003)
- Entry: Multi-EMA pullback to EMA21 with VWAP confirm (from STRAT-001)
- Exit: EMA9/21 pullback exit logic (from STRAT-014) + ADX regime filter
- Risk: ATR-based sizing, daily loss limit, partial profits at 1R/2R
"""

import sys
sys.path.insert(0, '.')
from backtest_engine import (
    load_data, calculate_indicators, apply_spread_slippage,
    run_full_validation, check_criteria, calculate_metrics,
    PIP_VALUE, SPREADS, SLIPPAGE_PIPS
)
from dataclasses import dataclass
from typing import List, Dict
import pandas as pd
import numpy as np
from datetime import datetime

@dataclass
class Trade:
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    pair: str
    direction: str
    entry_price: float
    exit_price: float
    size: float
    pnl_pips: float
    pnl_usd: float
    bars_held: int
    exit_reason: str

def run_ultimate_strategy(df: pd.DataFrame, pair: str, params: dict) -> List[Trade]:
    """
    ULTIMATE: STRAT-003 Regime + STRAT-001 Entry + STRAT-014 Exit
    """
    trades = []
    position = None
    
    atr_period = params.get('atr_period', 14)
    adx_period = params.get('adx_period', 14)
    atr_col = f'atr_{atr_period}'
    adx_col = f'adx_{adx_period}'
    
    # Risk params
    risk_per_trade = params.get('risk_per_trade', 0.01)  # 1% per trade
    daily_loss_limit = params.get('daily_loss_limit', 0.03)  # 3% daily
    partial_1r = params.get('partial_1r', True)
    partial_2r = params.get('partial_2r', True)
    adx_threshold = params.get('adx_threshold', 25)
    
    daily_pnl = {}
    
    for i in range(200, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i-1]
        date_key = row.name.date()
        
        # Daily loss limit check
        if daily_pnl.get(date_key, 0) <= -daily_loss_limit:
            continue
        
        atr_val = row[atr_col] if not pd.isna(row[atr_col]) else (row['high'] - row['low'])
        adx_val = row[adx_col] if not pd.isna(row[adx_col]) else 20
        
        # === REGIME FILTER (STRAT-003) ===
        regime_long = row['close'] > row['ema_200'] and row['ema_200'] > df.iloc[i-10]['ema_200']
        regime_short = row['close'] < row['ema_200'] and row['ema_200'] < df.iloc[i-10]['ema_200']
        
        # ADX regime filter - skip chop
        if adx_val < adx_threshold:
            # In chop: only allow mean reversion? For now, skip entries
            pass  # Allow but be more selective
        
        # === EXIT LOGIC (STRAT-014 + risk management) ===
        if position is not None:
            exit_price = None
            exit_reason = ""
            
            if position['direction'] == 'long':
                # STRAT-014 exit: close below EMA9
                ema9_exit = row['close'] < row['ema_9']
                
                # Trailing stops
                trail_ema21 = row['ema_21']
                hard_stop = position['stop_price']
                
                # Partial profit taking
                risk_pips = position['risk_pips']
                entry_price = position['entry_price']
                
                if partial_1r and row['high'] >= entry_price + risk_pips * PIP_VALUE[pair] and not position.get('partial_1r_taken', False):
                    # Take 50% at 1R
                    partial_size = position['size'] * 0.5
                    exit_price = apply_spread_slippage(entry_price + risk_pips * PIP_VALUE[pair], 'short', pair)
                    pnl_pips = (exit_price - entry_price) / PIP_VALUE[pair]
                    trades.append(Trade(
                        entry_time=position['entry_time'],
                        exit_time=row.name,
                        pair=pair,
                        direction='long',
                        entry_price=entry_price,
                        exit_price=exit_price,
                        size=partial_size,
                        pnl_pips=pnl_pips,
                        pnl_usd=pnl_pips * PIP_VALUE[pair] * partial_size * 100000,
                        bars_held=i - position['entry_idx'],
                        exit_reason="partial_1R"
                    ))
                    position['size'] = partial_size
                    position['partial_1r_taken'] = True
                    # Move stop to breakeven
                    position['stop_price'] = max(position['stop_price'], entry_price)
                
                if partial_2r and row['high'] >= entry_price + 2 * risk_pips * PIP_VALUE[pair] and not position.get('partial_2r_taken', False):
                    partial_size = position['size'] * 0.5
                    exit_price = apply_spread_slippage(entry_price + 2 * risk_pips * PIP_VALUE[pair], 'short', pair)
                    pnl_pips = (exit_price - entry_price) / PIP_VALUE[pair]
                    trades.append(Trade(
                        entry_time=position['entry_time'],
                        exit_time=row.name,
                        pair=pair,
                        direction='long',
                        entry_price=entry_price,
                        exit_price=exit_price,
                        size=partial_size,
                        pnl_pips=pnl_pips,
                        pnl_usd=pnl_pips * PIP_VALUE[pair] * partial_size * 100000,
                        bars_held=i - position['entry_idx'],
                        exit_reason="partial_2R"
                    ))
                    position['size'] = partial_size
                    position['partial_2r_taken'] = True
                
                # Full exit conditions
                if row['low'] <= position['stop_price']:
                    exit_price = apply_spread_slippage(position['stop_price'], 'short', pair)
                    exit_reason = "stop_loss"
                elif ema9_exit:
                    exit_price = apply_spread_slippage(row['close'], 'short', pair)
                    exit_reason = "ema9_exit"
                elif not regime_long:
                    exit_price = apply_spread_slippage(row['close'], 'short', pair)
                    exit_reason = "regime_change"
                    
            else:  # short
                ema9_exit = row['close'] > row['ema_9']
                trail_ema21 = row['ema_21']
                hard_stop = position['stop_price']
                
                risk_pips = position['risk_pips']
                entry_price = position['entry_price']
                
                if partial_1r and row['low'] <= entry_price - risk_pips * PIP_VALUE[pair] and not position.get('partial_1r_taken', False):
                    partial_size = position['size'] * 0.5
                    exit_price = apply_spread_slippage(entry_price - risk_pips * PIP_VALUE[pair], 'long', pair)
                    pnl_pips = (entry_price - exit_price) / PIP_VALUE[pair]
                    trades.append(Trade(
                        entry_time=position['entry_time'],
                        exit_time=row.name,
                        pair=pair,
                        direction='short',
                        entry_price=entry_price,
                        exit_price=exit_price,
                        size=partial_size,
                        pnl_pips=pnl_pips,
                        pnl_usd=pnl_pips * PIP_VALUE[pair] * partial_size * 100000,
                        bars_held=i - position['entry_idx'],
                        exit_reason="partial_1R"
                    ))
                    position['size'] = partial_size
                    position['partial_1r_taken'] = True
                    position['stop_price'] = min(position['stop_price'], entry_price)
                
                if partial_2r and row['low'] <= entry_price - 2 * risk_pips * PIP_VALUE[pair] and not position.get('partial_2r_taken', False):
                    partial_size = position['size'] * 0.5
                    exit_price = apply_spread_slippage(entry_price - 2 * risk_pips * PIP_VALUE[pair], 'long', pair)
                    pnl_pips = (entry_price - exit_price) / PIP_VALUE[pair]
                    trades.append(Trade(
                        entry_time=position['entry_time'],
                        exit_time=row.name,
                        pair=pair,
                        direction='short',
                        entry_price=entry_price,
                        exit_price=exit_price,
                        size=partial_size,
                        pnl_pips=pnl_pips,
                        pnl_usd=pnl_pips * PIP_VALUE[pair] * partial_size * 100000,
                        bars_held=i - position['entry_idx'],
                        exit_reason="partial_2R"
                    ))
                    position['size'] = partial_size
                    position['partial_2r_taken'] = True
                
                if row['high'] >= position['stop_price']:
                    exit_price = apply_spread_slippage(position['stop_price'], 'long', pair)
                    exit_reason = "stop_loss"
                elif ema9_exit:
                    exit_price = apply_spread_slippage(row['close'], 'long', pair)
                    exit_reason = "ema9_exit"
                elif not regime_short:
                    exit_price = apply_spread_slippage(row['close'], 'long', pair)
                    exit_reason = "regime_change"
            
            if exit_price is not None:
                pnl_pips = (exit_price - position['entry_price']) / PIP_VALUE[pair]
                if position['direction'] == 'short':
                    pnl_pips = -pnl_pips
                
                trades.append(Trade(
                    entry_time=position['entry_time'],
                    exit_time=row.name,
                    pair=pair,
                    direction=position['direction'],
                    entry_price=position['entry_price'],
                    exit_price=exit_price,
                    size=position['size'],
                    pnl_pips=pnl_pips,
                    pnl_usd=pnl_pips * PIP_VALUE[pair] * position['size'] * 100000,
                    bars_held=i - position['entry_idx'],
                    exit_reason=exit_reason
                ))
                
                # Track daily PnL
                daily_pnl[date_key] = daily_pnl.get(date_key, 0) + pnl_pips * PIP_VALUE[pair] * position['size'] * 100000 / 10000  # approximate %
                position = None
        
        # === ENTRY LOGIC (STRAT-001 + STRAT-003) ===
        if position is None:
            # Trend alignment (STRAT-001)
            ema_align_long = row['ema_9'] > row['ema_21'] > row['ema_50']
            ema_align_short = row['ema_9'] < row['ema_21'] < row['ema_50']
            
            # VWAP confirm (STRAT-001)
            vwap_long = row['close'] > row['vwap']
            vwap_short = row['close'] < row['vwap']
            
            # Pullback to EMA21 (STRAT-001/003)
            if regime_long and ema_align_long and vwap_long and adx_val >= adx_threshold:
                # Pullback: low touches EMA21, close above
                if prev['low'] <= prev['ema_21'] and prev['close'] > prev['ema_21']:
                    entry_price = apply_spread_slippage(row['open'], 'long', pair)
                    stop_price = prev['low'] - 1.5 * atr_val
                    risk_pips = (entry_price - stop_price) / PIP_VALUE[pair]
                    position = {
                        'direction': 'long',
                        'entry_time': row.name,
                        'entry_idx': i,
                        'entry_price': entry_price,
                        'stop_price': stop_price,
                        'risk_pips': risk_pips,
                        'size': 1.0,
                        'partial_1r_taken': False,
                        'partial_2r_taken': False
                    }
            
            elif regime_short and ema_align_short and vwap_short and adx_val >= adx_threshold:
                if prev['high'] >= prev['ema_21'] and prev['close'] < prev['ema_21']:
                    entry_price = apply_spread_slippage(row['open'], 'short', pair)
                    stop_price = prev['high'] + 1.5 * atr_val
                    risk_pips = (stop_price - entry_price) / PIP_VALUE[pair]
                    position = {
                        'direction': 'short',
                        'entry_time': row.name,
                        'entry_idx': i,
                        'entry_price': entry_price,
                        'stop_price': stop_price,
                        'risk_pips': risk_pips,
                        'size': 1.0,
                        'partial_1r_taken': False,
                        'partial_2r_taken': False
                    }
    
    return trades

# Test on key pairs
if __name__ == "__main__":
    from backtest_engine import run_full_validation
    
    # Monkey-patch to use our strategy
    import backtest_engine as be
    be.STRATEGY_RUNNERS['ULTIMATE'] = run_ultimate_strategy
    
    params = {
        'atr_period': 14,
        'adx_period': 14,
        'risk_per_trade': 0.01,
        'daily_loss_limit': 0.03,
        'partial_1r': True,
        'partial_2r': True,
        'adx_threshold': 25,
    }
    
    pairs = ['xauusd', 'us30', 'usdcad', 'eurusd', 'gbpjpy']
    timeframes = ['15min', '1h']
    
    for pair in pairs:
        for tf in timeframes:
            if pair == 'audusd' and tf != '1d':
                continue
            print(f"\nTesting ULTIMATE on {pair.upper()} {tf}")
            try:
                # Need to add to STRATEGY_RUNNERS temporarily
                result = be.run_full_validation('ULTIMATE', 'Ultimate Combined', pair, tf, params)
                passed, reasons = be.check_criteria(result)
                print(f"  Trades: {result.total_trades}, WR: {result.win_rate:.1%}, PF: {result.profit_factor:.2f}, DD: {result.max_drawdown_pct:.1f}%, OOS PF: {result.oos_profit_factor:.2f}, PASSED: {passed}")
                if reasons:
                    for r in reasons: print(f"  FAIL: {r}")
            except Exception as e:
                print(f"  ERROR: {e}")

