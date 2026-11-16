// The page's Alpine component. index.html uses it with <body x-data="scheduler">.
// It has to be registered on 'alpine:init', which Alpine fires just before it
// scans the page (this script loads first; Alpine itself is deferred).
document.addEventListener('alpine:init', () => {
    Alpine.data('scheduler', () => ({
        // Data loaded from the backend
        sessions: [],
        movies: [],
        shows: [],
        scheduleList: [],

        // Current selections
        selectedSessionId: '',
        selectedDateTime: '',
        selectedContentId: '',
        selectedContentName: '',
        selectedContentPoster: '',
        selectedEpisode: '',
        selectedSeriesEpisodes: [],
        selectedSeason: '',

        showError: false,
        errorText: '',

        // Modal state
        contentIsSelected: false,
        contentIsSeries: false,

        // awaiting schedule posting
        isAwaitingSchedulePost: false,

        // Alpine calls init() automatically when the component starts
        async init() {
            this.sessions = await getSessions();
            this.movies = await getLibrary();
            this.scheduleList = await getSchedule();
            this.shows = await getLibraryShows();
        },

        // Set an error message
        setError(message) {
            this.showError = true;
            this.errorText = message;
        },

        clearError() {
            this.showError = false;
            this.errorText = '';
        },

        // Earliest value the date inputs allow: midnight today, in the
        // "YYYY-MM-DDTHH:MM" local format that <input type="datetime-local"> uses.
        // (Same rule as before: earlier days are blocked, earlier times today are not.)
        earliestDateTime() {
            const now = new Date();
            const pad = (n) => String(n).padStart(2, '0');
            return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}T00:00`;
        },

        isDateValid(date) {
            const inputTime = new Date(date);
            const now = new Date();

            if (!date){
                return false;
            }

            return inputTime > now;

        },

        closeModal() {
            this.contentIsSelected = false;
            // Wait for the close animation to finish before clearing everything,
            // so the poster, episodes and date don't vanish while it fades out.
            // (Skipped if the modal was reopened in the meantime.)
            setTimeout(() => {
                if (!this.contentIsSelected) this.resetModal();
            }, 200);
        },

        resetModal() {
            this.selectedContentId = '';
            this.selectedContentName = '';
            this.selectedContentPoster = '';
            this.selectedEpisode = '';
            this.contentIsSeries = false;
            this.selectedDateTime = '';
            this.clearError();
            this.selectedSeason = '';

        },
    }));
});

// TEMP: hardcoded so index.html works when opened as a raw file. Change back to '/api' later.
const API_BASE = 'http://localhost:8000/api';

// Builds an Error from a failed response, using FastAPI's {"detail": "..."} message when there is one.
async function errorFromResponse(response) {
    try {
        const body = await response.json();
        if (typeof body.detail === 'string') return new Error(body.detail);
    } catch {
        // body wasn't JSON; fall through to the generic message
    }
    return new Error(`Response: ${response.status}`);
}

async function getLibrary() {
    const url = API_BASE + "/library";
    try {
        const response = await fetch(url, {
            headers: {
                "Content-Type": "application/json"
            }
        });
        if (!response.ok) {
            throw new Error(`Response: ${response.status}`);
        }
        return await response.json()
    } catch (error) {
        console.error(error.message)
    }
}

async function getLibraryShows() {
    const url = API_BASE + "/library/series";
    try {
        const response = await fetch(url, {
            headers: {
                "Content-Type": "application/json"
            }
        });
        if (!response.ok) {
            throw new Error(`Response: ${response.status}`);
        }
        return await response.json()
    } catch (error) {
        console.error(error.message)
    }
}

async function getSessions() {
    const url = API_BASE + "/sessions";
    try {
        const response = await fetch(url, {
            headers: {
                "Content-Type": "application/json"
            }
        });
        if (!response.ok) {
            throw new Error(`Response: ${response.status}`);
        }
        return await response.json()
    } catch (error) {
        console.error(error.message)
    }
}

async function getSeriesEpisodes(seriesId) {
    const url = API_BASE + "/library/series/episodes?seriesId=" + seriesId;
    try {
        const response = await fetch(url, {
            headers: {
                "Content-Type": "application/json"
            },
        });
        if (!response.ok) {
            throw new Error(`Response: ${response.status}`);
        }
        const episodeList = await response.json()
        const seasonMap = new Map();
        episodeList.forEach(episode => {
            let seasonNumber = episode.ParentIndexNumber
            if (!seasonMap.has(seasonNumber)) {
                seasonMap.set(seasonNumber, {
                    season : seasonNumber,
                    episodes: []
                })
            }
            seasonMap.get(seasonNumber).episodes.push({
                episode: episode.IndexNumber,
                id: episode.Id,
                name: episode.Name
            })
        });
        return Array.from(seasonMap.values())


    } catch (error) {
        console.error(error.message)
    }
}


function playContent(sessionId, contentId, contentName) {
    const url = API_BASE + '/play?contentId=' + contentId +'&sessionId=' + sessionId;
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
}

// Posts a schedule request. Resolves to true only if the job was actually added.
// (Bad input comes back as an error status with a "detail" message.)
async function postSchedule(url, date, sessionId, contentId, contentName) {
        let response
        try {
            response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                // The input gives local time with no timezone ("2026-11-20T19:00").
                // new Date() reads it as local time; toISOString() sends it as UTC.
                date: new Date(date).toISOString(),
                sessionId: sessionId,
                contentId: contentId,
                contentName: contentName
            })
        })
        } catch {
            throw new Error("Error reaching the Python API. Check connection")
        }

        if (!response.ok) {
            throw await errorFromResponse(response);
        }
        return true;

}

function schedule(date, sessionId, contentId, contentName) {
    return postSchedule(API_BASE + '/schedule', date, sessionId, contentId, contentName);
}

function scheduleShow(date, sessionId, contentId, contentName) {
    return postSchedule(API_BASE + '/schedule/show', date, sessionId, contentId, contentName);
}

async function getSchedule()  {
    const url = API_BASE + '/schedule';
    try {
        const response = await fetch(url, {
            headers: {
                "Content-Type": "application/json"
            }
        });
        if (!response.ok) {
            throw new Error(`Response: ${response.status}`);
        }
        return await response.json()
    } catch (error) {
        console.error(error.message)
    }
}

async function removeFromSchedule(jobId) {
    const url = API_BASE + '/schedule';
        const response = await fetch(url, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                jobId: jobId,
            })
        })
        if (!response.ok) {
            throw await errorFromResponse(response);
        }
}