import { Suspense } from 'react'
import { HomePageClient } from './HomePageClient'
import { createClient } from '@/utils/supabase/server'

async function getInitialProperties() {
  try {
    const supabase = await createClient()

    // Columns to select from foreclosure_listings with left join to zillow_enrichment
    const columns = `
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
        nearby_properties
      ),
      created_at,
      updated_at
    `

    // Get total count first
    const { count: totalCount } = await supabase
      .from('foreclosure_listings')
      .select('id', { count: 'exact', head: true })

    const total_count = totalCount || 0

    // Supabase has a 1000 row limit per query, so fetch in batches
    const allData: any[] = []
    const batchSize = 1000
    const maxFetch = 10000  // Large limit for client-side pagination
    let currentOffset = 0

    while (currentOffset < Math.min(maxFetch, total_count)) {
      const { data, error } = await supabase
        .from('foreclosure_listings')
        .select(columns)
        .order('sale_date', { ascending: false })
        .range(currentOffset, currentOffset + batchSize - 1)

      if (error) {
        console.error('Error fetching properties from Supabase:', error)
        break
      }

      if (data) {
        allData.push(...data)
        if (data.length < batchSize) break  // Reached the end
      }
      currentOffset += batchSize
    }

    return {
      properties: allData,
      count: total_count,
    }
  } catch (error) {
    console.error('Error in getInitialProperties:', error)
    return { properties: [], count: 0 }
  }
}

export default async function HomePage() {
  // Fetch data on the server for faster initial load
  const initialData = await getInitialProperties()

  return (
    <Suspense fallback={
      <div className="h-screen flex items-center justify-center bg-background-dark">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-400">Loading...</p>
        </div>
      </div>
    }>
      <HomePageClient initialData={initialData} />
    </Suspense>
  )
}
