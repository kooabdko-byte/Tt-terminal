import os
import asyncio
import logging
import requests

from contextlib import asynccontextmanager
from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BBK")

BOT_TOKEN = "8832788331:AAHQtEkgJLR7mIjHPfdYeg19r0M_rssYLmc"
CHAT_ID = "1296460762"

LIVE_URL = "https://www.scorebat.com/video-api/v3/feed/"

seen_matches = set()


def telegram_send(text):
    global BOT_TOKEN, CHAT_ID
    if not BOT_TOKEN or not CHAT_ID:
        logger.error("CRITICAL: Telegram token or chat ID is missing!")
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
        if not result.get("ok"):
            logger.error(f"Telegram API error description: {result.get('description')}")
            return False

        return True

    except Exception as e:
        logger.exception(f"Telegram sending failed: {e}")
        return False


def get_live_matches():
    try:
        response = requests.get(LIVE_URL, timeout=15)
        response.raise_for_status()
        data = response.json()
        response_data = data.get("response", [])
        
        matches = []
        for item in response_data:
            title = item.get("title", "")
            league = item.get("competition", "Live Match")
            match_id = item.get("match_id") or title
            
            teams = title.split(" - ")
            home = teams[0] if len(teams) > 1 else "Home"
            away = teams[1] if len(teams) > 1 else "Away"
            
            matches.append({
                "id": str(match_id),
                "home": home,
                "away": away,
                "league": league,
                "score": "Live",
                "minute": "Live"
            })
        
        if matches:
            return matches
    except Exception:
        logger.warning("ScoreBat fetch failed, using fallback data.")

    # Fallback data akka endpoint-ichi yoomiyyuu error hin kennineef
    return [{
        "id": "fallback_match_1",
        "home": "Live Match Testing",
        "away": "BBK System",
        "league": "Terminal League",
        "score": "0:0",
        "minute": "Live"
    }]


async def scan_matches():
    while True:
        try:
            matches = await asyncio.to_thread(get_live_matches)

            for match in matches:
                match_id = match.get("id")

                if not match_id:
                    continue

                home = match.get("home", "Home")
                away = match.get("away", "Away")
                league = match.get("league", "Football League")
                score = match.get("score", "Live")
                minute = match.get("minute", "Live")

                unique_key = f"{match_id}"

                if unique_key in seen_matches:
                    continue

                message = (
                    f"🔥 *ВАЖНЫЙ СИГНАЛ — BBK Terminal*\n\n"
                    f"⚽ {home} — {away} ({league})\n"
                    f"⏱ {minute} · счёт {score}\n"
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
