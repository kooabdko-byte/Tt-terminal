import os
import asyncio
import logging
import requests

from contextlib import asynccontextmanager
from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BBK")

BOT_TOKEN = os.getenv("8832788331:AAHQtEkgJLR7mIjHPfdYeg19r0M_rssYLmc", "").strip()
CHAT_ID = os.getenv("1296460762", "").strip()

LIVE_URL = "https://www.thesportsdb.com/api/v1/json/3/livescore.php?l=4328"

seen_matches = set()


def telegram_send(text):
    if not BOT_TOKEN or not CHAT_ID:
        logger.error("Telegram token or chat ID is missing")
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    try:
        response = requests.post(
            url,
            json={
                "chat_id": CHAT_ID,
                "text": text,
                "parse_mode": "Markdown",
                "reply_markup": {
                    "inline_keyboard": [[
                        {
                            "text": "Открыть терминал",
                            "callback_data": "open_terminal"
                        }
                    ]]
                }
            },
            timeout=15
        )

        result = response.json()
        logger.info(f"Telegram Raw Response: {result}")

        if not result.get("ok"):
            logger.error(f"Telegram API error description: {result.get('description')}")
            return False

        logger.info("Telegram message sent successfully")
        return True

    except Exception as e:
        logger.exception(f"Telegram sending failed with exception: {e}")
        return False


def get_live_matches():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(LIVE_URL, headers=headers, timeout=20)
    response.raise_for_status()
    data = response.json()
    return data.get("events") or []


async def scan_matches():
    while True:
        try:
            matches = await asyncio.to_thread(get_live_matches)

            for match in matches:
                match_id = match.get("idEvent")

                if not match_id:
                    continue

                home = match.get("strHomeTeam") or "Home"
                away = match.get("strAwayTeam") or "Away"
                league = match.get("strLeague") or "Unknown league"

                home_score = match.get("intHomeScore") or "0"
                away_score = match.get("intAwayScore") or "0"

                score = f"{home_score}:{away_score}"
                minute = match.get("strProgress") or "0"

                state = f"{score}|{minute}"
                unique_key = f"{match_id}|{state}"

                if unique_key in seen_matches:
                    continue

                message = (
                    f"🔥 *ВАЖНЫЙ СИГНАЛ — BBK Terminal*\n\n"
                    f"⚽ {home} — {away} ({league})\n"
                    f"⏱ {minute}' · счёт {score}\n"
                    f"🔥 Давит: {home}\n"
                    f"🔥 давление нарастает\n\n"
                    f"📌 Момент: возможный гол во 2-м тайме\n"
                    f"💡 Вариант входа: ТБ 0.5"
                )

                sent = await asyncio.to_thread(telegram_send, message)

                if sent:
                    seen_matches.add(unique_key)

                await asyncio.sleep(1)

        except Exception:
            logger.exception("Live scan failed")

        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(scan_matches())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="BBK Terminal", lifespan=lifespan)


@app.get("/")
def home():
    return {
        "status": "Running",
        "service": "BBK Terminal"
    }


@app.get("/api/test-telegram")
async def test_telegram():
    success = await asyncio.to_thread(
        telegram_send,
        "✅ *BBK TERMINAL*\n\nTelegram connection test successful!"
    )

    return {
        "status": "success" if success else "error",
        "telegram_sent": success
    }


@app.get("/api/live-scores")
async def live_scores():
    try:
        matches = await asyncio.to_thread(get_live_matches)

        return {
            "status": "success",
            "count": len(matches),
            "matches": matches
        }

    except Exception:
        logger.exception("Could not retrieve live scores")
        return {
            "status": "error",
            "message": "Live scores are temporarily unavailable"
        }


@app.get("/api/run-live-scan")
async def run_live_scan():
    try:
        matches = await asyncio.to_thread(get_live_matches)
        return {
            "status": "success",
            "message": "Live scan completed",
            "matches_found": len(matches)
        }

    except Exception:
        logger.exception("Manual live scan failed")
        return {
            "status": "error",
            "message": "Live scan failed. Check Render logs."
        }
