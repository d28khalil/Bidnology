"""Test OpenAI API models"""
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
print(f"API Key: {api_key[:20]}...")

client = OpenAI(api_key=api_key)

print("\n=== Testing available models ===")

# Try to list models
try:
    models = client.models.list()
    gpt_models = [m for m in models.data if 'gpt' in m.id.lower()]
    print(f"\nFound {len(gpt_models)} GPT models:")
    for m in sorted(gpt_models, key=lambda x: x.id)[-20:]:  # Show last 20
        print(f"  - {m.id}")
except Exception as e:
    print(f"Error listing models: {e}")

# Test a simple completion with gpt-4o
print("\n=== Testing gpt-4o ===")
try:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Say 'GPT-4o works!' in JSON format"}],
        max_tokens=50
    )
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"Error with gpt-4o: {e}")

# Test GPT-5 if available
print("\n=== Testing gpt-5 ===")
try:
    response = client.chat.completions.create(
        model="gpt-5",
        messages=[{"role": "user", "content": "Say 'GPT-5 works!' in JSON format"}],
        max_tokens=50
    )
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"Error with gpt-5: {e}")
