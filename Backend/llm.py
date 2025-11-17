# llm.py
import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"

def check_ollama():
    try:
        response = requests.get(OLLAMA_URL, timeout=2)
        return response.status_code == 200
    except:
        return False

def stream_llm(prompt: str, model: str = "deepseek-llm:7b"):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True
    }

    with requests.post(OLLAMA_URL, json=payload, stream=True) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode("utf-8"))
                    # Extract just the response token
                    if "response" in data:
                        yield data["response"]
                    # Stop if done
                    if data.get("done", False):
                        break
                except json.JSONDecodeError:
                    continue

def call_llm(prompt: str, model: str = "deepseek-llm:7b"):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(OLLAMA_URL, json=payload)
    response.raise_for_status()
    return response.json().get("response", "")