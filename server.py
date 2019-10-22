#! /usr/bin/python3

import socket
import json
import time
import random
import spotipy
import spotipy.util as util
from os import path
from os import environ

# For the server
host, port = '', 80
okResponse = "HTTP/1.1 200 OK" 
textResponse = okResponse + "Status: 200 OK\nContent-Type: text/plain\n\n"

# Variables for the questions
questions = []
responses = []
fields = {}

# Spotipy setup 
scope = 'user-library-read,user-read-currently-playing,streaming,playlist-read-private'
environ["SPOTIPY_REDIRECT_URI"] = "http://localhost/callback/"
with open("secret.txt", "r") as f:
    username = f.readline().strip()
    environ["SPOTIPY_CLIENT_ID"] = f.readline().strip()
    environ["SPOTIPY_CLIENT_SECRET"] = f.readline().strip()

token = util.prompt_for_user_token(username, scope)

if token:
    sp = spotipy.Spotify(auth=token)
    print("Spotify authentication successful")
else:
    print("Spotify authentication failed")

questionsPerIP = {}

# Get the users playlist names and URIs
possiblePlaylists = sp.user_playlists(username)["items"]
print(possiblePlaylists[0]["name"])
print(possiblePlaylists[0]["uri"])

# Determine which playlist to use for each option
playlists = []
numChoices = 5
print("Possible playlists:")
for j in range(len(possiblePlaylists)):
    print(str(j) + " - " + possiblePlaylists[j]["name"])
for i in range(numChoices):
    print("Which playlist for option " + str(i+1) + "?")
    choice = input()
    try:
        choice = int(choice)
    except:
        print("That wasn't a number!")
        exit()
    playlists.append({"uri": possiblePlaylists[choice]["uri"]})

# Get the LAN IP
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP
hostip = get_ip()

# Keep track of which IP votes for what
votesPerIP = {}

# Set up the server
listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
listen_socket.bind((host, port))
listen_socket.listen(1)
print("starting server on "  + str(hostip) + ":" + str(port))

# Load the files into the cache
with open("client.html") as f:
    clientPage = okResponse + f.read()
    clientPage = clientPage.encode("utf-8")
with open("screen.html") as f:
    screenPage = okResponse + f.read()
    screenPage = screenPage.encode("utf-8")

# Load a playlist from a URI
def loadPlaylist(uri):

    playlistInfo = []

    # Get the playlist
    playlist = sp.user_playlist(username, uri, fields="name,tracks,next,artists")
    print("loading playlist: " + playlist["name"])

    # Add the tracks to the track list
    tracks = playlist["tracks"]
    for track in tracks["items"]:
        playlistInfo.append({"title": track["track"]["name"], "artist": track["track"]["artists"][0]["name"], "uri": track["track"]["uri"]})

    # Keep getting them in groups of 100 until the entire playlist is loaded
    while tracks["next"]:
        tracks = sp.next(tracks)
        for track in tracks["items"]:
            playlistInfo.append({"title": track["track"]["name"], "artist": track["track"]["artists"][0]["name"], "uri": track["track"]["uri"]})

    print("loaded " + str(len(playlistInfo)) + " tracks")
    return playlistInfo

# Get a set of five choices 
def getChoices(current):

    # Add the songs to the options list
    options = {"canVote": True, "current": current, "next":[]}
    titles = []
    for i in range(numChoices):

        # If the title is used before, reroll
        randomNum = random.randint(0, len(playlists[i]["info"])-1)
        song = playlists[i]["info"][randomNum]
        while song["title"] in titles:
            randomNum = random.randint(0, len(playlists[i]["info"])-1)
            song = playlists[i]["info"][randomNum]

        options["next"].append({"title": song["title"], "artist": song["artist"], "votes": 0, "uri": song["uri"]})
        titles.append(song["title"])

    # Give one song a slight preference
    options["next"][random.randint(0, numChoices-1)]["votes"] = 1

    return options

# Load the playlists
for i in range(numChoices):
    playlists[i]["info"] = loadPlaylist(playlists[i]["uri"])

# Get the current song
current = sp.current_user_playing_track()

# Get the initial choices
options = getChoices(current)
options["canVote"] = False

# Setup the initial time
timeMilli = int(round(time.time() * 1000))
oldTime = timeMilli

# Timings
timeForNewSong = 3
timeForVoting = 30
updateMilli = 1000

# Main server loop
while True:

    # Get the new time
    timeMilli = int(round(time.time() * 1000))

    # If it's been long enough, see how far through the currently playing song is 
    if timeMilli - oldTime > updateMilli:

        #  Get the current song
        current = sp.current_user_playing_track()

        if current is not None:

            # See how far through the song we are
            progress = current["progress_ms"]
            duration = current["item"]["duration_ms"]

        else:

            # Otherwise give some values so it won't error
            progress = 0
            duration = 300

        remainingSeconds = (duration - progress) / 1000

        # If it's in the final thirty seconds of a song show the votes 
        if remainingSeconds >= timeForNewSong and remainingSeconds < timeForVoting and not options["canVote"]:

            # Get the new choices and start the vote
            options = getChoices(current)
            options["canVote"] = True
            print("voting started")

        # If it's in the final few seconds, count the votes and play the next song
        elif remainingSeconds < timeForNewSong and options["canVote"]:

            # Stop the voting
            options["canVote"] = False
            print("voting ended")

            # Play whichever song had most votes
            maxVotes = -1
            for song in options["next"]:
                if song["votes"] > maxVotes:
                    nextSongURI = song["uri"]
                    maxVotes = song["votes"]

            # TODO 1 won't work if restarted after doing this, since its not in a playlist anymore
            print("playing: " + str(nextSongURI))
            sp.start_playback(None, None, [nextSongURI])

        oldTime = timeMilli

    # Get the request
    client_connection, client_address = listen_socket.accept()
    request = client_connection.recv(1024).decode("utf-8")

    # DEBUG reload each request
    with open("client.html") as f:
        clientPage = "HTTP/1.1 200 OK" + f.read()
        clientPage = clientPage.encode("utf-8")
    with open("screen.html") as f:
        screenPage = "HTTP/1.1 200 OK" + f.read()
        screenPage = screenPage.encode("utf-8")

    # Parse the response
    responseType = ""
    split = request.split("\n")
    for line in split:
        if "GET" in line:
            if "/screen" in line:
                responseType = "screen"
            elif "/refresh" in line:
                responseType = "refresh"
            elif "/info" in line:
                responseType = "info"
            elif "/send" in line:
                num = line[line.find("send")+4:line.find("HTTP")]
                ind = -1
                try:
                    ind = int(num)-1
                except:    
                    pass

                ipString = str(client_address[0])

                if ind != -1:

                    if ipString in list(votesPerIP.keys()):
                        options["next"][votesPerIP[ipString]]["votes"] -= 1
                    votesPerIP[ipString] = ind
                    options["next"][ind]["votes"] += 1

            elif "/ " in line:
                responseType = "client"

            break

    # If reply is required
    if responseType != "":

        if responseType == "screen":
            print("screen connection from: " + str(client_address))
            response = screenPage
        elif responseType == "client":
            print("client connection from: " + str(client_address))
            response = clientPage
        elif responseType == "refresh":
            response = textResponse
            response += json.dumps(options).replace("'", "#x420")
            response = response.encode("utf-8")
        elif responseType == "info":
            response = textResponse
            if port == 80:
                response += "visit " + str(hostip) + " to vote"
            else:
                response += "visit " + str(hostip) + ":" + str(port) + " to vote"
            response = response.encode("utf-8")

        # Send the reply
        client_connection.sendall(response)
        client_connection.close()
