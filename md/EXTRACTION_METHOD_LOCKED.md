# EXTRACTION METHOD - LOCKED IN

## Date Locked: December 24, 2025

## Approved Method: FULL AI EXTRACTION ONLY

We use **ONLY** `scraper_hybrid.py` with `ai_full_extractor.py` for all data extraction.

### How It Works:

1. **Playwright** fetches property listings and detail pages (handles JavaScript-rendered content)
2. **Raw HTML** is stored in `PropertyDetails.raw_html`
3. **`extract_all_data_from_html()`** from `ai_full_extractor.py` extracts ALL fields from HTML using GPT-4o mini
4. **No mechanical extraction** - no BeautifulSoup, no regex patterns
5. **No fallback methods** - if AI extraction fails, the scrape fails

### Files We Use:

- ✅ `scraper_hybrid.py` - Main scraper (LOCKED IN)
- ✅ `ai_full_extractor.py` - Full AI extraction from HTML (LOCKED IN)
- ✅ `scraper_helper.py` - County mappings and field normalization

### Files We DO NOT Use:

- ❌ `ai_unified_processor.py.DEPRECATED` - Old AI categorization (only processed description text)
- ❌ `scraper_ai_full.py.DEPRECATED_STANDALONE` - Standalone AI scraper (used HTTP instead of Playwright)

### Why This Method:

1. **Complete Data Capture** - Extracts ALL fields from HTML, not just monetary from description
2. **Handles All Counties** - AI understands county-specific field variations ("Approx Judgment" vs "Final Judgment")
3. **Consistent Schema** - Maps everything to unified field names automatically
4. **Higher Accuracy** - AI understands context better than regex patterns

### Cost:

- **~$3-5/month** for daily scraping of all NJ counties
- **~500-1500 input tokens** per property (full HTML)
- **~500 output tokens** per property (structured JSON)

### Running the Scraper:

```bash
# Single county
./venv/bin/python scraper_hybrid.py --counties Salem

# Multiple counties
./venv/bin/python scraper_hybrid.py --counties Essex Middlesex Union

# All counties
for county in Camden Essex Burlington Bergen Monmouth Morris Hudson Union Passaic Gloucester Salem Atlantic Hunterdon Cape May Middlesex Cumberland; do
    ./venv/bin/python scraper_hybrid.py --counties "$county"
done
```

### NEVER:

- ❌ Do NOT use `ai_unified_processor.py` - it's deprecated
- ❌ Do NOT use `scraper_ai_full.py` - it's deprecated
- ❌ Do NOT add fallback to mechanical extraction
- ❌ Do NOT use regex patterns for data extraction
- ❌ Do NOT skip AI extraction to save cost - this will result in missing data

### IF AI EXTRACTION FAILS:

The scraper will raise a `RuntimeError`. This is intentional - do NOT add fallback code.
Instead:
1. Check your OpenAI API key in `.env`
2. Check `ai_full_extractor.py` for bugs
3. Check that `raw_html` is being populated in `scraper_hybrid.py`

### Making Changes:

If you need to change the extraction method:
1. Update this document with the new approach
2. Get explicit approval
3. Update the "Date Locked" timestamp

---

**This configuration is LOCKED IN. Do NOT change without explicit reason and testing.**
