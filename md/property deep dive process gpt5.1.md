# Property Deep Dive Process - GPT-5.1

## Overview

Automated real estate investment analysis workflow that combines free APIs with AI to generate comprehensive zoning and investment feasibility reports for any property.

---

## Cost Summary

| Scale | Cost |
|-------|------|
| **Per Property** | ~$0.04 (4 cents) |
| **100 properties/week** | ~$4.20/week |
| **Monthly (100 props)** | ~$18/month |
| **Annual (100 props)** | **~$220/year** |

---

## Step-by-Step Workflow

### Step 1: Geocoding (Nominatim - Free API)

**Purpose:** Convert address to coordinates and municipality data

**Input:** Property address

**Returns:**
- Latitude
- Longitude
- Municipality
- County

**API:** OpenStreetMap Nominatim (free, no API key required)

---

### Step 2: Zoning Lookup (Gemini 2.5 Pro)

**Purpose:** Search official government sources for zoning information

**Input:**
- Property address
- Municipality
- County
- Coordinates

**Searches:**
- Municipal zoning ordinances and zoning maps
- County GIS / Parcel Viewer
- Municipal code

**Excludes:** Commercial real estate sites (Zillow, LoopNet, etc.)

**Returns:**
```json
{
    "zoning_district": "official zoning code or 'Unknown'",
    "zoning_description": "from municipal ordinance or null",
    "lot_size": "size or null",
    "zoning_map_url": "direct URL or null",
    "confidence": "HIGH/MEDIUM/LOW"
}
```

**Cost:** ~$0.0006 per lookup

**Model:** `models/gemini-2.5-pro`

---

### Step 3: Deep Dive Analysis (GPT-5.1)

**Purpose:** Generate comprehensive investment analysis using gathered data

**Input:**
- Property context (address, coordinates, location)
- Zoning data (district, description, lot size)

**Prompt Requirements:**
```
Provide a deep-dive analysis on:

1. Possible real estate investment strategies (rank best to worst)
2. What the zoning likely allows or would allow (clearly label assumptions)
3. Typical bulk and setback requirements and how they impact buildable area
4. Highest and best use scenarios with pros, cons, and risk
5. A verification checklist stating what must be confirmed with the municipality
6. Auction Price Analysis & Maximum Bid Threshold (if upset amount provided)
```

**Returns:**
- Ranked investment strategies with pros/cons/risks
- Zoning allowances and constraints
- Bulk requirements with buildable envelope calculations
- Highest & Best Use scenarios
- Detailed verification checklist for municipality
- Price analysis and maximum bid threshold (when applicable)

**Cost:** ~$0.04 per property

**Model:** `gpt-5.1` via Responses API

**Settings:**
- `max_output_tokens: 8000`
- `temperature: 1`

---

### Step 4: Export to Word Document (Optional)

**Purpose:** Create formatted Word document with full analysis

**Output:** `.docx` file on desktop with:
- Title page with property details
- All analysis sections
- Proper formatting (headings, bullet points, bold text)

**Tool:** python-docx (free)

---

## API Keys & Configuration

### Required API Keys

| Service | API Key Location | Purpose |
|---------|------------------|---------|
| OpenAI | `OPENAI_API_KEY` in .env | GPT-5.1 access |
| Gemini | Hardcoded in script | Gemini 2.5 Pro zoning lookup |

### Gemini Model
- **Model:** `models/gemini-2.5-pro`
- **Pricing:** $1.25/1M input tokens, $2.50/1M output tokens
- **Package:** `google.generativeai` (deprecated, consider migrating to `google.genai`)

### GPT-5.1 Model
- **Model:** `gpt-5.1`
- **API:** Responses API (`client.responses.create`)
- **Pricing:** $1.25/1M input tokens, $10/1M output tokens
- **Important:** Use `max_completion_tokens` or `max_output_tokens` (NOT `max_tokens`)

---

## Tools & Libraries

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Runtime |
| openai | Latest | OpenAI API client |
| google-generativeai | Latest | Gemini API client |
| python-docx | Latest | Word document generation |
| python-dotenv | Latest | Environment variables |

---

## File Structure

```
C:\Projects\salesweb-crawl\
├── property deep dive process gpt5.1.md   (this file - documentation)
├── test_gpt51_real_property.py            (main script)
└── .env                                    (API keys)

Desktop\
├── kearny_analysis_word.py                (Word export script - optional)
└── [Property]_Analysis.docx               (generated Word output - optional)
```

---

## Token Usage Breakdown

### Typical Property Analysis

| Component | Input Tokens | Output Tokens | Cost |
|-----------|--------------|---------------|------|
| Gemini 2.5 Pro | ~240 | ~130 | $0.0006 |
| GPT-5.1 | ~260 | ~4,100 | $0.0410 |
| **Total** | **~500** | **~4,230** | **~$0.042** |

### Cost per Property

| Model | Input Cost | Output Cost | Total |
|-------|-----------|-------------|-------|
| Gemini 2.5 Pro | $0.0003 | $0.0003 | $0.0006 |
| GPT-5.1 | $0.0003 | $0.0410 | $0.0413 |
| **Grand Total** | | | **$0.042** |

---

## Sample Output

### Property Analyzed: 151 Seeley Avenue, Kearny, NJ 07032

**Data Gathered:**
- Zoning: R-1 (One-Family Residential)
- Lot Size: 0.092 acres (4,000 sq ft)
- Lot Dimensions: 40 ft x 100 ft
- Source: Gemini 2.5 Pro

**Analysis Sections:**
1. Ranked Investment Strategies
2. Zoning Allowances
3. Bulk & Setback Requirements
4. Highest & Best Use Scenarios
5. Verification Checklist

**Token Usage:** 4,387 total tokens
**Actual Cost:** $0.042

---

## Usage Instructions

### Running Analysis for New Property

1. Open `test_gpt51_real_property.py`
2. Update the address in two places:
   - Step 1: Geocoding section (Nominatim query)
   - Step 2: Gemini zoning prompt (property address)
   - Step 3: GPT-5.1 prompt (if upset amount needed)
3. Run: `python test_gpt51_real_property.py`

### Exporting to Word

1. Copy the GPT-5.1 output
2. Paste into `kearny_analysis_word.py` content variable
3. Run: `python kearny_analysis_word.py`
4. Word document saved to Desktop

---

## Important Notes

### GPT-5.1 API Behavior

- **Use Responses API:** `client.responses.create` (NOT `client.chat.completions.create`)
- **Parameter:** `max_output_tokens` (NOT `max_tokens`)
- **Temperature:** Must be `1` for GPT-5.1

### Gemini Model Names

- Current working model: `models/gemini-2.5-pro`
- Older names like `gemini-1.5-pro` and `gemini-pro` no longer work
- Use `genai.list_models()` to see available models

### Zoning Data Availability

- **Gemini Search:** Searches official government sources (municipal zoning ordinances, county GIS, municipal codes)
- **Commercial Sites Excluded:** Zillow, LoopNet, and other commercial real estate sites are explicitly excluded from search
- **Accuracy:** Varies by municipality - some have excellent online records, others have limited or outdated information

### Data Limitations

- **Property Details:** This workflow focuses on zoning analysis. Building size, property type, condition, and other details are NOT gathered
- **Assumption-Based:** GPT-5.1 analysis makes reasonable assumptions based on zoning when property-specific details are unavailable
- **Verification Required:** Always verify zoning and bulk requirements directly with the municipality before making investment decisions

---

## Future Improvements

### Potential Enhancements

- [ ] Add county tax record API for building details
- [ ] Add FEMA flood zone lookup
- [ ] Add school district data
- [ ] Add property type detection (residential vs commercial vs industrial)
- [ ] Migrate to `google-genai` package (deprecated warning)
- [ ] Create unified script that accepts address as CLI argument

### Cost Optimization

- Consider **GPT-5 Mini** ($0.009/property) for faster/cheaper analysis
- Consider **gpt-4o-mini** ($0.007/property) as alternative
- Current **GPT-5.1** provides highest quality at $0.04/property

---

## Troubleshooting

### Issue: GPT-5.1 returns empty content

**Solution:** Use Responses API with `max_output_tokens` parameter:
```python
response = client.responses.create(
    model="gpt-5.1",
    input=[...messages...],
    max_output_tokens=8000,
    temperature=1
)
text = response.output_text
```

### Issue: Gemini returns incorrect zoning

**Solution:** Gemini search accuracy varies by municipality. Some towns have excellent online zoning resources, others don't. Always verify zoning information directly with the municipality before making investment decisions.

### Issue: Gemini API key leaked/revoked

**Error:** `403 Your API key was reported as leaked`

**Solution:** Generate new API key from https://aistudio.google.com/app/apikey

### Issue: "models/gemini-1.5-pro is not found"

**Solution:** Use `models/gemini-2.5-pro` or `models/gemini-2.5-flash` instead

---

## Version History

| Date | Change |
|------|--------|
| 2025-01-18 | Simplified workflow - Gemini zoning search only, removed NJ GeoWeb and property research |
| 2025-01-17 | Initial documentation - GPT-5.1 + Gemini 2.5 Pro workflow |

---

## Contact

Questions or issues? Refer to:
- Project: `C:\Projects\salesweb-crawl\`
- Main script: `test_gpt51_real_property.py`
- Documentation: `property deep dive process gpt5.1.md` (this file)
