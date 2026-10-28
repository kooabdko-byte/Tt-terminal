
from fastapi import FastAPI, BackgroundTasks
import requests
import asyncio

app = FastAPI()

TELEGRAM_BOT_TOKEN = "8832788331:AAHQtEkgJLR7mIjHPfdYeg19r0M_rssYLmc"
CHAT_ID = "1296460762"

def send_telegram_alert(match_name: str, score: str, minute: str, signal: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    message = (
        f"⚽ *BBK Live Signal*\n\n"
        f"🏆 Match: {match_name}\n"
        f"⏱ Time: {minute}'\n"
        f"📊 Score: {score}\n"
        f"💡 Signal: {signal}"
    )
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        print("Telegram Response:", response.text)
    except Exception as e:
        print("Error:", e)

@app.get("/")
def home():
    return {"status": "Running"}

async def fetch_and_scan_live_matches():
    sample_live = [
        {"home": "Live Match 1", "away": "Live Match 2", "score": "0 - 0", "minute": "72", "signal": "ТБ 0.5"}
    ]
    
    for match in sample_live:
        send_telegram_alert(match["home"] + " vs " + match["away"], match["score"], match["minute"], match["signal"])
        await asyncio.sleep(2)

@app.get("/api/run-live-scan")
async def run_live_scan(background_tasks: BackgroundTasks):
    background_tasks.add_task(fetch_and_scan_live_matches)
    return {"status": "Started"}

