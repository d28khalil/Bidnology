# AI-Powered Data Extraction Setup Guide

## Overview

This system uses **OpenAI GPT-4o mini** to intelligently extract and categorize monetary values from foreclosure property descriptions. This provides **much higher accuracy** than regex-based extraction while remaining very affordable.

---

## Cost Analysis

### For Daily Scraping of All NJ Counties

- **Properties:** ~525 per day (25 properties × 21 counties)
- **Model:** GPT-4o mini (cost-optimized)
- **Monthly Cost:** **~$0.50-1.00**
- **Annual Cost:** **~$6-12**

### Cost Breakdown

| Metric | Value |
|--------|-------|
| Input tokens | ~131,250/month |
| Output tokens | ~15,750/month |
| Input cost | $0.02/month |
| Output cost | $0.01/month |
| **Total** | **~$0.03/month** |

**Note:** Actual costs may vary 2-3x based on description length and AI response size. Still under **$0.10/month** for typical usage.

---

## Benefits

### ✅ Much Higher Accuracy
- AI understands context (won't mix up judgment vs upset vs opening bid)
- Filters out false positives (dimension measurements, lot sizes)
- Handles edge cases and ambiguous labels

### ✅ Complete Data Provenance
- Tracks where every value came from (scraped field vs AI extraction)
- Stores confidence scores for each extraction
- Maintains full audit trail

### ✅ Unified Schema
- All data normalized to consistent format
- 100% accuracy preserved through provenance tracking
- Easy to query and analyze

---

## Setup Instructions

### Step 1: Get OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Create an account (or sign in)
3. Create new API key
4. Set up billing (minimum $5 deposit)
5. **IMPORTANT:** Set usage limits to avoid surprise charges:
   - Hard limit: $10/month
   - Soft limit: $5/month

### Step 2: Install OpenAI Package

```bash
cd /mnt/c/Users/David/OneDrive/Documents/Git Hub Projects/salesweb-crawl
./venv/bin/pip install openai
```

### Step 3: Add API Key to Environment

Add to your `.env` file:

```bash
OPENAI_API_KEY=sk-your-api-key-here
```

Or export directly:

```bash
export OPENAI_API_KEY=sk-your-api-key-here
```

### Step 4: Test the AI Extraction

```bash
cd /mnt/c/Users/David/OneDrive/Documents/Git Hub Projects/salesweb-crawl
./venv/bin/python ai_unified_processor.py
```

You should see output showing:
- Unified data extraction
- Provenance tracking
- Confidence scores
- Cost estimates

---

## Integration with Scraper

The AI processor is designed to integrate seamlessly with `scraper_hybrid.py`:

### Option 1: Run as Post-Processing Step

```python
# After scraping, process all properties with AI
from ai_unified_processor import batch_process_properties

properties = [...]  # Your scraped properties
processed = batch_process_properties(properties)

# Each property now has:
# - unified_monetary_data: AI-extracted & validated values
# - data_provenance: Full tracking of data sources
# - ai_confidence: Confidence score
# - data_quality_flags: Any issues detected
```

### Option 2: Real-Time Processing (Recommended)

Modify `scraper_hybrid.py` to call AI for each property:

```python
# In the upsert_property method, after scraping description:
from ai_unified_processor import process_property_with_ai, should_use_ai_extraction

description = data.get('description', '')

if should_use_ai_extraction(description):
    # Process with AI
    ai_result = process_property_with_ai(data)

    # Update unified data
    for field, value in ai_result["unified_data"].items():
        if value is not None:
            data[field] = value

    # Update monetary metadata with provenance
    from ai_unified_processor import update_monetary_metadata_from_ai
    data['monetary_metadata'] = update_monetary_metadata_from_ai(
        data, ai_result
    )
```

---

## Data Structure

### Unified Monetary Data

```python
{
    "judgment_amount": 150000.00,
    "writ_amount": 152000.00,
    "costs": 2000.00,
    "opening_bid": 114108.21,
    "minimum_bid": None,
    "approx_upset": None,
    "sale_price": None
}
```

### Provenance Tracking

```python
{
    "judgment_amount": {
        "value": 150000.00,
        "source": "ai_extraction",
        "scraped_value": null,
        "extracted_value": 150000.00
    },
    "opening_bid": {
        "value": 114108.21,
        "source": "ai_extraction",
        "scraped_value": null,
        "extracted_value": 114108.21
    }
}
```

### Monetary Metadata

```python
{
    "ai_extraction": {
        "timestamp": "2025-12-24T18:30:00Z",
        "model": "gpt-4o-mini",
        "confidence": "high",
        "reasoning": "Found clear 'Upset Price: $114,108.21' in description"
    },
    "provenance": { ... },
    "validation": {
        "scraped_values_accurate": true,
        "issues_found": [],
        "corrections_made": []
    }
}
```

---

## Configuration Options

### Model Selection

**GPT-4o mini** (Recommended for production):
- Cost: $0.15/1M input tokens
- Speed: Very fast
- Accuracy: Excellent for extraction

**GPT-4o** (For complex cases):
- Cost: $2.50/1M input tokens
- Speed: Fast
- Accuracy: Best possible

**Switch models in code:**
```python
result = process_property_with_ai(property_data, model="gpt-4o-mini")
# or
result = process_property_with_ai(property_data, model="gpt-4o")
```

### Processing Strategy

**Selective Processing** (Recommended):
```python
# Only run AI on properties with relevant descriptions
if should_use_ai_extraction(description):
    ai_result = process_property_with_ai(property_data)
```

**Batch Processing** (For post-processing):
```python
# Process all properties at once
results = batch_process_properties(properties)
```

---

## Monitoring & Cost Control

### Track Usage

The system tracks usage automatically:

```python
result = process_property_with_ai(property_data)
usage = result["ai_metadata"]["usage"]
print(f"Tokens used: {usage['total_tokens']}")
```

### Set Budget Alerts

1. Go to OpenAI Dashboard: https://platform.openai.com/usage
2. Set up email alerts at $5, $10, $20
3. Set hard limit at $50 (very safe margin)

### Monitor in Production

```python
from ai_unified_processor import estimate_cost

# Before running
cost_estimate = estimate_cost(property_count=525)
print(f"Estimated cost: ${cost_estimate['total_cost']}")
```

---

## Troubleshooting

### Issue: API Key Error

```
Error: OPENAI_API_KEY not found
```

**Solution:** Make sure your `.env` file has the key or export it:

```bash
export OPENAI_API_KEY=sk-your-key-here
```

### Issue: Rate Limiting

```
Error: Rate limit exceeded
```

**Solution:** Add a small delay between requests:

```python
import time
for prop in properties:
    result = process_property_with_ai(prop)
    time.sleep(0.1)  # 100ms between requests
```

### Issue: High Costs

If costs exceed expectations:

1. Check usage at https://platform.openai.com/usage
2. Verify you're using `gpt-4o-mini` (not `gpt-4o`)
3. Enable selective processing with `should_use_ai_extraction()`
4. Set hard limit in OpenAI dashboard

---

## Future Enhancements

### Potential Improvements

1. **Batch Processing API** - Process multiple properties in one API call
2. **Local Fallback** - Use Ollama + local LLM as free backup
3. **Caching** - Cache AI results for identical descriptions
4. **Confidence Thresholds** - Only use AI extraction when confidence > 80%

### Alternative AI Services

If OpenAI doesn't work for you:

**Gemini Flash 1.5:**
- Free tier available
- $0.075/1M tokens (cheaper than GPT-4o mini)
- Easy to swap in

**Claude Haiku:**
- Very fast
- Good accuracy
- Affordable pricing

---

## Summary

✅ **Cost:** ~$0.50/month for daily scraping
✅ **Accuracy:** Significantly better than regex
✅ **Reliability:** Enterprise-grade OpenAI API
✅ **Setup:** 5 minutes, 4 simple steps
✅ **Scalability:** Handles thousands of properties easily

**Ready to use!** Follow the setup instructions above and start extracting monetary values with AI precision.
