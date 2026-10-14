import json
import uuid
import urllib.request
import streamlit as st

st.set_page_config(page_title="A2A Demo", layout="wide")
st.title("A2A Protocol Demo")
st.caption("Host Agent finds remote agents, picks the right one, sends a Task, and shows the result.")

remote_agent_urls = [
    "http://127.0.0.1:8001",   # Weather Agent
    "http://127.0.0.1:8002",   # Hotel Agent
]

# ---------------------------------------------------------------
# STEP 1: DISCOVER - read every Agent Card (shown in the sidebar)
# ---------------------------------------------------------------
st.sidebar.header("Step 1: Discovered Agents")

agent_cards = []
for url in remote_agent_urls:
    try:
        card = json.loads(urllib.request.urlopen(url + "/.well-known/agent-card.json", timeout=3).read())
        agent_cards.append(card)
        with st.sidebar.expander(card["name"], expanded=True):
            st.write(card["description"])
            for skill in card["skills"]:
                st.write(f"Skill: **{skill['name']}**")
                st.write("Tags: " + ", ".join(skill["tags"]))
            st.caption("Full Agent Card")
            st.json(card, expanded=False)
    except Exception:
        st.sidebar.error(f"Cannot reach {url}. Is that agent running?")

# Chat history survives between reruns inside st.session_state
if "history" not in st.session_state:
    st.session_state.history = []

question = st.chat_input("Ask: What is the weather in Chennai?  or  Find me a hotel in Goa")

if question:
    item = {"question": question, "agent": None, "request": None, "response": None, "answer": None, "error": None}

    # -----------------------------------------------------------
    # STEP 2: CHOOSE - match words in the question with skill tags
    # -----------------------------------------------------------
    chosen_card = None
    for card in agent_cards:
        for skill in card["skills"]:
            for tag in skill["tags"]:
                if tag in question.lower():
                    chosen_card = card

    if chosen_card is None:
        item["error"] = "No agent has a skill for this. Ask about weather or hotels."
    else:
        item["agent"] = chosen_card["name"]

        # -------------------------------------------------------
        # STEP 3: SEND TASK - JSON-RPC 2.0, method "message/send"
        # -------------------------------------------------------
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
        item["request"] = request

        try:
            http_request = urllib.request.Request(
                chosen_card["url"],
                data=json.dumps(request).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            response = json.loads(urllib.request.urlopen(http_request, timeout=10).read())
            item["response"] = response

            # ---------------------------------------------------
            # STEP 4: RESULT - read the Artifact from the Task
            # ---------------------------------------------------
            if "error" in response:
                item["error"] = response["error"]["message"]
            else:
                item["answer"] = response["result"]["artifacts"][0]["parts"][0]["text"]
        except Exception as e:
            item["error"] = f"Could not talk to {chosen_card['name']}: {e}"

    st.session_state.history.append(item)

# ---------------------------------------------------------------
# Show every question and its A2A steps
# ---------------------------------------------------------------
if not st.session_state.history:
    st.info("Type a question below to see the A2A flow step by step.")

for item in st.session_state.history:
    with st.chat_message("user"):
        st.write(item["question"])

    with st.chat_message("assistant"):
        if item["agent"]:
            st.markdown(f"**Step 2: Chosen agent:** {item['agent']}")
        if item["request"]:
            with st.expander("Step 3: JSON-RPC request sent"):
                st.json(item["request"])
        if item["response"]:
            with st.expander("Step 4: JSON-RPC response received"):
                st.json(item["response"])
                st.write("Task state: **" + item["response"].get("result", {}).get("status", {}).get("state", "error") + "**")
        if item["answer"]:
            st.success(item["answer"])
        if item["error"]:
            st.warning(item["error"])
