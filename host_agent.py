# HOST AGENT (the "client agent" in A2A language)
# It talks to the user, and hands each request to the right remote agent.
# The A2A flow, step by step:
#   STEP 1  DISCOVER  : read each remote agent's Agent Card
#   STEP 2  CHOOSE    : pick the agent whose skills match the question
#   STEP 3  SEND TASK : send a JSON-RPC "message/send" request
#   STEP 4  RESULT    : read the Task status and the Artifact (the answer)
# Only the Python standard library is used. Nothing to install.

import json
import uuid
import urllib.request

# The host only needs to know WHERE the agents live. Everything else it learns from the Agent Cards.
remote_agent_urls = [
    "http://127.0.0.1:8001",   # Weather Agent
    "http://127.0.0.1:8002",   # Hotel Agent
]

# ---------------------------------------------------------------
# STEP 1: DISCOVER - download every Agent Card
# ---------------------------------------------------------------
print("=" * 60)
print("STEP 1: DISCOVER - reading Agent Cards")
print("=" * 60)

agent_cards = []
for url in remote_agent_urls:
    card_url = url + "/.well-known/agent-card.json"
    card = json.loads(urllib.request.urlopen(card_url).read())
    agent_cards.append(card)
    print(f"\nFound: {card['name']}  ({card['url']})")
    print(f"  About : {card['description']}")
    for skill in card["skills"]:
        print(f"  Skill : {skill['name']}  tags={skill['tags']}")

print("\nTry: 'What is the weather in Chennai?' or 'Find me a hotel in Goa'")

while True:
    question = input("\nYou (or 'exit'): ").strip()
    if question.lower() == "exit":
        break
    if question == "":
        continue

    # -----------------------------------------------------------
    # STEP 2: CHOOSE - match words in the question with skill tags
    # -----------------------------------------------------------
    print("\n" + "=" * 60)
    print("STEP 2: CHOOSE - which agent has the right skill?")
    print("=" * 60)

    chosen_card = None
    for card in agent_cards:
        for skill in card["skills"]:
            for tag in skill["tags"]:
                if tag in question.lower():
                    chosen_card = card

    if chosen_card is None:
        print("No agent has a skill for this. Ask about weather or hotels.")
        continue
    print(f"Chosen agent: {chosen_card['name']}")

    # -----------------------------------------------------------
    # STEP 3: SEND TASK - JSON-RPC 2.0 request, method "message/send"
    # -----------------------------------------------------------
    print("\n" + "=" * 60)
    print("STEP 3: SEND TASK - JSON-RPC request we send")
    print("=" * 60)

    request = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/send",
        "params": {
            "message": {
                "kind": "message",
                "messageId": str(uuid.uuid4()),
                "role": "user",
                "parts": [{"kind": "text", "text": question}],
            }
        },
    }
    print(json.dumps(request, indent=2))

    http_request = urllib.request.Request(
        chosen_card["url"],
        data=json.dumps(request).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    response = json.loads(urllib.request.urlopen(http_request).read())

    # -----------------------------------------------------------
    # STEP 4: RESULT - the remote agent returns a Task with Artifacts
    # -----------------------------------------------------------
    print("\n" + "=" * 60)
    print("STEP 4: RESULT - JSON-RPC response we got back")
    print("=" * 60)
    print(json.dumps(response, indent=2, ensure_ascii=False))

    if "error" in response:
        print(f"\nError from agent: {response['error']['message']}")
        continue

    task = response["result"]
    answer = task["artifacts"][0]["parts"][0]["text"]
    print(f"\nTask state : {task['status']['state']}")
    print(f"{chosen_card['name']} says: {answer}")
