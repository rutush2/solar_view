import requests
from app.config import OLLAMA_URL, OLLAMA_MODEL


def diagnose_live_window(summary_text: str) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": f"Analyze these live solar inverter metrics in 2 concise sentences (no code blocks):\n{summary_text}",
            "stream": False
        },
        timeout=60
    )
    if not response.ok:
        raise RuntimeError(f"Ollama error ({response.status_code}): {response.text}")
    return response.json().get("response", "").strip()