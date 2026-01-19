"""Test GPT-5.1 with detailed prompting to match Claude's level of detail"""
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Comprehensive system prompt to encourage detailed analysis
SYSTEM_PROMPT = """You are an expert real estate analyst and zoning specialist. Your task is to provide
thorough, detailed analysis with:

1. Multi-source research - cite specific sources
2. Structured breakdowns with clear sections
3. Specific numerical requirements (setbacks, lot sizes, coverage)
4. Practical implications and recommendations
5. Missing information gaps and next steps

Be exhaustive. If information isn't immediately available, explain what you're looking for
and where it might be found. Provide the same level of detail an expert consultant would."""

# The detailed research prompt
USER_PROMPT = """Please provide a comprehensive deep dive investment analysis for the following property:

PROPERTY DETAILS:
- Address: 51 Winay Terrace, Washington Twp, Long Valley, NJ 07853
- Property ID: 2279
- Zoning: R-1/R-2 Single-Family Residential Zone
- Lot Size: 0.624 acres (27,186 sq ft)
- Building Size: 2,618 sq ft
- Year Built: 1984
- Last Sale Price: $589,000
- Current Assessed: $471,900

ANALYSIS REQUESTED:
1. Zoning Analysis:
   - What does R-1/R-2 zoning specifically allow?
   - What are the bulk requirements (minimum lot area, front/side/rear yard setbacks)?
   - What is the maximum improved lot coverage percentage?
   - Are there special overlays or constraints?

2. Investment Strategies:
   - Renovate & Resell potential
   - Accessory Dwelling Unit (ADU) feasibility
   - Expansion/Addition opportunities
   - Land subdivision potential

3. Regulatory Constraints:
   - Height restrictions
   - Setback requirements
   - Coverage limits
   - Environmental constraints (wetlands, steep slopes, ridgelines)

4. Specific Questions:
   - What can be built on this property?
   - What are the bulk zone setbacks?
   - What is the better use for this property?
   - What are the constraints and opportunities?

Please source your findings from official Washington Township Morris County NJ zoning ordinances
and provide specific code sections where applicable. Be thorough and cite your sources."""

print("=" * 70)
print("Testing GPT-5.1 with Detailed Prompt")
print("=" * 70)

try:
    response = client.chat.completions.create(
        model="gpt-5.1",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT}
        ],
        max_tokens=8000,
        temperature=0
    )
    print("\n" + "=" * 70)
    print("GPT-5.1 RESPONSE:")
    print("=" * 70)
    print(response.choices[0].message.content)
    print("\n" + "=" * 70)
    print(f"Tokens used: {response.usage.total_tokens}")
    print("=" * 70)
except Exception as e:
    print(f"Error with gpt-5.1: {e}")

# Also try with even more explicit instructions
print("\n" + "=" * 70)
print("Testing GPT-5.1 with EXTREMELY Detailed Prompt")
print("=" * 70)

EXTREME_USER_PROMPT = """You are conducting professional due diligence on a real estate investment.
This requires exhaustive research.

PROPERTY: 51 Winay Terrace, Washington Twp, Long Valley, NJ 07853
ZONING: R-1/R-2 Single-Family Residential

TASK: Research and report on ALL of the following:

## PART 1: ZONING CODE RESEARCH
Search for and analyze the official Washington Township Morris County NJ zoning ordinances,
specifically:
- Chapter 217 Zoning Ordinance
- § 217-11 R-1/R-2 Single-Family Residential Zone regulations
- § 217-29 Schedule of Area, Yard and Building Requirements
- § 217-31 through § 217-39 Supplementary Regulations

Find and report:
- Minimum lot area requirements
- Front yard setback distance
- Side yard setback distances (each side)
- Rear yard setback distance
- Maximum lot coverage percentage
- Minimum lot width
- Maximum building height

## PART 2: PERMITTED USES
List ALL permitted uses in R-1/R-2 zone:
- Principal permitted uses
- Accessory uses
- Conditional uses
- Prohibited uses

## PART 3: DEVELOPMENT CONSTRAINTS
Identify ALL constraints that could affect this property:
- Floodplain requirements
- Steep slope restrictions (15%+ slopes)
- Ridgeline protection areas
- Stream corridor setbacks
- Conservation easements
- Highlands preservation area requirements

## PART 4: INVESTMENT ANALYSIS
For EACH strategy below, provide:
- Feasibility (allowed/not allowed under zoning)
- Estimated costs
- Potential returns
- Required approvals
- Timeline

Strategies to analyze:
A. Renovate and hold as rental
B. Renovate and resell
C. Add accessory apartment/ADU
D. Build addition/expansion
E. Subdivide property
F. Tear down and rebuild

## PART 5: SOURCES
Cite ALL sources with:
- Document name
- Section/code reference
- URL where applicable

Be exhaustive. If you cannot find specific information, explicitly state what is missing
and suggest where it might be found."""

try:
    response = client.chat.completions.create(
        model="gpt-5.1",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": EXTREME_USER_PROMPT}
        ],
        max_tokens=16000,
        temperature=0
    )
    print("\n" + "=" * 70)
    print("GPT-5.1 EXTREME RESPONSE:")
    print("=" * 70)
    print(response.choices[0].message.content)
    print("\n" + "=" * 70)
    print(f"Tokens used: {response.usage.total_tokens}")
    print("=" * 70)
except Exception as e:
    print(f"Error with gpt-5.1 extreme prompt: {e}")
