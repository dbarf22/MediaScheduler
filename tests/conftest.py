"""Shared setup for the backend tests.

Two safety rules for the whole suite:
  1. Never talk to the real Jellyfin server (so nothing plays on a real TV).
  2. Never touch the real jobs.sqlite (so your actual schedule is left alone).
"""
import pytest
import requests
from apscheduler.jobstores.memory import MemoryJobStore
from fastapi.testclient import TestClient

import jellyfin_communicator
import main
from fake_data import EPISODES, MOVIES, SERIES, SESSIONS

# Rule 2: swap the SQLite job store for an in-memory one before the scheduler
# ever starts, so jobs.sqlite is never opened.
main.scheduler.remove_jobstore("default")
main.scheduler.add_jobstore(MemoryJobStore(), "default")


@pytest.fixture(autouse=True)
def block_real_network(monkeypatch):
    """Rule 1, as a backstop: any real HTTP call made with `requests` fails the test."""
    def refuse(*args, **kwargs):
        raise RuntimeError("A test tried to make a real HTTP request. Mock it instead.")
    monkeypatch.setattr(requests.sessions.Session, "request", refuse)


class FakeJellyfin:
    """Stands in for jellyfin_communicator. Records every playContent call."""

    def __init__(self):
        self.played = []          # list of (contentId, sessionId)
        self.items = {ep["Id"]: ep | {"SeriesName": "Test Show"} for ep in EPISODES}

    def getActiveSessions(self):
        return SESSIONS

    def getLibraryMovies(self):
        return MOVIES

    def getLibrarySeries(self):
        return SERIES

    def getLibrarySeriesEpisodes(self, seriesId):
        return EPISODES if seriesId == "series-1" else []

    def getEpisodeName(self, itemId):
        # Jellyfin's /Items?ids=... returns a list of matching items
        return [self.items[itemId]] if itemId in self.items else []

    def playContent(self, contentId, sessionId):
        self.played.append((contentId, sessionId))


@pytest.fixture(autouse=True)
def jellyfin(monkeypatch):
    """Replaces every jellyfin_communicator function main.py uses with the fake."""
    fake = FakeJellyfin()
    for name in ["getActiveSessions", "getLibraryMovies", "getLibrarySeries",
                 "getLibrarySeriesEpisodes", "getEpisodeName", "playContent"]:
        monkeypatch.setattr(jellyfin_communicator, name, getattr(fake, name))
    return fake


@pytest.fixture(scope="session")
def client():
    """One test client for the whole run. `with` runs the app's lifespan, which starts the scheduler."""
    with TestClient(main.app) as c:
        yield c


@pytest.fixture(autouse=True)
def empty_schedule():
    """Every test starts (and ends) with no scheduled jobs."""
    main.scheduler.remove_all_jobs()
    yield
    main.scheduler.remove_all_jobs()
