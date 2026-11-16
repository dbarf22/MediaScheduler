"""Backend tests: call the FastAPI routes the same way the frontend does.

Jellyfin is faked (see conftest.py), so these run offline and never play anything.
"""
import time
from datetime import datetime, timedelta, timezone

import pytest
import requests

import jellyfin_communicator
import main
from fake_data import EPISODES, MOVIES, SERIES, SESSIONS


def in_the_future(**delta):
    """An ISO 8601 UTC string some time from now, like the frontend sends."""
    return (datetime.now(timezone.utc) + timedelta(**delta)).isoformat()


def schedule_body(**overrides):
    body = {"date": in_the_future(hours=1), "sessionId": "session-tv",
            "contentId": "movie-1", "contentName": "The Birds"}
    return body | overrides


# --------------------------------------------------------------------------
# Library / sessions
# --------------------------------------------------------------------------

@pytest.mark.parametrize("path, expected", [
    ("/api/sessions", SESSIONS),
    ("/api/library", MOVIES),
    ("/api/library/series", SERIES),
    ("/api/library/series/episodes?seriesId=series-1", EPISODES),
])
def test_read_routes_return_jellyfin_data(client, path, expected):
    response = client.get(path)
    assert response.status_code == 200
    assert response.json() == expected


def test_episodes_route_requires_series_id(client):
    assert client.get("/api/library/series/episodes").status_code == 422


def test_jellyfin_down_returns_502(client, monkeypatch):
    def down():
        raise requests.ConnectionError("connection refused")
    monkeypatch.setattr(jellyfin_communicator, "getActiveSessions", down)

    response = client.get("/api/sessions")
    assert response.status_code == 502
    assert "Jellyfin" in response.json()["detail"]


# --------------------------------------------------------------------------
# Scheduling a movie: POST /api/schedule
# --------------------------------------------------------------------------

def test_schedule_movie_adds_a_job(client):
    response = client.post("/api/schedule", json=schedule_body())
    assert response.status_code == 200

    jobs = main.scheduler.get_jobs()
    assert len(jobs) == 1
    assert jobs[0].args == ("movie-1", "session-tv", "The Birds")


@pytest.mark.parametrize("field", ["contentId", "sessionId", "date"])
def test_schedule_rejects_empty_fields(client, field):
    response = client.post("/api/schedule", json=schedule_body(**{field: ""}))
    assert response.status_code == 400
    assert main.scheduler.get_jobs() == []


def test_schedule_rejects_missing_fields(client):
    body = schedule_body()
    del body["sessionId"]
    assert client.post("/api/schedule", json=body).status_code == 422


@pytest.mark.parametrize("date, message", [
    ("not a date", "valid ISO 8601"),
    ("2099-01-01T10:00:00", "timezone"),               # no Z / offset
    ("2000-01-01T10:00:00Z", "future"),
])
def test_schedule_rejects_bad_dates(client, date, message):
    response = client.post("/api/schedule", json=schedule_body(date=date))
    assert response.status_code == 400
    assert message in response.json()["detail"]
    assert main.scheduler.get_jobs() == []


def test_schedule_accepts_a_z_suffix_and_offsets(client):
    assert client.post("/api/schedule", json=schedule_body(date="2099-01-01T10:00:00Z")).status_code == 200
    assert client.post("/api/schedule", json=schedule_body(date="2099-01-01T10:00:00-05:00")).status_code == 200
    assert len(main.scheduler.get_jobs()) == 2


# --------------------------------------------------------------------------
# Scheduling an episode: POST /api/schedule/show
# --------------------------------------------------------------------------

def test_schedule_episode_builds_title_from_season_and_number(client):
    response = client.post("/api/schedule/show", json=schedule_body(contentId="ep-2-1", contentName="Test Show"))
    assert response.status_code == 200
    assert main.scheduler.get_jobs()[0].args == ("ep-2-1", "session-tv", "Test Show: S2E1")


def test_schedule_episode_handles_season_zero(client, jellyfin):
    # Specials live in season 0. 0 is falsy, so this catches `if season:` mistakes.
    jellyfin.items["special"] = {"Id": "special", "Type": "Episode", "SeriesName": "Test Show",
                                 "Name": "Christmas Special", "ParentIndexNumber": 0, "IndexNumber": 1}
    client.post("/api/schedule/show", json=schedule_body(contentId="special"))
    assert main.scheduler.get_jobs()[0].args[2] == "Test Show: S0E1"


def test_schedule_episode_falls_back_to_name_without_numbers(client, jellyfin):
    jellyfin.items["unnumbered"] = {"Id": "unnumbered", "Type": "Episode", "SeriesName": "Test Show",
                                    "Name": "Behind the Scenes", "ParentIndexNumber": None, "IndexNumber": None}
    response = client.post("/api/schedule/show", json=schedule_body(contentId="unnumbered"))
    assert response.status_code == 200
    assert main.scheduler.get_jobs()[0].args[2] == "Test Show: Behind the Scenes"


def test_schedule_episode_unknown_id_is_404(client):
    response = client.post("/api/schedule/show", json=schedule_body(contentId="nope"))
    assert response.status_code == 404
    assert main.scheduler.get_jobs() == []


def test_schedule_episode_rejects_non_episodes(client, jellyfin):
    # Jellyfin returns unrelated items for a malformed id; those must not be scheduled.
    jellyfin.items["folder"] = {"Id": "folder", "Type": "CollectionFolder", "Name": "Movies"}
    assert client.post("/api/schedule/show", json=schedule_body(contentId="folder")).status_code == 404


def test_schedule_episode_validates_dates_too(client):
    response = client.post("/api/schedule/show", json=schedule_body(contentId="ep-1-1", date="2000-01-01T00:00:00Z"))
    assert response.status_code == 400


# --------------------------------------------------------------------------
# Listing and removing: GET / DELETE /api/schedule
# --------------------------------------------------------------------------

def test_list_schedule_is_empty_at_first(client):
    assert client.get("/api/schedule").json() == []


def test_list_schedule_shows_scheduled_items(client):
    client.post("/api/schedule", json=schedule_body())

    [item] = client.get("/api/schedule").json()
    assert item["contentId"] == "movie-1"
    assert item["sessionId"] == "session-tv"
    assert item["title"] == "The Birds"
    assert item["jobId"]
    assert item["date"]          # formatted for display, e.g. "01/01/99, 10:00 AM"


def test_delete_removes_the_job(client):
    client.post("/api/schedule", json=schedule_body())
    job_id = client.get("/api/schedule").json()[0]["jobId"]

    response = client.request("DELETE", "/api/schedule", json={"jobId": job_id})
    assert response.status_code == 204
    assert client.get("/api/schedule").json() == []


def test_delete_unknown_job_is_404(client):
    assert client.request("DELETE", "/api/schedule", json={"jobId": "nope"}).status_code == 404


def test_delete_empty_job_id_is_400(client):
    assert client.request("DELETE", "/api/schedule", json={"jobId": ""}).status_code == 400


# --------------------------------------------------------------------------
# Playback: the job actually fires
# --------------------------------------------------------------------------

def test_scheduled_job_calls_play_with_its_args(client, jellyfin):
    client.post("/api/schedule", json=schedule_body())
    job = main.scheduler.get_jobs()[0]

    job.func(*job.args)          # run it now instead of waiting an hour
    assert jellyfin.played == [("movie-1", "session-tv")]


def test_scheduled_job_fires_on_time(client, jellyfin):
    """Real end-to-end timing: schedule 1.5 seconds out and wait for it to play."""
    client.post("/api/schedule", json=schedule_body(date=in_the_future(seconds=1.5)))

    deadline = time.monotonic() + 5
    while not jellyfin.played and time.monotonic() < deadline:
        time.sleep(0.1)

    assert jellyfin.played == [("movie-1", "session-tv")]
    assert main.scheduler.get_jobs() == []    # one-off jobs remove themselves after running


# --------------------------------------------------------------------------
# Frontend is served
# --------------------------------------------------------------------------

def test_frontend_is_served(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert client.get("/script.js").status_code == 200
    assert client.get("/styles.css").status_code == 200
