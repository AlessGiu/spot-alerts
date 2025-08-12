import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    discord_webhook_url: str
    default_exchange: str = "BINANCE"
    default_symbol: str = "BTC/USDT"
    default_timeframe: str = "12h"
    volume_lookback: int = 20
    volume_multiplier: float = 1.2


def load_settings() -> Settings:
    return Settings(
        discord_webhook_url=os.getenv("DISCORD_WEBHOOK_URL", ""),
        default_exchange=os.getenv("DEFAULT_EXCHANGE", "BINANCE"),
        default_symbol=os.getenv("DEFAULT_SYMBOL", "BTC/USDT"),
        default_timeframe=os.getenv("DEFAULT_TIMEFRAME", "12h"),
        volume_lookback=int(os.getenv("VOLUME_LOOKBACK", "20")),
        volume_multiplier=float(os.getenv("VOLUME_MULTIPLIER", "1.2")),
    )