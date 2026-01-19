import { Suspense } from 'react'
import { AuctionHistoryClient } from './AuctionHistoryClient'
import { createClient } from '@/utils/supabase/server'

async function getPastAuctionProperties() {
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

    // Get total count first
    const { count: totalCount } = await supabase
      .from('foreclosure_listings')
      .select('id', { count: 'exact', head: true })

    const total_count = totalCount || 0

    // Fetch all properties (filtering will happen client-side)
    const allData: any[] = []
    const batchSize = 1000
    const maxFetch = 10000
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
      }

      currentOffset += batchSize

      // If we got fewer results than batch size, we've reached the end
      if (!data || data.length < batchSize) {
        break
      }
    }

    // Filter for past auctions on server side (initial filter)
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const pastAuctions = allData.filter(property => {
      if (!property.sale_date) return false
      const auctionDate = new Date(property.sale_date)
      return auctionDate < today
    })

    return {
      properties: pastAuctions,
      count: pastAuctions.length
    }
  } catch (error) {
    console.error('Error in getPastAuctionProperties:', error)
    return {
      properties: [],
      count: 0
    }
  }
}

export default async function AuctionHistoryPage() {
  const initialData = await getPastAuctionProperties()

  return (
    <Suspense fallback={<AuctionHistoryLoadingSkeleton />}>
      <AuctionHistoryClient initialData={initialData} />
    </Suspense>
  )
}

function AuctionHistoryLoadingSkeleton() {
  return (
    <div className="h-screen flex overflow-hidden bg-gray-50 dark:bg-background-dark">
      <div className="w-20 lg:w-64 flex-shrink-0 border-r border-gray-200 dark:border-border-dark bg-white dark:bg-background-dark" />
      <main className="flex-1 flex flex-col h-full">
        <div className="h-16 border-b border-gray-200 dark:border-border-dark bg-white dark:bg-surface-dark animate-pulse" />
        <div className="flex-1 p-3 lg:p-8">
          <div className="max-w-[1600px] mx-auto space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-32 bg-white dark:bg-surface-dark rounded-xl border border-gray-200 dark:border-border-dark animate-pulse" />
              ))}
            </div>
            <div className="h-16 bg-white dark:bg-surface-dark rounded-xl border border-gray-200 dark:border-border-dark animate-pulse" />
          </div>
        </div>
      </main>
    </div>
  )
}
