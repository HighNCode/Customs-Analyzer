# llm.py
import requests
import json
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENAI_API_KEY")
)

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

def call_llm(system_prompt: str, user_prompt: str, model: str = "deepseek-llm:7b"):
    payload = {
        "model": model,
        "system": system_prompt,
        "prompt": user_prompt,
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload)
    response.raise_for_status()
    
    # Ollama returns whole response as "message"
    return response.json().get("response", "")

DEFAULT_MODEL = "openai/gpt-oss-20b:free"  # CHANGE TO WHATEVER MODEL YOU WANT

def generate_llm_response(system_prompt: str, user_prompt: str, model: str = DEFAULT_MODEL):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.choices[0].message.content
    
    except Exception as e:
        print("LLM Error:", e)
        return None
