from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any

import pandas as pd

from .indicators import (
    detect_reversal_pattern,
    volume_spike,
    find_recent_swing_low,
    find_recent_swing_high,
)


@dataclass
class Signal:
    action: str  # BUY or SELL or NONE
    reason: str
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    tp1: Optional[float] = None
    tp2: Optional[float] = None
    extras: Optional[Dict[str, Any]] = None


def generate_signal(
    ohlcv: pd.DataFrame,
    rsi_value: Optional[float],
    weekly_recommendation: str,
    volume_lookback: int = 20,
    volume_multiplier: float = 1.2,
) -> Signal:
    if ohlcv.empty:
        return Signal(action="NONE", reason="No data")

    last_close = float(ohlcv["close"].iloc[-1])

    # Exit condition first
    if rsi_value is not None and rsi_value >= 70:
        return Signal(action="SELL", reason="RSI ≥ 70", entry_price=last_close)

    # Entry conditions
    if rsi_value is None or rsi_value > 30:
        return Signal(action="NONE", reason="RSI not ≤ 30")

    pattern = detect_reversal_pattern(ohlcv)
    if pattern is None:
        return Signal(action="NONE", reason="No reversal pattern")

    trend_ok = weekly_recommendation not in {"SELL", "STRONG_SELL"}
    if not trend_ok:
        return Signal(action="NONE", reason="Weekly trend bearish")

    vol_ok, vol, vol_avg = volume_spike(ohlcv, lookback=volume_lookback, multiplier=volume_multiplier)
    if not vol_ok:
        return Signal(action="NONE", reason="No volume spike")

    sl = find_recent_swing_low(ohlcv, window=10)
    if sl is None:
        return Signal(action="NONE", reason="No swing low")

    tp1 = last_close * 1.05
    tp2 = last_close * 1.10

    # Optionally use resistance as TP if available
    swing_high = find_recent_swing_high(ohlcv, window=10)
    if swing_high and swing_high > last_close:
        tp1 = min(tp1, swing_high)

    return Signal(
        action="BUY",
        reason=f"RSI ≤ 30, {pattern.replace('_', ' ')}, weekly trend ok, volume spike",
        entry_price=last_close,
        stop_loss=sl,
        tp1=tp1,
        tp2=tp2,
        extras={"volume": vol, "volume_avg": vol_avg, "pattern": pattern},
    )