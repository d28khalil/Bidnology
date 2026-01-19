import { Suspense } from 'react'
import { PropertyPageClient } from './PropertyPageClient'
import { createClient } from '@/utils/supabase/server'
import { notFound } from 'next/navigation'

async function getProperty(id: string) {
  try {
    const supabase = await createClient()

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
      refined_description,
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

    const { data, error } = await supabase
      .from('foreclosure_listings')
      .select(columns)
      .eq('id', id)
      .single()

    if (error || !data) {
      return null
    }

    return data
  } catch (error) {
    console.error('Error fetching property:', error)
    return null
  }
}

export async function generateMetadata({ params }: { params: { id: string } }) {
  const property = await getProperty(params.id)

  if (!property) {
    return {
      title: 'Property Not Found | Bidnology',
    }
  }

  return {
    title: `${property.property_address} - ${property.city}, ${property.state} | Bidnology`,
    description: `View foreclosure auction details for ${property.property_address}, ${property.city}, ${property.state}. Auction Date: ${property.sale_date}. Opening Bid: $${property.opening_bid?.toLocaleString()}.`,
  }
}

export default async function PropertyPage({ params }: { params: { id: string } }) {
  const property = await getProperty(params.id)

  if (!property) {
    notFound()
  }

  return (
    <Suspense fallback={
      <div className="h-screen flex items-center justify-center bg-background-dark">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-400">Loading property...</p>
        </div>
      </div>
    }>
      <PropertyPageClient property={property} />
    </Suspense>
  )
}
