from fastapi import FastAPI
from pydantic import BaseModel

import jellyfin_communicator
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
from contextlib import asynccontextmanager

# Stuff to initialize the sqlite db that holds jobs
jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
}

scheduler = BackgroundScheduler(jobstores=jobstores)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print('HI')
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

# Cors stuff
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models for bodies
class ScheduleRequest(BaseModel):
    date: str
    contentId: str
    sessionId: str

# API Calls
@app.get("/sessions")
async def get_sessions():
    return jellyfin_communicator.getActiveSessions()

@app.get("/library")
async def get_library_content():
    return jellyfin_communicator.getLibraryContents()

@app.post("/play")
async def play(contentId: str, sessionId: str):
    return jellyfin_communicator.playContent(contentId, sessionId)

@app.post("/schedule")
async def scheduleContent(body: ScheduleRequest):
    convertedDate = datetime.fromisoformat(body.date)
    scheduler.add_job(play, 'date', run_date=convertedDate, args=[body.contentId, body.sessionId])
    print("DONE")

def printer():
    print("p")