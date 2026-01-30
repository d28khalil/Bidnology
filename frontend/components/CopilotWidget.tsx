/**
 * CopilotWidget - AI Chatbot for Real Estate
 *
 * A floating chat widget in the bottom right corner with two modes:
 * - Investor Copilot: General real estate Q&A
 * - Forensic Agent: Deep property analysis
 *
 * Uses Gemini REST API for Next.js compatibility
 */

'use client'

import React, { useState, useRef, useEffect } from 'react'
import { getApiKey, saveApiKey, clearApiKey, hasApiKey } from '@/lib/apiKey'
import { RefinedReport } from './RefinedReport'
import { exportAnalysisPdf } from '@/lib/exportAnalysisPdf'

// Types
type GroundingChunk = {
  web?: {
    uri: string
    title: string
  }
}

type Message = {
  id: string
  role: 'user' | 'model'
  text: string
  groundingChunks?: GroundingChunk[]
  timestamp: number
}

type AnalysisData = {
  property_address: string
  comprehensive_analysis?: {
    property_narrative: string
    investment_thesis: string
    risk_assessment_detailed: string
  }
  property_details: {
    year_built: number | string
    building_sqft: number | string
    lot_size_sqft: number | string
    lot_dimensions: string
    assessed_value: number
    tax_amount: number
    flood_zone: string
    parcel_id: string
  }
  zoning_analysis: {
    current_zoning_designation: string
    conforming_status: string
    buildable_area_analysis?: string
    bulk_and_setback_requirements: {
      min_lot_size: { value: number; unit: string }
      max_building_coverage: string | number
      setbacks: string
    }
  }
  rental_analysis: {
    estimated_monthly_rent: { low: number; high: number }
    section_8_fmr: number
    gross_yield_percentage: string
    rental_demand_rating: string
  }
  market_analysis: {
    school_district_rating: string
    est_days_on_market: string
    neighborhood_class_estimate: string
    recent_flip_activity: string
  }
  rehab_matrix: {
    light_cosmetic: { cost: number; description: string }
    moderate_update: { cost: number; description: string }
    full_gut: { cost: number; description: string }
  }
  auction_price_analysis: {
    upset_amount: number
    property_worth_scenarios: {
      conservative_scenario: { estimate: number; description: string }
      optimistic_scenario: { estimate: number; description: string }
    }
    max_bid_calculation: string
    break_even_point: string
    analysis_notes: string
  }
  investment_strategies_ranked: Array<{
    rank: number
    strategy: string
    risk_level: string
    explanation: string
    est_profit_potential: number
    break_even_offer: number
  }>
  highest_best_use_scenarios?: Array<{
    scenario: string
    pros: string
    cons: string
    risk: string
    financials: {
      est_rehab_cost: number
      est_arv: number
      est_profit: number
      roi_percentage: string
    }
  }>
  verification_checklist?: Array<{
    category: string
    item: string
    action_needed: string
  }>
}

// System Instructions
const COPILOT_SYSTEM_INSTRUCTION = `You are an ELITE REAL ESTATE INVESTOR & ANALYST.
Your role is to act as a real-time consultant for the user. You have access to Google Search.

CAPABILITIES:
1. **Property Analysis**: Answer specific questions about address data, history, or comps.
2. **Investment Math**: Calculate Cap Rates, Cash-on-Cash Return, and BRRRR math instantly.
3. **Market Trends**: Search for current interest rates, local absorption rates, and news.

TONE:
Professional, direct, analytical, and highly knowledgeable. Use bullet points for clarity.
ALWAYS cite your sources when retrieving data from the web.`

const FORENSIC_SYSTEM_INSTRUCTION = `You are a FORENSIC REAL ESTATE RESEARCH AGENT. Your goal is to provide a "Wall of Text" level detail followed by a highly specific, math-heavy JSON report.

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
  "comprehensive_analysis": {
    "property_narrative": "Detailed paragraph describing the property context and physical characteristics.",
    "investment_thesis": "Strategic argument for why this is a good or bad deal based on the numbers.",
    "risk_assessment_detailed": "Explicit list of risks (environmental, title, market) and mitigation steps."
  },
  "property_details": {
    "year_built": "number or string (e.g. '1950 (Est)')",
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
    "buildable_area_analysis": "Text explaining the buildable envelope and expansion potential based on setbacks/coverage.",
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
  ],
  "verification_checklist": [
    { "category": "Zoning", "item": "string", "action_needed": "string" }
  ]
}
\`\`\``

const MODEL_NAME = 'gemini-2.0-flash'
const GEMINI_API_URL = `https://generativelanguage.googleapis.com/v1beta/models/${MODEL_NAME}:streamGenerateContent`

// Helper to parse JSON from text
const parseAnalysisJson = (text: string): AnalysisData | null => {
  const jsonStart = text.indexOf('```json')
  const jsonEnd = text.lastIndexOf('```')
  if (jsonStart !== -1 && jsonEnd > jsonStart) {
    try {
      const jsonStr = text.substring(jsonStart + 7, jsonEnd)
      return JSON.parse(jsonStr) as AnalysisData
    } catch (e) { return null }
  }
  return null
}

// API Call function
async function callGeminiAPI(prompt: string, systemInstruction: string, apiKey: string, onProgress?: (text: string) => void): Promise<{ text: string; groundingChunks: GroundingChunk[] }> {
  console.log('[GeminiAPI] Starting API call to:', GEMINI_API_URL)

  const response = await fetch(`${GEMINI_API_URL}?key=${apiKey}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      systemInstruction: {
        parts: [{ text: systemInstruction }]
      },
      contents: [{
        parts: [{ text: prompt }]
      }],
      generationConfig: {
        temperature: 0.0,
        topP: 0.1,
        maxOutputTokens: 8192,
      },
      tools: [{ googleSearch: {} }],
      safetySettings: [
        { category: 'HARM_CATEGORY_HARASSMENT', threshold: 'BLOCK_NONE' },
        { category: 'HARM_CATEGORY_HATE_SPEECH', threshold: 'BLOCK_NONE' },
        { category: 'HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold: 'BLOCK_NONE' },
        { category: 'HARM_CATEGORY_DANGEROUS_CONTENT', threshold: 'BLOCK_NONE' },
      ],
    }),
  })

  console.log('[GeminiAPI] Response status:', response.status, response.statusText)

  if (!response.ok) {
    const errorText = await response.text()
    console.error('[GeminiAPI] Error response:', errorText)
    throw new Error(`Gemini API error: ${response.status} ${response.statusText} - ${errorText}`)
  }

  const reader = response.body?.getReader()
  if (!reader) throw new Error('No response body')

  const decoder = new TextDecoder()
  let rawResponse = ''
  let fullText = ''
  const collectedGrounding: GroundingChunk[] = []

  console.log('[GeminiAPI] Starting to read stream...')

  // Read the entire stream first
  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    rawResponse += decoder.decode(value, { stream: true })
  }

  console.log('[GeminiAPI] Complete raw response received, length:', rawResponse.length)

  // Parse the complete response as JSON array
  try {
    // The response should be a JSON array like [{...}, {...}, ...]
    const responses = JSON.parse(rawResponse) as Array<any>

    console.log('[GeminiAPI] Parsed', responses.length, 'response objects')

    // Extract text from each response in the array
    for (const response of responses) {
      const text = response.candidates?.[0]?.content?.parts?.[0]?.text
      if (text) {
        fullText += text
        onProgress?.(fullText)
      }

      // Collect grounding metadata
      if (response.candidates?.[0]?.groundingMetadata?.groundingChunks) {
        collectedGrounding.push(...response.candidates[0].groundingMetadata.groundingChunks)
      }
    }

    console.log('[GeminiAPI] Final text length:', fullText.length)
  } catch (e) {
    console.error('[GeminiAPI] Failed to parse response as JSON array:', e)
    console.log('[GeminiAPI] Raw response (first 1000 chars):', rawResponse.substring(0, 1000))
    throw new Error('Failed to parse Gemini API response')
  }

  return { text: fullText, groundingChunks: collectedGrounding }
}

export const CopilotWidget = () => {
  const [isOpen, setIsOpen] = useState(false)
  const [isExpanded, setIsExpanded] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [agentMode, setAgentMode] = useState<'investor' | 'forensic'>('investor')
  const [showAgentMenu, setShowAgentMenu] = useState(false)
  const [showApiKeyEntry, setShowApiKeyEntry] = useState(false)
  const [showSettingsMenu, setShowSettingsMenu] = useState(false)
  const [apiKeyInput, setApiKeyInput] = useState('')

  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Initialize with greeting
  useEffect(() => {
    const greeting = agentMode === 'investor'
      ? 'I am your Real Estate Investor Expert. Ask me about any property, market trends, or investment calculations.'
      : 'Forensic Mode Activated. I will generate deep, structured analysis reports. Please provide an address and upset price.'

    setMessages([{
      id: 'init-' + Date.now(),
      role: 'model',
      text: greeting,
      timestamp: Date.now()
    }])
  }, [agentMode])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    if (isOpen) scrollToBottom()
  }, [messages, isOpen])

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const apiKey = getApiKey()
    console.log('[Copilot] API Key retrieved:', apiKey ? `Found (${apiKey.slice(0, 10)}...)` : 'NOT FOUND')

    if (!apiKey) {
      console.log('[Copilot] No API key, showing entry modal')
      setShowApiKeyEntry(true)
      return
    }

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      text: input.trim(),
      timestamp: Date.now()
    }

    setMessages(prev => [...prev, userMsg])
    setInput('')
    setIsLoading(true)

    const modelMsgId = (Date.now() + 1).toString()

    try {
      setMessages(prev => [...prev, { id: modelMsgId, role: 'model', text: '', timestamp: Date.now() }])

      const systemInstruction = agentMode === 'investor' ? COPILOT_SYSTEM_INSTRUCTION : FORENSIC_SYSTEM_INSTRUCTION

      console.log('[Copilot] Calling Gemini API...')
      const { text: fullText, groundingChunks } = await callGeminiAPI(
        userMsg.text,
        systemInstruction,
        apiKey,
        (progressText) => {
          setMessages(prev => prev.map(m => m.id === modelMsgId ? { ...m, text: progressText } : m))
        }
      )

      console.log('[Copilot] API call completed, response length:', fullText.length)
      setMessages(prev => prev.map(m => m.id === modelMsgId ? {
        ...m,
        text: fullText,
        groundingChunks: Array.from(new Map(groundingChunks.map(item => [item.web?.uri, item])).values())
      } : m))
    } catch (error) {
      console.error('[Copilot] Error:', error)
      setMessages(prev => prev.map(m => m.id === modelMsgId ? {
        ...m,
        text: `Error: ${error instanceof Error ? error.message : 'Failed to get response'}`
      } : m))
    } finally {
      console.log('[Copilot] Setting isLoading to false')
      setIsLoading(false)
    }
  }

  const toggleAgentMode = (mode: 'investor' | 'forensic') => {
    setAgentMode(mode)
    setShowAgentMenu(false)
    setShowSettingsMenu(false)
  }

  const handleSaveApiKey = () => {
    if (apiKeyInput.trim()) {
      saveApiKey(apiKeyInput.trim())
      setShowApiKeyEntry(false)
      setApiKeyInput('')
    }
  }

  const handleClearApiKey = () => {
    clearApiKey()
    setMessages([])
  }

  const handleExportChat = async () => {
    // Find the last message with analysis data (RefinedReport)
    const lastAnalysisMessage = messages
      .filter((msg) => msg.role === 'model' && parseAnalysisJson(msg.text))
      .pop()

    if (!lastAnalysisMessage) {
      alert('No analysis report to export. Please run a property analysis first.')
      return
    }

    const analysisData = parseAnalysisJson(lastAnalysisMessage.text)
    if (!analysisData) {
      alert('Could not parse analysis data.')
      return
    }

    try {
      await exportAnalysisPdf(analysisData)
    } catch (error) {
      console.error('Error exporting PDF:', error)
      alert('Failed to export PDF. Please try again.')
    }
  }

  return (
    <>
      <div className={`z-50 transition-all duration-300 ${isExpanded ? 'fixed inset-0' : 'fixed bottom-6 right-6'}`}>
        {isOpen && (
          <div className={`flex flex-col bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 shadow-2xl overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-200 ${isExpanded ? 'w-full h-full rounded-none' : 'rounded-2xl w-[400px] h-[550px]'}`}>
          {/* Header */}
          <div className="flex items-center justify-between p-4 bg-gray-100 dark:bg-gray-800 border-b border-gray-300 dark:border-gray-700">
            {/* Agent Selector */}
            <div className="relative">
              <button
                onClick={() => setShowAgentMenu(!showAgentMenu)}
                className="flex items-center gap-2 hover:bg-gray-200 dark:hover:bg-gray-700 p-1.5 rounded-lg transition-colors"
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${agentMode === 'investor' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-purple-500/20 text-purple-400'}`}>
                  <span className="material-symbols-outlined text-lg">
                    {agentMode === 'investor' ? 'auto_awesome' : 'smart_toy'}
                  </span>
                </div>
                <div className="text-left">
                  <h3 className="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-1">
                    {agentMode === 'investor' ? 'Investor Copilot' : 'Forensic Agent'}
                    <span className="material-symbols-outlined text-sm">expand_more</span>
                  </h3>
                  <p className="text-[10px] text-gray-500 dark:text-gray-400 flex items-center gap-1">
                    <span className={`w-1.5 h-1.5 rounded-full animate-pulse ${agentMode === 'investor' ? 'bg-emerald-500' : 'bg-purple-500'}`}></span>
                    Online • {agentMode === 'investor' ? 'Expert Mode' : 'Report Mode'}
                  </p>
                </div>
              </button>

              {/* Agent Dropdown */}
              {showAgentMenu && (
                <div className="absolute top-full left-0 mt-2 w-48 bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-xl shadow-xl z-50 overflow-hidden">
                  <button
                    onClick={() => toggleAgentMode('investor')}
                    className={`w-full text-left px-4 py-3 text-sm flex items-center gap-3 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors ${agentMode === 'investor' ? 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400'}`}
                  >
                    <span className="material-symbols-outlined text-emerald-400">auto_awesome</span>
                    <span>Investor Copilot</span>
                  </button>
                  <button
                    onClick={() => toggleAgentMode('forensic')}
                    className={`w-full text-left px-4 py-3 text-sm flex items-center gap-3 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors ${agentMode === 'forensic' ? 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400'}`}
                  >
                    <span className="material-symbols-outlined text-purple-400">smart_toy</span>
                    <span>Forensic Agent</span>
                  </button>
                </div>
              )}
            </div>

            <div className="flex items-center gap-1">
              <button onClick={() => setIsExpanded(!isExpanded)} className="p-1.5 text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">
                <span className="material-symbols-outlined text-lg">
                  {isExpanded ? 'compress' : 'open_in_full'}
                </span>
              </button>
              <button
                onClick={handleExportChat}
                className="p-1.5 text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                title="Export chat"
              >
                <span className="material-symbols-outlined text-lg">download</span>
              </button>
              <div className="relative">
                <button
                  onClick={() => {
                    setShowSettingsMenu(!showSettingsMenu)
                    setShowAgentMenu(false)
                  }}
                  className="p-1.5 text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                  title="Settings"
                >
                  <span className="material-symbols-outlined text-lg">settings</span>
                </button>

                {/* Settings Dropdown */}
                {showSettingsMenu && (
                  <div className="absolute top-full right-0 mt-2 w-56 bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-xl shadow-xl z-50 overflow-hidden">
                    <div className="px-4 py-2 border-b border-gray-200 dark:border-gray-700">
                      <p className="text-xs text-gray-500 dark:text-gray-400 font-medium">API Key</p>
                      <p className="text-xs text-gray-400 dark:text-gray-500 truncate">
                        {hasApiKey() ? 'Configured (localStorage)' : 'Not configured'}
                      </p>
                    </div>
                    <button
                      onClick={() => {
                        handleClearApiKey()
                        setShowSettingsMenu(false)
                      }}
                      className="w-full text-left px-4 py-3 text-sm flex items-center gap-3 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-red-500 dark:text-red-400"
                    >
                      <span className="material-symbols-outlined">delete</span>
                      <span>Clear API Key</span>
                    </button>
                  </div>
                )}
              </div>
              <button onClick={() => { setIsOpen(false); setTimeout(() => setIsExpanded(false), 0); }} className="p-1.5 text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">
                <span className="material-symbols-outlined text-lg">close</span>
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50 dark:bg-gray-950">
            {messages.map((msg) => {
              // Check if this message contains a JSON report (Forensic mode output)
              const reportData = parseAnalysisJson(msg.text)

              // Keep text before the json block for context/scratchpad
              let contentToDisplay = msg.text
              if (reportData) {
                const jsonStart = msg.text.indexOf('```json')
                if (jsonStart !== -1) {
                  contentToDisplay = msg.text.substring(0, jsonStart).trim()
                }
              }

              return (
                <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  {msg.role === 'model' && (
                    <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-800 flex items-center justify-center flex-shrink-0">
                      <span className="material-symbols-outlined text-sm text-gray-600 dark:text-gray-400">
                        {agentMode === 'investor' ? 'auto_awesome' : 'smart_toy'}
                      </span>
                    </div>
                  )}
                  <div className={`max-w-[85%] rounded-2xl text-sm ${
                    msg.role === 'user'
                      ? 'bg-purple-600 text-white px-4 py-3'
                      : 'bg-white dark:bg-gray-900 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700 w-full'
                  }`}>
                    {/* Text Content (Search Scratchpad / Intro) */}
                    {contentToDisplay && (
                      <div className="px-4 pt-3 whitespace-pre-wrap leading-relaxed">
                        {contentToDisplay}
                      </div>
                    )}

                    {/* Structured Report */}
                    {!isLoading && reportData && msg.role === 'model' && (
                      <div className="px-4 pb-4">
                        <div className="mt-3 -mx-2">
                          <RefinedReport data={reportData} />
                        </div>
                      </div>
                    )}

                    {/* Loading state */}
                    {!msg.text && !reportData && (
                      <div className="px-4 py-3">
                        <span className="flex items-center gap-2 text-gray-400 italic animate-pulse">
                          <span className="material-symbols-outlined text-lg animate-spin">refresh</span>
                          Thinking...
                        </span>
                      </div>
                    )}

                    {/* Sources */}
                    {msg.groundingChunks && msg.groundingChunks.length > 0 && (
                      <div className="mt-3 pt-2 px-4 border-t border-gray-200 dark:border-gray-700 flex flex-wrap gap-2">
                        {msg.groundingChunks.map((chunk, i) => chunk.web?.uri && (
                          <a key={i} href={chunk.web.uri} target="_blank" rel="noreferrer"
                            className="flex items-center gap-1 text-[10px] bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 px-2 py-1 rounded text-gray-600 dark:text-gray-400 transition-colors">
                            <span className="material-symbols-outlined text-sm">open_in_new</span>
                            <span className="truncate max-w-[100px]">{chunk.web.title}</span>
                          </a>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-3 bg-white dark:bg-gray-900 border-t border-gray-300 dark:border-gray-700">
            <form onSubmit={handleSend} className="relative flex items-center gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={agentMode === 'investor' ? 'Ask about market data...' : 'Enter Address & Upset Price...'}
                className="flex-1 bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:border-purple-500 transition-colors"
              />
              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className="p-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg disabled:opacity-50 transition-colors flex items-center justify-center"
              >
                <span className="material-symbols-outlined text-lg">send</span>
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Toggle Button */}
      {!isOpen && (
        <button
          onClick={() => { setIsOpen(true); setIsExpanded(false); }}
          className="w-14 h-14 bg-purple-600 hover:bg-purple-700 text-white rounded-full shadow-lg hover:shadow-purple-500/25 transition-all duration-300 flex items-center justify-center group"
        >
          <span className="material-symbols-outlined text-3xl group-hover:scale-110 transition-transform">chat</span>
          <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full border-2 border-white animate-pulse"></span>
        </button>
      )}
      </div>

      {/* API Key Entry Modal */}
      {showApiKeyEntry && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white dark:bg-gray-900 rounded-2xl p-6 max-w-md w-full shadow-2xl">
            <div className="w-12 h-12 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="material-symbols-outlined text-2xl text-red-500">vpn_key</span>
            </div>
            <h3 className="text-xl font-bold text-center text-gray-900 dark:text-white mb-2">API Key Required</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 text-center mb-6">
              The Gemini API key is not configured. Enter your key below to continue.
            </p>
            <div className="space-y-4">
              <input
                type="password"
                value={apiKeyInput}
                onChange={(e) => setApiKeyInput(e.target.value)}
                placeholder="AIza..."
                className="w-full bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-xl px-4 py-3 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                autoFocus
                onKeyDown={(e) => e.key === 'Enter' && handleSaveApiKey()}
              />
              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setShowApiKeyEntry(false)
                    setApiKeyInput('')
                  }}
                  className="flex-1 py-3 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-xl font-medium transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveApiKey}
                  disabled={!apiKeyInput.trim()}
                  className="flex-1 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-xl font-medium transition-colors disabled:opacity-50"
                >
                  Save Key
                </button>
              </div>
            </div>
            <p className="text-xs text-gray-400 dark:text-gray-500 text-center mt-4">
              Stored securely in your browser's local storage.
            </p>
          </div>
        </div>
      )}
    </>
  )
}
