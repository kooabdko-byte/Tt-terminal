from fastapi import FastAPI, BackgroundTasks
import requests
import asyncio

app = FastAPI()

TELEGRAM_BOT_TOKEN = "8832788331:AAHQtEkgJLR7mIjHPfdYeg19r0M_rssYLmc"
CHAT_ID = "1296460762"

def send_telegram_alert(match_name: str, score: str, minute: str, pressure: str, action_type: str, moment: str, signal: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "Открыть терминал", "callback_data": "open_terminal"}]
        ]
    }
    
    message = (
        f"🔥 *ВАЖНЫЙ СИГНАЛ — BBK Terminal*\n\n"
        f"⚽ {match_name}\n"
        f"⏱ {minute} · счёт {score}\n"
        f"🔥 Давит: {pressure}\n"
        f"{action_type}\n\n"
        f"📌 Момент: {moment}\n"
        f"💡 Вариант входа: {signal}"
    )
    
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    }
    
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error: {e}")

@app.get("/")
def home():
    return {"status": "Running"}

async def fetch_and_scan_live_matches():
    try:
        url = "https://www.thesportsdb.com/api/v1/json/3/livescore.php?l=4328"
        response = requests.get(url)
        data = response.json()
        events = data.get("events", [])
        
        if events:
            for item in events:
                home_team = item.get("strHomeTeam", "Home")
                away_team = item.get("strAwayTeam", "Away")
                league = item.get("strLeague", "Live")
                match_name = f"{home_team} — {away_team} ({league})"
                score = f"{item.get('intHomeScore', '0')}:{item.get('intAwayScore', '0')}"
                minute = f"{item.get('strProgress', '0')}'"
                
                send_telegram_alert(
                    match_name,
                    score,
                    minute,
                    home_team,
                    "🔥 давление нарастает",
                    "возможный гол во 2-м тайме",
                    "ТБ 0.5"
                )
                await asyncio.sleep(2)
        else:
            print("No active live matches found at the moment.")
            
    except Exception as e:
        print(f"API Error: {e}")

@app.get("/api/run-live-scan")
async def run_live_scan(background_tasks: BackgroundTasks):
    background_tasks.add_task(fetch_and_scan_live_matches)
    return {"status": "Started"}
