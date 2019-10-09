#! /usr/bin/python3

import socket
import json
import random
import spotipy
import spotipy.util as util
from os import path
from os import environ

# Settings
host, port = '', 80
okResponse = "HTTP/1.1 200 OK" 
textResponse = okResponse + "Status: 200 OK\nContent-Type: text/plain\n\n"

# Variables for the questions
questions = []
responses = []
fields = {}

# Spotipy setup 
scope = 'user-library-read,user-read-currently-playing'
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

# Song options DEBUG
options = {"canVote": True, "current": "", "next":[]}
options["next"].append({"title": "All Star", "artist": "Smash Mouth", "votes": 3})
options["next"].append({"title": "Mr Brightside", "artist": "The Killers", "votes": 0})
options["next"].append({"title": "Bohemian Rhapsody", "artist": "Queen", "votes": 0})
options["next"].append({"title": "Don't Stop Me Now", "artist": "Queen", "votes": 0})
options["next"].append({"title": "Moonage Daydream", "artist": "David Bowie", "votes": 1})

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

# Get a set of five choices 
def getChoices():

    current = sp.current_user_playing_track()

    # If the user is playing a playlist
    if current["context"]["type"] == "playlist":

        # Get the playlist
        playlistURI = current["context"]["uri"]
        playlist = sp.user_playlist(username, playlistURI)
        print("currently playing playlist: " + playlist["name"])

        # Pick 5 random songs from this playlist TODO 1

        # Update the options TODO 1

        return[]

    else:
        print("not currently playing a playlist")
        return []



getChoices()

# Main server loop
while True:

    # If it's been long enough, see how far through the currently playing song is TODO 1




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
                response += "visit " + str(hostip) + "<br> to vote on the next song"
            else:
                response += "visit " + str(hostip) + ":" + str(port) + "<br> to vote on the next song"
            response = response.encode("utf-8")

        # Send the reply
        client_connection.sendall(response)
        client_connection.close()
