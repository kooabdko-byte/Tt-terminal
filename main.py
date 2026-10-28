from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="BBK Decision Terminal API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "BBK Terminal is running successfully!"}

@app.get("/api/matches/live")
def get_live_matches():
    return {
        "status": "success",
        "matches": [
            {
                "match": "Venezia — Inter",
                "league": "Serie A",
                "minute": 61,
                "score": "0:0",
                "dominance": "Inter",
                "pressure_status": "🔥 давление нарастает",
                "moment": "возможный гол во 2-м тайме",
                "bet_option": "ТБ 0.5"
            }
        ]
    }
