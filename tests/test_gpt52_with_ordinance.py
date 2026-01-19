"""Test GPT-5.2 with retrieved ordinance text for property 2279"""
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

# Retrieved ordinance text from eCode360
ORDINANCE_TEXT = """
WASHINGTON TOWNSHIP MORRIS COUNTY NJ ZONING ORDINANCE - CHAPTER 217

=== USE REGULATIONS (§ 217-11 R-1/R-2 Single-Family Residential Zone) ===
Principal permitted uses: same as R-5
Permitted accessory uses: same as R-5
Conditional uses: same as R-5

=== SUPPLEMENTARY LOT, HEIGHT AND YARD REGULATIONS (§ 217-31 through § 217-39) ===

§ 217-31 Lot regulations:
- All lots within the R-1 Zone and R-1/R-2 Zone created in a subdivision must have a minimum improvable lot area of 7,500 square feet (within the setbacks)

§ 217-32 Height regulations:
- No building shall exceed 35 feet in height

§ 217-33 Yard regulations:
- For buildings other than single-family dwellings, minimum front yard: 40 feet
- For single-family dwellings, front yard shall be the average front yard of the two nearest adjacent buildings, but no less than 25 feet
- Minimum side yard for each side: 15 feet for single-family dwellings
- Minimum rear yard: 30 feet

§ 217-34 Improved lot coverage:
- The maximum improved lot coverage shall include all impervious surfaces such as buildings, structures, driveways, tennis courts and patios
- Maximum improved lot coverage varies by zone

§ 217-35 Number of buildings restricted:
- Only one principal residential building permitted per lot

§ 217-36 Setbacks from stream corridors and state open waters:
- A 25-foot wide easement shall be required along each side of all streams

§ 217-37 Flag lots:
- Minimum pole width: 20 feet
- Minimum flag width: 60 feet

§ 217-38 Steep slopes, ridgeline, mountainside, hillside and viewshed protection areas:
- 15% to 20% slopes: special review required
- Over 20% slopes: no permitted disturbance
- Ridgeline protection: 100-foot buffer zone, 60-foot no-disturbance area

§ 217-39 Minimum lot requirements where public water and sewer are not proposed:
- Where connection to public water and a public sanitary sewer system are not proposed, no lot in a residential zone shall be created which does not meet the bulk requirements of the R-1/R-2 Zone or the zone in which they are actually located, whichever is greater.

§ 217-39.1 Resource conservation calculations:
- Impervious coverage calculations for steep slopes and conservation areas
"""

# Property details
PROPERTY_DETAILS = """
PROPERTY: 51 Winay Terrace, Washington Twp, Long Valley, NJ 07853
- Property ID: 2279
- Zoning: R-1/R-2 Single-Family Residential Zone
- Lot Size: 0.624 acres (27,186 sq ft)
- Building Size: 2,618 sq ft
- Year Built: 1984
- Last Sale Price: $589,000
- Current Assessed: $471,900

NOTE: The specific Schedule of Area, Yard and Building Requirements (§ 217-29) was not accessible
through web sources. The PDF is corrupted and the eCode360 direct link is blocked. The above
ordinance text represents all available information from accessible sources.
"""

SYSTEM_PROMPT = """You are an expert real estate analyst and zoning specialist. Your task is to provide
thorough, detailed analysis with specific numerical requirements and practical recommendations.

You have been provided with:
1. Retrieved ordinance text from Washington Township Morris County NJ
2. Property details for 51 Winay Terrace

IMPORTANT: The Schedule of Area, Yard and Building Requirements (§ 217-29) was NOT accessible -
the PDF is corrupted and eCode360 direct link is blocked. Please work with the available
ordinance text and note any limitations or missing information.

Provide:
1. Zoning analysis based on available ordinance text
2. Investment strategy recommendations
3. Regulatory constraints
4. Missing information that would be needed for complete analysis
5. Recommended next steps to obtain complete Schedule information
"""

USER_PROMPT = f"""{PROPERTY_DETAILS}

{ORDINANCE_TEXT}

Please provide a comprehensive deep dive investment analysis for this property, working with
the available ordinance text. Be explicit about:

1. What bulk requirements ARE known from the available text
2. What bulk requirements are MISSING (from § 217-29 Schedule)
3. How the property compares to known requirements
4. Investment strategies that appear feasible
5. What additional information is needed and how to obtain it
6. Whether you can provide any guidance on typical R-1/R-2 requirements in NJ municipalities
"""

print("=" * 80)
print("GPT-5.2 ANALYSIS WITH RETRIEVED ORDINANCE TEXT")
print("=" * 80)

try:
    response = client.chat.completions.create(
        model="gpt-5.2",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT}
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
