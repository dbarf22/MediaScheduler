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