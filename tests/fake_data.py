"""Made-up Jellyfin data shared by the backend and frontend tests.

The shapes match what jellyfin_communicator returns (and what the API passes
straight through to the frontend).
"""

SESSIONS = [
    {"Id": "session-tv", "Client": "Jellyfin Web", "DeviceName": "Living Room TV", "SupportsRemoteControl": True},
    {"Id": "session-phone", "Client": "Jellyfin Android", "DeviceName": "Phone", "SupportsRemoteControl": False},
]

MOVIES = [
    {"Id": "movie-1", "Name": "The Birds", "Type": "Movie", "ProductionYear": 1963, "posterLink": ""},
    {"Id": "movie-2", "Name": "Blade Runner", "Type": "Movie", "ProductionYear": 1982, "posterLink": ""},
]

SERIES = [
    {"Id": "series-1", "Name": "Test Show", "Type": "Series", "ProductionYear": 2001, "posterLink": ""},
]

# Raw episode list for series-1, the way Jellyfin returns it (flat, not grouped by season)
EPISODES = [
    {"Id": "ep-1-1", "Name": "Pilot", "Type": "Episode", "ParentIndexNumber": 1, "IndexNumber": 1},
    {"Id": "ep-1-2", "Name": "The Second One", "Type": "Episode", "ParentIndexNumber": 1, "IndexNumber": 2},
    {"Id": "ep-2-1", "Name": "Season Two Opener", "Type": "Episode", "ParentIndexNumber": 2, "IndexNumber": 1},
]
