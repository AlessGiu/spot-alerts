from __future__ import annotations

from typing import Literal, Optional, Tuple
import pandas as pd


def compute_rsi(series_close: pd.Series, length: int = 14) -> pd.Series:
    delta = series_close.diff()
    gain = (delta.where(delta > 0, 0.0)).rolling(window=length).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=length).mean()
    rs = gain / loss.replace(0, 1e-9)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def is_bullish_engulfing(df: pd.DataFrame) -> bool:
    if len(df) < 2:
        return False
    prev = df.iloc[-2]
    curr = df.iloc[-1]
    prev_bear = prev["close"] < prev["open"]
    curr_bull = curr["close"] > curr["open"]
    if not (prev_bear and curr_bull):
        return False
    prev_body = abs(prev["close"] - prev["open"])
    curr_body = abs(curr["close"] - curr["open"])
    engulf = curr["open"] <= prev["close"] and curr["close"] >= prev["open"]
    return curr_body > prev_body and engulf


def is_hammer(df: pd.DataFrame) -> bool:
    if len(df) < 1:
        return False
    c = df.iloc[-1]
    body = abs(c["close"] - c["open"])
    upper = c["high"] - max(c["open"], c["close"])
    lower = min(c["open"], c["close"]) - c["low"]
    if body == 0:
        return False
    # Lower shadow at least 2x body, small upper shadow
    return lower >= 2 * body and upper <= 0.5 * body


def detect_reversal_pattern(df: pd.DataFrame) -> Optional[Literal["bullish_engulfing", "hammer"]]:
    if is_bullish_engulfing(df):
        return "bullish_engulfing"
    if is_hammer(df):
        return "hammer"
    return None


def volume_spike(df: pd.DataFrame, lookback: int = 20, multiplier: float = 1.2) -> Tuple[bool, float, float]:
    if len(df) < lookback + 1:
        return False, float("nan"), float("nan")
    vol = df["volume"].iloc[-1]
    avg = df["volume"].iloc[-(lookback + 1):-1].mean()
    return vol >= avg * multiplier, vol, avg


def find_recent_swing_low(df: pd.DataFrame, window: int = 10) -> Optional[float]:
    if len(df) < window + 2:
        return None
    lows = df["low"].iloc[-(window + 2):-1]
    return float(lows.min())


def find_recent_swing_high(df: pd.DataFrame, window: int = 10) -> Optional[float]:
    if len(df) < window + 2:
        return None
    highs = df["high"].iloc[-(window + 2):-1]
    return float(highs.max())