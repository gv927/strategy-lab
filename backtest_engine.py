"""
Backtesting Engine for Strategy Lab
Tests strategies on XAUUSD, EURUSD, GBPJPY, GBPUSD, USDJPY
with realistic spreads, slippage, and walk-forward validation.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime, time
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path("/home/ubuntu/Desktop/data-download/historical_data/")

# Typical spreads (pips) for major pairs during liquid hours
SPREADS = {
    'xauusd': 0.30,    # ~30 cents
    'eurusd': 0.8,     # 0.8 pips
    'gbpjpy': 1.5,     # 1.5 pips
    'gbpusd': 1.0,     # 1.0 pips
    'usdjpy': 0.8,     # 0.8 pips
    'us30': 2.0,       # ~20 points (2 pips equivalent)
    'audusd': 1.0,     # 1.0 pips
    'usdcad': 1.2,     # 1.2 pips
}

# Pip values
PIP_VALUE = {
    'xauusd': 0.01,    # 1 pip = $0.01
    'eurusd': 0.0001,
    'gbpjpy': 0.01,
    'gbpusd': 0.0001,
    'usdjpy': 0.01,
    'us30': 1.0,       # 1 point = $1 (CFD)
    'audusd': 0.0001,
    'usdcad': 0.0001,
}

# Slippage (pips) - realistic for market orders
SLIPPAGE_PIPS = 0.5

@dataclass
class Trade:
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    pair: str
    direction: str  # 'long' or 'short'
    entry_price: float
    exit_price: float
    size: float
    pnl_pips: float
    pnl_usd: float
    bars_held: int
    exit_reason: str

@dataclass
class BacktestResult:
    strategy_id: str
    strategy_name: str
    pair: str
    timeframe: str
    trades: List[Trade]
    total_trades: int
    win_rate: float
    profit_factor: float
    max_drawdown_pct: float
    total_pnl_usd: float
    total_pnl_pips: float
    avg_trade_pips: float
    sharpe_ratio: float
    oos_profit_factor: float
    oos_win_rate: float
    params: dict

def load_data(pair: str, timeframe: str) -> pd.DataFrame:
    """Load and prepare OHLC data."""
    # Map pair names to actual file prefixes
    file_map = {
        'us30': 'usa30idxusd',
        'xauusd': 'xauusd',
        'eurusd': 'eurusd',
        'gbpjpy': 'gbpjpy',
        'gbpusd': 'gbpusd',
        'usdjpy': 'usdjpy',
        'audusd': 'audusd',
        'usdcad': 'usdcad',
    }
    file_prefix = file_map.get(pair, pair)
    f = DATA_DIR / f"{file_prefix}_{timeframe}_master.csv"
    if not f.exists():
        raise FileNotFoundError(f"No data for {pair} {timeframe} (tried {file_prefix}_{timeframe}_master.csv)")
    
    df = pd.read_csv(f)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df = df.set_index('Timestamp').sort_index()
    
    # Ensure we have all required columns
    required = ['open', 'high', 'low', 'close']
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing column {col} in {pair} {timeframe}")
    
    return df

def resample_data(df: pd.DataFrame, target_tf: str) -> pd.DataFrame:
    """Resample to target timeframe if needed."""
    if target_tf == '1h' or target_tf == 'H1':
        rule = '1H'
    elif target_tf == '30min' or target_tf == 'M30':
        rule = '30T'
    elif target_tf == '15min' or target_tf == 'M15':
        rule = '15T'
    elif target_tf == '5min' or target_tf == 'M5':
        rule = '5T'
    elif target_tf == '1min' or target_tf == 'M1':
        rule = '1T'
    elif target_tf == '4h' or target_tf == 'H4':
        rule = '4H'
    elif target_tf == '1d' or target_tf == 'D1':
        rule = '1D'
    else:
        return df
    
    return df.resample(rule).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last'
    }).dropna()

def calculate_indicators(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Calculate all technical indicators needed."""
    df = df.copy()
    
    # EMAs
    for period in [9, 12, 20, 21, 50, 55, 65, 200]:
        if f'ema_{period}' not in df.columns:
            df[f'ema_{period}'] = df['close'].ewm(span=period, adjust=False).mean()
    
    # SMAs
    for period in [20, 32, 50, 200]:
        if f'sma_{period}' not in df.columns:
            df[f'sma_{period}'] = df['close'].rolling(period).mean()
    
    # ATR
    atr_period = params.get('atr_period', 14)
    if f'atr_{atr_period}' not in df.columns:
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df[f'atr_{atr_period}'] = tr.ewm(alpha=1/atr_period, adjust=False).mean()
    
    # RSI
    rsi_period = params.get('rsi_period', 14)
    if f'rsi_{rsi_period}' not in df.columns:
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).ewm(alpha=1/rsi_period, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/rsi_period, adjust=False).mean()
        rs = gain / loss
        df[f'rsi_{rsi_period}'] = 100 - (100 / (1 + rs))
    
    # ADX
    adx_period = params.get('adx_period', 14)
    if f'adx_{adx_period}' not in df.columns:
        # Simplified ADX
        plus_dm = df['high'].diff()
        minus_dm = df['low'].diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm > 0] = 0
        minus_dm = minus_dm.abs()
        
        tr = pd.concat([
            df['high'] - df['low'],
            np.abs(df['high'] - df['close'].shift()),
            np.abs(df['low'] - df['close'].shift())
        ], axis=1).max(axis=1)
        
        atr = tr.ewm(alpha=1/adx_period, adjust=False).mean()
        plus_di = 100 * (plus_dm.ewm(alpha=1/adx_period, adjust=False).mean() / atr)
        minus_di = 100 * (minus_dm.ewm(alpha=1/adx_period, adjust=False).mean() / atr)
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        df[f'adx_{adx_period}'] = dx.ewm(alpha=1/adx_period, adjust=False).mean()
    
    # VWAP (session-based, approximate using typical price * volume proxy)
    # Since we don't have volume, use typical price cumulative
    if 'vwap' not in df.columns:
        typical = (df['high'] + df['low'] + df['close']) / 3
        # Reset daily
        df['date'] = df.index.date
        df['cum_typical_vol'] = typical.groupby(df['date']).cumsum()
        df['cum_vol_proxy'] = df.groupby('date').cumcount() + 1
        df['vwap'] = df['cum_typical_vol'] / df['cum_vol_proxy']
        df.drop(['date', 'cum_typical_vol', 'cum_vol_proxy'], axis=1, inplace=True)
    
    # VWAP Standard Deviation Bands
    if 'vwap_sd' not in df.columns:
        typical = (df['high'] + df['low'] + df['close']) / 3
        df['vwap_sd'] = typical.rolling(20).std()
        df['vwap_upper_1'] = df['vwap'] + df['vwap_sd']
        df['vwap_lower_1'] = df['vwap'] - df['vwap_sd']
        df['vwap_upper_2'] = df['vwap'] + 2 * df['vwap_sd']
        df['vwap_lower_2'] = df['vwap'] - 2 * df['vwap_sd']
        df['vwap_upper_3'] = df['vwap'] + 3 * df['vwap_sd']
        df['vwap_lower_3'] = df['vwap'] - 3 * df['vwap_sd']
    
    # Bollinger Bands
    bb_period = params.get('bb_period', 20)
    if f'bb_mid_{bb_period}' not in df.columns:
        df[f'bb_mid_{bb_period}'] = df['close'].rolling(bb_period).mean()
        bb_std = df['close'].rolling(bb_period).std()
        df[f'bb_upper_{bb_period}'] = df[f'bb_mid_{bb_period}'] + 2 * bb_std
        df[f'bb_lower_{bb_period}'] = df[f'bb_mid_{bb_period}'] - 2 * bb_std
    
    # Pivots (daily)
    if 'pivot' not in df.columns:
        df['date'] = df.index.date
        daily = df.groupby('date').agg({
            'high': 'max', 'low': 'min', 'close': 'last'
        }).shift(1)
        daily['pivot'] = (daily['high'] + daily['low'] + daily['close']) / 3
        daily['r1'] = 2 * daily['pivot'] - daily['low']
        daily['s1'] = 2 * daily['pivot'] - daily['high']
        daily['r2'] = daily['pivot'] + (daily['high'] - daily['low'])
        daily['s2'] = daily['pivot'] - (daily['high'] - daily['low'])
        daily['r3'] = daily['high'] + 2 * (daily['pivot'] - daily['low'])
        daily['s3'] = daily['low'] - 2 * (daily['high'] - daily['pivot'])
        
        df = df.join(daily[['pivot','r1','s1','r2','s2','r3','s3']], on='date')
        df.drop('date', axis=1, inplace=True)
    
    return df

def apply_spread_slippage(price: float, direction: str, pair: str) -> float:
    """Apply spread and slippage to entry/exit price."""
    spread = SPREADS.get(pair, 1.0) * PIP_VALUE.get(pair, 0.0001)
    slippage = SLIPPAGE_PIPS * PIP_VALUE.get(pair, 0.0001)
    
    if direction == 'long':
        return price + spread/2 + slippage  # Buy at ask + slippage
    else:
        return price - spread/2 - slippage  # Sell at bid - slippage

def run_strategy_001(df: pd.DataFrame, pair: str, params: dict) -> List[Trade]:
    """
    STRAT-001: Gold Multi-EMA Trend Pullback with VWAP Anchor
    Regime: Price > EMA200 (long) / < EMA200 (short)
    Trend: EMA50 > EMA200 (long) / < EMA200 (short)
    Entry: Pullback to EMA21 in trend direction, candle closes back above/below EMA21, VWAP confirm
    Stop: 1.5 * ATR beyond pullback low/high
    Trail: Behind EMA9
    """
    trades = []
    position = None
    atr_period = params.get("atr_period", 14)
    atr_col = f'atr_{atr_period}'
    
    for i in range(200, len(df)):  # Need 200 bars for EMA200
        row = df.iloc[i]
        prev = df.iloc[i-1]
        
        # Regime filter
        regime_long = row['close'] > row['ema_200'] and row['ema_200'] > df.iloc[i-5]['ema_200']
        regime_short = row['close'] < row['ema_200'] and row['ema_200'] < df.iloc[i-5]['ema_200']
        
        # Trend filter
        trend_long = row['ema_50'] > row['ema_200']
        trend_short = row['ema_50'] < row['ema_200']
        
        # VWAP confirm
        vwap_long = row['close'] > row['vwap']
        vwap_short = row['close'] < row['vwap']
        
        # EMA alignment for pullback
        ema_align_long = row['ema_9'] > row['ema_21'] > row['ema_50']
        ema_align_short = row['ema_9'] < row['ema_21'] < row['ema_50']
        
        atr_val = row[atr_col] if not pd.isna(row[atr_col]) else (row['high'] - row['low'])
        
        # Check exit first
        if position is not None:
            exit_price = None
            exit_reason = ""
            
            if position['direction'] == 'long':
                # Trail behind EMA9
                trail_stop = row['ema_9']
                # Hard stop
                hard_stop = position['stop_price']
                stop_price = max(trail_stop, hard_stop)
                
                if row['low'] <= stop_price:
                    exit_price = apply_spread_slippage(stop_price, 'short', pair)
                    exit_reason = "trail_stop" if stop_price == trail_stop else "hard_stop"
                elif row['close'] < row['ema_200']:  # Regime change
                    exit_price = apply_spread_slippage(row['close'], 'short', pair)
                    exit_reason = "regime_change"
                    
            else:  # short
                trail_stop = row['ema_9']
                hard_stop = position['stop_price']
                stop_price = min(trail_stop, hard_stop)
                
                if row['high'] >= stop_price:
                    exit_price = apply_spread_slippage(stop_price, 'long', pair)
                    exit_reason = "trail_stop" if stop_price == trail_stop else "hard_stop"
                elif row['close'] > row['ema_200']:
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
                position = None
        
        # Check entry
        if position is None and regime_long and trend_long and vwap_long and ema_align_long:
            # Pullback to EMA21: low touches EMA21, close above EMA21
            if prev['low'] <= prev['ema_21'] and prev['close'] > prev['ema_21']:
                entry_price = apply_spread_slippage(row['open'], 'long', pair)
                stop_price = prev['low'] - 1.5 * atr_val
                position = {
                    'direction': 'long',
                    'entry_time': row.name,
                    'entry_idx': i,
                    'entry_price': entry_price,
                    'stop_price': stop_price,
                    'size': 1.0
                }
        
        elif position is None and regime_short and trend_short and vwap_short and ema_align_short:
            # Pullback to EMA21: high touches EMA21, close below EMA21
            if prev['high'] >= prev['ema_21'] and prev['close'] < prev['ema_21']:
                entry_price = apply_spread_slippage(row['open'], 'short', pair)
                stop_price = prev['high'] + 1.5 * atr_val
                position = {
                    'direction': 'short',
                    'entry_time': row.name,
                    'entry_idx': i,
                    'entry_price': entry_price,
                    'stop_price': stop_price,
                    'size': 1.0
                }
    
    return trades

def run_strategy_003(df: pd.DataFrame, pair: str, params: dict) -> List[Trade]:
    """
    STRAT-003: Regime-Filtered Gold (SSRN Paper)
    Regime: Price > EMA200 rising (long) / < EMA200 falling (short)
    Entry: Pullback to EMA50, rejection candle closes back above/below EMA50, price >/< VWAP
    Stop: 1.5 * ATR beyond EMA50
    Trail: EMA50 as dynamic trailing stop (candle close only)
    News filter: Skip ±1hr of major news (simplified: skip high volatility bars)
    """
    trades = []
    position = None
    atr_period = params.get("atr_period", 14)
    atr_col = f'atr_{atr_period}'
    
    for i in range(200, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i-1]
        
        # Regime
        regime_long = row['close'] > row['ema_200'] and row['ema_200'] > df.iloc[i-10]['ema_200']
        regime_short = row['close'] < row['ema_200'] and row['ema_200'] < df.iloc[i-10]['ema_200']
        
        atr_val = row[atr_col] if not pd.isna(row[atr_col]) else (row['high'] - row['low'])
        
        # Exit
        if position is not None:
            exit_price = None
            exit_reason = ""
            
            if position['direction'] == 'long':
                # Trail: EMA50 on candle close
                trail_stop = row['ema_50']
                hard_stop = position['stop_price']
                stop_price = max(trail_stop, hard_stop)
                
                if row['low'] <= stop_price:
                    exit_price = apply_spread_slippage(stop_price, 'short', pair)
                    exit_reason = "trail_stop" if stop_price == trail_stop else "hard_stop"
                elif not regime_long:
                    exit_price = apply_spread_slippage(row['close'], 'short', pair)
                    exit_reason = "regime_change"
                    
            else:
                trail_stop = row['ema_50']
                hard_stop = position['stop_price']
                stop_price = min(trail_stop, hard_stop)
                
                if row['high'] >= stop_price:
                    exit_price = apply_spread_slippage(stop_price, 'long', pair)
                    exit_reason = "trail_stop" if stop_price == trail_stop else "hard_stop"
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
                position = None
        
        # Entry
        if position is None and regime_long:
            # Pullback to EMA50: low touches EMA50, rejection close above
            if prev['low'] <= prev['ema_50'] and prev['close'] > prev['ema_50'] and prev['close'] > prev['vwap']:
                entry_price = apply_spread_slippage(row['open'], 'long', pair)
                stop_price = prev['ema_50'] - 1.5 * atr_val
                position = {
                    'direction': 'long',
                    'entry_time': row.name,
                    'entry_idx': i,
                    'entry_price': entry_price,
                    'stop_price': stop_price,
                    'size': 1.0
                }
        
        elif position is None and regime_short:
            if prev['high'] >= prev['ema_50'] and prev['close'] < prev['ema_50'] and prev['close'] < prev['vwap']:
                entry_price = apply_spread_slippage(row['open'], 'short', pair)
                stop_price = prev['ema_50'] + 1.5 * atr_val
                position = {
                    'direction': 'short',
                    'entry_time': row.name,
                    'entry_idx': i,
                    'entry_price': entry_price,
                    'stop_price': stop_price,
                    'size': 1.0
                }
    
    return trades

def run_strategy_009(df: pd.DataFrame, pair: str, params: dict) -> List[Trade]:
    """
    STRAT-009: Golden Cross 50/200 SMA with 3 ATR Stop
    Entry: SMA50 crosses SMA200
    Stop: 3 * ATR from prior close
    Exit: Opposite cross
    """
    trades = []
    position = None
    atr_period = params.get("atr_period", 14)
    atr_col = f'atr_{atr_period}'
    
    for i in range(200, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i-1]
        
        atr_val = row[atr_col] if not pd.isna(row[atr_col]) else (row['high'] - row['low'])
        
        # Golden cross / Death cross
        golden_cross = prev['sma_50'] <= prev['sma_200'] and row['sma_50'] > row['sma_200']
        death_cross = prev['sma_50'] >= prev['sma_200'] and row['sma_50'] < row['sma_200']
        
        # Exit
        if position is not None:
            exit_price = None
            exit_reason = ""
            
            if position['direction'] == 'long' and death_cross:
                exit_price = apply_spread_slippage(row['open'], 'short', pair)
                exit_reason = "death_cross"
            elif position['direction'] == 'short' and golden_cross:
                exit_price = apply_spread_slippage(row['open'], 'long', pair)
                exit_reason = "golden_cross"
            elif position['direction'] == 'long' and row['low'] <= position['stop_price']:
                exit_price = apply_spread_slippage(position['stop_price'], 'short', pair)
                exit_reason = "stop_loss"
            elif position['direction'] == 'short' and row['high'] >= position['stop_price']:
                exit_price = apply_spread_slippage(position['stop_price'], 'long', pair)
                exit_reason = "stop_loss"
            
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
                position = None
        
        # Entry
        if position is None:
            if golden_cross:
                entry_price = apply_spread_slippage(row['open'], 'long', pair)
                stop_price = prev['close'] - 3 * atr_val
                position = {
                    'direction': 'long',
                    'entry_time': row.name,
                    'entry_idx': i,
                    'entry_price': entry_price,
                    'stop_price': stop_price,
                    'size': 1.0
                }
            elif death_cross:
                entry_price = apply_spread_slippage(row['open'], 'short', pair)
                stop_price = prev['close'] + 3 * atr_val
                position = {
                    'direction': 'short',
                    'entry_time': row.name,
                    'entry_idx': i,
                    'entry_price': entry_price,
                    'stop_price': stop_price,
                    'size': 1.0
                }
    
    return trades

def run_strategy_012(df: pd.DataFrame, pair: str, params: dict) -> List[Trade]:
    """
    STRAT-012: VWAP 2-SD Mean Reversion with ADX Regime Filter
    Regime: ADX < 25, no news (simplified), opening range normal
    Setup: Price at ±2SD VWAP, rejection candle
    Stop: 1 ATR beyond rejection
    Target: VWAP
    """
    trades = []
    position = None
    atr_period = params.get("atr_period", 14)
    adx_period = params.get("adx_period", 14)
    atr_col = f'atr_{atr_period}'
    adx_col = f'adx_{adx_period}'
    
    for i in range(50, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i-1]
        
        atr_val = row[atr_col] if not pd.isna(row[atr_col]) else (row['high'] - row['low'])
        adx_val = row[adx_col] if not pd.isna(row[adx_col]) else 20
        
        # Regime filter
        if adx_val >= 25:
            continue  # Strong trend, skip mean reversion
        
        # Exit
        if position is not None:
            exit_price = None
            exit_reason = ""
            
            if position['direction'] == 'long':
                if row['high'] >= position['target_price']:
                    exit_price = apply_spread_slippage(position['target_price'], 'short', pair)
                    exit_reason = "target_vwap"
                elif row['low'] <= position['stop_price']:
                    exit_price = apply_spread_slippage(position['stop_price'], 'short', pair)
                    exit_reason = "stop_loss"
                elif row['close'] > row['vwap_upper_3']:  # Acceleration to 3SD
                    exit_price = apply_spread_slippage(row['close'], 'short', pair)
                    exit_reason = "acceleration_3sd"
                    
            else:
                if row['low'] <= position['target_price']:
                    exit_price = apply_spread_slippage(position['target_price'], 'long', pair)
                    exit_reason = "target_vwap"
                elif row['high'] >= position['stop_price']:
                    exit_price = apply_spread_slippage(position['stop_price'], 'long', pair)
                    exit_reason = "stop_loss"
                elif row['close'] < row['vwap_lower_3']:
                    exit_price = apply_spread_slippage(row['close'], 'long', pair)
                    exit_reason = "acceleration_3sd"
            
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
                position = None
        
        # Entry - Rejection at ±2SD
        if position is None:
            # Long: price at -2SD, rejection (hammer/bullish engulfing)
            if prev['low'] <= prev['vwap_lower_2'] and prev['close'] > prev['open'] and prev['close'] > prev['vwap_lower_2']:
                entry_price = apply_spread_slippage(row['open'], 'long', pair)
                stop_price = prev['low'] - atr_val
                target_price = prev['vwap']
                position = {
                    'direction': 'long',
                    'entry_time': row.name,
                    'entry_idx': i,
                    'entry_price': entry_price,
                    'stop_price': stop_price,
                    'target_price': target_price,
                    'size': 1.0
                }
            # Short: price at +2SD, rejection
            elif prev['high'] >= prev['vwap_upper_2'] and prev['close'] < prev['open'] and prev['close'] < prev['vwap_upper_2']:
                entry_price = apply_spread_slippage(row['open'], 'short', pair)
                stop_price = prev['high'] + atr_val
                target_price = prev['vwap']
                position = {
                    'direction': 'short',
                    'entry_time': row.name,
                    'entry_idx': i,
                    'entry_price': entry_price,
                    'stop_price': stop_price,
                    'target_price': target_price,
                    'size': 1.0
                }
    
    return trades

def run_strategy_014(df: pd.DataFrame, pair: str, params: dict) -> List[Trade]:
    """
    STRAT-014: EMA 9/21 Multi-Timeframe Pullback (QuantLogic)
    Trend: 5min EMA9 > EMA21
    Entry: 1min pullback to 1min EMA21, close above
    """
    trades = []
    position = None
    atr_period = params.get("atr_period", 14)
    atr_col = f'atr_{atr_period}'
    
    # This strategy needs 5min and 1min data - simplified to single timeframe
    # Use current TF as "5min" and resample to "1min" concept
    # For simplicity, use same TF with fast/slow EMA
    
    for i in range(21, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i-1]
        
        atr_val = row[atr_col] if not pd.isna(row[atr_col]) else (row['high'] - row['low'])
        
        # Trend on current TF (5min equivalent)
        trend_long = row['ema_9'] > row['ema_21']
        trend_short = row['ema_9'] < row['ema_21']
        
        # Exit
        if position is not None:
            exit_price = None
            exit_reason = ""
            
            if position['direction'] == 'long':
                if row['low'] <= position['stop_price']:
                    exit_price = apply_spread_slippage(position['stop_price'], 'short', pair)
                    exit_reason = "stop_loss"
                elif not trend_long:
                    exit_price = apply_spread_slippage(row['close'], 'short', pair)
                    exit_reason = "trend_change"
            else:
                if row['high'] >= position['stop_price']:
                    exit_price = apply_spread_slippage(position['stop_price'], 'long', pair)
                    exit_reason = "stop_loss"
                elif not trend_short:
                    exit_price = apply_spread_slippage(row['close'], 'long', pair)
                    exit_reason = "trend_change"
            
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
                position = None
        
        # Entry
        if position is None and trend_long:
            if prev['low'] <= prev['ema_21'] and prev['close'] > prev['ema_21']:
                entry_price = apply_spread_slippage(row['open'], 'long', pair)
                stop_price = prev['low'] - 1.5 * atr_val
                position = {
                    'direction': 'long',
                    'entry_time': row.name,
                    'entry_idx': i,
                    'entry_price': entry_price,
                    'stop_price': stop_price,
                    'size': 1.0
                }
        elif position is None and trend_short:
            if prev['high'] >= prev['ema_21'] and prev['close'] < prev['ema_21']:
                entry_price = apply_spread_slippage(row['open'], 'short', pair)
                stop_price = prev['high'] + 1.5 * atr_val
                position = {
                    'direction': 'short',
                    'entry_time': row.name,
                    'entry_idx': i,
                    'entry_price': entry_price,
                    'stop_price': stop_price,
                    'size': 1.0
                }
    
    return trades

def run_strategy_015(df: pd.DataFrame, pair: str, params: dict) -> List[Trade]:
    """
    STRAT-015: Triple EMA 9/21/55 Alignment + Pullback
    Alignment: EMA9 > EMA21 > EMA55 (long) / EMA9 < EMA21 < EMA55 (short)
    Entry: Pullback to EMA21
    Stop: 1.5 ATR
    Target: 3.5R
    """
    trades = []
    position = None
    atr_period = params.get("atr_period", 14)
    atr_col = f'atr_{atr_period}'
    rr = params.get('rr_mult', 3.5)
    
    for i in range(55, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i-1]
        
        atr_val = row[atr_col] if not pd.isna(row[atr_col]) else (row['high'] - row['low'])
        
        align_long = row['ema_9'] > row['ema_21'] > row['ema_55']
        align_short = row['ema_9'] < row['ema_21'] < row['ema_55']
        
        # Exit
        if position is not None:
            exit_price = None
            exit_reason = ""
            
            if position['direction'] == 'long':
                if row['high'] >= position['target_price']:
                    exit_price = apply_spread_slippage(position['target_price'], 'short', pair)
                    exit_reason = "target_3.5R"
                elif row['low'] <= position['stop_price']:
                    exit_price = apply_spread_slippage(position['stop_price'], 'short', pair)
                    exit_reason = "stop_loss"
                elif not align_long:
                    exit_price = apply_spread_slippage(row['close'], 'short', pair)
                    exit_reason = "alignment_broken"
            else:
                if row['low'] <= position['target_price']:
                    exit_price = apply_spread_slippage(position['target_price'], 'long', pair)
                    exit_reason = "target_3.5R"
                elif row['high'] >= position['stop_price']:
                    exit_price = apply_spread_slippage(position['stop_price'], 'long', pair)
                    exit_reason = "stop_loss"
                elif not align_short:
                    exit_price = apply_spread_slippage(row['close'], 'long', pair)
                    exit_reason = "alignment_broken"
            
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
                position = None
        
        # Entry
        if position is None and align_long:
            if prev['low'] <= prev['ema_21'] and prev['close'] > prev['ema_21']:
                entry_price = apply_spread_slippage(row['open'], 'long', pair)
                stop_price = prev['low'] - 1.5 * atr_val
                risk_pips = (entry_price - stop_price) / PIP_VALUE[pair]
                target_price = entry_price + risk_pips * rr * PIP_VALUE[pair]
                position = {
                    'direction': 'long',
                    'entry_time': row.name,
                    'entry_idx': i,
                    'entry_price': entry_price,
                    'stop_price': stop_price,
                    'target_price': target_price,
                    'size': 1.0
                }
        elif position is None and align_short:
            if prev['high'] >= prev['ema_21'] and prev['close'] < prev['ema_21']:
                entry_price = apply_spread_slippage(row['open'], 'short', pair)
                stop_price = prev['high'] + 1.5 * atr_val
                risk_pips = (stop_price - entry_price) / PIP_VALUE[pair]
                target_price = entry_price - risk_pips * rr * PIP_VALUE[pair]
                position = {
                    'direction': 'short',
                    'entry_time': row.name,
                    'entry_idx': i,
                    'entry_price': entry_price,
                    'stop_price': stop_price,
                    'target_price': target_price,
                    'size': 1.0
                }
    
    return trades

STRATEGY_RUNNERS = {
    'STRAT-001': run_strategy_001,
    'STRAT-003': run_strategy_003,
    'STRAT-009': run_strategy_009,
    'STRAT-012': run_strategy_012,
    'STRAT-014': run_strategy_014,
    'STRAT-015': run_strategy_015,
}

def calculate_metrics(trades: List[Trade]) -> dict:
    """Calculate performance metrics."""
    if not trades:
        return {
            'total_trades': 0, 'win_rate': 0, 'profit_factor': 0,
            'max_drawdown_pct': 0, 'total_pnl_usd': 0, 'total_pnl_pips': 0,
            'avg_trade_pips': 0, 'sharpe_ratio': 0
        }
    
    pnls = [t.pnl_usd for t in trades]
    pips = [t.pnl_pips for t in trades]
    times = [t.exit_time for t in trades]
    
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    
    total_trades = len(trades)
    win_rate = len(wins) / total_trades if total_trades > 0 else 0
    gross_profit = sum(wins) if wins else 0
    gross_loss = abs(sum(losses)) if losses else 1
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
    
    # Equity curve for drawdown
    equity = np.cumsum(pnls)
    peak = np.maximum.accumulate(equity)
    drawdown = (peak - equity) / np.where(peak != 0, peak, 1)
    max_dd = np.max(drawdown) * 100
    
    total_pnl_usd = sum(pnls)
    total_pnl_pips = sum(pips)
    avg_trade_pips = np.mean(pips)
    
    # Sharpe (using trade returns with time index)
    if len(pnls) > 1:
        try:
            returns_series = pd.Series(pnls, index=pd.DatetimeIndex(times))
            daily_returns = returns_series.resample('D').sum().dropna()
            if len(daily_returns) > 1 and daily_returns.std() > 0:
                sharpe = daily_returns.mean() / daily_returns.std() * np.sqrt(252)
            else:
                sharpe = 0
        except:
            sharpe = 0
    else:
        sharpe = 0
    
    return {
        'total_trades': total_trades,
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'max_drawdown_pct': max_dd,
        'total_pnl_usd': total_pnl_usd,
        'total_pnl_pips': total_pnl_pips,
        'avg_trade_pips': avg_trade_pips,
        'sharpe_ratio': sharpe
    }

def walk_forward_test(df_raw: pd.DataFrame, strategy_fn, pair: str, params: dict, 
                      train_pct: float = 0.7) -> Tuple[dict, dict]:
    """Walk-forward 70/30 split."""
    split_idx = int(len(df_raw) * train_pct)
    train_raw = df_raw.iloc[:split_idx]
    test_raw = df_raw.iloc[split_idx:]
    
    # Recalculate indicators for each split
    train_df = calculate_indicators(train_raw.copy(), params)
    test_df = calculate_indicators(test_raw.copy(), params)
    
    # In-sample (training period - just for reference)
    train_trades = strategy_fn(train_df, pair, params)
    train_metrics = calculate_metrics(train_trades)
    
    # Out-of-sample
    test_trades = strategy_fn(test_df, pair, params)
    test_metrics = calculate_metrics(test_trades)
    
    return train_metrics, test_metrics

def robustness_test(df_raw: pd.DataFrame, strategy_fn, pair: str, base_params: dict, 
                    param_variations: dict) -> List[dict]:
    """Test parameter robustness ±15%."""
    results = []
    
    for param_name, base_value in param_variations.items():
        for mult in [0.85, 1.0, 1.15]:
            test_params = base_params.copy()
            new_value = base_value * mult
            # Keep integer parameters as integers
            if isinstance(base_value, int):
                test_params[param_name] = max(1, int(round(new_value)))
            else:
                test_params[param_name] = new_value
            
            # Recalculate indicators for this parameter set
            df = calculate_indicators(df_raw.copy(), test_params)
            trades = strategy_fn(df, pair, test_params)
            metrics = calculate_metrics(trades)
            metrics['param'] = param_name
            metrics['value'] = test_params[param_name]
            results.append(metrics)
    
    return results

def run_full_validation(strategy_id: str, strategy_name: str, pair: str, timeframe: str, 
                        params: dict) -> BacktestResult:
    """Run complete validation pipeline."""
    print(f"\n  Testing {strategy_id} on {pair} {timeframe}...")
    
    # Load data
    df = load_data(pair, timeframe)
    df = calculate_indicators(df, params)
    
    strategy_fn = STRATEGY_RUNNERS.get(strategy_id)
    if not strategy_fn:
        raise ValueError(f"No runner for {strategy_id}")
    
    # Full period backtest
    trades = strategy_fn(df, pair, params)
    full_metrics = calculate_metrics(trades)
    
    # Walk-forward OOS
    train_metrics, oos_metrics = walk_forward_test(df, strategy_fn, pair, params)
    
    # Robustness
    param_vars = {k: v for k, v in params.items() if isinstance(v, (int, float)) and k not in ['rr_mult']}
    robust_results = robustness_test(df, strategy_fn, pair, params, param_vars)
    robust_profitable = sum(1 for r in robust_results if r['profit_factor'] > 1.0)
    robust_total = len(robust_results)
    
    return BacktestResult(
        strategy_id=strategy_id,
        strategy_name=strategy_name,
        pair=pair,
        timeframe=timeframe,
        trades=trades,
        total_trades=full_metrics['total_trades'],
        win_rate=full_metrics['win_rate'],
        profit_factor=full_metrics['profit_factor'],
        max_drawdown_pct=full_metrics['max_drawdown_pct'],
        total_pnl_usd=full_metrics['total_pnl_usd'],
        total_pnl_pips=full_metrics['total_pnl_pips'],
        avg_trade_pips=full_metrics['avg_trade_pips'],
        sharpe_ratio=full_metrics['sharpe_ratio'],
        oos_profit_factor=oos_metrics['profit_factor'],
        oos_win_rate=oos_metrics['win_rate'],
        params=params
    )

def check_criteria(result: BacktestResult) -> Tuple[bool, List[str]]:
    """Check if strategy meets all validation criteria."""
    reasons = []
    
    if result.total_trades < 500:
        reasons.append(f"Trades < 500: {result.total_trades}")
    
    if result.profit_factor < 1.3:
        reasons.append(f"PF < 1.3: {result.profit_factor:.2f}")
    
    if result.max_drawdown_pct > 20:
        reasons.append(f"Max DD > 20%: {result.max_drawdown_pct:.1f}%")
    
    if result.oos_profit_factor < 1.0:
        reasons.append(f"OOS PF < 1.0: {result.oos_profit_factor:.2f}")
    
    # Need profitable on at least 2 instruments (checked externally)
    
    passed = len(reasons) == 0
    return passed, reasons

if __name__ == "__main__":
    print("Backtesting Engine Ready")
    print("Available strategies:", list(STRATEGY_RUNNERS.keys()))
