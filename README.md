# partyScreen

Ever hosted a party and had people complain about the music? Well if you use this then they lose their right to.

### Features
 - people can vote on their phones to decide on the next song
 - have the graph of votes displayed on a tv (or any device)
 - by default there are five choices at a time
 - these choices can come from different playlists
 - one song always starts with one vote
 - admin commands for the host (and anyone they give the password to)

### Screenshots

The voting screen people see on their phones. This automatically refreshes whenever there are new song choices.
![screenshot of voting screen](https://raw.githubusercontent.com/Lumorti/partyScreen/master/voting.png)

The screen that should be put up on the TV showing the current voting progress.
![screenshot of votes screen](https://raw.githubusercontent.com/Lumorti/partyScreen/master/screen.png)

### Setup

This depends on the latest version of Spotipy, a Python library, available [here](https://github.com/plamere/spotipy).

You'll need to create a Spotify App [here](https://developer.spotify.com/dashboard/login) to get a client secret and client ID.

Then you need to create the "secret.txt" file, which contains the following, each on their own line:
 - your spotify username
 - your spotify client id
 - your spotify client secret
 - the spotify device ID of the device that the music should stream to

Place this file in this directory, then start the server using:
```bash
sudo ./server.py
```

You'll then be prompted to authorise the script to access your playlists, then prompted to choose which playlist is used for each song option. 

After this the server should be running, connect to the IP (or use localhost if on the same machine) to view the voting. 

To view the screen visit "IP/screen", to view the admin page visit "IP/admin".

The admin password can be changed at the top of the server.py file.

