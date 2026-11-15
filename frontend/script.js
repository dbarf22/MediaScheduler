// Attaches a date+time picker to the input matching `selector`.
// `whenDateChosen` is a function that gets called with the chosen value
// as an ISO (UTC) string, or '' when the picker is cleared.
function dateTimePicker(selector, whenDateChosen) {
    return flatpickr(selector, {
        altInput: true,
        altFormat: 'n/j/Y, h:i K',
        enableTime: true,
        dateFormat: 'Z',
        minDate: 'today',
        // flatpickr's own option: it calls this function whenever the date changes
        onChange: (selectedDates, dateStr) => whenDateChosen(dateStr)
    });
}

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

        // Modal state
        contentIsSelected: false,
        contentIsSeries: false,

        // Alpine calls init() automatically when the component starts
        async init() {
            this.sessions = await getSessions();
            this.movies = await getLibrary();
            this.scheduleList = await getSchedule();
            this.shows = await getLibraryShows();
        },

        closeModal() {
            this.selectedContentId = '';
            this.selectedContentName = '';
            this.selectedContentPoster = '';
            this.selectedEpisode = '';
            this.contentIsSelected = false;
            this.contentIsSeries = false;
            // clearing flatpickr also resets selectedDateTime via its onChange
            ['dates', 'seriesDates'].forEach(id => document.getElementById(id)?._flatpickr?.clear());
            this.selectedDateTime = '';
        },
    }));
});

async function getLibrary() {
    const url = "http://localhost:8000/library";
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
    const url = "http://localhost:8000/library/series";
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
    const url = "http://localhost:8000/sessions";
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
    const url = "http://localhost:8000/library/series/episodes?seriesId=" + seriesId;
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
        console.log(Array.from(seasonMap.values()))
        return Array.from(seasonMap.values())


    } catch (error) {
        console.error(error.message)
    }
}

function playContent(sessionId, contentId, contentName) {
    const url = 'http://localhost:8000/play?contentId=' + contentId +'&sessionId=' + sessionId;
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
}

// Posts a schedule request. Resolves to true only if the job was actually added.
// (The backend answers 200 with an "Error" key for bad input, so check the body too.)
async function postSchedule(url, date, sessionId, contentId, contentName) {
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                date: date,
                sessionId: sessionId,
                contentId: contentId,
                contentName: contentName
            })
        })
        if (!response.ok) {
            throw new Error(`Response: ${response.status}`);
        }
        const result = await response.json();
        if (result.Error) {
            throw new Error(result.Error);
        }
        return true;
    } catch (error) {
        console.error(error.message)
        return false;
    }
}

function schedule(date, sessionId, contentId, contentName) {
    return postSchedule('http://localhost:8000/schedule', date, sessionId, contentId, contentName);
}

function scheduleShow(date, sessionId, contentId, contentName) {
    return postSchedule('http://localhost:8000/schedule/show', date, sessionId, contentId, contentName);
}

async function getSchedule()  {
    const url = 'http://localhost:8000/schedule';
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
    const url = 'http://localhost:8000/schedule';
    try {
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
            throw new Error(`Response: ${response.status}`);
        }
    } catch (error) {
        console.log(error.message)
    }
}