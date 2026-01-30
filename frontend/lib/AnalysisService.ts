/**
 * Property Analysis Service
 *
 * Uses Gemini 2.0 Flash with Google Search for forensic real estate research.
 *
 * Based on Integration Kit from app (3).zip
 * Uses REST API instead of @google/genai SDK for Next.js compatibility
 */

import { getApiKey } from './apiKey'

// Analysis Data Type - must match the schema in SYSTEM_INSTRUCTION
export type AnalysisData = {
  property_address: string;
  comprehensive_analysis?: {
    property_narrative: string;
    investment_thesis: string;
    risk_assessment_detailed: string;
  };
  property_details: {
    year_built: number | string;
    building_sqft: number | string;
    lot_size_sqft: number | string;
    lot_dimensions: string;
    assessed_value: number;
    tax_amount: number;
    flood_zone: string;
    parcel_id: string;
  };
  zoning_analysis: {
    current_zoning_designation: string;
    conforming_status: string;
    buildable_area_analysis?: string;
    bulk_and_setback_requirements: {
      min_lot_size: { value: number; unit: string };
      max_building_coverage: string | number;
      setbacks: string;
    };
  };
  rental_analysis: {
    estimated_monthly_rent: { low: number; high: number };
    section_8_fmr: number;
    gross_yield_percentage: string;
    rental_demand_rating: string;
  };
  market_analysis: {
    school_district_rating: string;
    est_days_on_market: string;
    neighborhood_class_estimate: string;
    recent_flip_activity: string;
  };
  rehab_matrix: {
    light_cosmetic: { cost: number; description: string };
    moderate_update: { cost: number; description: string };
    full_gut: { cost: number; description: string };
  };
  auction_price_analysis: {
    upset_amount: number;
    property_worth_scenarios: {
      conservative_scenario: { estimate: number; description: string };
      optimistic_scenario: { estimate: number; description: string };
    };
    max_bid_calculation: string;
    break_even_point: string;
    analysis_notes: string;
  };
  investment_strategies_ranked: Array<{
    rank: number;
    strategy: string;
    risk_level: string;
    explanation: string;
    est_profit_potential: number;
    break_even_offer: number;
  }>;
  highest_best_use_scenarios?: Array<{
    scenario: string;
    pros: string;
    cons: string;
    risk: string;
    financials: {
      est_rehab_cost: number;
      est_arv: number;
      est_profit: number;
      roi_percentage: string;
    };
  }>;
  verification_checklist?: Array<{
    category: string;
    item: string;
    action_needed: string;
  }>;
};

// System Instruction for Forensic Real Estate Research
const SYSTEM_INSTRUCTION = `You are a FORENSIC REAL ESTATE RESEARCH AGENT. Your goal is to provide a "Wall of Text" level detail followed by a highly specific, math-heavy JSON report.

### INPUT ANALYSIS
The user will provide an address and an "Upset Amount" (Starting Bid).
Example Upset: $4,503,000. You must handle high-value commercial/multi-family analysis just as well as residential.

### ELABORATION REQUIREMENT (CRITICAL)
- **EVERY field in the JSON must be filled with detailed, specific content.**
- **NEVER** use placeholder text like "N/A", "TBD", "To be determined", or single words.
- **NEVER** leave numeric fields as 0 or null - calculate real estimates.
- For descriptions, write 2-3 sentences explaining the reasoning, not just a label.
- For pros/cons, provide 3-4 specific, actionable points per item.
- **Show your work** - when you calculate a number, explain the formula and inputs used.

### REQUIRED ANALYSIS POINTS (EXECUTE THESE IN ORDER)

1. **Investment Strategies (Ranked)**
   - Rank strategies (Flip, Rental, BRRRR, Development) from Best to Worst.
   - **CRITICAL: CALCULATE DISTINCT BREAK-EVEN OFFERS** (These MUST be different values based on the strategy's math):
     * **Flip Strategy**: Break Even = Optimistic ARV - (Rehab Cost + 10% Closing/Selling Costs + 5% Holding Costs). *Price to make $0 profit.*
     * **Buy & Hold / Rental**: Break Even = ((Monthly Rent * 12 * 0.65) / Market Cap Rate) - Rehab Cost. *(Assumes 35% OpEx. Use 6-8% Cap Rate based on class).*
     * **BRRRR**: Break Even = (ARV * 0.75) - Rehab Cost - Closing Costs. *(Price where you get all cash back on refi).*
   - **CALCULATE PROFIT**: Estimate Net Profit if purchased at the UPSET PRICE.

2. **Zoning & Buildable Area (ZONING RESCUE PROTOCOL)**
   - Identify the specific Zone Code (e.g., R-2, C-1).
   - **CRITICAL - IF DATA IS MISSING**:
     * **NEVER** return "N/A", "0", or "Unknown" for bulk requirements.
     * **DERIVE** the likely zoning based on the lot size and satellite context.
     * **USE THESE DEFAULTS** if specific town code is not found:
       - **Urban/Row (Lot < 3k sf)**: Min Lot 2,500sf | Cov 60% | Setbacks: F 10', S 3', R 15'.
       - **Suburban Std (Lot 4k-8k sf)**: Min Lot 5,000sf | Cov 35% | Setbacks: F 25', S 8', R 25'.
       - **Estate/Rural (Lot > 10k sf)**: Min Lot 10,000sf | Cov 25% | Setbacks: F 40', S 15', R 40'.
     * **LABEL** these values as "(Est based on typical [Type] standards)".
   - **BUILDABLE AREA**: Write a DETAILED PARAGRAPH explaining:
     * The buildable envelope calculation: (Lot Size × Max Coverage) - Setbacks
     * What the coverage and setbacks allow (e.g., "With 35% coverage on a 5,000 sqft lot and 25ft front setbacks, you have approximately X sqft of buildable footprint")
     * Expansion potential (e.g., "This supports a 2-story structure of approximately X total sqft" or "Additional expansion may be possible through variances")
     * Any assumptions made if using estimates
   - **DO NOT** just write numbers - write a comprehensive paragraph that explains the buildable area analysis in detail.

3. **Highest & Best Use Scenarios (with DETAILED FINANCIALS)**
   - Provide 2-3 distinct scenarios (e.g., "As-Is Rental", "Value-Add Reno", "Ground-up Construction").
   - For EACH scenario, you MUST provide:
     * **Detailed PROS**: 3-4 specific advantages of this strategy
     * **Detailed CONS**: 3-4 specific disadvantages or challenges
     * **RISK Level**: Low, Medium, or High with brief explanation
     * **FINANCIAL PROFORMA** (REQUIRED for each scenario):
       - **Est. Rehab Cost**: Calculate based on Building SqFt and scenario (e.g., Light $25/sqft, Moderate $55/sqft, Full Gut $90/sqft)
       - **Est. ARV**: Calculate realistic After Repair Value for this specific strategy
       - **Est. Profit**: ARV - (Upset Price + Rehab Cost + 10% Soft Costs) - MUST BE A REAL NUMBER, NOT $0
       - **ROI %**: (Profit / Total Investment) × 100 - MUST BE A PERCENTAGE, NOT "N/A"
   - **DO NOT** leave financials as $0 or N/A - calculate real numbers for every scenario.

4. **Verification Checklist (Due Diligence) - REQUIRED**
   - **CRITICAL**: You MUST include this section with at least 5-7 specific verification items.
   - Create a checklist of exactly what the user must ask/verify with the municipality.
   - Categorize items into: Zoning, Building Permits, Environmental, Title, Flood Zone, etc.
   - Each item must have:
     * **category**: The area of verification (Zoning, Building Permits, etc.)
     * **item**: What to verify (e.g., "Verify the current zoning designation")
     * **action_needed**: Specific steps to take (e.g., "Contact the zoning officer to confirm...")
   - Examples of items to include:
     * Zoning verification with township
     * Outstanding violations or restrictions
     * Building permits and certificates of occupancy
     * Flood zone determination
     * Environmental concerns
     * Title issues
   - **DO NOT** skip this section or leave it empty.

5. **Auction Price Analysis**
   - **Valuation**: Provide Conservative, Moderate, and Optimistic ARV (After Repair Value).
   - **MAX BID THRESHOLD**:
     * Formula: Max Bid = (Conservative ARV * 0.70) - Est. Rehab - Holding Costs (10% of ARV).
     * State the price point where the deal becomes UNPROFITABLE (Red Zone).

### DATA GATHERING (The "No Unknowns" Search)
Execute iterative searches to fill the "Search Scratchpad" completely.
1. **Identify Block & Lot**: Search "[County] NJ tax records [Address]" or "NJparcels.com [Address]".
2. **Lot Size & Dimensions**: Search "[Address] lot lines map" or "GIS map [County] [Address]".
3. **Zoning Code**: Search "[Town] Zoning Map PDF". Find the specific zone (e.g., R-1, C-2).
4. **Rental Intelligence**: Search "[Zip Code] HUD FMR 2024" (Section 8 rents) and "Rentometer [Address]" or "Zillow rent zestimate [Address]".

### PHASE 3: FINAL JSON (Strict Schema)
Fill this JSON with **detailed strings**.
\`\`\`json
{
  "property_address": "string",
  "property_details": {
    "year_built": "number or string",
    "building_sqft": "number or string",
    "lot_size_sqft": "number or string",
    "lot_dimensions": "string",
    "assessed_value": number,
    "tax_amount": number,
    "flood_zone": "string",
    "parcel_id": "string"
  },
  "zoning_analysis": {
    "current_zoning_designation": "string",
    "conforming_status": "string",
    "bulk_and_setback_requirements": {
      "min_lot_size": {"value": number, "unit": "sqft"},
      "max_building_coverage": "percentage or number",
      "setbacks": "string"
    }
  },
  "rental_analysis": {
    "estimated_monthly_rent": { "low": number, "high": number },
    "section_8_fmr": number,
    "gross_yield_percentage": "string",
    "rental_demand_rating": "string"
  },
  "market_analysis": {
    "school_district_rating": "string",
    "est_days_on_market": "string",
    "neighborhood_class_estimate": "string",
    "recent_flip_activity": "string"
  },
  "rehab_matrix": {
    "light_cosmetic": { "cost": number, "description": "string" },
    "moderate_update": { "cost": number, "description": "string" },
    "full_gut": { "cost": number, "description": "string" }
  },
  "auction_price_analysis": {
    "upset_amount": number,
    "property_worth_scenarios": {
      "conservative_scenario": {"estimate": number, "description": "string"},
      "optimistic_scenario": {"estimate": number, "description": "string"}
    },
    "max_bid_calculation": "string",
    "break_even_point": "string",
    "analysis_notes": "string"
  },
  "investment_strategies_ranked": [
    {
      "rank": 1,
      "strategy": "string",
      "risk_level": "string",
      "explanation": "string",
      "est_profit_potential": number,
      "break_even_offer": number
    }
  ],
  "highest_best_use_scenarios": [
    {
      "scenario": "string",
      "pros": "string",
      "cons": "string",
      "risk": "string",
      "financials": {
          "est_rehab_cost": number,
          "est_arv": number,
          "est_profit": number,
          "roi_percentage": "string"
      }
    }
  ]
}
\`\`\`
IMPORTANT: Complete the entire JSON object. Do NOT cut off mid-JSON. Ensure ALL closing brackets and braces are present. The est_profit_potential and break_even_offer fields are REQUIRED.`;

const GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:streamGenerateContent";

async function callGeminiAPI(prompt: string, apiKey: string, onProgress?: (text: string) => void): Promise<string> {
  const response = await fetch(`${GEMINI_API_URL}?key=${apiKey}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      systemInstruction: {
        parts: [{ text: SYSTEM_INSTRUCTION }]
      },
      contents: [{
        parts: [{ text: prompt }]
      }],
      generationConfig: {
        temperature: 0.0,
        topP: 0.1,
        maxOutputTokens: 8192,
      },
      tools: [{
        googleSearch: {}
      }],
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Gemini API error: ${response.status} ${response.statusText} - ${errorText}`);
  }

  // Read the entire streaming response
  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("No response body");
  }

  const decoder = new TextDecoder();
  let rawResponse = "";
  let fullText = "";

  // Accumulate the entire raw response
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    rawResponse += decoder.decode(value, { stream: true });
  }

  // Parse the complete response as JSON array
  try {
    const responses = JSON.parse(rawResponse) as Array<any>;

    // Extract text from each response in the array
    for (const response of responses) {
      const text = response.candidates?.[0]?.content?.parts?.[0]?.text;
      if (text) {
        fullText += text;
        onProgress?.(fullText);
      }
    }
  } catch (e) {
    console.error("[AnalysisService] Failed to parse response:", e);
    throw new Error("Failed to parse Gemini API response");
  }

  return fullText;
}

/**
 * Analyze a property using Gemini with Google Search
 *
 * @param address - Property address (e.g., "127 Highland Avenue, Pennsville, NJ 08070")
 * @param upsetAmount - Upset amount from auction listing
 * @returns AnalysisData or null if parsing fails
 */
export const analyzeProperty = async (
  address: string,
  upsetAmount: number
): Promise<AnalysisData | null> => {
  const apiKey = getApiKey();
  if (!apiKey) {
    console.error("API_KEY not found in environment");
    console.log("Available env vars:", {
      API_KEY: typeof process !== 'undefined' ? process.env.API_KEY : 'process undefined',
      REACT_APP_API_KEY: typeof process !== 'undefined' ? process.env.REACT_APP_API_KEY : 'process undefined',
      NEXT_PUBLIC_API_KEY: typeof process !== 'undefined' ? process.env.NEXT_PUBLIC_API_KEY : 'process undefined',
    });
    throw new Error("API key is not configured. Please add NEXT_PUBLIC_API_KEY to your .env.local file.");
  }

  const prompt = `${address}. Upset Amount: $${upsetAmount}`;

  try {
    const fullText = await callGeminiAPI(prompt, apiKey);

    console.log('[AnalysisService] Response length:', fullText.length);
    console.log('[AnalysisService] Response preview (first 500 chars):', fullText.substring(0, 500));

    // Extract JSON from Markdown block
    const jsonStart = fullText.indexOf("```json");
    const jsonEnd = fullText.lastIndexOf("```");

    if (jsonStart !== -1 && jsonEnd > jsonStart) {
      const jsonStr = fullText.substring(jsonStart + 7, jsonEnd);
      console.log('[AnalysisService] Extracted JSON string length:', jsonStr.length);
      try {
        return JSON.parse(jsonStr) as AnalysisData;
      } catch (parseError) {
        console.error('[AnalysisService] JSON parse error:', parseError);
        console.log('[AnalysisService] JSON string that failed to parse (first 1000 chars):', jsonStr.substring(0, 1000));
        throw new Error(`Failed to parse JSON: ${parseError}`);
      }
    }

    console.error('[AnalysisService] Failed to extract JSON from response');
    console.log('[AnalysisService] Full response:', fullText);
    return null;
  } catch (error) {
    console.error('[AnalysisService] Analysis failed:', error);
    throw error;
  }
};

/**
 * Stream analysis with on-progress callback
 *
 * @param address - Property address
 * @param upsetAmount - Upset amount
 * @param onProgress - Callback with incremental text updates
 * @returns Final AnalysisData or null
 */
export const analyzePropertyStream = async (
  address: string,
  upsetAmount: number,
  onProgress?: (text: string) => void
): Promise<AnalysisData | null> => {
  const apiKey = getApiKey();
  if (!apiKey) {
    console.error("API_KEY not found in environment");
    console.log("Available env vars:", {
      API_KEY: typeof process !== 'undefined' ? process.env.API_KEY : 'process undefined',
      REACT_APP_API_KEY: typeof process !== 'undefined' ? process.env.REACT_APP_API_KEY : 'process undefined',
      NEXT_PUBLIC_API_KEY: typeof process !== 'undefined' ? process.env.NEXT_PUBLIC_API_KEY : 'process undefined',
    });
    throw new Error("API key is not configured. Please add NEXT_PUBLIC_API_KEY to your .env.local file.");
  }

  const prompt = `${address}. Upset Amount: $${upsetAmount}`;

  try {
    const fullText = await callGeminiAPI(prompt, apiKey, onProgress);

    console.log('[AnalysisService] Response length:', fullText.length);
    console.log('[AnalysisService] Response preview (first 500 chars):', fullText.substring(0, 500));

    // Extract JSON from Markdown block
    const jsonStart = fullText.indexOf("```json");
    const jsonEnd = fullText.lastIndexOf("```");

    if (jsonStart !== -1 && jsonEnd > jsonStart) {
      const jsonStr = fullText.substring(jsonStart + 7, jsonEnd);
      console.log('[AnalysisService] Extracted JSON string length:', jsonStr.length);
      try {
        return JSON.parse(jsonStr) as AnalysisData;
      } catch (parseError) {
        console.error('[AnalysisService] JSON parse error:', parseError);
        console.log('[AnalysisService] JSON string that failed to parse (first 1000 chars):', jsonStr.substring(0, 1000));
        throw new Error(`Failed to parse JSON: ${parseError}`);
      }
    }

    console.error('[AnalysisService] Failed to extract JSON from response');
    console.log('[AnalysisService] Full response:', fullText);
    return null;
  } catch (error) {
    console.error('[AnalysisService] Analysis failed:', error);
    throw error;
  }
};

/**
 * Export analysis as PDF
 *
 * @param data - AnalysisData to export
 */
export const exportAnalysisPdf = async (data: AnalysisData) => {
  const { exportAnalysisPdf: exportPdf } = await import('./exportAnalysisPdf');
  return exportPdf(data);
};