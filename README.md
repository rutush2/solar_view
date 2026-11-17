
```markdown
# solar_view

Real-time solar inverter monitoring and local AI diagnostic dashboard built with FastAPI, SQLite, Ollama, and Streamlit.

## Architecture
- **FastAPI + Uvicorn (`app/main.py`)**: Runs a non-blocking background loop that writes live inverter readings every 2 seconds into a rolling 600-row SQLite window (`solar_data.db`).
- **Database Layer (`app/db.py`)**: Manages SQLite schema initialization, live reading generation across four inverters (`INV-01` through `INV-04`), and sliding-window retention.
- **View & Aggregation (`app/view.py`)**: Computes live total array output, average panel temperature, active fault alerts, and recent metrics for diagnostics.
- **Local AI Client (`app/ollama_client.py`)**: Sends the recent window of readings to a local Ollama instance (`llama3`) for concise operational diagnostics.
- **Streamlit Dashboard (`ui/dashboard.py`)**: Auto-refreshes every 2 seconds via `@st.fragment(run_every=2)`, automatically converts UTC timestamps to the viewer's browser timezone (`st.context.timezone`), and displays live AC power and panel temperature charts alongside inverter status indicators.

## Project Structure
```text
solar_view/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── db.py
│   ├── main.py
│   ├── ollama_client.py
│   └── view.py
├── ui/
│   └── dashboard.py
├── .gitignore
├── requirements.txt
└── README.md

```

## Setup & Running

1. **Install dependencies:**
```bash
pip install -r requirements.txt

```


2. **Ensure Ollama is running locally with `llama3` available:**
```bash
ollama pull llama3

```


3. **Start the FastAPI backend:**
```bash
uvicorn app.main:app --reload

```


4. **In a second terminal, start the Streamlit dashboard:**
```bash
streamlit run ui/dashboard.py

```



