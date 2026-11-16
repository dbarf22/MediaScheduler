from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import jellyfin_communicator

from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.jobstores.base import JobLookupError
import requests
from datetime import datetime, timezone
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

# TEMP: lets index.html opened as a raw file (origin "null") call the API. Remove along with the hardcoded API_BASE.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# If Jellyfin can't be reached (or times out), answer 502 Bad Gateway instead of crashing with a 500.
@app.exception_handler(requests.RequestException)
async def jellyfin_unreachable(request: Request, error: requests.RequestException):
    return JSONResponse(status_code=502, content={"detail": "Couldn't reach Jellyfin. Is it running?"})

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

# Frontend

app.frontend("/", directory="frontend")

# API Calls
# Every route below is registered on this router, so they all live under /api
# (e.g. /api/sessions). That keeps them from ever clashing with frontend files.
api = APIRouter(prefix="/api")

@api.get("/sessions")
async def get_sessions():
    return jellyfin_communicator.getActiveSessions()

@api.get("/library")
async def get_library_content():
    return jellyfin_communicator.getLibraryMovies()

@api.get("/library/series")
async def get_library_series():
    return jellyfin_communicator.getLibrarySeries()

@api.get("/library/series/episodes")
async def get_series_episodes(seriesId: str):
    return jellyfin_communicator.getLibrarySeriesEpisodes(seriesId)

def parseFutureDate(date: str) -> datetime:
    """Turns the request's date string into a datetime, or raises a 400 explaining what's wrong."""
    try:
        convertedDate = datetime.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Date isn't a valid ISO 8601 date")
    if convertedDate.tzinfo is None:
        raise HTTPException(status_code=400, detail="Date must include a timezone")
    if convertedDate < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Date must be in the future")
    return convertedDate

@api.post("/schedule/show")
async def scheduleContentShow(body: ScheduleRequest):
    if body.contentId == '' or body.sessionId == '' or body.date == '':
        raise HTTPException(status_code=400, detail="Please provide all required fields")
    convertedDate = parseFutureDate(body.date)

    query = jellyfin_communicator.getEpisodeName(body.contentId)

    # Jellyfin ignores a malformed id and returns other items, so also check we really got an episode.
    if not query or query[0].get("Type") != "Episode":
        raise HTTPException(status_code=404, detail="No episode with that id")

    episode = query[0]
    seriesName = episode.get("SeriesName")
    season = episode.get("ParentIndexNumber")
    number = episode.get("IndexNumber")
    name = episode.get("Name")

    if season is not None and number is not None:
        title = f"{seriesName}: S{season}E{number}"
    else:
        title = f"{seriesName}: {name}"

    scheduler.add_job(play, 'date', run_date=convertedDate, args=[body.contentId, body.sessionId, title])
    return {"Success" : "Item added to schedule successfully"}

@api.post("/schedule")
async def scheduleContent(body: ScheduleRequest):
    if body.contentId == '' or body.sessionId == '' or body.date == '':
        raise HTTPException(status_code=400, detail="Please provide all required fields")
    convertedDate = parseFutureDate(body.date)

    scheduler.add_job(play, 'date', run_date=convertedDate, args=[body.contentId, body.sessionId, body.contentName])
    return {"Success" : "Item added to schedule successfully"}

@api.get("/schedule")
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

@api.delete("/schedule", status_code=204)
async def deleteSchedule(body: DeleteScheduleRequest):
    if body.jobId == '':
        raise HTTPException(status_code=400, detail="Please provide a job id")
    try:
        scheduler.remove_job(body.jobId)
    except JobLookupError:
        raise HTTPException(status_code=404, detail="No scheduled item with that id")

app.include_router(api)

# Non-api methods

def play(contentId: str, sessionId: str, contentName: str):
    return jellyfin_communicator.playContent(contentId, sessionId)