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

RAPIDAPI_KEY = "sportapi7.p.rapidapi.com"
RAPIDAPI_HOST = "api-football-v1.p.rapidapi.com"

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
                            "url": "https://LINKI_WEB_APP_KEE.onrender.com"
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

def get_match_statistics(match_id, home_name, away_name):
    url = f"https://{RAPIDAPI_HOST}/v3/fixtures/statistics"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }
    
    try:
        response = requests.get(url, headers=headers, params={"fixture": match_id}, timeout=10)
        if response.status_code != 200:
            return home_name

        data = response.json().get("response", [])
        if len(data) < 2:
            return home_name

        home_shots = 0
        away_shots = 0

        for team_stat in data:
            team_name = team_stat.get("team", {}).get("name")
            statistics = team_stat.get("statistics", [])
            
            shots = 0
            for stat in statistics:
                if stat.get("type") in ["Total Shots", "Shots on Goal"]:
                    val = stat.get("value")
                    if val is not None:
                        shots += int(val)
            
            if team_name == home_name:
                home_shots = shots
            else:
                away_shots = shots

        if away_shots > home_shots:
            return away_name
        return home_name

    except Exception:
        return home_name

def get_live_matches_from_rapidapi():
    url = f"https://{RAPIDAPI_HOST}/v3/fixtures"
    querystring = {"live": "all"}
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }

    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=15)
        if response.status_code != 200:
            return []

        data = response.json().get("response", [])
        matches = []

        for item in data:
            fixture = item.get("fixture", {})
            teams = item.get("teams", {})
            goals = item.get("goals", {})
            league_info = item.get("league", {})

            match_id = fixture.get("id")
            home = teams.get("home", {}).get("name", "Home")
            away = teams.get("away", {}).get("name", "Away")
            league = league_info.get("name", "League")
            
            home_goals = goals.get("home", 0) if goals.get("home") is not None else 0
            away_goals = goals.get("away", 0) if goals.get("away") is not None else 0
            score = f"{home_goals}:{away_goals}"
            
            elapsed = fixture.get("status", {}).get("elapsed", 0)
            minute = f"{elapsed}'" if elapsed else "Live"

            pressure_team = get_match_statistics(match_id, home, away)

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
    except Exception as e:
        logger.warning(f"API Fetch failed: {e}")
        return []

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
    success = telegram_send("Test Home", "Test Away", "Test League", "45'", "0:0", "Test Team")
    if success:
        return {"status": "success", "message": "Ergaan Telegram irratti milkaa'inaan ergameera!"}
    else:
        return {"status": "error", "message": "Ergaa erguu irratti rakkoon jira, Bot Token ykn Chat ID kee ilaali."}
