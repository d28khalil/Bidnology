# Zoning API Feature Summary

## Overview

The Zoning API feature is an enrichment system for NJ foreclosure properties that combines geocoding, municipal zoning data retrieval, and GPT-5.2 AI analysis to provide comprehensive investment analysis reports.

## What We're Attempting to Do

### Problem Statement

When analyzing foreclosure properties for investment potential, critical zoning information is scattered across multiple sources:
- Municipal zoning codes (often in PDFs or proprietary systems)
- County GIS databases
- Township websites
- Third-party code hosting platforms (eCode360)

Investors need to know:
- What can be built on a property?
- What are the bulk requirements (setbacks, lot coverage, height limits)?
- What investment strategies are feasible (ADU, subdivision, expansion)?
- What regulatory constraints exist?

### Solution Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Property       │ -> │  Geocoding      │ -> │  County         │
│  Address        │    │  + County Det.  │    │  Detection      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        v
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Investment     │ <- │  GPT-5.2        │ <- │  Zoning Data    │
│  Report         │    │  Analysis       │    │  Retrieval      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Key Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Geocoding** | Nominatim/MapQuest | Convert address to coordinates + extract county |
| **Zoning Detection** | NJ GeoWeb API | Determine zoning district from parcel data |
| **Ordinance Retrieval** | eCode360, Township sites | Fetch zoning ordinance text |
| **AI Analysis** | GPT-5.1/5.2 | Interpret regulations + provide investment advice |

---

## GPT-5.1/5.2 Summary Functionality

### Model Comparison

| Aspect | GPT-5.1 | GPT-5.2 |
|--------|---------|---------|
| **Analysis Approach** | Uses training data, provides specific numbers | Requires verified ordinance sources |
| **Detail Level** | High - provides setbacks, lot areas, coverage | Highest - but only with verified sources |
| **Without Sources** | Will provide analysis from training data | Refuses to analyze without sources |
| **max_tokens Parameter** | ✅ Supported | ❌ Use `max_completion_tokens` instead |
| **temperature Range** | 0-2 | Only supports `1` |

### Why GPT-5.2?

GPT-5.2 provides the most accurate analysis because it:
1. **Refuses to hallucinate** - Won't make up zoning requirements
2. **Requires citations** - Demands verified ordinance sources
3. **Provides detailed analysis** - When given sources, delivers comprehensive reports

The challenge: GPT-5.2 requires actual ordinance text, not just property details.

---

## Summary Input Structure

### Input to GPT-5.2

```python
# 1. Property Details
PROPERTY_DETAILS = """
PROPERTY: {address}
- Property ID: {id}
- Zoning: {zoning_district}
- Lot Size: {lot_size}
- Building Size: {building_size}
- Year Built: {year}
- Last Sale Price: {sale_price}
- Current Assessed: {assessed_value}
"""

# 2. Retrieved Ordinance Text
ORDINANCE_TEXT = """
{MUNICIPALITY} ZONING ORDINANCE - CHAPTER {chapter}

=== USE REGULATIONS (§ {section}) ===
{permitted_uses_text}

=== SUPPLEMENTARY REGULATIONS (§ {sections}) ===
{lot_regulations}
{height_regulations}
{yard_regulations}
{coverage_regulations}
{environmental_constraints}
"""

# 3. System Prompt
SYSTEM_PROMPT = """You are an expert real estate analyst and zoning specialist.
Provide thorough, detailed analysis with specific numerical requirements and
practical recommendations."""

# 4. User Prompt
USER_PROMPT = f"""{PROPERTY_DETAILS}

{ORDINANCE_TEXT}

Please provide a comprehensive deep dive investment analysis for this property,
working with the available ordinance text. Be explicit about:
1. What bulk requirements ARE known from the available text
2. What bulk requirements are MISSING
3. How the property compares to known requirements
4. Investment strategies that appear feasible
5. What additional information is needed and how to obtain it
"""
```

### API Call Pattern

```python
response = client.chat.completions.create(
    model="gpt-5.2",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT}
    ],
    max_completion_tokens=8000,  # Different from max_tokens
    temperature=1  # GPT-5 only supports temperature=1
)
```

---

## Current Progress Position

### ✅ Completed Tasks

| Task | Status | Notes |
|------|--------|-------|
| **GPT Model Comparison** | ✅ Complete | Tested 4o, 4-turbo, 5, 5.1, 5.2 |
| **Geocoding Enhancement** | ✅ Complete | County extraction for accurate municipality ID |
| **Zoning Data Retrieval** | ✅ Complete | NJ GeoWeb + eCode360 integration |
| **Use Regulations Retrieved** | ✅ Complete | R-1/R-2 permitted uses from eCode360 |
| **Supplementary Regulations** | ✅ Complete | §§ 217-31 through 217-39 retrieved |

### ⚠️ In Progress / Known Issues

| Issue | Status | Workaround |
|-------|--------|------------|
| **§ 217-29 Schedule PDF** | ❌ Corrupted | Direct contact with township required |
| **eCode360 Direct Link** | ❌ Blocked | Alternative retrieval methods needed |
| **Missing Bulk Requirements** | ⚠️ Partial | Some retrieved, Schedule missing |

### 📋 Pending Tasks

1. **Obtain Complete Schedule Requirements**
   - Contact Washington Township Zoning Officer: 908-876-4711
   - OPRA request for § 217-29 table
   - Alternative: Find cached/third-party sources

2. **Additional County Endpoints**
   - Bergen County
   - Essex County
   - Hudson County
   - Others

3. **Test on Additional Properties**
   - Beyond Property 2279 (51 Winay Terrace)

---

## Analysis Output Example

### What the Report Contains

```
## Zoning Analysis for 51 Winay Terrace

### 1. Known Requirements (from retrieved text)
- Height Limit: 35 feet max
- Front Yard: Average of 2 adjacent buildings, min 25 ft
- Side Yards: 15 ft each (30 ft combined)
- Rear Yard: 30 ft
- Stream Setback: 25 ft easement each side
- Steep Slopes >20%: No permitted disturbance

### 2. Missing Requirements (§ 217-29 Schedule)
- Minimum lot area
- Minimum lot width/frontage
- Maximum improved lot coverage %
- Accessory structure setbacks

### 3. Investment Strategy Assessment
┌─────────────────────┬─────────────┬────────────┐
│ Strategy            │ Feasibility │ Risk Level │
├─────────────────────┼─────────────┼────────────┤
│ Interior Renovation │ High        │ Low        │
│ Modest Addition     │ Medium      │ Moderate   │
│ Accessory Structures│ Unknown     │ Mod-High   │
│ Subdivision         │ Unknown     │ High       │
└─────────────────────┴─────────────┴────────────┘

### 4. Next Steps
- Contact township for Schedule values
- Obtain survey for exact setbacks
- Environmental assessment (wetlands, slopes)
```

---

## Technical Implementation Notes

### Files Created/Modified

| File | Purpose |
|------|---------|
| `test_gpt52_with_ordinance.py` | Test GPT-5.2 with retrieved ordinance text |
| `test_gpt52_explicit.py` | Test with extremely explicit prompting |
| `compare_model_detail.py` | Compare detail levels across models |
| `test_gpt51_detailed.py` | Test GPT-5.1 with detailed prompts |

### Key Technical Concepts

- **NJ GeoWeb**: New Jersey's GIS system for property/zoning data
- **eCode360**: Municipal code hosting platform (ecode360.com)
- **Bulk Requirements**: Zoning technical requirements (lot area, setbacks, coverage)
- **Improved Lot Coverage**: Percentage of lot covered by impervious surfaces
- **Setbacks**: Minimum distances from property lines where building cannot occur
- **R-1/R-2 Zone**: Single-Family Residential Zone designation

---

## Error Handling

### Known Errors and Solutions

| Error | Source | Solution |
|-------|--------|----------|
| **PDF Corrupted** | Township website | Direct contact with township |
| **Access Forbidden** | eCode360 | Use alternative pages or contact township |
| **Wrong Municipality** | Multiple Washington Townships in NJ | County verification critical |
| **Missing Schedule Values** | § 217-29 inaccessible | OPRA request + phone contact |

---

## Next Steps

1. **Immediate**: Contact Washington Township Zoning Officer for Schedule values
2. **Short-term**: Add more county parcel endpoints
3. **Long-term**: Build production API with caching for ordinance text

---

*Last Updated: 2025-01-17*
*Test Property: 2279 (51 Winay Terrace, Washington Twp, Long Valley, NJ 07853)*
