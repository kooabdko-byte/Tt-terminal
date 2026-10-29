from fastapi import FastAPI, BackgroundTasks
import requests
import asyncio
import random

app = FastAPI()

TELEGRAM_BOT_TOKEN = "8832788331:AAHQtEkgJLR7mIjHPfdYeg19r0M_rssYLmc"
CHAT_ID = "1296460762"

def send_telegram_alert(score: str, minute: str, signal: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "Открыть терминал", "callback_data": "open_terminal"}]
        ]
    }
    
    message = (
        f"🔥 *ВАЖНЫЙ СИГНАЛ — BBK Terminal*\n\n"
        f"⏱ Time: {minute}\n"
        f"📊 счëт: {score}\n"
        f"💡 Вариант входа: {signal}"
    )
    
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    }
    
    try:
        response = requests.post(url, json=payload)
        print("Telegram Response:", response.text)
    except Exception as e:
        print(f"Error: {e}")

@app.get("/")
def home():
    return {"status": "Running"}

async def fetch_and_scan_live_matches():
    live_scans = [
        {"score": f"{random.randint(0,1)}:{random.randint(0,1)}", "minute": f"{random.randint(60,85)}'", "signal": "ТБ 0.5"},
        {"score": f"{random.randint(1,2)}:{random.randint(0,1)}", "minute": f"{random.randint(55,80)}'", "signal": "ТБ 1.5"}
    ]
    
    for item in live_scans:
        send_telegram_alert(item["score"], item["minute"], item["signal"])
        await asyncio.sleep(2)

@app.get("/api/run-live-scan")
async def run_live_scan(background_tasks: BackgroundTasks):
    background_tasks.add_task(fetch_and_scan_live_matches)
    return {"status": "Started"}



