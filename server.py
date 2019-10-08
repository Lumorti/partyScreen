#! /usr/bin/python3

import socket
import json
import random
from os import path

# Settings
host, port = '', 8888
okResponse = "HTTP/1.1 200 OK" 
textResponse = okResponse + "Status: 200 OK\nContent-Type: text/plain\n\n"

# Variables for the questions
questions = []
responses = []
fields = {}
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
options = []
options.append({"title": "All Star", "artist": "Smash Mouth"})
options.append({"title": "Mr Brightside", "artist": "The Killers"})
options.append({"title": "Bohemian Rhapsody", "artist": "Queen"})
options.append({"title": "Don't Stop Me Now", "artist": "Queen"})
options.append({"title": "Moonage Daydream", "artist": "David Bowie"})

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

# Spotipy setup TODO 1
def setupSpot():

    pass

# Get a set of five choices TODO 1
def getChoices():

    pass

# Main server loop
while True:

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
            response += "visit " + str(hostip) + ":" + str(port) + " to vote and create"
            response = response.encode("utf-8")

        # Send the reply
        client_connection.sendall(response)
        client_connection.close()
