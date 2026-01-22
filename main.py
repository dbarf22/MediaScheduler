from fastapi import FastAPI, requests
import jellyfin_communicator, database_manager
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/sessions")
async def get_sessions():
    return jellyfin_communicator.getActiveSessions()

@app.get("/images/{id}")
async def get_image(id: str):
    return jellyfin_communicator.getItemPrimaryPicture(id)

@app.get("/library")
async def get_library_content():
    return jellyfin_communicator.getLibraryContents()

@app.post("/play")
async def play(sessionID: str, contentID: str):
    return jellyfin_communicator.playContent(contentID, sessionID)