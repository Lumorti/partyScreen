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
options.append({"title": "skip song", "artist": ""})
options.append({"title": "refresh choices", "artist": ""})
options.append({"title": "All Star", "artist": "Smash Mouth"})
options.append({"title": "Mr Brightside", "artist": "The Killers"})
options.append({"title": "Bohemian Rhapsody", "artist": "Queen"})

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
with open("questions.json") as f:
    questions = json.load(f)["data"]
with open("fields.json") as f:
    fields = json.load(f)
if path.exists("saved_responses.json"):
    with open("saved_responses.json") as f:
        responses = json.load(f)
if path.exists("saved_fields.json"):
    with open("saved_fields.json") as f:
        fields = json.load(f)

# Save the answers given so far to a file 
def saveAnswers():
    with open("saved_responses.json", "w+") as f:
        json.dump(responses, f)
    with open("saved_fields.json", "w+") as f:
        json.dump(fields, f)

# Generate a question TODO 1
def getQuestion():

    index = random.randint(0,len(questions)-1)

    q = questions[index]["text"]

    # See if any words need replacing e.g. $(NAME)
    inWord = False
    word = ""
    i = 0
    while i < len(q):

        if q[i] == "$":
            inWord = True

        elif q[i] == ")" and inWord:
            inWord = False

            # Determine the word to replace it with
            newWord = "ERROR"
            for field in list(fields.keys()):
                if field == word:
                    newIndex = random.randint(0, len(fields[field])-1)
                    newWord = fields[field][newIndex]

            q = q[:i-len(word)-2] + "<span>" + newWord + "</span>" + q[i+1:]
            q = q.replace("  ", " ")
            q = q.replace(" :", ":")
            q = q.replace(" ?", "?")
            q = q.replace(" ,", ",")
            i = -1

            word = ""

        elif inWord and q[i] != "(":
            word += q[i]

        i += 1

    return q, index

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
            elif "/send" in line:
                answer = line[line.find("/send")+5:line.find("HTTP")]
                answer = answer.replace("%20", " ")
                answer = answer.strip()
                ques = questionsPerIP[str(client_address[0])]
                if ques[0:4] == "Give":
                    field = ""
                    for q in questions:
                        if q["type"] == "request" and q["text"][0:15] == ques[0:15]:
                            field = q["field"]
                            break
                    fields[field].append(answer)
                else:
                    responses.append({"question": ques, "answer": answer, "laughs":0, "scares":0,"up":0,"down":0})
                saveAnswers()
            elif "/answer" in line:
                responseType = "answer"
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
            q, i = getQuestion()
            response += q
            response = response.encode("utf-8")
            questionsPerIP[str(client_address[0])] = q
        elif responseType == "answer":
            response = textResponse
            #TODO 1 choose best response

            # If any have been shown less than twice, show them

            # Otherwise pick randomly

            response = response.encode("utf-8")
        elif responseType == "info":
            response = textResponse
            response += "visit " + str(hostip) + ":" + str(port) + " to vote and create"
            response = response.encode("utf-8")

        # Send the reply
        client_connection.sendall(response)
        client_connection.close()
