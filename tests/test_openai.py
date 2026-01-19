"""
Quick test of OpenAI API for foreclosure data extraction
"""
import os
from openai import OpenAI

# Load API key from .env file
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

load_env()

# Initialize client
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    print("❌ OPENAI_API_KEY not found in .env file")
    exit(1)

print(f"✅ API Key found: {api_key[:20]}...")

client = OpenAI(api_key=api_key)

# Test with Salem County example
print("\n" + "="*60)
print("Testing OpenAI API with Salem County Example")
print("="*60)

test_description = """Approximate Dimensions: .55 AC
Upset Price: $114,108.21. The upset amount may be subject to further orders of additional sums.
Occupancy Status: Owner Occupied"""

try:
    response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[
            {
                'role': 'system',
                'content': 'You are a foreclosure data expert. Extract the upset price from the description and return only the number.'
            },
            {
                'role': 'user',
                'content': f'Description: {test_description}\n\nWhat is the upset price? Return only the number.'
            }
        ],
        max_tokens=50,
        temperature=0
    )

    result = response.choices[0].message.content.strip()
    print(f"\n✅ SUCCESS! AI extracted: ${result}")

    # Show usage
    if response.usage:
        print(f"\n📊 Token Usage:")
        print(f"  Input: {response.usage.prompt_tokens} tokens")
        print(f"  Output: {response.usage.completion_tokens} tokens")
        print(f"  Total: {response.usage.total_tokens} tokens")

        # Calculate cost
        input_cost = (response.usage.prompt_tokens / 1_000_000) * 0.15
        output_cost = (response.usage.completion_tokens / 1_000_000) * 0.60
        total_cost = input_cost + output_cost
        print(f"\n💰 Cost: ${total_cost:.6f} (less than 1 cent!)")

    print("\n" + "="*60)
    print("✅ OpenAI API is working correctly!")
    print("="*60)

except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nPlease check:")
    print("1. Your OpenAI API key is valid")
    print("2. You have billing set up at https://platform.openai.com/")
    print("3. The API key has proper permissions")
