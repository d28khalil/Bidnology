'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@clerk/nextjs'
import { ShareSheet } from '@/components/ShareSheet'
import { PropertyNotes } from '@/components/PropertyNotes'
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
}

export function PropertyDetailModal({ property, isOpen, onClose, onSkipTrace, isSkipTraceInProgress }: PropertyDetailModalProps) {
  const [shareSheetOpen, setShareSheetOpen] = useState(false)
  const [notes, setNotes] = useState<UserNote | null>(null)
  const [tags, setTags] = useState<UserTag[]>([])
  const [refinedDescription, setRefinedDescription] = useState<string | null>(null)
  const [isRefining, setIsRefining] = useState(false)
  const { userId } = useAuth()

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
