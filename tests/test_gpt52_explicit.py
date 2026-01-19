"""Test GPT-5.2 with extremely explicit prompting"""
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

# EXTREMELY explicit prompt that leaves no ambiguity
EXPLICIT_SYSTEM_PROMPT = """You are the most thorough zoning research analyst. Your task is to provide comprehensive, detailed analysis with:
1. Specific numerical requirements
2. Exact code citations
3. All relevant details and nuances
4. No hedging or asking for clarification - the municipality IS specified

When given a specific municipality with county and state, proceed with analysis using your training data. Do NOT ask for clarification or links."""

EXPLICIT_USER_PROMPT = """This is a specific request about ONE municipality. DO NOT ask for clarification. The municipality is:

WASHINGTON TOWNSHIP, MORRIS COUNTY, NEW JERSEY (also known as Long Valley, NJ)
- NOT Bergen County
- NOT Warren County
- NOT Gloucester County
- Morris County ONLY

ZONING DISTRICTS TO ANALYZE: R-1/R-2 Single-Family Residential Zone (as designated in Washington Township Morris County NJ Code Chapter 217)

Provide a comprehensive analysis of ALL bulk requirements for the R-1/R-2 zone:

## REQUIRED OUTPUT - Provide ALL of the following:

### 1. MINIMUM LOT AREA
- Minimum lot area in square feet (with public water & sewer)
- Minimum lot area in square feet (with well & septic)
- Source citation

### 2. FRONT YARD SETBACK
- Minimum front yard setback in feet
- Any exceptions or variations
- Source citation

### 3. SIDE YARD SETBACKS
- Minimum side yard for EACH side in feet
- Minimum COMBINED side yards in feet (if applicable)
- Source citation

### 4. REAR YARD SETBACK
- Minimum rear yard setback in feet
- Any exceptions or variations
- Source citation

### 5. MAXIMUM LOT COVERAGE
- Maximum building/lot coverage percentage
- Whether this includes impervious surfaces or just buildings
- Source citation

### 6. ADDITIONAL REQUIREMENTS
- Maximum building height
- Minimum lot width
- Any other relevant bulk requirements

## SOURCES TO CITE:
Washington Township Morris County NJ Code Chapter 217 Zoning, specifically:
- § 217-11 R-1/R-2 Single-Family Residential Zone
- § 217-29 Schedule of Area, Yard and Building Requirements
- Any related sections

PROCEED WITH ANALYSIS. Do NOT ask for clarification. The municipality is Washington Township, Morris County, New Jersey."""

print("=" * 80)
print("TESTING GPT-5.2 WITH EXTREMELY EXPLICIT PROMPT")
print("=" * 80)

try:
    response = client.chat.completions.create(
        model="gpt-5.2",
        messages=[
            {"role": "system", "content": EXPLICIT_SYSTEM_PROMPT},
            {"role": "user", "content": EXPLICIT_USER_PROMPT}
        ],
        max_completion_tokens=8000,
        temperature=1
    )

    content = response.choices[0].message.content
    tokens = response.usage.total_tokens

    print("\n" + "=" * 80)
    print("GPT-5.2 RESPONSE:")
    print("=" * 80)
    print(content)
    print("\n" + "=" * 80)
    print(f"TOTAL TOKENS: {tokens}")
    print("=" * 80)

except Exception as e:
    print(f"\nERROR: {e}")

# Also test with a simpler direct approach
print("\n\n" + "=" * 80)
print("TESTING GPT-5.2 WITH SIMPLER DIRECT APPROACH")
print("=" * 80)

SIMPLE_PROMPT = """You are researching Washington Township Morris County NJ zoning ordinances. Specifically Chapter 217 Zoning.

What are the R-1/R-2 zone bulk requirements? Provide:
1. Minimum lot area
2. Front yard setback
3. Side yard setbacks
4. Rear yard setback
5. Maximum lot coverage

Cite the specific code sections. Be thorough and provide exact numbers.

This is Washington Township in Morris County NJ (Long Valley area). Proceed with your analysis based on your training data."""

try:
    response = client.chat.completions.create(
        model="gpt-5.2",
        messages=[
            {"role": "system", "content": "You are an expert zoning analyst. Provide detailed analysis with specific code citations and exact numerical requirements."},
            {"role": "user", "content": SIMPLE_PROMPT}
        ],
        max_completion_tokens=4000,
        temperature=1
    )

    content = response.choices[0].message.content
    tokens = response.usage.total_tokens

    print("\n" + "=" * 80)
    print("GPT-5.2 SIMPLE RESPONSE:")
    print("=" * 80)
    print(content)
    print("\n" + "=" * 80)
    print(f"TOTAL TOKENS: {tokens}")
    print("=" * 80)

except Exception as e:
    print(f"\nERROR: {e}")
