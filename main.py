
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

API_URL = "https://sportscore.com/api/widget/matches/"
seen_states = {}


def send_telegram(message):
    if not BOT_TOKEN or not CHAT_ID:
        logger.error("Missing Telegram token or chat ID")
        return False

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": message},
            timeout=15,
        )
        result = response.json()

        if not response.ok or not result.get("ok"):
            logger.error(
                "Telegram HTTP %s: %s",
                response.status_code,
                result.get("description", result),
            )
            return False

        return True

    except Exception:
        logger.exception("Telegram send failed")
        return False


def get_matches():
    response = requests.get(
        API_URL,
        params={"sport": "football", "limit": 50},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()

    if not isinstance(data.get("matches"), list):
        raise ValueError("Unexpected API response format")

    return data["matches"]


@app.get("/")
def home():
    return {"status": "Running", "service": "BBK Terminal"}


@app.get("/api/test-telegram")
async def test_telegram():
    sent = await asyncio.to_thread(
        send_telegram,
        "BBK Terminal: Telegram connection test."
    )
    return {"telegram_sent": sent}


@app.get("/api/live-scores")
async def live_scores():
    try:
        matches = await asyncio.to_thread(get_matches)
        return {"status": "success", "count": len(matches),
                "matches": matches}
    except Exception:
        logger.exception("Live-score API failed")
        return {"status": "error", "message": "Check Render logs"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="BBK Terminal", lifespan=lifespan)

