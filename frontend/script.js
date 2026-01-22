async function getLibrary() {
    const url = "http://localhost:8000/library";
    try {
        const response = await fetch(url);
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
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Response: ${response.status}`);
        }
        return await response.json()
    } catch (error) {
        console.error(error.message)
    }
}

function playContent(sessionID, contentID) {
    const url = 'http://localhost:8000/play?contentId=' + contentID +'&sessionId=' + sessionID;

    fetch(url, {
        method: 'POST'
    })

}

