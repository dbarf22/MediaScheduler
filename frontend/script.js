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

async function schedule(date, sessionId, contentId, contentName) {
    const url = 'http://localhost:8000/schedule';
        await fetch(url, {
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