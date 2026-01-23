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
    contentName: str

# API Calls
@app.get("/sessions")
async def get_sessions():
    return jellyfin_communicator.getActiveSessions()

@app.get("/library")
async def get_library_content():
    return jellyfin_communicator.getLibraryContents()

@app.post("/schedule")
async def scheduleContent(body: ScheduleRequest):
    if body.contentId == '' or body.sessionId == '' or body.date == '':
        return {"Error" : "Please provide all required fields"}
    convertedDate = datetime.fromisoformat(body.date)
    scheduler.add_job(play, 'date', run_date=convertedDate, args=[body.contentId, body.sessionId, body.contentName])
    return {"Success" : "Item added to schedule successfully"}

@app.get("/schedule")
async def getSchedule():
    jobList = []
    for job in scheduler.get_jobs():
        jobList.append({
            'contentId' : job.args[0],
            'sessionId' : job.args[1],
            'title' : job.args[2],
            'date' : job.trigger.run_date.isoformat()
        })
    return jobList


# Non-api methods

def play(contentId: str, sessionId: str, contentName: str):
    return jellyfin_communicator.playContent(contentId, sessionId)