from dotenv import load_dotenv
import os, requests

load_dotenv()
JELLYFIN_URL=os.getenv("JELLYFIN_URL")
JELLYFIN_API_KEY=os.getenv("JELLYFIN_API_KEY")

headers = {
    "Authorization": f"MediaBrowser Token={JELLYFIN_API_KEY}",
}

# API Stuff for getting library content and searching

def getLibraryMovies():
    params = {
        "sortBy" : "SortName,ProductionYear",
        "sortOrder" : "Ascending",
        "includeItemTypes": "Movie",
        "recursive": "true",
    }
    link: str = f"{JELLYFIN_URL}/items"
    response = requests.get(link, headers=headers, params=params)

    response = response.json()['Items']

    filter = {"Name", "Id","Type"}

    # for every movie in the response, key is equal to value for every pair movie.items() if that key is in the filter
    # reminder that ** will actually unpack the dictionary that the k: v for k.. line makes
    # thus you get the 2 results and the poster link all as an entry in the dictionary instead
    # and each entry gets added to response

    response = [{**{k: v for k, v in movie.items() if k in filter},
                 "posterLink" : f"{JELLYFIN_URL}/Items/{movie['Id']}/Images/"
                                f"Primary?fillHeight=311&fillWidth=207&quality=50"} for movie in response]
    return response

# Get all TV shows

def getLibrarySeries():
    params = {
        "sortBy" : "SortName,ProductionYear",
        "sortOrder" : "Ascending",
        "includeItemTypes": "Series",
        "recursive": "true",
    }
    link: str = f"{JELLYFIN_URL}/items"
    response = requests.get(link, headers=headers, params=params)

    response = response.json()['Items']

    filter = {"Name", "Id","Type"}

    # for every movie in the response, key is equal to value for every pair movie.items() if that key is in the filter
    # reminder that ** will actually unpack the dictionary that the k: v for k.. line makes
    # thus you get the 2 results and the poster link all as an entry in the dictionary instead
    # and each entry gets added to response

    response = [{**{k: v for k, v in movie.items() if k in filter},
                 "posterLink" : f"{JELLYFIN_URL}/Items/{movie['Id']}/Images/"
                                f"Primary?fillHeight=311&fillWidth=207&quality=50"} for movie in response]
    return response

#

# Get episodes+seasons for a given series
def getLibrarySeriesEpisodes(seriesId: str):
    params = {
        "seriesId" : seriesId,
    }
    link: str = f"{JELLYFIN_URL}/Shows/{seriesId}/Episodes"
    response = requests.get(link, headers=headers, params=params)

    response = response.json()['Items']

    filter = {"Name", "Id", "Type","ParentIndexNumber", "IndexNumber", }

    response = [{**{k: v for k, v in episode.items() if k in filter}} for episode in response]

    return response

def getEpisodeName(seriesId: str):
    params = {
        "ids" : seriesId,
    }
    link: str = f"{JELLYFIN_URL}/Items"
    response = requests.get(link, headers=headers, params=params)
    response = response.json()['Items']
    return response

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

