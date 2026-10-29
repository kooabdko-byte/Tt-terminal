import os
import asyncio
import logging
import requests

from fastapi import FastAPI, BackgroundTasks

app = FastAPI(title="BBK Terminal")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bbk")

# Put these values in your hosting environment variables.
TELEGRAM_BOT_TOKEN = os.getenv("8832788331:AAHQtEkgJLR7mIjHPfdYeg19r0M_rssYLmc", "")
CHAT_ID = os.getenv("1296460762", "")

LIVE_URL = (
    "https://www.thesportsdb.com/"
    "api/v1/json/3/livescore.php?s=Soccer"
)

seen_matches = {}


def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        logger.error("Telegram token or chat ID is missing.")
        return False

    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    try:
        response = requests.post(
            url,
            json={
                "chat_id": CHAT_ID,
                "text": text,
            },
            timeout=15,
        )
        response.raise_for_status()

        result = response.json()
        return result.get("ok", False)

    except requests.RequestException as exc:
        logger.error("Telegram request failed: %s", exc)
        return False


@app.get("/")
def home():
    return {
        "status": "Running",
        "service": "BBK Terminal",
    }


@app.get("/api/live-scores")
async def live_scores():
    try:
        response = await asyncio.to_thread(
            requests.get,
            LIVE_URL,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        events = data.get("events") or data.get("livescore") or []

        return {
            "status": "success",
            "count": len(events),
            "matches": events,
        }

    except (requests.RequestException, ValueError) as exc:
        logger.error("Live-score request failed: %s", exc)
        return {
            "status": "error",
            "message": "Live-score data is temporarily unavailable.",
        }


@app.get("/api/run-live-scan")
async def run_live_scan(background_tasks: BackgroundTasks):
    background_tasks.add_task(scan_matches)

    return {
        "status": "Started",
        "message": "Live-score scan started.",
    }


async def scan_matches():
    try:
        response = await asyncio.to_thread(
            requests.get,
            LIVE_URL,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        events = data.get("events") or data.get("livescore") or []

        for item in events:
            home = item.get("strHomeTeam", "Home")
            away = item.get("strAwayTeam", "Away")
            league = item.get("strLeague", "Unknown league")
            score_home = item.get("intHomeScore")
            score_away = item.get("intAwayScore")
            minute = item.get("strProgress", "Unknown")

            match_id = item.get("idEvent") or f"{home}-{away}"

            score = f"{score_home}:{score_away}"
            state = f"{score}|{minute}"

            # Send only when the score/state changes.
            if seen_matches.get(match_id) == state:
                continue

            seen_matches[match_id] = state

            message = (
                "⚽ BBK TERMINAL — LIVE SCORE\n\n"
                f"🏆 League: {league}\n"
                f"⚽ Match: {home} — {away}\n"
                f"📊 Score: {score}\n"
                f"⏱ Progress: {minute}\n\n"
                "ℹ️ Live-score information only.\n"
                "Score and match status depend on the data provider."
            )

            await asyncio.to_thread(send_telegram_message, message)
            await asyncio.sleep(1)

    except (requests.RequestException, ValueError) as exc:
        logger.error("Live scan failed: %s", exc)
