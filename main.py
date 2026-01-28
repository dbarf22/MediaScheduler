from fastapi import FastAPI
from pydantic import BaseModel
from zoneinfo import ZoneInfo
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

class DeleteScheduleRequest(BaseModel):
    jobId: str

class SeriesEpisodeRequest(BaseModel):
    seriesId: str

# API Calls
@app.get("/sessions")
async def get_sessions():
    return jellyfin_communicator.getActiveSessions()

@app.get("/library")
async def get_library_content():
    return jellyfin_communicator.getLibraryMovies()

@app.get("/library/series")
async def get_library_series():
    return jellyfin_communicator.getLibrarySeries()

@app.get("/library/series/episodes")
async def get_series_episodes(seriesId: str):
    return jellyfin_communicator.getLibrarySeriesEpisodes(seriesId)

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
        date = job.trigger.run_date
        dateString = date.astimezone().strftime("%D, %I:%M %p")
        jobList.append({
            'contentId' : job.args[0],
            'sessionId' : job.args[1],
            'title' : job.args[2],
            'date' : dateString,
            'jobId' : job.id
        })
    return jobList

@app.delete("/schedule")
async def deleteSchedule(body: DeleteScheduleRequest):
    if body.jobId == '':
        return {"Error" : "Please provide a job id"}
    scheduler.remove_job(body.jobId)

# Non-api methods

def play(contentId: str, sessionId: str, contentName: str):
    return jellyfin_communicator.playContent(contentId, sessionId)