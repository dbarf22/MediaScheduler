import json

from dotenv import load_dotenv
import os, requests

load_dotenv()
JELLYFIN_URL=os.getenv("JELLYFIN_URL")
JELLYFIN_API_KEY=os.getenv("JELLYFIN_API_KEY")

headers = {
    "Authorization": f"MediaBrowser Token={JELLYFIN_API_KEY}",
}

# API Stuff for getting library content and searching

def getLibraryContents():
    params = {
        "sortBy" : "SortName,ProductionYear",
        "sortOrder" : "Ascending",
        "includeItemTypes": "Movie",
        "recursive": "true",
        "fields" : "PrimaryImageAspectRatio,MediaSourceCount",
        "imageTypeLimit" : "1",
        "enableImageTypes" : "Primary",
        "startIndex" : "0"
    }
    link: str = f"{JELLYFIN_URL}/items"
    response = requests.get(link, headers=headers, params=params)
    responseJson = response.json()

    filtered = json.loads(responseJson)


def getLibraryContentByName(query: str):
    params = {
        "searchTerm" : query,
        "imit" : "24",
        "Fields" : "PrimaryImageAspectRatio,CanDelete,BasicSyncInfo",
        "Recursive" : "True",
        "ImageTypeLimit" : "1",
        "IncludePeople" : "false",
        "IncludeMedia" : "true",
        "IncludeGenres" : "false",
        "IncludeStudios" : "false",
        "IncludeArtists" : "false",
        "IncludeItemTypes" : "Movie,Series"
    }
    link: str = f"{JELLYFIN_URL}/items"
    response = requests.get(link, headers=headers, params=params)
    return response.json()

# getting the list of active jellyfin sessions
def getActiveSessions():
    params = {}
    link: str = f"{JELLYFIN_URL}/Sessions"
    response = requests.get(link, headers=headers, params=params)
    return response.json()

# Stuff for playing content

def playContent(contentID: str, sessionID: str):
    params = {
        "playCommand" : "PlayNow",
        "itemIds" : contentID,
    }
    link : str = f"{JELLYFIN_URL}/Sessions/{sessionID}/Playing"
    response = requests.post(link, headers=headers, params=params)

def stopContent(sessionID: str):
    link : str = f"{JELLYFIN_URL}/Sessions/{sessionID}/Playing/Stop"
    response = requests.post(link, headers=headers)

