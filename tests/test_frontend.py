"""Frontend tests: drive the real page in a headless browser.

The page is served from frontend/ by a tiny static server, and every /api call
is answered by FakeApi below instead of the Python backend. So these test the
HTML/JS/Alpine on their own, without Jellyfin or FastAPI running.

Needs internet access: Alpine.js is loaded from a CDN.
"""
import functools
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
from playwright.sync_api import Page, expect

from fake_data import EPISODES, MOVIES, SERIES, SESSIONS

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

# The page calls the API cross-origin while API_BASE is hardcoded to localhost:8000,
# so the fake responses need CORS headers or the browser would refuse them.
CORS = {"Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*"}

FUTURE = "2099-06-01T19:30"     # what a user would type into the datetime-local input
PAST = "2000-01-01T08:00"


class FakeApi:
    """Answers the page's /api requests and records them so tests can check what was sent."""

    def __init__(self):
        self.schedule = []        # what GET /api/schedule returns
        self.requests = []        # every (method, path, json body) the page sent
        self.post_error = None    # set to (status, detail) to make the next schedule POST fail
        self.post_unreachable = False  # set True to make the next schedule POST fail at the network level

    def sent(self, method, path):
        """Bodies of every request the page made to this method + path."""
        return [body for m, p, body in self.requests if m == method and p == path]

    def handle(self, route, request):
        url = urlparse(request.url)
        path, method = url.path, request.method
        if method == "OPTIONS":   # CORS preflight
            return route.fulfill(status=204, headers=CORS)

        body = request.post_data_json if request.post_data else None
        self.requests.append((method, path, body))

        def reply(data=None, status=200):
            return route.fulfill(status=status, json=data, headers=CORS)

        if method == "GET" and path == "/api/sessions":
            return reply(SESSIONS)
        if method == "GET" and path == "/api/library":
            return reply(MOVIES)
        if method == "GET" and path == "/api/library/series":
            return reply(SERIES)
        if method == "GET" and path == "/api/library/series/episodes":
            series_id = parse_qs(url.query).get("seriesId", [""])[0]
            return reply(EPISODES if series_id == "series-1" else [])
        if method == "GET" and path == "/api/schedule":
            return reply(self.schedule)

        if method == "POST" and path in ("/api/schedule", "/api/schedule/show"):
            if self.post_unreachable:
                self.post_unreachable = False
                return route.abort()
            if self.post_error:
                status, detail = self.post_error
                self.post_error = None
                return reply({"detail": detail}, status)
            self.schedule.append({"contentId": body["contentId"], "sessionId": body["sessionId"],
                                  "title": body["contentName"], "date": "06/01/99, 07:30 PM",
                                  "jobId": f"job-{len(self.schedule) + 1}"})
            return reply({"Success": "Item added to schedule successfully"})

        if method == "DELETE" and path == "/api/schedule":
            self.schedule = [item for item in self.schedule if item["jobId"] != body["jobId"]]
            return route.fulfill(status=204, headers=CORS)

        return reply({"detail": "Not Found"}, 404)


@pytest.fixture(scope="session")
def frontend_url():
    """Serves frontend/ on a free port for the whole test run."""
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, *args):    # keep test output quiet
            pass

    handler = functools.partial(QuietHandler, directory=str(FRONTEND_DIR))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}/"
    server.shutdown()


@pytest.fixture
def api():
    return FakeApi()


@pytest.fixture
def app(page: Page, frontend_url, api):
    """The page, loaded, with the fake API wired in. No device selected yet."""
    page.route("**/api/**", api.handle)
    page.route("https://fonts.googleapis.com/**", lambda route: route.abort())   # not needed, just slow
    page.goto(frontend_url)
    return page


@pytest.fixture
def ready(app):
    """The page with the TV selected, so the library is showing."""
    app.select_option("#sessions", "session-tv")
    expect(app.locator(".media-card").first).to_be_visible()
    return app


def movie_modal(page):
    return page.locator(".selected-content-card", has_text="Schedule Movie")


def series_modal(page):
    return page.locator(".selected-content-card", has_text="Schedule Episode")


def open_series(page):
    page.get_by_role("button", name="Series").click()
    page.locator(".media-card", has_text="Test Show").click()
    expect(series_modal(page)).to_be_visible()


# --------------------------------------------------------------------------
# Picking a device
# --------------------------------------------------------------------------

def test_asks_for_a_device_first(app):
    expect(app.get_by_text("Select a device to begin")).to_be_visible()
    expect(app.locator(".media-card")).to_have_count(0)


def test_device_list_only_has_remote_controllable_sessions(app):
    expect(app.locator("#sessions option")).to_have_text(["Select a session", "Jellyfin Web - Living Room TV"])


def test_choosing_a_device_shows_the_movies(ready):
    expect(ready.get_by_text("Select a device to begin")).to_have_count(0)
    expect(ready.locator(".media-card:visible .card-titles")).to_have_text(["The Birds", "Blade Runner"])


def test_series_tab_shows_the_shows(ready):
    ready.get_by_role("button", name="Series").click()
    expect(ready.locator(".media-card:visible .card-titles")).to_have_text(["Test Show"])


# --------------------------------------------------------------------------
# Scheduling a movie
# --------------------------------------------------------------------------

def test_schedule_a_movie(ready, api):
    ready.locator(".media-card", has_text="The Birds").click()
    modal = movie_modal(ready)
    expect(modal).to_be_visible()
    expect(modal.locator(".selected-content-name")).to_have_text("The Birds")

    submit = modal.get_by_role("button", name="Submit")
    expect(submit).to_be_disabled()             # no date yet
    modal.locator("#dates").fill(FUTURE)
    expect(submit).to_be_enabled()
    submit.click()

    expect(ready.locator(".modal")).to_be_hidden()
    expect(ready.locator(".schedule-item")).to_contain_text("The Birds")

    # The date is sent as UTC, converted from the user's local time
    expected_date = ready.evaluate(f"new Date('{FUTURE}').toISOString()")
    assert api.sent("POST", "/api/schedule") == [{
        "date": expected_date, "sessionId": "session-tv", "contentId": "movie-1", "contentName": "The Birds",
    }]


def test_past_dates_cannot_be_submitted(ready):
    ready.locator(".media-card", has_text="The Birds").click()
    modal = movie_modal(ready)
    modal.locator("#dates").fill(PAST)
    expect(modal.get_by_role("button", name="Submit")).to_be_disabled()


def test_backend_error_is_shown_and_modal_stays_open(ready, api):
    api.post_error = (400, "Date must be in the future")
    ready.locator(".media-card", has_text="The Birds").click()
    modal = movie_modal(ready)
    modal.locator("#dates").fill(FUTURE)
    modal.get_by_role("button", name="Submit").click()

    expect(modal.locator(".error-text")).to_have_text("Date must be in the future")
    expect(modal).to_be_visible()
    expect(ready.locator(".schedule-item")).to_have_count(0)


def test_unreachable_backend_shows_connection_error(ready, api):
    api.post_unreachable = True
    ready.locator(".media-card", has_text="The Birds").click()
    modal = movie_modal(ready)
    modal.locator("#dates").fill(FUTURE)
    modal.get_by_role("button", name="Submit").click()

    expect(modal.locator(".error-text")).to_contain_text("Error reaching the Python API")


def test_error_clears_when_modal_is_reopened(ready, api):
    api.post_error = (400, "Something went wrong")
    ready.locator(".media-card", has_text="The Birds").click()
    modal = movie_modal(ready)
    modal.locator("#dates").fill(FUTURE)
    modal.get_by_role("button", name="Submit").click()
    expect(modal.locator(".error-text")).to_be_visible()

    modal.get_by_role("button", name="Go Back").click()
    expect(ready.locator(".modal")).to_be_hidden()
    ready.locator(".media-card", has_text="Blade Runner").click()
    expect(movie_modal(ready).locator(".error-text")).to_be_hidden()


# --------------------------------------------------------------------------
# Scheduling an episode
# --------------------------------------------------------------------------

def test_series_modal_lists_seasons_and_starts_on_the_first(ready):
    open_series(ready)
    modal = series_modal(ready)
    expect(modal.locator(".season-button")).to_have_text(["Season 1", "Season 2"])
    expect(modal.locator(".season-button-selected")).to_have_text("Season 1")
    expect(modal.locator(".episode-name")).to_have_text(["Pilot", "The Second One"])
    expect(modal.locator(".episode-number")).to_have_text(["E1", "E2"])


def test_switching_seasons_shows_that_seasons_episodes(ready):
    open_series(ready)
    modal = series_modal(ready)
    modal.get_by_role("button", name="Season 2").click()
    expect(modal.locator(".season-button-selected")).to_have_text("Season 2")
    expect(modal.locator(".episode-name")).to_have_text(["Season Two Opener"])


def test_schedule_an_episode(ready, api):
    open_series(ready)
    modal = series_modal(ready)
    submit = modal.get_by_role("button", name="Submit")

    modal.locator("#seriesDates").fill(FUTURE)
    expect(submit).to_be_disabled()             # date set, but no episode picked yet

    modal.get_by_role("button", name="Season 2").click()
    modal.locator(".episode-button", has_text="Season Two Opener").click()
    expect(modal.locator(".episode-button-selected")).to_contain_text("Season Two Opener")
    expect(submit).to_be_enabled()
    submit.click()

    expect(ready.locator(".modal")).to_be_hidden()
    [sent] = api.sent("POST", "/api/schedule/show")
    assert sent["contentId"] == "ep-2-1"         # the episode, not the series
    assert sent["sessionId"] == "session-tv"


# --------------------------------------------------------------------------
# Closing the modal
# --------------------------------------------------------------------------

def test_go_back_closes_and_resets_the_modal(ready):
    open_series(ready)
    modal = series_modal(ready)
    modal.get_by_role("button", name="Season 2").click()
    modal.locator(".episode-button").first.click()
    modal.locator("#seriesDates").fill(FUTURE)

    modal.get_by_role("button", name="Go Back").click()
    expect(ready.locator(".modal")).to_be_hidden()
    ready.wait_for_timeout(300)    # the reset runs just after the close animation

    open_series(ready)
    expect(modal.locator(".episode-button-selected")).to_have_count(0)
    expect(modal.locator(".season-button-selected")).to_have_text("Season 1")
    expect(modal.locator("#seriesDates")).to_have_value("")


def test_clicking_the_backdrop_closes_the_modal(ready):
    ready.locator(".media-card", has_text="The Birds").click()
    expect(movie_modal(ready)).to_be_visible()

    viewport = ready.viewport_size
    ready.mouse.click(5, viewport["height"] - 5)   # bottom-left corner: backdrop, not the card
    expect(ready.locator(".modal")).to_be_hidden()


# --------------------------------------------------------------------------
# Scheduled items list
# --------------------------------------------------------------------------

def test_remove_a_scheduled_item(app, api):
    api.schedule = [{"contentId": "movie-1", "sessionId": "session-tv", "title": "The Birds",
                     "date": "06/01/99, 07:30 PM", "jobId": "job-1"}]
    app.select_option("#sessions", "session-tv")
    item = app.locator(".schedule-item")
    expect(item).to_contain_text("The Birds")
    expect(item).to_contain_text("06/01/99, 07:30 PM")

    item.get_by_role("button", name="Remove").click()
    expect(item).to_have_count(0)
    assert api.sent("DELETE", "/api/schedule") == [{"jobId": "job-1"}]
