from __future__ import annotations

import argparse
from typing import List

from bot.config import load_settings
from bot.data_providers import get_tradingview_analysis, get_ccxt_ohlcv
from bot.strategy import generate_signal
from bot.discord_notifier import send_discord_message


def parse_args() -> argparse.Namespace:
    settings = load_settings()
    parser = argparse.ArgumentParser(description="RSI Reversal Bot (Discord Alerts)")
    parser.add_argument("--exchange", type=str, default=settings.default_exchange)
    parser.add_argument("--symbol", type=str, default=settings.default_symbol)
    parser.add_argument("--symbols", type=str, default=None, help="Comma-separated list overrides --symbol")
    parser.add_argument("--timeframe", type=str, default=settings.default_timeframe)
    parser.add_argument("--volume-lookback", type=int, default=settings.volume_lookback)
    parser.add_argument("--volume-multiplier", type=float, default=settings.volume_multiplier)
    return parser.parse_args()


def format_discord_message(pair: str, timeframe: str, signal, weekly_rec: str) -> str:
    lines: List[str] = []
    if signal.action == "BUY":
        lines.append(f"RSI Signal - {pair} ({timeframe})")
        lines.append(f"\n")
        lines.append(f"📈 Entrée : {signal.entry_price:.2f}")
        if signal.stop_loss:
            lines.append(f"⛔ Stop : {signal.stop_loss:.2f}")
        if signal.tp1:
            lines.append(f"🎯 TP1 : {signal.tp1:.2f}")
        if signal.tp2:
            lines.append(f" | TP2 : {signal.tp2:.2f}")
        if signal.extras:
            pattern = signal.extras.get("pattern")
            vol = signal.extras.get("volume")
            avg = signal.extras.get("volume_avg")
            lines.append(f"\n✅ Confirmation : {pattern.replace('_', ' ').title()} + Volume ↑ ({vol:.0f} vs avg {avg:.0f})")
        lines.append(f"⏳ Tendance Weekly {weekly_rec.lower().replace('_', ' ')}")
    elif signal.action == "SELL":
        lines.append(f"RSI Exit - {pair} ({timeframe})")
        lines.append(f"\n")
        lines.append(f"💸 Sortie : RSI ≥ 70 @ {signal.entry_price:.2f}")
        lines.append(f"⏳ Tendance Weekly {weekly_rec.lower().replace('_', ' ')}")
    else:
        lines.append(f"No signal - {pair} ({timeframe}) : {signal.reason}")
    return "\n".join(lines)


def run_once(exchange: str, pair: str, timeframe: str, vol_lookback: int, vol_mult: float, webhook_url: str) -> None:
    # TA for primary timeframe
    tv = get_tradingview_analysis(symbol=pair, exchange=exchange, interval=timeframe)
    rsi_value = tv.get("rsi")

    # TA for weekly trend
    tv_weekly = get_tradingview_analysis(symbol=pair, exchange=exchange, interval="1W")
    weekly_rec = tv_weekly.get("summary", {}).get("RECOMMENDATION", "NEUTRAL")

    # OHLCV for candle/pattern detection and volume
    df = get_ccxt_ohlcv(symbol=pair, exchange=exchange, timeframe=timeframe, limit=200)

    signal = generate_signal(
        ohlcv=df,
        rsi_value=rsi_value,
        weekly_recommendation=weekly_rec,
        volume_lookback=vol_lookback,
        volume_multiplier=vol_mult,
    )

    title = f"{signal.action} - {pair} ({timeframe})" if signal.action != "NONE" else f"Info - {pair} ({timeframe})"
    description = format_discord_message(pair, timeframe, signal, weekly_rec)

    send_discord_message(
        webhook_url=webhook_url,
        title=title,
        description=description,
        color=0x2ecc71 if signal.action == "BUY" else (0xe74c3c if signal.action == "SELL" else 0x95a5a6),
        chart_url=None,
    )


if __name__ == "__main__":
    args = parse_args()
    settings = load_settings()

    pairs = [p.strip() for p in (args.symbols.split(",") if args.symbols else [args.symbol]) if p.strip()]
    for pair in pairs:
        run_once(
            exchange=args.exchange,
            pair=pair,
            timeframe=args.timeframe,
            vol_lookback=args.volume_lookback,
            vol_mult=args.volume_multiplier,
            webhook_url=settings.discord_webhook_url,
        )