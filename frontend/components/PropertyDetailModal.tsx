'use client'

import { useState, useEffect, useMemo } from 'react'
import { useUser } from '@/contexts/UserContext'
import { ShareSheet } from '@/components/ShareSheet'
import { PropertyNotes } from '@/components/PropertyNotes'
import { RefinedReport } from '@/components/RefinedReport'
import { analyzePropertyStream, exportAnalysisPdf, type AnalysisData } from '@/lib/AnalysisService'
import { getUserNote, getPropertyTags, refineDescription, type UserTag, type UserNote } from '@/lib/api/client'

// ============================================================================
// SKIP TRACE DISPLAY COMPONENT
// ============================================================================

interface SkipTraceDisplayProps {
  data: any
}

function SkipTraceDisplay({ data }: SkipTraceDisplayProps) {
  if (!data) return null

  // Helper to extract data from various Tracerfy response formats
  const extractOwners = (): Array<{ name?: string; phones?: string[]; emails?: string[] }> => {
    const owners: Array<{ name?: string; phones?: string[]; emails?: string[] }> = []

    // Handle the backend format_for_display format: {owners, phones, emails}
    if (data.owners && Array.isArray(data.owners)) {
      return data.owners
    }

    // Helper to build name from first/last name
    const buildName = (item: any): string | undefined => {
      // Try direct name fields first
      if (item.name) return item.name
      if (item.full_name) return item.full_name
      if (item.fullName) return item.fullName
      if (item.owner_name) return item.owner_name
      if (item.ownerName) return item.ownerName

      // Try first_name + last_name (raw Tracerfy format)
      const first = item.first_name || item.firstName || ''
      const last = item.last_name || item.lastName || ''
      if (first || last) {
        return `${first} ${last}`.trim()
      }

      return undefined
    }

    // Handle array format
    if (Array.isArray(data)) {
      for (const item of data) {
        if (typeof item === 'object' && item !== null) {
          owners.push({
            name: buildName(item),
            phones: extractPhones(item),
            emails: extractEmails(item),
          })
        }
      }
    }
    // Handle single object format
    else if (typeof data === 'object' && data !== null) {
      // Check if it has a data/results property
      const nestedData = data.data || data.results || data.records
      if (nestedData && Array.isArray(nestedData)) {
        for (const item of nestedData) {
          if (typeof item === 'object' && item !== null) {
            owners.push({
              name: buildName(item),
              phones: extractPhones(item),
              emails: extractEmails(item),
            })
          }
        }
      } else {
        // Direct object
        owners.push({
          name: buildName(data),
          phones: extractPhones(data),
          emails: extractEmails(data),
        })
      }
    }

    return owners.filter(o => o.name || o.phones?.length || o.emails?.length)
  }

  const extractPhones = (item: any): string[] => {
    const phones: string[] = []

    // Direct fields
    if (item.phone) phones.push(item.phone)
    if (item.phone_number) phones.push(item.phone_number)
    if (item.phoneNumber) phones.push(item.phoneNumber)
    if (item.contact_phone) phones.push(item.contact_phone)

    // Raw Tracerfy fields: mobile_1, mobile_2, etc.
    for (let i = 1; i <= 5; i++) {
      const mobile = item[`mobile_${i}`]
      const landline = item[`landline_${i}`]
      if (mobile) phones.push(mobile)
      if (landline) phones.push(landline)
    }

    // Raw Tracerfy primary_phone
    if (item.primary_phone) phones.push(item.primary_phone)

    // Array fields
    if (Array.isArray(item.phones)) {
      for (const p of item.phones) {
        if (typeof p === 'string') phones.push(p)
        else if (p?.number || p?.phone) phones.push(p.number || p.phone)
      }
    }
    if (Array.isArray(item.phone_numbers)) {
      for (const p of item.phone_numbers) {
        if (typeof p === 'string') phones.push(p)
        else if (p?.number || p?.phone) phones.push(p.number || p.phone)
      }
    }

    return phones.filter(p => p && p !== '')
  }

  const extractEmails = (item: any): string[] => {
    const emails: string[] = []

    if (item.email) emails.push(item.email)
    if (item.email_address) emails.push(item.email_address)
    if (item.emailAddress) emails.push(item.emailAddress)

    // Raw Tracerfy fields: email_1, email_2, etc.
    for (let i = 1; i <= 5; i++) {
      const email = item[`email_${i}`]
      if (email) emails.push(email)
    }

    if (Array.isArray(item.emails)) {
      for (const e of item.emails) {
        if (typeof e === 'string') emails.push(e)
        else if (e?.address || e?.email) emails.push(e.address || e.email)
      }
    }
    if (Array.isArray(item.email_addresses)) {
      for (const e of item.email_addresses) {
        if (typeof e === 'string') emails.push(e)
        else if (e?.address || e?.email) emails.push(e.address || e.email)
      }
    }

    return emails.filter(e => e && e !== '')
  }

  const owners = extractOwners()

  if (owners.length === 0) {
    return (
      <div className="text-gray-500 dark:text-gray-500 text-sm italic">
        No contact information available
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {owners.map((owner, idx) => (
        <div key={idx} className="border border-gray-300 dark:border-border-dark rounded-lg p-3 bg-white dark:bg-background-dark overflow-hidden">
          {owner.name && (
            <div className="flex items-center gap-2 mb-2 min-w-0">
              <span className="material-symbols-outlined text-primary text-sm shrink-0">person</span>
              <span className="text-gray-900 dark:text-white font-medium truncate">{owner.name}</span>
            </div>
          )}

          <div className="space-y-2 ml-7">
            {/* Phone Numbers */}
            {owner.phones && owner.phones.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {owner.phones.map((phone, phoneIdx) => (
                  <a
                    key={phoneIdx}
                    href={`tel:${phone}`}
                    className="inline-flex items-center gap-1 px-2 py-1 bg-emerald-100 dark:bg-emerald-500/10 border border-emerald-300 dark:border-emerald-500/20 rounded text-emerald-700 dark:text-emerald-400 text-sm hover:bg-emerald-200 dark:hover:bg-emerald-500/20 transition-colors"
                  >
                    <span className="material-symbols-outlined text-[14px] shrink-0">call</span>
                    <span className="truncate">{phone}</span>
                  </a>
                ))}
              </div>
            )}

            {/* Email Addresses */}
            {owner.emails && owner.emails.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {owner.emails.map((email, emailIdx) => (
                  <a
                    key={emailIdx}
                    href={`mailto:${email}`}
                    className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 dark:bg-blue-500/10 border border-blue-300 dark:border-blue-500/20 rounded text-blue-700 dark:text-blue-400 text-sm hover:bg-blue-200 dark:hover:bg-blue-500/20 transition-colors"
                  >
                    <span className="material-symbols-outlined text-[14px] shrink-0">email</span>
                    <span className="truncate">{email}</span>
                  </a>
                ))}
              </div>
            )}

            {/* No contact info warning */}
            {!owner.phones?.length && !owner.emails?.length && (
              <p className="text-gray-500 dark:text-gray-500 text-xs">No contact details available</p>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

// ============================================================================
// ZONING ANALYSIS DISPLAY COMPONENT
// ============================================================================

interface ZoningAnalysisDisplayProps {
  data: any
}

function ZoningAnalysisDisplay({ data }: ZoningAnalysisDisplayProps) {
  const [view, setView] = useState<'refined' | 'scratchpad' | 'raw'>('refined')

  if (!data) return null

  const formatCurrency = (val: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val)
  const formatNumber = (val: number) => new Intl.NumberFormat('en-US').format(val)

  // Extract data from the nested zoning_analysis structure
  const zoningAnalysis = data.zoning_analysis || data.zoning || data.zoningAnalysis || data

  // Nested data extraction - all data is inside zoning_analysis
  const zoningOrdinance = zoningAnalysis.zoning_ordinance_summary || zoningAnalysis.ordinance || {}
  const propertyDetails = zoningAnalysis.property_details || data.property_details || {}
  const auctionAnalysisRaw = zoningAnalysis.auction_price_analysis || data.auction_price_analysis || data.auction_analysis || {}
  const highestBestUseData = zoningAnalysis.highest_and_best_use_analysis || data.highest_and_best_use_analysis || data.highest_and_best_use_scenarios || data.highestAndBestUse || {}
  const investmentStrategies = zoningAnalysis.investment_strategies || data.investment_strategies || data.investment_strategies_ranked || []
  const verificationChecklist = zoningAnalysis.verification_checklist || data.verification_checklist || []

  // Normalize auction analysis data from different structures
  const scenarios = auctionAnalysisRaw.property_worth_scenarios || auctionAnalysisRaw.scenarios || {}
  const maxBid = auctionAnalysisRaw.maximum_unprofitable_bid || auctionAnalysisRaw.max_bid || {}
  const auctionAnalysis = {
    upset_amount: auctionAnalysisRaw.upset_amount,
    conservative_valuation: scenarios.conservative_scenario?.estimate || scenarios.conservative?.estimate || auctionAnalysisRaw.conservative_valuation,
    conservative_rationale: scenarios.conservative_scenario?.description || scenarios.conservative?.description || auctionAnalysisRaw.conservative_rationale,
    moderate_valuation: scenarios.moderate_scenario?.estimate || scenarios.moderate?.estimate || auctionAnalysisRaw.moderate_valuation,
    moderate_rationale: scenarios.moderate_scenario?.description || scenarios.moderate?.description || auctionAnalysisRaw.moderate_rationale,
    optimistic_valuation: scenarios.optimistic_scenario?.estimate || scenarios.optimistic?.estimate || auctionAnalysisRaw.optimistic_valuation,
    optimistic_rationale: scenarios.optimistic_scenario?.description || scenarios.optimistic?.description || auctionAnalysisRaw.optimistic_rationale,
    maximum_unprofitable_bid: maxBid.bid_price || maxBid.price || auctionAnalysisRaw.maximum_unprofitable_bid,
    max_bid_rationale: maxBid.description || auctionAnalysisRaw.max_bid_rationale,
    analysis_notes: auctionAnalysisRaw.analysis_notes
  }

  // Zoning designation
  const zoningDesignation = zoningAnalysis.current_zoning_designation || zoningAnalysis.designation || zoningAnalysis.zoning_designation

  // Permitted uses - check nested ordinance summary
  const permittedUses = zoningOrdinance.permitted_uses || zoningAnalysis.permitted_uses || zoningAnalysis.allowed_uses_primary || []

  // Conditional uses - check nested ordinance summary
  const conditionalUses = zoningOrdinance.conditional_uses || zoningAnalysis.conditional_uses || zoningAnalysis.allowed_uses_conditional || []

  // Bulk requirements - check nested structure
  const bulkRequirements = zoningAnalysis.bulk_and_setback_requirements || zoningAnalysis.bulk_requirements || data.bulk_requirements || {}

  // Impact on buildable area - extract from bulk requirements if separate
  const buildableImpact = bulkRequirements.impact_on_buildable_area || zoningAnalysis.impact_on_buildable_area || zoningAnalysis.buildable_area_impact

  // Assumptions
  const assumptions = zoningAnalysis.assumptions || []

  // Ordinance source
  const ordinanceSource = zoningAnalysis.ordinance_source || zoningAnalysis.source

  // Convert highest_and_best_use_analysis object to array if needed
  const highestBestUse = Array.isArray(highestBestUseData)
    ? highestBestUseData
    : Object.values(highestBestUseData).filter((item: any) => item?.name || item?.scenario)

  return (
    <div className="space-y-4 text-sm">
      {/* Metadata Header with Toggle */}
      <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 pb-3 border-b dark:border-gray-700">
        <div className="flex items-center gap-3">
          {data._metadata && <span className="font-medium">AI Analysis via {data._metadata.model}</span>}
          {data._metadata?.elapsed_seconds && <span>{data._metadata.elapsed_seconds}s</span>}
          {data._metadata?.google_search_enabled && <span className="text-blue-500">• Google Search Enabled</span>}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setView('refined')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              view === 'refined'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
            }`}
          >
            <span className="material-symbols-outlined text-[14px]">visibility</span>
            Refined
          </button>
          <button
            onClick={() => setView('scratchpad')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              view === 'scratchpad'
                ? 'bg-purple-500 text-white'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
            }`}
          >
            <span className="material-symbols-outlined text-[14px]">search</span>
            Search Summary
          </button>
          <button
            onClick={() => setView('raw')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              view === 'raw'
                ? 'bg-gray-700 text-white'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
            }`}
          >
            <span className="material-symbols-outlined text-[14px]">code</span>
            Raw JSON
          </button>
        </div>
      </div>

      {/* Raw JSON View */}
      {view === 'raw' && (
        <div className="bg-gray-900 dark:bg-black rounded-lg p-4 overflow-x-auto max-h-[700px] overflow-y-auto">
          <pre className="text-xs text-gray-300 font-mono whitespace-pre-wrap break-words">
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      )}

      {/* Scratchpad / Search Summary View */}
      {view === 'scratchpad' && (
        <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4 border border-purple-200 dark:border-purple-800">
          <h3 className="font-semibold text-purple-900 dark:text-purple-300 text-sm mb-3 flex items-center gap-2">
            <span className="material-symbols-outlined text-purple-500">search</span>
            AI Research Notes & Search Summary
          </h3>
          {data._scratchpad || data.scratchpad ? (
            <div className="text-xs text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap font-mono bg-white dark:bg-gray-900 p-3 rounded border border-purple-100 dark:border-purple-900">
              {data._scratchpad || data.scratchpad}
            </div>
          ) : (
            <p className="text-xs text-gray-500 dark:text-gray-500 italic">No search summary available. This analysis may have been generated before the search summary feature was enabled.</p>
          )}
          {data.ordinance_source || zoningAnalysis?.ordinance_source ? (
            <div className="mt-3">
              <span className="text-xs text-purple-700 dark:text-purple-400 font-medium">Source:</span>
              <a
                href={zoningAnalysis?.ordinance_source || data.ordinance_source}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-blue-600 dark:text-blue-400 hover:underline ml-2 break-all"
              >
                {zoningAnalysis?.ordinance_source || data.ordinance_source}
              </a>
            </div>
          ) : null}
        </div>
      )}

      {/* Refined View */}
      {view === 'refined' && (
        <div className="space-y-4">
          {/* Property Address */}
          {data.property_address && (
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
              <div className="bg-gray-50 dark:bg-gray-800 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                <h4 className="font-semibold text-gray-900 dark:text-gray-100 text-sm flex items-center gap-2">
                  <svg className="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                  Property Address
                </h4>
              </div>
              <div className="bg-white dark:bg-gray-900 p-4">
                <p className="text-sm text-gray-900 dark:text-gray-100">{data.property_address}</p>
              </div>
            </div>
          )}

          {/* Property Details */}
          {Object.keys(propertyDetails).length > 0 && (
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
              <div className="bg-gray-50 dark:bg-gray-800 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                <h4 className="font-semibold text-gray-900 dark:text-gray-100 text-sm flex items-center gap-2">
                  <svg className="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>
                  Property Details
                </h4>
              </div>
              <div className="bg-white dark:bg-gray-900 p-4">
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 text-xs">
                  {propertyDetails.year_built && <div><span className="text-gray-600 dark:text-gray-400">Year Built:</span> <span className="font-medium text-gray-900 dark:text-gray-100">{propertyDetails.year_built}</span></div>}
                  {propertyDetails.building_sqft_above_grade && <div><span className="text-gray-600 dark:text-gray-400">Building SqFt:</span> <span className="font-medium text-gray-900 dark:text-gray-100">{formatNumber(propertyDetails.building_sqft_above_grade)}</span></div>}
                  {propertyDetails.building_sqft && <div><span className="text-gray-600 dark:text-gray-400">Building SqFt:</span> <span className="font-medium text-gray-900 dark:text-gray-100">{formatNumber(propertyDetails.building_sqft)}</span></div>}
                  {propertyDetails.lot_size_sqft && <div><span className="text-gray-600 dark:text-gray-400">Lot Size SqFt:</span> <span className="font-medium text-gray-900 dark:text-gray-100">{formatNumber(propertyDetails.lot_size_sqft)}</span></div>}
                  {propertyDetails.lot_size_acres && <div><span className="text-gray-600 dark:text-gray-400">Lot Acres:</span> <span className="font-medium text-gray-900 dark:text-gray-100">{propertyDetails.lot_size_acres}</span></div>}
                  {propertyDetails.assessed_value && <div><span className="text-gray-600 dark:text-gray-400">Assessed Value:</span> <span className="font-medium text-gray-900 dark:text-gray-100">{formatCurrency(propertyDetails.assessed_value)}</span></div>}
                  {propertyDetails.tax_amount && <div><span className="text-gray-600 dark:text-gray-400">Annual Taxes:</span> <span className="font-medium text-gray-900 dark:text-gray-100">{formatCurrency(propertyDetails.tax_amount)}</span></div>}
                  {propertyDetails.flood_zone && <div><span className="text-gray-600 dark:text-gray-400">Flood Zone:</span> <span className="font-medium text-gray-900 dark:text-gray-100">{propertyDetails.flood_zone}</span></div>}
                  {propertyDetails.sewer_service && <div><span className="text-gray-600 dark:text-gray-400">Sewer:</span> <span className="font-medium text-gray-900 dark:text-gray-100">{propertyDetails.sewer_service}</span></div>}
                  {propertyDetails.water_service && <div><span className="text-gray-600 dark:text-gray-400">Water:</span> <span className="font-medium text-gray-900 dark:text-gray-100">{propertyDetails.water_service}</span></div>}
                </div>
              </div>
            </div>
          )}

          {/* Parcel ID */}
          {propertyDetails.parcel_id && (
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
              <div className="bg-gray-50 dark:bg-gray-800 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                <h4 className="font-semibold text-gray-900 dark:text-gray-100 text-sm">Parcel ID</h4>
              </div>
              <div className="bg-white dark:bg-gray-900 p-4">
                <span className="text-gray-600 dark:text-gray-400 font-medium text-xs">Parcel ID:</span>{' '}
                <span className="font-mono text-gray-900 dark:text-gray-100 text-sm">{propertyDetails.parcel_id}</span>
              </div>
            </div>
          )}

          {/* Zoning Information */}
          {(zoningDesignation || permittedUses.length > 0 || conditionalUses.length > 0) && (
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
              <div className="bg-gray-50 dark:bg-gray-800 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                <h4 className="font-semibold text-gray-900 dark:text-gray-100 text-sm flex items-center gap-2">
                  <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  Zoning Analysis
                </h4>
              </div>
              <div className="bg-white dark:bg-gray-900 p-4 space-y-3">
                {zoningDesignation && (
                  <div>
                    <span className="text-xs text-gray-600 dark:text-gray-400">Zoning Designation:</span>
                    <span className="ml-2 font-medium text-gray-900 dark:text-gray-100">{zoningDesignation}</span>
                  </div>
                )}
                {ordinanceSource && (
                  <div className="text-xs text-gray-700 dark:text-gray-300">
                    <span className="font-medium">Ordinance Source:</span> {ordinanceSource}
                  </div>
                )}
                {permittedUses.length > 0 && (
                  <div>
                    <span className="text-xs text-gray-600 dark:text-gray-400 font-medium">Primary Permitted Uses:</span>
                    <ul className="mt-1 space-y-1">
                      {permittedUses.map((use: string, idx: number) => (
                        <li key={idx} className="text-xs text-gray-700 dark:text-gray-300 ml-4">• {use}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {conditionalUses.length > 0 && (
                  <div>
                    <span className="text-xs text-gray-600 dark:text-gray-400 font-medium">Conditional Uses:</span>
                    <ul className="mt-1 space-y-1">
                      {conditionalUses.map((use: string, idx: number) => (
                        <li key={idx} className="text-xs text-gray-700 dark:text-gray-300 ml-4">• {use}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {assumptions.length > 0 && (
                  <div className="text-xs text-yellow-700 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20 rounded p-2">
                    <span className="font-medium">Assumptions:</span>
                    <ul className="mt-1 space-y-1">
                      {assumptions.map((assumption: string, idx: number) => (
                        <li key={idx} className="ml-4">• {assumption}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Bulk & Setback Requirements */}
          {bulkRequirements && Object.keys(bulkRequirements).length > 0 && (
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
              <div className="bg-gray-50 dark:bg-gray-800 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                <h4 className="font-semibold text-gray-900 dark:text-gray-100 text-sm">Bulk & Setback Requirements</h4>
              </div>
              <div className="bg-white dark:bg-gray-900 p-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 text-xs">
                  {Object.entries(bulkRequirements).map(([key, value]) => {
                    if (key === 'impact_on_buildable_area') return null
                    let displayValue: string | number | null = null
                    if (typeof value === 'object' && value !== null) {
                      if ('value' in value) {
                        displayValue = (value as { value: string | number }).value
                      } else {
                        displayValue = JSON.stringify(value)
                      }
                    } else if (value !== null && value !== undefined) {
                      displayValue = value as string | number
                    }
                    return displayValue !== null && displayValue !== undefined ? (
                      <div key={key}>
                        <span className="text-gray-600 dark:text-gray-400">{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</span>{' '}
                        <span className="font-medium text-gray-900 dark:text-gray-100">{displayValue}</span>
                      </div>
                    ) : null
                  })}
                </div>
              </div>
            </div>
          )}

          {/* Buildable Area Impact */}
          {buildableImpact && (
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
              <div className="bg-gray-50 dark:bg-gray-800 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                <h4 className="font-semibold text-gray-900 dark:text-gray-100 text-sm">Buildable Area Impact</h4>
              </div>
              <div className="bg-white dark:bg-gray-900 p-4">
                <p className="text-xs text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-line">{buildableImpact}</p>
              </div>
            </div>
          )}

          {/* Investment Strategies (Ranked) */}
          {investmentStrategies && investmentStrategies.length > 0 && (
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
              <div className="bg-gray-50 dark:bg-gray-800 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                <h4 className="font-semibold text-gray-900 dark:text-gray-100 text-sm flex items-center gap-2">
                  <svg className="w-4 h-4 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>
                  Investment Strategies (Ranked)
                </h4>
              </div>
              <div className="bg-white dark:bg-gray-900 p-4 space-y-3">
                {investmentStrategies.map((strategy: any, idx: number) => (
                  <div key={idx} className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4 border-l-4 border-purple-500">
                    <div className="flex items-start justify-between mb-2">
                      <span className="font-medium text-purple-900 dark:text-purple-300">
                        #{strategy.rank} {strategy.strategy}
                      </span>
                      <span className={`text-xs px-2 py-1 rounded shrink-0 ${
                        strategy.risk_level === 'Low' || strategy.risk_level === 'Low to Moderate' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
                        strategy.risk_level === 'Medium' || strategy.risk_level === 'Moderate' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400' :
                        'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                      }`}>
                        {strategy.risk_level} Risk
                      </span>
                    </div>
                    {strategy.description && (
                      <p className="text-xs text-gray-700 dark:text-gray-300 mb-2">{strategy.description}</p>
                    )}
                    {strategy.pros && strategy.pros.length > 0 && (
                      <div className="text-xs">
                        <span className="text-green-700 dark:text-green-400 font-medium">Pros:</span>
                        <ul className="mt-1 space-y-0.5 ml-4">
                          {strategy.pros.map((pro: string, pidx: number) => (
                            <li key={pidx} className="text-gray-700 dark:text-gray-300">• {pro}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {strategy.cons && strategy.cons.length > 0 && (
                      <div className="text-xs mt-2">
                        <span className="text-red-700 dark:text-red-400 font-medium">Cons:</span>
                        <ul className="mt-1 space-y-0.5 ml-4">
                          {strategy.cons.map((con: string, cidx: number) => (
                            <li key={cidx} className="text-gray-700 dark:text-gray-300">• {con}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Highest & Best Use Scenarios */}
          {highestBestUse && highestBestUse.length > 0 && (
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
              <div className="bg-gray-50 dark:bg-gray-800 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                <h4 className="font-semibold text-gray-900 dark:text-gray-100 text-sm">Highest & Best Use Scenarios</h4>
              </div>
              <div className="bg-white dark:bg-gray-900 p-4 space-y-3">
                {highestBestUse.map((scenario: any, idx: number) => (
                  <div key={idx} className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
                    <div className="flex items-start justify-between mb-1">
                      <span className="font-medium text-sm text-gray-900 dark:text-gray-100">{scenario.name || scenario.scenario}</span>
                      <span className={`text-xs px-2 py-0.5 rounded shrink-0 ${
                        scenario.risk === 'Low' || scenario.risk_level === 'Low' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
                        scenario.risk === 'Medium' || scenario.risk_level === 'Medium' || scenario.risk === 'Moderate' || scenario.risk_level === 'Moderate' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400' :
                        'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                      }`}>
                        {scenario.risk || scenario.risk_level} Risk
                      </span>
                    </div>
                    {scenario.description && (
                      <p className="text-xs text-gray-600 dark:text-gray-400 mt-2 leading-relaxed">{scenario.description}</p>
                    )}
                    {scenario.analysis && !scenario.description && (
                      <p className="text-xs text-gray-600 dark:text-gray-400 mt-2 leading-relaxed">{scenario.analysis}</p>
                    )}
                    {scenario.pros && scenario.pros.length > 0 && (
                      <div className="text-xs mt-2">
                        <span className="text-green-700 dark:text-green-400 font-medium">Pros:</span>
                        <ul className="mt-1 space-y-0.5 ml-4">
                          {scenario.pros.map((pro: string, pidx: number) => (
                            <li key={pidx} className="text-gray-700 dark:text-gray-300">• {pro}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {scenario.cons && scenario.cons.length > 0 && (
                      <div className="text-xs mt-2">
                        <span className="text-red-700 dark:text-red-400 font-medium">Cons:</span>
                        <ul className="mt-1 space-y-0.5 ml-4">
                          {scenario.cons.map((con: string, cidx: number) => (
                            <li key={cidx} className="text-gray-700 dark:text-gray-300">• {con}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Auction Price Analysis */}
          {auctionAnalysis && Object.keys(auctionAnalysis).length > 0 && (
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
              <div className="bg-gray-50 dark:bg-gray-800 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                <h4 className="font-semibold text-gray-900 dark:text-gray-100 text-sm flex items-center gap-2">
                  <svg className="w-4 h-4 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  Auction Price Analysis
                </h4>
              </div>
              <div className="bg-white dark:bg-gray-900 p-4 space-y-3">
                {auctionAnalysis.upset_amount !== undefined && (
                  <div className="flex justify-between items-center py-2 border-b border-gray-200 dark:border-gray-700">
                    <span className="text-gray-600 dark:text-gray-400">Upset Amount</span>
                    <span className="font-bold text-lg text-amber-600 dark:text-amber-400">{formatCurrency(auctionAnalysis.upset_amount)}</span>
                  </div>
                )}
                {auctionAnalysis.conservative_valuation !== undefined && (
                  <div className="py-2">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-gray-600 dark:text-gray-400">Conservative Valuation</span>
                      <span className="font-semibold text-green-600 dark:text-green-400">{formatCurrency(auctionAnalysis.conservative_valuation)}</span>
                    </div>
                    {auctionAnalysis.conservative_rationale && (
                      <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">{auctionAnalysis.conservative_rationale}</p>
                    )}
                  </div>
                )}
                {auctionAnalysis.moderate_valuation !== undefined && (
                  <div className="py-2">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-gray-600 dark:text-gray-400">Moderate Valuation</span>
                      <span className="font-semibold text-blue-600 dark:text-blue-400">{formatCurrency(auctionAnalysis.moderate_valuation)}</span>
                    </div>
                    {auctionAnalysis.moderate_rationale && (
                      <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">{auctionAnalysis.moderate_rationale}</p>
                    )}
                  </div>
                )}
                {auctionAnalysis.optimistic_valuation !== undefined && (
                  <div className="py-2">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-gray-600 dark:text-gray-400">Optimistic Valuation</span>
                      <span className="font-semibold text-purple-600 dark:text-purple-400">{formatCurrency(auctionAnalysis.optimistic_valuation)}</span>
                    </div>
                    {auctionAnalysis.optimistic_rationale && (
                      <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">{auctionAnalysis.optimistic_rationale}</p>
                    )}
                  </div>
                )}
                {auctionAnalysis.maximum_unprofitable_bid !== undefined && (
                  <div className="mt-3 p-3 bg-red-50 dark:bg-red-900/30 rounded border border-red-200 dark:border-red-800">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium text-red-900 dark:text-red-300">Maximum Unprofitable Bid</span>
                      <span className="font-bold text-red-900 dark:text-red-300">{formatCurrency(auctionAnalysis.maximum_unprofitable_bid)}</span>
                    </div>
                    {auctionAnalysis.max_bid_rationale && (
                      <p className="text-xs text-red-700 dark:text-red-400 mt-1">{auctionAnalysis.max_bid_rationale}</p>
                    )}
                  </div>
                )}
                {auctionAnalysis.analysis_notes && (
                  <div className="mt-3 p-3 bg-gray-50 dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700">
                    <p className="text-xs text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-line">{auctionAnalysis.analysis_notes}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Environmental Constraints */}
          {data.environmental_constraints && (
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
              <div className="bg-gray-50 dark:bg-gray-800 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                <h4 className="font-semibold text-gray-900 dark:text-gray-100 text-sm">Environmental Constraints</h4>
              </div>
              <div className="bg-white dark:bg-gray-900 p-4 text-xs space-y-2">
                {data.environmental_constraints.flood_zone && <div className="flex items-start gap-2"><span className="text-gray-600 dark:text-gray-400 shrink-0">Flood Zone:</span> <span className="text-gray-900 dark:text-gray-100">{data.environmental_constraints.flood_zone}</span></div>}
                {data.environmental_constraints.wetlands && <div className="flex items-start gap-2"><span className="text-gray-600 dark:text-gray-400 shrink-0">Wetlands:</span> <span className="text-gray-900 dark:text-gray-100">{data.environmental_constraints.wetlands}</span></div>}
                {data.environmental_constraints.other && <div className="flex items-start gap-2"><span className="text-gray-600 dark:text-gray-400 shrink-0">Other:</span> <span className="text-gray-900 dark:text-gray-100">{data.environmental_constraints.other}</span></div>}
              </div>
            </div>
          )}

          {/* Utilities */}
          {data.utilities && (
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
              <div className="bg-gray-50 dark:bg-gray-800 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                <h4 className="font-semibold text-gray-900 dark:text-gray-100 text-sm">Utilities</h4>
              </div>
              <div className="bg-white dark:bg-gray-900 p-4 text-xs">
                {Object.entries(data.utilities).map(([k, v], idx) => (
                  <span key={k} className="text-gray-900 dark:text-gray-100">
                    <span className="font-medium">{k.charAt(0).toUpperCase() + k.slice(1)}:</span> {String(v)}{idx < Object.entries(data.utilities).length - 1 ? ' • ' : ''}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Verification Checklist */}
          {verificationChecklist && verificationChecklist.length > 0 && (
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
              <div className="bg-gray-50 dark:bg-gray-800 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                <h4 className="font-semibold text-gray-900 dark:text-gray-100 text-sm flex items-center gap-2">
                  <svg className="w-4 h-4 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" /></svg>
                  Verification Checklist
                </h4>
              </div>
              <div className="bg-white dark:bg-gray-900 p-4">
                <ul className="space-y-2">
                  {verificationChecklist.map((item: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-2 text-xs text-gray-700 dark:text-gray-300">
                      <span className="text-orange-500 mt-0.5 shrink-0">•</span>
                      <span className="leading-relaxed">{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ============================================================================
// NEW AI ANALYSIS DISPLAY COMPONENT (Uses Integration Kit)
// ============================================================================

interface NewAIAnalysisDisplayProps {
  data: AnalysisData
  rawText?: string
}

function NewAIAnalysisDisplay({ data, rawText }: NewAIAnalysisDisplayProps) {
  const [view, setView] = useState<'refined' | 'raw'>('refined')

  // Parse data if raw text is provided
  const parsedData = useMemo(() => {
    if (data) return data
    if (!rawText) return null
    const jsonStart = rawText.indexOf('```json')
    const jsonEnd = rawText.lastIndexOf('```')
    if (jsonStart !== -1 && jsonEnd > jsonStart) {
      try {
        const jsonStr = rawText.substring(jsonStart + 7, jsonEnd)
        return JSON.parse(jsonStr) as AnalysisData
      } catch (e) {
        console.error('[NewAIAnalysisDisplay] Failed to parse JSON from raw text:', e)
        return null
      }
    }
    return null
  }, [data, rawText])

  const displayData = data || parsedData

  // Show error state with raw text available
  if (!displayData) {
    if (rawText && rawText.length > 0) {
      return (
        <div className="space-y-3">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
            <div className="flex items-center gap-2 text-red-700 dark:text-red-400 text-sm font-medium mb-1">
              <span className="material-symbols-outlined text-lg">error</span>
              Analysis parsing failed
            </div>
            <p className="text-red-600 dark:text-red-500 text-xs">
              The AI returned a response but the JSON could not be parsed. This may be due to an incomplete response or formatting issues.
            </p>
          </div>
          <div className="text-gray-600 dark:text-gray-400 text-xs">
            <button
              onClick={() => setView('raw')}
              className="text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
            >
              <span className="material-symbols-outlined text-sm">visibility</span>
              View raw response
            </button>
          </div>
          {view === 'raw' && (
            <div className="bg-gray-900 dark:bg-black rounded-lg p-4 overflow-x-auto max-h-[300px] overflow-y-auto">
              <pre className="text-xs text-gray-300 font-mono whitespace-pre-wrap break-words">
                {rawText}
              </pre>
            </div>
          )}
        </div>
      )
    }
    return (
      <div className="text-gray-500 dark:text-gray-500 text-sm">
        No analysis data available
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Toggle Header */}
      <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 pb-3 border-b dark:border-gray-700">
        <div className="flex items-center gap-3">
          <span className="font-medium">Forensic Real Estate Analysis</span>
          <span className="text-blue-500">• Gemini 2.0 Flash + Google Search</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setView('refined')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              view === 'refined'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
            }`}
          >
            <span className="material-symbols-outlined text-[14px]">visibility</span>
            Refined Analysis
          </button>
          <button
            onClick={() => setView('raw')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              view === 'raw'
                ? 'bg-gray-700 text-white'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
            }`}
          >
            <span className="material-symbols-outlined text-[14px]">code</span>
            Raw JSON
          </button>
        </div>
      </div>

      {/* Content */}
      {view === 'refined' ? (
        <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
          <RefinedReport data={displayData} />
        </div>
      ) : (
        <div className="bg-gray-900 dark:bg-black rounded-lg p-4 overflow-x-auto max-h-[500px] overflow-y-auto">
          <pre className="text-xs text-gray-300 font-mono whitespace-pre-wrap break-words">
            {JSON.stringify(displayData, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

// ============================================================================
// PROPERTY DETAIL MODAL
// ============================================================================

interface PropertyDetailModalProps {
  property?: {
    id: string
    address: string
    city: string
    state: string
    zip: string
    apn?: string
    image: string
    auctionDate: string
    openingBid: number
    approxUpset?: number
    approxJudgment?: number
    estimatedARV: number
    spread: number
    aiConfidence: number
    status?: string
    beds?: number
    baths?: number
    sqft?: number
    yearBuilt?: number
    propertyType?: string
    zestimate?: number
    rentZestimate?: number
    // Enrichment data
    taxHistoryData?: any[]
    taxHistoryCount?: number
    comparablesData?: any[]
    comparablesCount?: number
    skipTraceData?: any
    streetViewImages?: any
    zoningAnalysis?: any
    // Auction details
    description?: string
    refined_description?: string
    sheriff_number?: string
    plaintiff?: string
    plaintiff_attorney?: string
    defendant?: string
    // Status history
    statusHistory?: Array<{
      status: string
      date: string
      notes?: string
    }>
  }
  isOpen: boolean
  onClose: () => void
  onSkipTrace?: () => Promise<{ success: boolean; message?: string }>
  isSkipTraceInProgress?: boolean
  onZoningAnalysis?: () => Promise<{ success: boolean; data?: any; message?: string }>
  isZoningAnalysisInProgress?: boolean
}

export function PropertyDetailModal({ property, isOpen, onClose, onSkipTrace, isSkipTraceInProgress, onZoningAnalysis, isZoningAnalysisInProgress }: PropertyDetailModalProps) {
  const [shareSheetOpen, setShareSheetOpen] = useState(false)
  const [notes, setNotes] = useState<UserNote | null>(null)
  const [tags, setTags] = useState<UserTag[]>([])
  const [refinedDescription, setRefinedDescription] = useState<string | null>(null)
  const [isRefining, setIsRefining] = useState(false)

  // New AI Analysis state
  const [aiAnalysisData, setAiAnalysisData] = useState<AnalysisData | null>(null)
  const [aiAnalysisRaw, setAiAnalysisRaw] = useState<string | null>(null)
  const [isAiAnalyzing, setIsAiAnalyzing] = useState(false)

  const { userId } = useUser()

  // Fetch notes and tags when property changes
  useEffect(() => {
    if (property && userId) {
      // Fetch notes
      getUserNote(parseInt(property.id), userId).then(setNotes).catch(console.error)

      // Fetch tags
      getPropertyTags(parseInt(property.id), userId).then(setTags).catch(console.error)
    } else {
      setNotes(null)
      setTags([])
    }
  }, [property, userId])

  // Sync refined_description from property and auto-refine if needed
  useEffect(() => {
    if (!property) return

    if (property.refined_description) {
      setRefinedDescription(property.refined_description)
      setIsRefining(false)
    } else if (property.description && isOpen && !isRefining) {
      // Auto-refine when modal opens and there's no cached refined version
      const descriptionToRefine = property.description
      const autoRefine = async () => {
        setIsRefining(true)
        try {
          const result = await refineDescription(parseInt(property.id), descriptionToRefine)
          setRefinedDescription(result.refined_description)
        } catch (error) {
          console.error('Failed to auto-refine description:', error)
        } finally {
          setIsRefining(false)
        }
      }
      autoRefine()
    }
  }, [property?.id, property?.refined_description, property?.description, isOpen])

  // Reset AI analysis when property changes
  useEffect(() => {
    if (property) {
      setAiAnalysisData(null)
      setAiAnalysisRaw(null)
      setIsAiAnalyzing(false)
    }
  }, [property?.id])

  // New AI Analysis handler - uses the frontend AnalysisService directly
  const handleNewAIAnalysis = async () => {
    if (!property) return

    setIsAiAnalyzing(true)
    setAiAnalysisRaw('')
    setAiAnalysisData(null)

    try {
      const upsetAmount = property.approxUpset || property.approxJudgment || 0
      const address = `${property.address}, ${property.city}, ${property.state} ${property.zip}`

      const result = await analyzePropertyStream(address, upsetAmount, (progressText) => {
        // Update raw text during streaming
        setAiAnalysisRaw(progressText)
      })

      if (result) {
        setAiAnalysisData(result)
      }
    } catch (error) {
      console.error('AI Analysis failed:', error)
      // Keep the raw text even if parsing failed
    } finally {
      setIsAiAnalyzing(false)
    }
  }

  if (!isOpen) return null
  if (!property) return null

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  const getStatusConfig = (status?: string) => {
    const statusLower = status?.toLowerCase() || 'scheduled'
    // Handle combined statuses like "bankruptcy/adjourned"
    if (statusLower.includes('bankruptcy')) return { color: 'bg-purple-100 dark:bg-purple-500/20 text-purple-700 dark:text-purple-400 border-purple-300 dark:border-purple-500/30' }
    if (statusLower === 'scheduled') return { color: 'bg-blue-100 dark:bg-blue-500/20 text-blue-700 dark:text-blue-400 border-blue-300 dark:border-blue-500/30' }
    if (statusLower === 'adjourned') return { color: 'bg-yellow-100 dark:bg-yellow-500/20 text-yellow-700 dark:text-yellow-400 border-yellow-300 dark:border-yellow-500/30' }
    if (statusLower === 'sold') return { color: 'bg-emerald-100 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-400 border-emerald-300 dark:border-emerald-500/30' }
    if (statusLower === 'canceled' || statusLower === 'cancelled') return { color: 'bg-red-100 dark:bg-red-500/20 text-red-700 dark:text-red-400 border-red-300 dark:border-red-500/30' }
    if (statusLower === 'borrower occupied') return { color: 'bg-orange-100 dark:bg-orange-500/20 text-orange-700 dark:text-orange-400 border-orange-300 dark:border-orange-500/30' }
    return { color: 'bg-gray-200 dark:bg-gray-500/20 text-gray-700 dark:text-gray-400 border-gray-400 dark:border-gray-500/30' }
  }

  const handleShare = () => {
    setShareSheetOpen(true)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className="w-full max-w-4xl h-[95vh] sm:h-[90vh] bg-white dark:bg-[#141923] border border-gray-300 dark:border-border-dark rounded-xl shadow-2xl flex flex-col overflow-hidden relative animate-in fade-in zoom-in duration-200">
        {/* Header - simplified */}
        <div className="h-16 sm:h-16 flex items-center justify-between px-4 sm:px-6 border-b border-gray-300 dark:border-border-dark bg-gray-100 dark:bg-surface-dark shrink-0 gap-2 sm:gap-4">
          {/* Address section */}
          <div className="flex flex-col min-w-0 flex-1">
            <h2 className="text-base sm:text-lg font-bold text-gray-900 dark:text-white leading-tight">{property.address}</h2>
            <div className="flex items-center gap-1.5 sm:gap-2 text-xs sm:text-sm text-gray-600 dark:text-gray-400 mt-0.5">
              <span className="truncate">{`${property.city}, ${property.state} ${property.zip}`}</span>
              {property.apn && (
                <>
                  <span className="w-1 h-1 bg-gray-400 dark:bg-gray-600 rounded-full shrink-0 hidden sm:block" />
                  <span className="font-mono text-primary truncate hidden sm:block">APN: {property.apn}</span>
                </>
              )}
              {property.status && (
                <>
                  <span className="w-1 h-1 bg-gray-400 dark:bg-gray-600 rounded-full shrink-0 hidden sm:block" />
                  <span className={`text-xs font-bold px-2 py-0.5 rounded border uppercase tracking-wide shrink-0 hidden sm:block ${getStatusConfig(property.status).color}`}>
                    {property.status}
                  </span>
                </>
              )}
            </div>
          </div>
          {/* Action buttons */}
          <div className="flex items-center gap-1 sm:gap-2 shrink-0">
            <button
              onClick={handleNewAIAnalysis}
              disabled={isAiAnalyzing || !!aiAnalysisData}
              className={`flex items-center gap-1.5 px-2 sm:px-3 py-2 rounded-lg text-sm font-medium transition-colors shrink-0 ${
                aiAnalysisData
                  ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30 cursor-default'
                  : isAiAnalyzing
                  ? 'bg-purple-500/50 text-gray-300 cursor-wait'
                  : 'bg-purple-600 text-white hover:bg-purple-700'
              }`}
              title="AI Analysis"
            >
              {isAiAnalyzing ? (
                <>
                  <span className="material-symbols-outlined text-[16px] animate-spin">smart_toy</span>
                  <span className="hidden sm:inline">Analyzing...</span>
                </>
              ) : aiAnalysisData ? (
                <>
                  <span className="material-symbols-outlined text-[16px]">check_circle</span>
                  <span className="hidden sm:inline">Analyzed</span>
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-[16px]">smart_toy</span>
                  <span className="hidden sm:inline">AI Analysis</span>
                </>
              )}
            </button>
            {onSkipTrace && (
              <button
                onClick={onSkipTrace}
                disabled={isSkipTraceInProgress || !!property.skipTraceData}
                className={`flex items-center gap-1.5 px-2 sm:px-3 py-2 rounded-lg text-sm font-medium transition-colors shrink-0 ${
                  property.skipTraceData
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 cursor-default'
                    : isSkipTraceInProgress
                    ? 'bg-primary/50 text-gray-300 cursor-wait'
                    : 'bg-primary text-white hover:bg-primary/90'
                }`}
              >
                {isSkipTraceInProgress ? (
                  <>
                    <span className="material-symbols-outlined text-[16px] animate-spin">refresh</span>
                    <span className="hidden sm:inline">Tracing...</span>
                  </>
                ) : property.skipTraceData ? (
                  <>
                    <span className="material-symbols-outlined text-[16px]">check_circle</span>
                    <span className="hidden sm:inline">Traced</span>
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined text-[16px]">contact_phone</span>
                    <span className="hidden sm:inline">Skip Trace</span>
                  </>
                )}
              </button>
            )}
            <button
              onClick={handleShare}
              className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-300 dark:hover:bg-white/5 rounded-lg transition-colors shrink-0"
              title="Share property"
            >
              <span className="material-symbols-outlined">share</span>
            </button>
            <button
              onClick={onClose}
              className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-300 dark:hover:bg-white/5 rounded-lg transition-colors shrink-0"
            >
              <span className="material-symbols-outlined">close</span>
            </button>
          </div>
        </div>

        {/* Content - Scrollable */}
        <div className="flex-1 overflow-y-auto overflow-x-hidden p-3 sm:p-4 lg:p-6">
          {/* Details Section */}
          <div className="space-y-4 sm:space-y-5 max-w-full">
            {/* Property Stats */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3">
              <div className="bg-white dark:bg-surface-dark border border-gray-300 dark:border-border-dark rounded-lg p-3 sm:p-3">
                <p className="text-gray-600 dark:text-gray-500 text-xs mb-1">Bedrooms</p>
                <p className="text-gray-900 dark:text-white text-base sm:text-lg font-semibold">{property.beds ?? '-'}</p>
              </div>
              <div className="bg-white dark:bg-surface-dark border border-gray-300 dark:border-border-dark rounded-lg p-3 sm:p-3">
                <p className="text-gray-600 dark:text-gray-500 text-xs mb-1">Bathrooms</p>
                <p className="text-gray-900 dark:text-white text-base sm:text-lg font-semibold">{property.baths ?? '-'}</p>
              </div>
              <div className="bg-white dark:bg-surface-dark border border-gray-300 dark:border-border-dark rounded-lg p-3 sm:p-3">
                <p className="text-gray-600 dark:text-gray-500 text-xs mb-1">Sq Ft</p>
                <p className="text-gray-900 dark:text-white text-base sm:text-lg font-semibold">{property.sqft?.toLocaleString() ?? '-'}</p>
              </div>
              <div className="bg-white dark:bg-surface-dark border border-gray-300 dark:border-border-dark rounded-lg p-3 sm:p-3">
                <p className="text-gray-600 dark:text-gray-500 text-xs mb-1">Year Built</p>
                <p className="text-gray-900 dark:text-white text-base sm:text-lg font-semibold">{property.yearBuilt ?? '-'}</p>
              </div>
            </div>

            {/* Financial Summary */}
            <div className="bg-white dark:bg-surface-dark border border-gray-300 dark:border-border-dark rounded-lg p-4 sm:p-5">
              <h3 className="text-gray-900 dark:text-white font-semibold mb-3 sm:mb-4 flex items-center gap-2">
                <span className="material-symbols-outlined text-primary">payments</span>
                Financial Summary
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 sm:gap-4">
                {property.approxUpset && (
                  <div>
                    <p className="text-gray-600 dark:text-gray-500 text-xs">Approx Upset</p>
                    <p className="text-gray-900 dark:text-white font-medium">{formatCurrency(property.approxUpset)}</p>
                  </div>
                )}
                {property.approxJudgment && (
                  <div>
                    <p className="text-gray-600 dark:text-gray-500 text-xs">Approx Judgment</p>
                    <p className="text-gray-900 dark:text-white font-medium">{formatCurrency(property.approxJudgment)}</p>
                  </div>
                )}
                {property.zestimate && (
                  <div>
                    <p className="text-gray-600 dark:text-gray-500 text-xs">Zestimate</p>
                    <p className="text-blue-600 dark:text-blue-400 font-medium">{formatCurrency(property.zestimate)}</p>
                  </div>
                )}
                {property.rentZestimate && (
                  <div>
                    <p className="text-gray-600 dark:text-gray-500 text-xs">Rent Zestimate</p>
                    <p className="text-purple-600 dark:text-purple-400 font-medium">{formatCurrency(property.rentZestimate)}/mo</p>
                  </div>
                )}
                <div>
                  <p className="text-gray-600 dark:text-gray-500 text-xs">Spread</p>
                  <p className={`font-medium ${property.spread >= 30 ? 'text-emerald-600 dark:text-emerald-400' : property.spread >= 10 ? 'text-yellow-600 dark:text-yellow-500' : 'text-red-600 dark:text-red-400'}`}>
                    +{property.spread.toFixed(1)}%
                  </p>
                </div>
              </div>
            </div>

            {/* Auction Details */}
            <div className="bg-white dark:bg-surface-dark border border-gray-300 dark:border-border-dark rounded-lg divide-y divide-gray-300 dark:divide-border-dark">
              <div className="flex items-center justify-between p-4">
                <span className="text-gray-700 dark:text-gray-400 text-sm">Auction Date</span>
                <span className="text-gray-900 dark:text-white font-medium">{property.auctionDate}</span>
              </div>
              {property.sheriff_number && (
                <div className="flex items-center justify-between p-4">
                  <span className="text-gray-700 dark:text-gray-400 text-sm">Sheriff Number</span>
                  <span className="text-gray-900 dark:text-white font-medium font-mono text-sm">{property.sheriff_number}</span>
                </div>
              )}
              {property.plaintiff && (
                <div className="flex items-center justify-between p-4">
                  <span className="text-gray-700 dark:text-gray-400 text-sm">Plaintiff</span>
                  <span className="text-gray-900 dark:text-white font-medium text-right max-w-[60%]">{property.plaintiff}</span>
                </div>
              )}
              {property.plaintiff_attorney && (
                <div className="flex items-center justify-between p-4">
                  <span className="text-gray-700 dark:text-gray-400 text-sm">Plaintiff Attorney</span>
                  <span className="text-gray-900 dark:text-white font-medium text-right max-w-[60%]">{property.plaintiff_attorney}</span>
                </div>
              )}
              {property.defendant && (
                <div className="flex items-center justify-between p-4">
                  <span className="text-gray-700 dark:text-gray-400 text-sm">Defendant</span>
                  <span className="text-gray-900 dark:text-white font-medium text-right max-w-[60%]">{property.defendant}</span>
                </div>
              )}
            </div>

            {/* Auction Description */}
            {property.description && (
              <div className="bg-white dark:bg-surface-dark border border-gray-300 dark:border-border-dark rounded-lg p-4 sm:p-5">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-gray-900 dark:text-white font-semibold">Auction Description</h3>
                  {isRefining && (
                    <div className="flex items-center gap-1.5 text-primary text-sm">
                      <span className="material-symbols-outlined text-[16px] animate-spin">refresh</span>
                      <span>Refining with AI...</span>
                    </div>
                  )}
                </div>

                {/* Original Description */}
                <div className="mb-4">
                  <p className="text-xs text-gray-500 dark:text-gray-500 uppercase tracking-wide mb-2 font-medium">Original</p>
                  <p className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">{property.description}</p>
                </div>

                {/* Refined Description */}
                {refinedDescription && (
                  <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                    <p className="text-xs text-primary uppercase tracking-wide mb-2 font-medium flex items-center gap-1">
                      <span className="material-symbols-outlined text-[14px]">auto_awesome</span>
                      AI-Refined Version
                    </p>
                    <p className="text-gray-800 dark:text-gray-200 text-sm leading-relaxed whitespace-pre-wrap bg-blue-50 dark:bg-blue-900/10 p-3 rounded-lg border border-blue-100 dark:border-blue-800/30">
                      {refinedDescription}
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Skip Trace Data */}
            {property.skipTraceData && (
              <div className="bg-white dark:bg-surface-dark border border-gray-300 dark:border-border-dark rounded-lg p-4 sm:p-5">
                <h3 className="text-gray-900 dark:text-white font-semibold mb-3 flex items-center gap-2">
                  <span className="material-symbols-outlined text-emerald-600 dark:text-emerald-400">contact_phone</span>
                  Skip Trace Results
                </h3>
                <SkipTraceDisplay data={property.skipTraceData} />
              </div>
            )}

            {/* Zoning Analysis */}
            {property.zoningAnalysis && (
              <div className="bg-white dark:bg-surface-dark border border-gray-300 dark:border-border-dark rounded-lg p-4 sm:p-5">
                <h3 className="text-gray-900 dark:text-white font-semibold mb-3 flex items-center gap-2">
                  <span className="material-symbols-outlined text-purple-600 dark:text-purple-400">smart_toy</span>
                  AI Zoning Analysis
                </h3>
                <ZoningAnalysisDisplay data={property.zoningAnalysis} />
              </div>
            )}

            {/* New AI Analysis (Integration Kit) */}
            {(aiAnalysisData || aiAnalysisRaw || isAiAnalyzing) && (
              <div className="bg-white dark:bg-surface-dark border border-gray-300 dark:border-border-dark rounded-lg p-4 sm:p-5">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-gray-900 dark:text-white font-semibold flex items-center gap-2">
                    <span className="material-symbols-outlined text-emerald-600 dark:text-emerald-400">auto_awesome</span>
                    Forensic Real Estate Analysis
                  </h3>
                  {aiAnalysisData && (
                    <button
                      onClick={async () => {
                        try {
                          await exportAnalysisPdf(aiAnalysisData)
                        } catch (error) {
                          console.error('Failed to export PDF:', error)
                          alert('Failed to export PDF. Please try again.')
                        }
                      }}
                      className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-300 dark:hover:bg-white/5 rounded-lg transition-colors"
                      title="Export Analysis as PDF"
                    >
                      <span className="material-symbols-outlined">picture_as_pdf</span>
                    </button>
                  )}
                </div>
                {isAiAnalyzing && !aiAnalysisData && (
                  <div className="flex items-center gap-3 text-gray-600 dark:text-gray-400">
                    <span className="material-symbols-outlined animate-spin">refresh</span>
                    <span>Running deep analysis with Google Search...</span>
                  </div>
                )}
                {(aiAnalysisData || aiAnalysisRaw) && (
                  <NewAIAnalysisDisplay data={aiAnalysisData!} rawText={aiAnalysisRaw || undefined} />
                )}
              </div>
            )}

            {/* Status History */}
            {property.statusHistory && property.statusHistory.length > 0 && (
              <div className="bg-white dark:bg-surface-dark border border-gray-300 dark:border-border-dark rounded-lg p-4 sm:p-5">
                <h3 className="text-gray-900 dark:text-white font-semibold mb-3 flex items-center gap-2">
                  <span className="material-symbols-outlined text-primary">history</span>
                  Status History
                </h3>
                <div className="space-y-3">
                  {property.statusHistory.map((entry, idx) => (
                    <div key={idx} className="flex gap-3 relative">
                      {/* Timeline line */}
                      {idx < property.statusHistory!.length - 1 && (
                        <div className="absolute left-[27px] sm:left-[31px] top-12 bottom-0 w-0.5 bg-gray-300 dark:bg-border-dark ml-[-1px]" />
                      )}
                      <div className="flex flex-col items-center">
                        <div className={`w-3 h-3 rounded-full border-2 ${getStatusConfig(entry.status).color.replace('bg-', 'border-').split(' ')[0]} ${getStatusConfig(entry.status).color.split(' ')[1] || 'bg-gray-400'} shrink-0 z-10`} />
                      </div>
                      <div className="flex-1 pb-3 min-w-0">
                        <div className="flex items-center justify-between gap-2 mb-1 flex-wrap">
                          <span className={`text-xs font-semibold px-2 py-0.5 rounded uppercase tracking-wide ${getStatusConfig(entry.status).color}`}>
                            {entry.status}
                          </span>
                          <span className="text-gray-600 dark:text-gray-500 text-xs shrink-0">{entry.date}</span>
                        </div>
                        {entry.notes && (
                          <p className="text-gray-700 dark:text-gray-400 text-xs break-words">{entry.notes}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* User Notes - Only show if logged in */}
            {userId && (
              <PropertyNotes
                propertyId={parseInt(property.id)}
                userId={userId}
              />
            )}

            {/* Bottom Spacer */}
            <div className="h-4" />
          </div>
        </div>
      </div>

      <ShareSheet
        property={{
          id: property.id,
          address: property.address,
          city: property.city,
          state: property.state,
          zip: property.zip,
          auctionDate: property.auctionDate,
          openingBid: property.openingBid,
          approxUpset: property.approxUpset,
          approxJudgment: property.approxJudgment,
          estimatedARV: property.estimatedARV,
          zestimate: property.zestimate,
          rentZestimate: property.rentZestimate,
          spread: property.spread,
          beds: property.beds,
          baths: property.baths,
          sqft: property.sqft,
          yearBuilt: property.yearBuilt,
          propertyType: property.propertyType,
          apn: property.apn,
          status: property.status,
          description: property.description,
          refined_description: refinedDescription || undefined,
          sheriff_number: property.sheriff_number,
          plaintiff: property.plaintiff,
          plaintiff_attorney: property.plaintiff_attorney,
          defendant: property.defendant,
          skipTraceData: property.skipTraceData,
          statusHistory: property.statusHistory,
          tags: tags.map(t => ({ name: t.name, color: t.color })),
          notes: notes ? [{ note: notes.note, created_at: notes.created_at }] : [],
        }}
        isOpen={shareSheetOpen}
        onClose={() => setShareSheetOpen(false)}
        onShareComplete={(type) => {
          console.log('Share completed:', type)
        }}
      />
    </div>
  )
}
