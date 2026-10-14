# WEATHER AGENT (a "remote agent" in A2A language)
# It runs a tiny web server on port 8001 and does 2 things:
#   1. GET  /.well-known/agent-card.json  ->  tells the world who it is (Agent Card)
#   2. POST /                             ->  receives a task (JSON-RPC "message/send") and replies
# Only the Python standard library is used. Nothing to install.

import socket
import json
import uuid

HOST = "127.0.0.1"
PORT = 8001

# ---------------------------------------------------------------
# The AGENT CARD: the "business card" of this agent.
# Other agents read this to learn what we can do and where to call us.
# ---------------------------------------------------------------
agent_card = {
    "name": "Weather Agent",
    "description": "Tells you the current weather of a city",
    "url": f"http://{HOST}:{PORT}/",
    "version": "1.0.0",
    "protocolVersion": "0.3.0",
    "capabilities": {"streaming": False},
    "defaultInputModes": ["text"],
    "defaultOutputModes": ["text"],
    "skills": [
        {
            "id": "get_weather",
            "name": "Get Weather",
            "description": "Returns today's weather for a city",
            "tags": ["weather", "temperature", "rain", "forecast"],
            "examples": ["What is the weather in Chennai?"],
        }
    ],
}

# Fake data, so the demo works without any API key
weather_data = {
    "chennai": "32°C and sunny",
    "bangalore": "24°C with light rain",
    "mumbai": "29°C and humid",
    "delhi": "35°C and very hot",
    "goa": "30°C with sea breeze",
}

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen()
print(f"Weather Agent is running on http://{HOST}:{PORT}")
print(f"Agent Card: http://{HOST}:{PORT}/.well-known/agent-card.json\n")

while True:
    # Wait for someone to connect
    conn, addr = server.accept()

    # Read the HTTP headers
    data = b""
    while b"\r\n\r\n" not in data:
        chunk = conn.recv(4096)
        if not chunk:
            break
        data += chunk
    headers, _, body = data.partition(b"\r\n\r\n")
    header_lines = headers.decode().split("\r\n")
    method = header_lines[0].split(" ")[0]   # GET or POST
    path = header_lines[0].split(" ")[1]     # the URL path

    # Read the HTTP body (the JSON) using Content-Length
    body_length = 0
    for line in header_lines[1:]:
        if line.lower().startswith("content-length:"):
            body_length = int(line.split(":")[1])
    while len(body) < body_length:
        body += conn.recv(4096)

    # ---------- Route 1: someone wants our Agent Card ----------
    if method == "GET" and path == "/.well-known/agent-card.json":
        print("[Discovery] Someone read my Agent Card")
        reply = agent_card

    # ---------- Route 2: someone sent us a task ----------
    elif method == "POST" and path == "/":
        request = json.loads(body)

        if request["method"] == "message/send":
            user_text = request["params"]["message"]["parts"][0]["text"]
            print(f"[Task] Received: {user_text}")

            # Do the actual work: find a city in the text
            answer = "Sorry, I only know Chennai, Bangalore, Mumbai, Delhi and Goa."
            for city in weather_data:
                if city in user_text.lower():
                    answer = f"Weather in {city.title()}: {weather_data[city]}"

            # Reply with an A2A TASK that is "completed" and holds an ARTIFACT (the result)
            reply = {
                "jsonrpc": "2.0",
                "id": request["id"],
                "result": {
                    "kind": "task",
                    "id": str(uuid.uuid4()),
                    "contextId": str(uuid.uuid4()),
                    "status": {"state": "completed"},
                    "artifacts": [
                        {
                            "artifactId": str(uuid.uuid4()),
                            "name": "weather_report",
                            "parts": [{"kind": "text", "text": answer}],
                        }
                    ],
                },
            }
            print(f"[Task] Replied: {answer}\n")
        else:
            # JSON-RPC standard error for an unknown method
            reply = {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {"code": -32601, "message": "Method not found"},
            }

    else:
        reply = {"error": "Not found"}

    # Send the HTTP response back and close the connection
    reply_bytes = json.dumps(reply).encode()
    conn.sendall(
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: application/json\r\n"
        + f"Content-Length: {len(reply_bytes)}\r\n".encode()
        + b"Connection: close\r\n\r\n"
        + reply_bytes
    )
    conn.close()
