from typing import Dict, Any, List
import time

import ccxt
import pandas as pd
from tradingview_ta import TA_Handler, Interval


TRADINGVIEW_INTERVAL_MAP = {
    "12h": Interval.INTERVAL_12_HOURS,
    "1d": Interval.INTERVAL_1_DAY,
    "1D": Interval.INTERVAL_1_DAY,
    "1w": Interval.INTERVAL_1_WEEK,
    "1W": Interval.INTERVAL_1_WEEK,
    "1h": Interval.INTERVAL_1_HOUR,
    "4h": Interval.INTERVAL_4_HOURS,
}


def get_tradingview_analysis(symbol: str, exchange: str, interval: str) -> Dict[str, Any]:
    try:
        handler = TA_Handler(
            symbol=symbol.replace("/", ""),
            screener="crypto",
            exchange=exchange,
            interval=TRADINGVIEW_INTERVAL_MAP.get(interval, interval),
        )
        analysis = handler.get_analysis()
        return {
            "rsi": analysis.indicators.get("RSI"),
            "volume": analysis.indicators.get("Volume"),
            "summary": analysis.summary,
            "indicators": analysis.indicators,
        }
    except Exception:
        return {"rsi": None, "volume": None, "summary": {}, "indicators": {}}


def get_ccxt_ohlcv(symbol: str, exchange: str, timeframe: str, limit: int = 200) -> pd.DataFrame:
    ex = getattr(ccxt, exchange.lower())()
    # Retry on rate limits
    retries = 3
    delay = 1.0
    last_err: Exception | None = None
    for _ in range(retries):
        try:
            ohlcv: List[List[float]] = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
            return df
        except Exception as err:  # noqa: BLE001
            last_err = err
            time.sleep(delay)
            delay *= 2
    if last_err:
        raise last_err
    raise RuntimeError("Unknown error fetching OHLCV")