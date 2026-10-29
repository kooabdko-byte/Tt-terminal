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
                "reply_markup": {
                    "inline_keyboard": [[
                        {
                            "text": "🔄 Check Live Scores",
                            "callback_data": "check_scores"
                        }
                    ]]
                }
            },
            timeout=15
        )

        result = response.json()

        if not result.get("ok"):
            logger.error("Telegram API error: %s", result)
            return False

        logger.info("Telegram message sent")
        return True

    except Exception:
        logger.exception("Telegram sending failed")
        return False


def get_live_matches():
    response = requests.get(LIVE_URL, timeout=20)
    response.raise_for_status()
    data = response.json()
    return data.get("events") or []


async def scan_matches():
    while True:
        try:
            matches = await asyncio.to_thread(get_live_matches)

            logger.info("Live matches found: %s", len(matches))

            for match in matches:
                match_id = match.get("idEvent")

                if not match_id:
                    continue

                home = match.get("strHomeTeam") or "Home"
                away = match.get("strAwayTeam") or "Away"
                league = match.get("strLeague") or "Unknown league"

                home_score = match.get("intHomeScore")
                away_score = match.get("intAwayScore")

                score = f"{home_score}:{away_score}"
                minute = match.get("strProgress") or "Unknown"

                state = f"{score}|{minute}"

                # Avoid repeated messages for unchanged match states.
                unique_key = f"{match_id}|{state}"

                if unique_key in seen_matches:
                    continue

                message = (
                    "🔥 BBK TERMINAL — LIVE MATCH\n\n"
                    f"🏆 League: {league}\n"
                    f"⚽ {home} — {away}\n"
                    f"📊 Score: {score}\n"
                    f"⏱ Time: {minute}\n\n"
                    "ℹ️ Live-score update.\n"
                    "This is not a verified goal prediction."
                )

                sent = await asyncio.to_thread(telegram_send, message)

                if sent:
                    seen_matches.add(unique_key)

                await asyncio.sleep(1)

        except Exception:
            logger.exception("Live scan failed")

        # Check again every 60 seconds.
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
        "✅ BBK TERMINAL\n\nTelegram connection test successful!"
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
