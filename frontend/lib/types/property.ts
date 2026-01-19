// ============================================================================
// PROPERTY TYPES - Matching Backend API (Investor-Focused Organization)
// ============================================================================

/**
 * Property type matching the backend enrichment_routes.py /properties endpoint.
 * Fields are organized by investor decision-making priority:
 * 1. PROPERTY IDENTIFICATION - Address, location
 * 2. AUCTION DETAILS - When/Where
 * 3. FINANCIALS - The Deal Math
 * 4. LEGAL PARTIES
 * 5. PROPERTY SPECS - For Repair Estimates
 * 6. ADDITIONAL INFO
 * 7. ENRICHMENT STATUS - Data quality indicator
 * 8. ENRICHED DATA - Zillow data (via left join)
 */
export interface Property {
  // ========================================================================
  // PROPERTY IDENTIFICATION
  // ========================================================================
  id: number
  property_id?: number
  sheriff_number?: string
  case_number?: string
  property_address: string
  city?: string
  state?: string
  zip_code?: string
  county_name?: string

  // ========================================================================
  // AUCTION DETAILS (When/Where)
  // ========================================================================
  sale_date?: string
  sale_time?: string
  court_name?: string
  property_status?: 'scheduled' | 'adjourned' | 'sold' | 'cancelled'
  status_detail?: string
  status_history?: Array<{ date: string; status: string }>

  // ========================================================================
  // FINANCIALS (The Deal Math)
  // ========================================================================
  opening_bid?: number
  approx_upset?: number
  judgment_amount?: number
  minimum_bid?: number
  sale_price?: number

  // ========================================================================
  // LEGAL PARTIES
  // ========================================================================
  plaintiff?: string
  plaintiff_attorney?: string
  defendant?: string

  // ========================================================================
  // PROPERTY SPECS (For Repair Estimates)
  // ========================================================================
  property_type?: string
  lot_size?: number

  // ========================================================================
  // ADDITIONAL INFO
  // ========================================================================
  filing_date?: string
  judgment_date?: string
  writ_date?: string
  sale_terms?: string
  attorney_notes?: string
  general_notes?: string
  description?: string
  refined_description?: string
  details_url?: string
  data_source_url?: string

  // ========================================================================
  // ENRICHMENT STATUS (Data Quality Indicator)
  // ========================================================================
  zillow_zpid?: number
  zillow_enrichment_status?: 'pending' | 'auto_enriched' | 'fully_enriched' | 'failed' | 'not_enriched'
  zillow_enriched_at?: string

  // ========================================================================
  // ENRICHED DATA (from zillow_enrichment table via left join)
  // Note: Supabase returns this as an array (null if empty, [{...}] if has data)
  // ========================================================================
  zillow_enrichment?: ZillowEnrichment[] | null

  // ========================================================================
  // TIMESTAMPS
  // ========================================================================
  created_at?: string
  updated_at?: string
}

/**
 * ZillowEnrichment type - data joined from zillow_enrichment table via left join.
 * Contains the fields returned by the backend /properties endpoint.
 */
export interface ZillowEnrichment {
  zpid?: number
  // Valuation (for ARV/spread calculation)
  zestimate?: number
  zestimate_low?: number
  zestimate_high?: number
  // Property specs
  bedrooms?: number
  bathrooms?: number
  sqft?: number
  year_built?: number
  lot_size?: number
  property_type?: string
  // Sales history
  last_sold_date?: string
  last_sold_price?: number
  // Images array (JSONB field)
  images?: string[]
  // Tax data (ongoing cost for investors)
  tax_assessment?: number
  tax_assessment_year?: number
  tax_billed?: number
  tax_history?: any[]
  // Walkability scores
  walk_score?: number
  transit_score?: number
  bike_score?: number
  // Zestimate history
  zestimate_history?: any[]
  // Additional enrichment data (not in main properties endpoint but available in full enrichment)
  id?: number
  property_id?: number
  enrichment_status?: 'pending' | 'auto_enriched' | 'fully_enriched' | 'failed' | 'not_enriched'
  enriched_at?: string
  last_updated_at?: string
  enrichment_mode?: 'auto' | 'full'
  api_call_count?: number
  // Other JSONB fields (available but not in main endpoint)
  price_history?: any[]
  climate_risk?: any
  similar_properties?: any[]
  comps?: any[]  // Alias for comparables
  nearby_properties?: any[]
  raw_api_response?: Record<string, any>
  street_view_images?: Record<string, string>
  person_id?: string
  skip_trace_data?: Record<string, any>
  skip_tracing?: Record<string, any>
  skip_traced_at?: string
  rent_zestimate?: number
  owner_info?: {
    name?: string
    agent?: string
  }
}

export interface MarketAnomaly {
  id: number
  property_id: number
  is_anomaly: boolean
  z_score: number
  price_difference_percent: number
  comparable_count: number
  avg_comparable_price: number
  confidence_score: number
  analysis_date: string
  is_verified?: boolean
  feedback?: string
  verified_by?: string
  verified_at?: string
}

export interface ComparableSalesAnalysis {
  id: number
  property_id: number
  arv_estimate?: number
  confidence_score: number
  comparable_properties: any[]
  analysis_summary?: string
  created_at: string
  updated_at: string
}

export interface SavedProperty {
  id: number
  user_id: string
  property_id: number
  notes?: string
  kanban_stage: KanbanStage
  saved_at: string
  stage_updated_at: string
  foreclosure_listings?: Property
}

export type KanbanStage = 'researching' | 'analyzing' | 'due_diligence' | 'bidding' | 'won' | 'lost' | 'archived'

export interface WatchlistItem {
  id: number
  user_id: string
  property_id: number
  alert_on_price_change: boolean
  alert_on_status_change: boolean
  alert_on_new_comps: boolean
  alert_on_auction_near: boolean
  auction_alert_days: number
  watch_notes?: string
  priority: 'low' | 'normal' | 'high'
  created_at: string
  updated_at: string
  foreclosure_listings?: Property
}

export interface Alert {
  id: number
  user_id: string
  property_id: number
  alert_type: 'price_change' | 'status_change' | 'new_comps' | 'auction_near'
  title: string
  message: string
  is_read: boolean
  created_at: string
  foreclosure_listings?: Property
}

export interface DealCriteria {
  id?: number
  user_id: string
  county_id?: number
  // Deal criteria fields
  max_opening_bid?: number
  min_equity_spread?: number
  max_purchase_price?: number
  min_arv_spread?: number
  min_beds?: number
  max_beds?: number
  min_baths?: number
  min_sqft?: number
  property_types?: string[]
  sale_date_window_days?: number
  is_anomaly_only?: boolean
  counties?: number[]
  // Alert settings
  enable_alerts?: boolean
  created_at?: string
  updated_at?: string
}

export interface PropertyMatch {
  property_id: number
  match_score: number
  match_category: 'hot' | 'warm' | 'cold'
  criteria_met: Record<string, any>
  property?: Property
}

export interface DataQualityScore {
  property_id: number
  quality_score: number
  is_complete: boolean
  missing_fields: string[]
  tag?: string
  recommendation?: string
  created_at?: string
}

export interface County {
  id: number
  name: string
  state: string
}

// Filter types
export interface PropertyFilters {
  county_id?: number[]
  min_opening_bid?: number
  max_opening_bid?: number
  min_approx_upset?: number
  max_approx_upset?: number
  sale_date_from?: string
  sale_date_to?: string
  min_beds?: number
  max_beds?: number
  min_baths?: number
  min_sqft?: number
  property_status?: string[]
  hot_deals_only?: boolean
  my_matches_only?: boolean
  search?: string
}

// API Response wrappers
export interface PaginatedResponse<T> {
  data: T[]
  count: number
  page?: number
  limit?: number
}

export interface ApiErrorResponse {
  detail: string
}

// ============================================================================
// USER PROPERTY OVERRIDES - User-specific tracking with history
// ============================================================================

export interface PropertyOverrides {
  property_id: number
  approx_upset_override?: number | null
  judgment_amount_override?: number | null
  starting_bid_override?: number | null
  bid_cap_override?: number | null
  property_sold_override?: string | number | null  // ISO timestamp or sale price
}

export interface PropertyOverride {
  id: number
  user_id: string
  property_id: number
  field_name: 'approx_upset' | 'judgment_amount' | 'starting_bid' | 'bid_cap' | 'property_sold'
  original_value?: number | null
  new_value: number | string  // Can be number (price) or string (date timestamp)
  previous_spread?: number | null
  notes?: string | null
  created_at: string
}

export interface OverrideHistoryItem {
  id: number
  original_value?: number | null
  new_value: number | string  // Can be number (price) or string (date timestamp)
  previous_spread?: number | null
  notes?: string | null
  created_at: string
}
