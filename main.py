from fastapi import FastAPI, BackgroundTasks
import requests
import asyncio

app = FastAPI(title="BBK Terminal")

TELEGRAM_BOT_TOKEN = "8832788331:AAHQtEkgJLR7mIjHPfdYeg19r0M_rssYLmc"
CHAT_ID = "1296460762"

def send_telegram_alert(match_name: str, signal: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    message = f"⚽ *BBK Signal*\n\nMatch: {match_name}\nSignal: {signal}"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error: {e}")

@app.get("/")
def home():
    return {"status": "Running"}

async def monitor_live_matches():
    live_matches = [
        {"home": "Real Madrid", "away": "Barcelona", "minute": "75'", "signal": "ТБ 1.5"},
        {"home": "Arsenal", "away": "Chelsea", "minute": "82'", "signal": "Next Goal: Home"}
    ]
    
    for match in live_matches:
        match_name = f"{match['home']} vs {match['away']} ({match['minute']})"
        send_telegram_alert(match_name, match['signal'])
        await asyncio.sleep(2)

@app.get("/api/run-live-scan")
async def run_live_scan(background_tasks: BackgroundTasks):
    background_tasks.add_task(monitor_live_matches)
    return {"status": "Started"}

