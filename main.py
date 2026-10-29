

from fastapi import FastAPI, BackgroundTasks
import requests
import asyncio

app = FastAPI()

TELEGRAM_BOT_TOKEN = "8832788331:AAHQtEkgJLR7mIjHPfdYeg19r0M_rssYLmc"
CHAT_ID = "1296460762"

def send_telegram_alert(score: str, minute: str, signal: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    message = (
        f"🔥 *ВАЖНЫЙ СИГНАЛ — BBK Terminal*\n\n"
        f"⏱ Time: {minute}\n"
        f"📊 счëт: {score}\n"
        f"💡 Вариант входа: {signal}"
    )
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

async def fetch_and_scan_live_matches():
    try:
        url = "https://www.thesportsdb.com/api/v1/json/3/all_leagues.php"
        response = requests.get(url)
        data = response.json()
        
        live_url = "https://www.thesportsdb.com/api/v1/json/3/livescore.php?l=4328"
        live_res = requests.get(live_url)
        live_data = live_res.json()
        events = live_data.get("events", [])
        
        if events:
            for item in events:
                score = f"{item.get('intHomeScore', '0')}:{item.get('intAwayScore', '0')}"
                minute = f"{item.get('strProgress', '0')}'"
                signal = "ТБ 0.5"
                send_telegram_alert(score, minute, signal)
                await asyncio.sleep(2)
        else:
            print("No live events found.")
            
    except Exception as e:
        print(f"API Error: {e}")

@app.get("/api/run-live-scan")
async def run_live_scan(background_tasks: BackgroundTasks):
    background_tasks.add_task(fetch_and_scan_live_matches)
    return {"status": "Started"}
