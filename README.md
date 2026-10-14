# A2A Protocol: Simple Demo

A beginner friendly demo of **A2A (Agent2Agent)**, the open protocol that lets AI agents
find each other and work together over plain HTTP + JSON.

No functions, no classes, no API keys, nothing to install. Only the Python standard library.

## Files

| File | Role in A2A | Port |
|---|---|---|
| `weather_agent.py` | Remote agent. Knows the weather | 8001 |
| `hotel_agent.py` | Remote agent. Suggests hotels | 8002 |
| `host_agent.py` | Client agent. Talks to you and sends work to the right agent | none |

## How to run

Open **3 terminals** in this folder:

```
python weather_agent.py
python hotel_agent.py
python host_agent.py
```

Then type in the host terminal:

```
What is the weather in Chennai?
Find me a hotel in Goa
```

## Run with a web UI (optional)

`host_agent_ui.py` does the same 4 steps but shows them in the browser. It needs Streamlit, installed in a local venv:

```
python -m venv .venv
.venv\Scripts\activate
pip install streamlit
```

Start the two agents as above, then in a third terminal (with the venv active):

```
streamlit run host_agent_ui.py
```

The browser opens at http://localhost:8501. The sidebar shows the discovered Agent Cards, and each question shows the chosen agent, the JSON-RPC request, the response and the answer.

## What you will see (the 4 steps of A2A)

1. **Discover**: the host reads `GET /.well-known/agent-card.json` from each agent. The Agent Card lists the agent's name, URL and skills.
2. **Choose**: the host matches words in your question with each skill's tags.
3. **Send Task**: the host sends a JSON-RPC 2.0 request with method `message/send`. The message is made of `parts`.
4. **Get Result**: the remote agent replies with a **Task** (`status.state = completed`) that holds an **Artifact** (the answer).

Every request and response is printed as JSON, so you can see exactly what travels between agents.

## Key words

| Word | Meaning |
|---|---|
| Agent Card | JSON "business card" of an agent: who it is, where it lives, what skills it has |
| Message | One turn of conversation, made of Parts (text, file, data) |
| Task | A unit of work with a status: submitted, working, completed, failed |
| Artifact | The output the agent produced for the task |
| JSON-RPC | Simple request/response format: `method`, `params`, `id`, then `result` or `error` |
