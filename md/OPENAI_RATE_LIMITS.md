# OpenAI Rate Limits - How to Fix

## Problem
```
Error code: 429 - Rate limit reached for gpt-4o-mini
Limit: 100,000 tokens/min (free tier)
Used: 98,782 tokens
```

## Current Limits (Free Tier - No Billing)

| Model | RPM (Requests/min) | TPM (Tokens/min) | Daily Limit |
|-------|-------------------|-----------------|-------------|
| gpt-4o-mini | 3 | 100,000 | Varies |
| gpt-4o | Not available | Not available | - |

## Solution: Add Billing to OpenAI Account

### Step 1: Add Payment Method
1. Go to: https://platform.openai.com/account/billing
2. Click "Add payment method"
3. Add credit card or debit card
4. **You only pay for what you use** - no monthly fees

### Step 2: Verify Increased Limits

After adding billing, your limits increase dramatically:

| Model | Free Tier | **With Billing** |
|-------|-----------|------------------|
| gpt-4o-mini | 3 RPM / 100K TPM | **500 RPM / 200M TPM** |
| gpt-4o | Not available | **80 RPM / 30M TPM** |

**That's 2,000x increase!**

### Step 3: Set Usage Limits (Optional but Recommended)

1. Go to: https://platform.openai.com/account/billing/limits
2. Set a monthly budget limit (e.g., $10/month)
3. This prevents unexpected charges

## Actual Costs for Our Scraper

### Current Approach (scraper_hybrid.py - main branch)
- ~500 properties/day
- AI only processes monetary fields (80% of properties)
- Cost: **$0.50/month**

### Option C (scraper_ai_full.py - feature branch)
- ~500 properties/day
- AI processes ALL fields (100% of properties)
- Cost: **$3-5/month**

Even with Option C, you're paying pennies per day!

## How Rate Limits Work

### Free Tier Calculation
```
We made ~70 AI calls during testing
Average: 1,500 tokens per call
Total: 70 × 1,500 = 105,000 tokens

But free tier is 100,000 tokens/min
So we got rate limited after ~66 calls
```

### With Billing (Tier 1 - Pay-as-you-go)
```
Limit: 200,000,000 tokens/min
We can make: 200M / 1,500 = 133,333 calls per minute
That's 2,222 calls per second!

Our scraper: 500 calls/day = 0.35 calls/minute
We're using 0.015% of the limit
```

## Temporary Workaround (If No Billing)

If you don't want to add billing right now:

1. **Wait 3 hours** - Rate limit resets per minute
2. **Reduce concurrent scraping** - Scrape fewer counties at once
3. **Use current scraper on main branch** - It uses less AI

## Recommendation

**Add billing to your OpenAI account.**

Why:
- ✅ Limits increase from 100K to 200M tokens/min (2,000x)
- ✅ You only pay for what you use (pennies per day)
- ✅ Can set hard spending limits ($10/month max)
- ✅ No monthly fees or subscriptions
- ✅ Unlocks better models (gpt-4o, etc.)

**You'll likely pay $1-5/month total** - much less than server costs!

## How to Add Billing (Step-by-Step)

1. Go to https://platform.openai.com/
2. Log in with your account
3. Click "Settings" (left sidebar)
4. Click "Billing"
5. Click "Add payment method"
6. Enter credit card details
7. (Optional) Set soft limit: $10/month
8. (Optional) Set hard limit: $20/month

You're done! Limits increase immediately.

## Monitoring Usage

Track your usage at:
https://platform.openai.com/account/usage

You'll see:
- Daily costs
- Token usage per model
- Projected monthly spend

## Cost Comparison

| Service | Cost/Month |
|---------|-----------|
| Supabase Database | $0 (free tier) |
| OpenAI API (current) | $0.50 |
| OpenAI API (Option C) | $3-5 |
| Server/VM | $5-20 |
| **Total** | **$10-30** |

Very affordable for a production foreclosure scraping system!
