"""Test GPT-5.2 API"""
import os
from dotenv import load_dotenv
from openai import OpenAI
import json

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

print("=== Testing GPT-5.2 ===")
try:
    response = client.chat.completions.create(
        model="gpt-5.2",
        messages=[{"role": "user", "content": "Say 'GPT-5.2 works!' in JSON format"}],
        max_completion_tokens=50
    )
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"Error with gpt-5.2: {e}")

print("\n=== Testing GPT-5.2 with JSON mode ===")
try:
    response = client.chat.completions.create(
        model="gpt-5.2",
        messages=[{"role": "user", "content": "Return a JSON object with 'status' and 'message' keys"}],
        max_completion_tokens=50,
        response_format={"type": "json_object"}
    )
    result = response.choices[0].message.content
    print(f"Response: {result}")
    data = json.loads(result)
    print(f"Parsed: {data}")
except Exception as e:
    print(f"Error: {e}")
