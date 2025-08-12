from __future__ import annotations

from typing import Optional
import requests


def send_discord_message(
    webhook_url: str,
    title: str,
    description: str,
    color: int = 0x2ecc71,
    chart_url: Optional[str] = None,
) -> None:
    if not webhook_url:
        return
    embed = {
        "title": title,
        "description": description,
        "color": color,
    }
    if chart_url:
        embed["url"] = chart_url
    payload = {"embeds": [embed]}
    headers = {"Content-Type": "application/json"}
    try:
        requests.post(webhook_url, json=payload, headers=headers, timeout=10)
    except Exception:
        # Avoid crashing the bot on webhook issues
        pass