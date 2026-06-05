from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from raceweek.api.routes import router

app = FastAPI(
    title="RaceWeek Strategist API",
    version="1.0.0",
    description="Local-first API for fantasy motorsport strategy recommendations.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
