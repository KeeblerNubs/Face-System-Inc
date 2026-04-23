from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
REQUEST_TIMEOUT = float(os.getenv("BOT_REQUEST_TIMEOUT", "30"))


async def _api_get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"{API_BASE_URL.rstrip('/')}{path}"
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "🤖 Face-System bot is online.\n\n"
        "Commands:\n"
        "/health - API health check\n"
        "/platforms - list supported social platforms\n"
        "/social <username> - search username across platforms\n"
        "/phone <number> [region] - reverse phone number lookup"
    )
    await update.message.reply_text(text)


async def health(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        data = await _api_get("/health")
        await update.message.reply_text(f"API status: {data.get('status', 'unknown')}")
    except httpx.HTTPError as exc:
        logger.exception("Health request failed")
        await update.message.reply_text(f"Health check failed: {exc}")


async def platforms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        data = await _api_get("/platforms")
    except httpx.HTTPError as exc:
        logger.exception("Platform list request failed")
        await update.message.reply_text(f"Failed to fetch platforms: {exc}")
        return

    platform_list = data.get("platforms", [])
    total = data.get("count", len(platform_list))

    preview = ", ".join(platform_list[:25])
    suffix = "..." if len(platform_list) > 25 else ""
    await update.message.reply_text(
        f"Supported platforms: {total}\n{preview}{suffix}"
    )


async def social(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /social <username>")
        return

    username = context.args[0].strip()
    try:
        data = await _api_get("/search/social", params={"username": username})
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text if exc.response is not None else str(exc)
        await update.message.reply_text(f"Social search failed: {detail}")
        return
    except httpx.HTTPError as exc:
        await update.message.reply_text(f"Social search failed: {exc}")
        return

    results = data.get("results", [])
    if not results:
        await update.message.reply_text(
            f"No profiles found for '{username}'."
        )
        return

    lines = [
        f"Profiles found for '{username}': {len(results)}",
    ]
    for item in results[:15]:
        lines.append(f"- {item['platform']}: {item['url']}")

    if len(results) > 15:
        lines.append(f"...and {len(results) - 15} more")

    await update.message.reply_text("\n".join(lines), disable_web_page_preview=True)


async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /phone <number> [region]")
        return

    number = context.args[0].strip()
    params: dict[str, Any] = {"number": number}
    if len(context.args) > 1:
        params["region"] = context.args[1].strip().upper()

    try:
        data = await _api_get("/search/phone", params=params)
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text if exc.response is not None else str(exc)
        await update.message.reply_text(f"Phone lookup failed: {detail}")
        return
    except httpx.HTTPError as exc:
        await update.message.reply_text(f"Phone lookup failed: {exc}")
        return

    formats = data.get("formats", {})
    timezones = data.get("timezones") or []
    lines = [
        f"Phone lookup for {formats.get('international') or number}:",
        f"- Valid: {data.get('valid')}",
        f"- Country: +{data.get('country_code')} ({data.get('region_code') or 'unknown'})",
        f"- Location: {data.get('location') or 'unknown'}",
        f"- Carrier: {data.get('carrier') or 'unknown'}",
        f"- Line type: {data.get('line_type')}",
        f"- Timezones: {', '.join(timezones) if timezones else 'unknown'}",
        f"- E.164: {formats.get('e164', 'n/a')}",
    ]
    await update.message.reply_text("\n".join(lines), disable_web_page_preview=True)


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not set. "
            "Set TELEGRAM_BOT_TOKEN environment variable before starting the bot."
        )

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("health", health))
    application.add_handler(CommandHandler("platforms", platforms))
    application.add_handler(CommandHandler("social", social))
    application.add_handler(CommandHandler("phone", phone))

    logger.info("Starting Telegram bot (API base URL: %s)", API_BASE_URL)
    application.run_polling()


if __name__ == "__main__":
    main()
