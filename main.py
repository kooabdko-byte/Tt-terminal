import os
import asyncio
import logging
import requests

from contextlib import asynccontextmanager
from fastapi import FastAPI
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BBK")

BOT_TOKEN = "8832788331:AAHQtEkgJLR7mIjHPfdYeg19r0M_rssYLmc"
CHAT_ID = "1296460762"

RAPIDAPI_KEY = "d1ad3d7f77mshf3e5ebb95be15bap11d73bjsn2443e9f131af"
RAPIDAPI_HOST = "sportapi7.p.rapidapi.com"

seen_matches = set()

def telegram_send(home, away, league, minute, score, pressure_team):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    message = (
        f"🔥 *ВАЖНЫЙ СИГНАЛ — BBK Terminal*\n\n"
        f"{home} — {away} ({league})\n"
        f"⏱ {minute} · счёт {score}\n"
        f"Давит: {pressure_team}\n"
        f"⚡ бьют чаще\n\n"
        f"Момент: возможный гол в матче\n"
        f"Вариант входа: ТБ 2.5"
    )

    try:
        response = requests.post(
            url,
            json={
                "chat_id": CHAT_ID,
                "text": message,
                "parse_mode": "Markdown",
                "reply_markup": {
                    "inline_keyboard": [[
                        {
                            "text": "Открыть терминал",
                            "url": "https://tt-terminal-20-02oc.onrender.com"
                        }
                    ]]
                }
            },
            timeout=15
        )
        return response.json().get("ok", False)
    except Exception as e:
        logger.exception(f"Telegram error: {e}")
        return False

def get_live_matches_from_rapidapi():
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }

    endpoints = [
        (f"https://{RAPIDAPI_HOST}/v1/matches/live", {}),
        (f"https://{RAPIDAPI_HOST}/v1/events/live", {}),
        (f"https://{RAPIDAPI_HOST}/v3/fixtures", {"live": "all"}),
        (f"https://{RAPIDAPI_HOST}/matches/live", {}),
        (f"https://{RAPIDAPI_HOST}/api/v1/matches/live", {})
    ]

    res_data = None
    for url, params in endpoints:
        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            logger.info(f"Testing URL: {url} -> Status: {response.status_code}")
            if response.status_code == 200:
                res_data = response.json()
                logger.info(f"Successfully fetched from {url}")
                break
        except Exception as e:
            logger.warning(f"Error calling {url}: {e}")

    if not res_data:
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        fallback_url = f"https://{RAPIDAPI_HOST}/v3/fixtures"
        try:
            response = requests.get(fallback_url, headers=headers, params={"date": today_str}, timeout=15)
            if response.status_code == 200:
                res_data = response.json()
                logger.info("Fetched fallback fixtures by date")
        except Exception as e:
            logger.warning(f"Fallback error: {e}")

    if not res_data:
        return []

    if isinstance(res_data, list):
        data = res_data
    elif isinstance(res_data, dict):
        data = res_data.get("events", res_data.get("matches", res_data.get("response", res_data.get("data", res_data.get("fixtures", [])))))
    else:
        data = []

    if not isinstance(data, list):
        data = []

    matches = []
    for item in data:
        if not isinstance(item, dict):
            continue

        home_team = item.get("homeTeam", item.get("teams", {}).get("home", {}))
        away_team = item.get("awayTeam", item.get("teams", {}).get("away", {}))
        
        home = home_team.get("name", "Home Team") if isinstance(home_team, dict) else str(home_team)
        away = away_team.get("name", "Away Team") if isinstance(away_team, dict) else str(away_team)
        
        league_info = item.get("tournament", item.get("league", item.get("competition", {})))
        league = league_info.get("name", "Live League") if isinstance(league_info, dict) else str(league_info)

        match_id = item.get("id", item.get("fixture", {}).get("id", "1"))
        
        home_score = item.get("homeScore", item.get("goals", {}).get("home", 0))
        away_score = item.get("awayScore", item.get("goals", {}).get("away", 0))
        if not isinstance(home_score, int): home_score = 0
        if not isinstance(away_score, int): away_score = 0
        score = f"{home_score}:{away_score}"

        status_info = item.get("status", {})
        elapsed = status_info.get("elapsed", status_info.get("minute", 15)) if isinstance(status_info, dict) else 15
        minute = f"{elapsed}'" if elapsed else "Live"

        pressure_team = home

        matches.append({
            "id": str(match_id),
            "home": home,
            "away": away,
            "league": league,
            "score": score,
            "minute": minute,
            "pressure_team": pressure_team
        })

    return matches

async def scan_matches():
    while True:
        try:
            matches = await asyncio.to_thread(get_live_matches_from_rapidapi)

            for match in matches:
                match_id = match.get("id")
                if not match_id or match_id in seen_matches:
                    continue

                sent = await asyncio.to_thread(
                    telegram_send,
                    match["home"], 
                    match["away"], 
                    match["league"],
                    match["minute"], 
                    match["score"], 
                    match["pressure_team"]
                )

                if sent:
                    seen_matches.add(match_id)

                await asyncio.sleep(2)
        except Exception:
            logger.exception("Scan loop error")

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

app = FastAPI(title="Terminal BBK", lifespan=lifespan)

@app.get("/")
def home():
    return {"status": "Running", "terminal": "BBK Active"}

@app.get("/api/live-matches")
def api_live_matches():
    matches = get_live_matches_from_rapidapi()
    return {"status": "success", "count": len(matches), "matches": matches}

@app.get("/api/test-telegram")
def test_telegram():
    success = telegram_send("Real Madrid", "Barcelona", "La Liga", "75'", "2:1", "Real Madrid")
    if success:
        return {"status": "success", "message": "Ergaan Telegram irratti milkaa'inaan ergameera!"}
    else:
        return {"status": "error", "message": "Ergaa erguu irratti rakkoon jira."}
