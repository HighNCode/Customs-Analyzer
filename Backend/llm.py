# llm.py
import requests
import json
from openai import OpenAI
import os
from dotenv import load_dotenv
import re

load_dotenv()

# Initialize OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENAI_API_KEY")
)

# this fucker will be used to generate sql queries
SQL_MODEL = "openai/gpt-oss-20b:free"

# this fucker is my eyes and ears for analysis
ANALYSIS_MODEL = "tngtech/deepseek-r1t2-chimera:free"  

def generate_llm_response(system_prompt: str, user_prompt: str, model: str = SQL_MODEL):
    #this fucker will be used to generate sql queries
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

def stream_llm_analysis(prompt: str, model: str = ANALYSIS_MODEL):
    
    try:
        print(f"🤖 Using model: {model}")
        
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            stream=True,
            temperature=0.7,
            max_tokens=2000
        )
        
        in_thinking = False
        buffer = ""
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                
                # Handle DeepSeek R1 thinking tags if using that model
                if "deepseek" in model.lower() or "r1" in model.lower():
                    # Buffer content to detect thinking tags
                    buffer += content
                    
                    # Check for thinking tag boundaries
                    if "<think>" in buffer:
                        in_thinking = True
                        buffer = buffer.split("<think>", 1)[-1]
                        continue
                    
                    if "</think>" in buffer:
                        in_thinking = False
                        buffer = buffer.split("</think>", 1)[-1]
                        continue
                    
                    if not in_thinking and buffer:
                        yield_content = buffer
                        buffer = ""
                        if yield_content.strip():
                            print(f"📤 Yielding: {yield_content[:50]}...")  # Debug
                            yield yield_content
                else:
                    if content.strip():
                        print(f"📤 Yielding: {content[:50]}...")  # Have to improve this
                        yield content
        
        if buffer.strip() and not in_thinking:
            print(f"📤 Yielding final: {buffer[:50]}...")
            yield buffer
                
    except Exception as e:
        print(f"❌ Streaming Error: {e}")
        yield f"Error generating analysis: {str(e)}"


def stream_llm_analysis_fallback(prompt: str):
    
    try:
        print("🔄 Using fallback non-streaming analysis...")
        
        response = client.chat.completions.create(
            model=ANALYSIS_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        
        # Remove thinking tags if present
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
        
        # Yield content in chunks for smoother display
        chunk_size = 50
        for i in range(0, len(content), chunk_size):
            yield content[i:i+chunk_size]
            
    except Exception as e:
        print(f"❌ Fallback Error: {e}")
        yield f"Error generating analysis: {str(e)}"

#below is the previous implementation using Ollama and OpenRouter
# # llm.py
# import requests
# import json
# from openai import OpenAI
# import os
# from dotenv import load_dotenv

# load_dotenv()

# # Initialize OpenRouter client
# client = OpenAI(
#     base_url="https://openrouter.ai/api/v1",
#     api_key=os.getenv("OPENAI_API_KEY")
# )

# OLLAMA_URL = "http://localhost:11434/api/generate"

# def check_ollama():
#     try:
#         response = requests.get(OLLAMA_URL, timeout=2)
#         return response.status_code == 200
#     except:
#         return False

# def stream_llm(prompt: str, model: str = "deepseek-llm:7b"):
#     payload = {
#         "model": model,
#         "prompt": prompt,
#         "stream": True
#     }

#     with requests.post(OLLAMA_URL, json=payload, stream=True) as response:
#         response.raise_for_status()
#         for line in response.iter_lines():
#             if line:
#                 try:
#                     data = json.loads(line.decode("utf-8"))
#                     # Extract just the response token
#                     if "response" in data:
#                         yield data["response"]
#                     # Stop if done
#                     if data.get("done", False):
#                         break
#                 except json.JSONDecodeError:
#                     continue

# def call_llm(system_prompt: str, user_prompt: str, model: str = "deepseek-llm:7b"):
#     payload = {
#         "model": model,
#         "system": system_prompt,
#         "prompt": user_prompt,
#         "stream": False
#     }

#     response = requests.post(OLLAMA_URL, json=payload)
#     response.raise_for_status()
    
#     # Ollama returns whole response as "message"
#     return response.json().get("response", "")

# DEFAULT_MODEL = "openai/gpt-oss-20b:free"  # CHANGE TO WHATEVER MODEL YOU WANT

# def generate_llm_response(system_prompt: str, user_prompt: str, model: str = DEFAULT_MODEL):
#     try:
#         response = client.chat.completions.create(
#             model=model,
#             messages=[
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user", "content": user_prompt}
#             ]
#         )
#         return response.choices[0].message.content
    
#     except Exception as e:
#         print("LLM Error:", e)
#         return None
