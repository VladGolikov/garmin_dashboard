from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import mileage

app = FastAPI(title="Garmin Mileage API", version="1.0")

# Разрешаем CORS для Vue.js (localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mileage.router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Garmin Mileage API. Go to /api/monthly"}