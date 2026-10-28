from fastapi import FastAPI
import requests

app = FastAPI(title="BBK Decision Terminal API")

TELEGRAM_BOT_TOKEN = "TOKEN_BOT_KEETII_ASITTI_GALCHI"
CHAT_ID = "CHAT_ID_KEETII_ASITTI_GALCHI"

def send_telegram_alert(match_name: str, signal: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    message = f"⚽ *BBK Betting Signal*\n\nMatch: {match_name}\nSignal: {signal}"
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
    return {"status": "BBK Terminal is running successfully!"}

# Fakkeenya test godhuuf
@app.get("/api/test-telegram")
def test_telegram():
    send_telegram_alert("Venezia — Inter", "ТБ 0.5 (Pressure high)")
    return {"status": "Telegram alert sent successfully!"}

