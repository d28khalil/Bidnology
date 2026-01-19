"""Compare detail level across GPT models with the same prompt"""
import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

# Handle UTF-8 encoding for Windows console
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# The same prompt for all models
TEST_PROMPT = """Please provide a comprehensive analysis of Washington Township Morris County NJ R-1/R-2 zoning bulk requirements.

Specifically find:
1. Minimum lot area for R-1/R-2 zone
2. Front yard setback requirement
3. Side yard setback requirements
4. Rear yard setback requirement
5. Maximum lot coverage percentage

Source your findings from official zoning ordinances. Be thorough and cite specific code sections."""

MODELS_TO_TEST = ["gpt-4o", "gpt-4-turbo", "gpt-5", "gpt-5.1", "gpt-5.2"]

print("=" * 80)
print("COMPARING MODEL DETAIL LEVELS")
print("=" * 80)

for model in MODELS_TO_TEST:
    print(f"\n{'=' * 80}")
    print(f"MODEL: {model}")
    print("=" * 80)

    try:
        # GPT-5+ uses max_completion_tokens, earlier models use max_tokens
        token_param = "max_completion_tokens" if model.startswith("gpt-5") else "max_tokens"
        # GPT-5 only supports temperature=1
        temp = 1 if model.startswith("gpt-5") else 0

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert zoning analyst. Provide detailed, thorough analysis with specific citations. Be exhaustive in your research."
                },
                {"role": "user", "content": TEST_PROMPT}
            ],
            **{token_param: 4000},
            temperature=temp
        )

        content = response.choices[0].message.content
        tokens = response.usage.total_tokens

        print(content)
        print(f"\n--- Tokens: {tokens} ---")

    except Exception as e:
        print(f"ERROR: {e}")

print("\n" + "=" * 80)
print("COMPARISON COMPLETE")
print("=" * 80)
