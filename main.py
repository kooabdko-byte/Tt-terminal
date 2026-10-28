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
        f"⏱ Time: {minute}\n"
        f"📊 Score: {score}\n"
        f"💡 Signal: {signal}"
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
        url = "https://www.thesportsdb.com/api/v1/json/3/latestsoccer.php"
        requests.get(url)
        
        sample_live = [
            {"home": "Live Team A", "away": "Live Team B", "score": "1 - 0", "minute": "68'", "signal": "ТБ 1.5"}
        ]
        
        for match in sample_live:
            match_name = f"{match['home']} vs {match['away']}"
            send_telegram_alert(match_name, match['score'], match['minute'], match['signal'])
            await asyncio.sleep(2)
            
    except Exception as e:
        print(f"API Error: {e}")

@app.get("/api/run-live-scan")
async def run_live_scan(background_tasks: BackgroundTasks):
    background_tasks.add_task(fetch_and_scan_live_matches)
    return {"status": "Started"}

