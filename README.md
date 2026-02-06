# About This Project

This is an accessibility project designed to facilitate the automation of media playback on any TV or computer using
a media app called Jellyfin. This is designed with caregivers in mind, meaning they can ensure whoever they're taking
care of can still watch the shows and movies that bring them comfort if they are incapable of using a remote or
streaming UI. My idea for this app is that it can be deployed in homes, nursing homes, and hospitals. Users can select
a movie or TV show episode, a device, and choose a time and day for it to play. Once that time hits, the device
will automatically start playing the chosen content.

# Technical Stuff
The backend for this app is built in Python, with the scheduling being handled by APScheduler, and the schedule
database being handled with SQLite. The frontend is written with Alpine.JS, meaning it's incredibly lightweight and 
responsive, coming with little to no baggage when compared to a framework like React. I really enjoyed writing
in Alpine, since the process is much more HTML forward, akin to Svelte, than React's more JS focused style. This was
also my first time designing anything with CSS, and there's definitely much room for improvement, but I am happy with how
it turned out!

# Screenshots

![Movies menu](movies.png)
![Shows menu](shows.png)
![Select menu](selected.png)
