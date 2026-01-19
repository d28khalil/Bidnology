'use client'

import { useState, useEffect, useRef } from 'react'
import { createClient } from '@/utils/supabase/client'
import { Property } from '@/lib/types/property'
import {
  generateCacheKey,
  getCachedProperties,
  setCachedProperties,
  clearCacheKey,
} from '@/lib/utils/propertyCache'

interface PropertyListResponse {
  count: number
  properties: Property[]
}

interface UsePropertiesOptions {
  county_id?: number
  state?: string
  city?: string
  property_status?: string
  min_upset_price?: number
  max_upset_price?: number
  limit?: number
  offset?: number
  search?: string
  order_by?: string
  order?: 'asc' | 'desc' | null
  property_ids?: number[]  // Filter by specific property IDs
  enrichment_status?: string  // Filter by enrichment status
  initialData?: { properties: Property[]; count: number }  // SSR initial data
  enableCache?: boolean  // Enable/disable caching (default: true)
  cacheTTL?: number  // Cache TTL in milliseconds (default: 5 minutes)
  bypassCache?: boolean  // Force refetch, bypassing cache
}

interface UsePropertiesResult {
  properties: Property[]
  count: number
  isLoading: boolean
  error: string | null
  isFromCache: boolean
  refetch: () => Promise<void>
  clearCache: () => void
  updateProperty: (propertyId: number) => Promise<void>
}

// Columns to select from foreclosure_listings with left join to zillow_enrichment
const PROPERTY_COLUMNS = `
  id,
  property_id,
  sheriff_number,
  case_number,
  property_address,
  city,
  state,
  zip_code,
  county_name,
  sale_date,
  sale_time,
  court_name,
  property_status,
  status_detail,
  status_history,
  opening_bid,
  approx_upset,
  judgment_amount,
  minimum_bid,
  sale_price,
  plaintiff,
  plaintiff_attorney,
  defendant,
  property_type,
  lot_size,
  filing_date,
  judgment_date,
  writ_date,
  sale_terms,
  attorney_notes,
  general_notes,
  description,
  details_url,
  data_source_url,
  zillow_zpid,
  zillow_enrichment_status,
  zillow_enriched_at,
  zillow_enrichment!left(
    zpid,
    zestimate,
    zestimate_low,
    zestimate_high,
    bedrooms,
    bathrooms,
    sqft,
    year_built,
    lot_size,
    property_type,
    last_sold_date,
    last_sold_price,
    images,
    tax_assessment,
    tax_assessment_year,
    tax_billed,
    walk_score,
    transit_score,
    bike_score,
    tax_history,
    price_history,
    zestimate_history,
    climate_risk,
    comps,
    similar_properties,
    nearby_properties,
    skip_tracing
  ),
  created_at,
  updated_at
`

/**
 * Helper function to build Supabase query with filters
 */
function buildQuery(options: UsePropertiesOptions, supabase: ReturnType<typeof createClient>) {
  let query = supabase.from('foreclosure_listings').select(PROPERTY_COLUMNS, { count: 'exact' })

  // Apply filters
  if (options.county_id !== undefined) query = query.eq('county_id', options.county_id)
  if (options.state) query = query.eq('state', options.state.toUpperCase())
  if (options.city) query = query.eq('city', options.city)
  if (options.property_status) query = query.eq('property_status', options.property_status)
  if (options.min_upset_price !== undefined) query = query.gte('approx_upset', options.min_upset_price)
  if (options.max_upset_price !== undefined) query = query.lte('approx_upset', options.max_upset_price)
  if (options.enrichment_status) query = query.eq('zillow_enrichment_status', options.enrichment_status)
  if (options.property_ids && options.property_ids.length > 0) {
    query = query.in('id', options.property_ids)
  }
  if (options.search) {
    query = query.or(`property_address.ilike.%${options.search}%,city.ilike.%${options.search}%`)
  }

  // Apply ordering
  // For zestimate in joined table, we can't sort server-side - will be done client-side
  const isZestimateSort = options.order_by?.includes('zillow_enrichment')
  if (options.order_by && options.order && !isZestimateSort) {
    // For monetary columns, when sorting descending, we need to ensure NULLs sort last
    // Use nullsFirst: false for descending order to put NULL values at the end
    const isDescending = options.order === 'desc'
    query = query.order(options.order_by, {
      ascending: options.order === 'asc',
      nullsFirst: !isDescending // NULLs first for ascending, last for descending
    })
  }

  return query
}

/**
 * Fetch properties with batch handling for Supabase 1000 row limit
 */
async function fetchPropertiesBatched(
  options: UsePropertiesOptions,
  limit: number,
  offset: number
): Promise<{ properties: Property[]; count: number }> {
  const supabase = createClient()

  // Build base query for count
  const countQuery = buildQuery({ ...options, limit: undefined, offset: undefined }, supabase)
  const { count, error: countError } = await countQuery

  if (countError) {
    throw new Error(countError.message)
  }

  const totalCount = count || 0
  const batchSize = 1000
  const allData: any[] = []
  let currentOffset = offset
  let remaining = limit

  // Check if zestimate sort - will need client-side sorting
  const isZestimateSort = options.order_by?.includes('zillow_enrichment')

  // Fetch in batches to handle Supabase's 1000 row limit
  while (remaining > 0 && currentOffset < Math.min(offset + limit, totalCount)) {
    const currentBatchSize = Math.min(batchSize, remaining, totalCount - currentOffset)
    let dataQuery = buildQuery(options, supabase)

    // Note: Ordering is already applied in buildQuery for non-zestimate columns

    const { data, error } = await dataQuery.range(currentOffset, currentOffset + currentBatchSize - 1)

    if (error) {
      throw new Error(error.message)
    }

    if (data) {
      allData.push(...data)
      remaining -= data.length
      currentOffset += data.length

      if (data.length < currentBatchSize) break
    } else {
      break
    }
  }

  // Client-side sorting for zestimate (from joined table)
  let properties = allData as Property[]
  if (isZestimateSort && options.order) {
    properties.sort((a, b) => {
      const aZestimate = a.zillow_enrichment?.[0]?.zestimate ?? 0
      const bZestimate = b.zillow_enrichment?.[0]?.zestimate ?? 0
      return options.order === 'desc' ? bZestimate - aZestimate : aZestimate - bZestimate
    })
  }

  return { properties, count: totalCount }
}

export function useProperties(options: UsePropertiesOptions = {}): UsePropertiesResult {
  const [properties, setProperties] = useState<Property[]>(options.initialData?.properties || [])
  const [count, setCount] = useState(options.initialData?.count || 0)
  const [isLoading, setIsLoading] = useState(!options.initialData)
  const [error, setError] = useState<string | null>(null)
  const [isFromCache, setIsFromCache] = useState(false)

  // Use a ref to track if this is the initial mount with initialData
  const initialDataLoadedRef = useRef(!!options.initialData)

  // Cache options
  const enableCache = options.enableCache !== false // Default to true
  const cacheTTL = options.cacheTTL || 5 * 60 * 1000 // Default 5 minutes
  const bypassCache = options.bypassCache || false

  useEffect(() => {
    // Skip fetching on initial mount if we have SSR initialData
    // This prevents the double reload issue
    if (initialDataLoadedRef.current) {
      initialDataLoadedRef.current = false
      return
    }

    // Generate cache key
    const cacheKey = generateCacheKey(options)

    // Check cache first (if enabled and not bypassing)
    if (enableCache && !bypassCache) {
      const cached = getCachedProperties(cacheKey)
      if (cached) {
        setProperties(cached.properties)
        setCount(cached.count)
        setIsLoading(false)
        setIsFromCache(true)
        setError(null)
        return
      }
    }

    setIsLoading(true)
    setIsFromCache(false)

    const fetchProperties = async () => {
      setError(null)

      try {
        const limit = options.limit || 50
        const offset = options.offset || 0

        const result = await fetchPropertiesBatched(options, limit, offset)
        setProperties(result.properties)
        setCount(result.count)

        // Cache the results if enabled
        if (enableCache) {
          setCachedProperties(cacheKey, result.properties, result.count, cacheTTL, {
            queryKey: cacheKey,
            county_id: options.county_id,
            state: options.state,
            city: options.city,
            property_status: options.property_status,
            min_upset_price: options.min_upset_price,
            max_upset_price: options.max_upset_price,
            search: options.search,
          })
        }
      } catch (err) {
        console.error('Error fetching properties:', err)
        setError(err instanceof Error ? err.message : 'Failed to fetch properties')
        setProperties([])
        setCount(0)
      } finally {
        setIsLoading(false)
      }
    }

    fetchProperties()
  }, [
    options.county_id,
    options.state,
    options.city,
    options.property_status,
    options.min_upset_price,
    options.max_upset_price,
    options.search,
    options.order_by,
    options.order,
    options.property_ids?.join(','),
    options.enrichment_status,
    options.limit,
    options.offset,
    enableCache,
    cacheTTL,
    bypassCache,
  ])

  const refetch = async () => {
    setIsLoading(true)
    setIsFromCache(false)
    setError(null)

    const cacheKey = generateCacheKey(options)

    try {
      const limit = options.limit || 50
      const offset = options.offset || 0

      const result = await fetchPropertiesBatched(options, limit, offset)
      setProperties(result.properties)
      setCount(result.count)

      // Update cache
      if (enableCache) {
        setCachedProperties(cacheKey, result.properties, result.count, cacheTTL, {
          queryKey: cacheKey,
          county_id: options.county_id,
          state: options.state,
          city: options.city,
          property_status: options.property_status,
          min_upset_price: options.min_upset_price,
          max_upset_price: options.max_upset_price,
          search: options.search,
        })
      }
    } catch (err) {
      console.error('Error fetching properties:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch properties')
      setProperties([])
      setCount(0)
    } finally {
      setIsLoading(false)
    }
  }

  // Clear cache for current query
  const clearCache = () => {
    const cacheKey = generateCacheKey(options)
    clearCacheKey(cacheKey)
  }

  // Update a single property in the local state (for skip trace updates)
  // This avoids refetching all properties which causes page reload
  const updateProperty = async (propertyId: number) => {
    try {
      const supabase = createClient()

      // Fetch the specific property with fresh enrichment data
      const { data, error } = await supabase
        .from('foreclosure_listings')
        .select(PROPERTY_COLUMNS)
        .eq('id', propertyId)
        .single()

      if (error) {
        console.error('Error updating property:', error)
        return
      }

      if (data) {
        // Update just this property in the local state
        setProperties(prev =>
          prev.map(p => p.id === propertyId ? data as Property : p)
        )

        // Invalidate cache for this query since data changed
        if (enableCache) {
          clearCache()
        }
      }
    } catch (err) {
      console.error('Error updating property:', err)
    }
  }

  return {
    properties,
    count,
    isLoading,
    error,
    isFromCache,
    refetch,
    clearCache,
    updateProperty,
  }
}

/**
 * Transform backend Property to frontend PropertyRow format
 * This adapts the backend schema to what the UI components expect
 *
 * Investor-Focused Metrics:
 * - Spread: (ARV - Opening Bid) / Opening Bid * 100
 * - ARV: Zestimate from enrichment or fallback to approx_upset
 * - Opening Bid: opening_bid field or approx_upset fallback
 * - AI Status: Based on enrichment quality and deal spread
 */
export function transformPropertyToRow(
  property: Property,
  overrides?: {
    approxUpsetOverride?: number
    approxJudgmentOverride?: number
    startingBidOverride?: number
    bidCapOverride?: number
    propertySoldOverride?: string | number  // ISO timestamp or sale price
  }
): {
  id: string
  address: string
  city: string
  state: string
  zip: string
  county?: string
  image: string
  auctionDate: string
  status?: string
  beds?: number
  baths?: number
  sqft?: number
  openingBid: number
  approxUpset?: number
  approxJudgment?: number
  zestimate?: number
  estimatedARV: number
  spread: number
  aiConfidence: number
  aiStatus: 'excellent' | 'good' | 'warning' | 'caution'
  zpid?: number
  zillowUrl?: string
  googleMapsUrl?: string
  taxHistoryCount?: number
  taxHistoryData?: any[]
  comparablesCount?: number
  comparablesData?: any[]
  skipTraceData?: any
  streetViewImages?: any
  yearBuilt?: number
  lotSize?: number
  lastSoldDate?: string
  lastSoldPrice?: number
  zestimateLow?: number
  zestimateHigh?: number
  rentZestimate?: number
  climateRisk?: {
    flood?: number
    fire?: number
    storm?: number
  }
  ownerInfo?: {
    name?: string
    agent?: string
  }
  dayOfWeek?: string
  hasTaxHistory?: boolean
  hasComparables?: boolean
  hasSkipTrace?: boolean
  hasStreetView?: boolean
  // Auction details
  description?: string
  sheriff_number?: string
  plaintiff?: string
  plaintiff_attorney?: string
  defendant?: string
  statusHistory?: Array<{ date: string; status: string }>
  // Override values
  approxUpsetOverride?: number
  approxJudgmentOverride?: number
  startingBidOverride?: number
  bidCapOverride?: number
  propertySoldOverride?: string | number  // ISO timestamp or sale price
} {
  // ========================================================================
  // FINANCIALS CALCULATION (The Deal Math)
  // ========================================================================
  const openingBid = property.opening_bid || property.approx_upset || 0

  // zillow_enrichment comes as an array from Supabase left join: null or [{...}]
  const enrichment = property.zillow_enrichment && property.zillow_enrichment.length > 0
    ? property.zillow_enrichment[0]
    : null

  // Raw zestimate from Zillow (may be undefined if not enriched)
  const zestimate = enrichment?.zestimate

  // estimatedARV falls back to approx_upset if no zestimate
  const estimatedARV = zestimate || property.approx_upset || 0

  // Spread calculation: (Zestimate - higher of approx_judgment/approx_upset) / higher price
  // Use the higher of approx_upset or judgment_amount as the cost basis
  // Use override values if provided, otherwise use original property values
  const upsetPrice = overrides?.approxUpsetOverride ?? property.approx_upset ?? 0
  const judgmentPrice = overrides?.approxJudgmentOverride ?? property.judgment_amount ?? 0
  const higherPrice = Math.max(upsetPrice, judgmentPrice)

  // Calculate spread: (Zestimate - Higher of upset/judgment) / Higher price
  // If we have a zestimate, use it with the higher price; otherwise use fallback
  const basePrice = higherPrice > 0 ? higherPrice : openingBid
  const resaleValue = zestimate || estimatedARV
  const spread = basePrice > 0 ? ((resaleValue - basePrice) / basePrice) * 100 : 0

  // ========================================================================
  // AI CONFIDENCE & STATUS (Data Quality Indicator)
  // ========================================================================
  let aiStatus: 'excellent' | 'good' | 'warning' | 'caution' = 'caution'
  let aiConfidence = 50

  if (property.zillow_enrichment_status === 'fully_enriched') {
    aiConfidence = 85
    if (spread > 30) {
      aiStatus = 'excellent'
      aiConfidence = 92
    } else if (spread > 20) {
      aiStatus = 'good'
      aiConfidence = 85
    } else if (spread > 10) {
      aiStatus = 'warning'
      aiConfidence = 75
    }
  } else if (property.zillow_enrichment_status === 'auto_enriched') {
    aiConfidence = 70
    aiStatus = spread > 20 ? 'good' : 'warning'
  }

  // ========================================================================
  // AUCTION DATE FORMATTING
  // ========================================================================
  const auctionDate = property.sale_date
    ? new Date(property.sale_date).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
    : 'TBD'

  // Day of week from sale_date
  const dayOfWeek = property.sale_date
    ? new Date(property.sale_date).toLocaleDateString('en-US', { weekday: 'long' })
    : undefined

  // ========================================================================
  // PROPERTY IMAGE
  // ========================================================================
  // Use local house PNG placeholder for properties without images
  const image =
    enrichment?.images?.[0] || '/house-placeholder.png'

  // ========================================================================
  // ZILLOW LINK
  // ========================================================================
  const zpid = enrichment?.zpid || property.zillow_zpid
  const zillowUrl = zpid ? `https://www.zillow.com/homedetails/${zpid}_zpid/` : undefined

  // ========================================================================
  // GOOGLE MAPS LINK
  // ========================================================================
  const fullAddress = `${property.property_address}, ${property.city || ''} ${property.state || ''} ${property.zip_code || ''}`.trim().replace(/\s+,/, ',').replace(/,\s*,/, ',')
  const googleMapsUrl = fullAddress ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(fullAddress)}` : undefined

  // ========================================================================
  // PROPERTY SPECS (from enrichment)
  // ========================================================================
  const beds = enrichment?.bedrooms
  const baths = enrichment?.bathrooms
  const sqft = enrichment?.sqft

  // ========================================================================
  // ACTUAL DATA COUNTS (instead of boolean checkmarks)
  // ========================================================================
  const taxHistoryCount = enrichment?.tax_history?.length || 0
  const taxHistoryData = enrichment?.tax_history || []
  const comparablesCount = enrichment?.comps?.length ||
                          enrichment?.similar_properties?.length || 0
  const comparablesData = enrichment?.comps || enrichment?.similar_properties || []
  const skipTraceData = enrichment?.skip_tracing
  const streetViewImages = enrichment?.street_view_images

  // Additional enrichment data
  const yearBuilt = enrichment?.year_built
  const lotSize = enrichment?.lot_size
  const lastSoldDate = enrichment?.last_sold_date
  const lastSoldPrice = enrichment?.last_sold_price
  const zestimateLow = enrichment?.zestimate_low
  const zestimateHigh = enrichment?.zestimate_high
  const rentZestimate = enrichment?.rent_zestimate
  const climateRisk = enrichment?.climate_risk
  const ownerInfo = enrichment?.owner_info

  return {
    id: property.id.toString(),
    address: property.property_address,
    city: property.city || '',
    state: property.state || '',
    zip: property.zip_code || '',
    county: property.county_name,
    image,
    auctionDate,
    status: property.property_status,
    beds,
    baths,
    sqft,
    openingBid,
    approxUpset: property.approx_upset,
    approxJudgment: property.judgment_amount,
    zestimate,
    estimatedARV,
    spread: Math.max(0, spread),
    aiConfidence,
    aiStatus,
    zpid,
    zillowUrl,
    googleMapsUrl,
    // Pass actual counts/data instead of booleans
    taxHistoryCount,
    taxHistoryData,
    comparablesCount,
    comparablesData,
    skipTraceData,
    streetViewImages,
    // Additional enrichment data
    yearBuilt,
    lotSize,
    lastSoldDate,
    lastSoldPrice,
    zestimateLow,
    zestimateHigh,
    rentZestimate,
    climateRisk,
    ownerInfo,
    dayOfWeek,
    // Keep booleans for backward compatibility
    hasTaxHistory: taxHistoryCount > 0,
    hasComparables: comparablesCount > 0,
    hasSkipTrace: !!skipTraceData,
    hasStreetView: !!streetViewImages,
    // Auction details
    description: property.description,
    sheriff_number: property.sheriff_number,
    plaintiff: property.plaintiff,
    plaintiff_attorney: property.plaintiff_attorney,
    defendant: property.defendant,
    statusHistory: property.status_history,
    // Override values (if provided)
    approxUpsetOverride: overrides?.approxUpsetOverride,
    approxJudgmentOverride: overrides?.approxJudgmentOverride,
    startingBidOverride: overrides?.startingBidOverride,
    bidCapOverride: overrides?.bidCapOverride,
    propertySoldOverride: overrides?.propertySoldOverride,
  }
}
