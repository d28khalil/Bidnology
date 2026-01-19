'use client'

import { useState, useEffect, useRef } from 'react'
import { normalizeStatus, normalizeStatusHistory, getStatusColor } from '@/lib/utils/statusNormalizer'
import { EditableCell } from './EditableCell'

interface PropertyRowProps {
  property: {
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
    // Keep for backward compatibility
    hasTaxHistory?: boolean
    hasComparables?: boolean
    hasSkipTrace?: boolean
    hasStreetView?: boolean
    statusHistory?: Array<{ date: string; status: string }>
    // Override values
    approxUpsetOverride?: number
    approxJudgmentOverride?: number
    // New bid tracking overrides
    startingBidOverride?: number
    bidCapOverride?: number
    propertySoldOverride?: string | number  // ISO timestamp or sale price
  }
  tags?: Array<{ id: number; name: string; color: string }>
  allTags?: Array<{ id: number; name: string; color: string }>
  onOpenModal?: (property: PropertyRowProps['property']) => void
  onSkipTrace?: (propertyId: number) => Promise<{ success: boolean; message?: string }>
  onAddTag?: (propertyId: number, tagId: number) => Promise<void>
  onRemoveTag?: (propertyId: number, tagId: number) => Promise<void>
  skipTraceInProgress?: boolean
  // Property overrides handlers
  onSaveOverride?: (propertyId: number, fieldName: 'approx_upset' | 'judgment_amount' | 'starting_bid' | 'bid_cap' | 'property_sold', newValue: number | null, notes?: string, propertySoldDate?: string) => Promise<void>
  onGetOverrideHistory?: (propertyId: number, fieldName: 'approx_upset' | 'judgment_amount' | 'starting_bid' | 'bid_cap' | 'property_sold') => Promise<Array<{
    id: number
    original_value: number | null
    new_value: number | string
    previous_spread: number | null
    notes: string | null
    created_at: string
  }>>
  onRevertOverride?: (propertyId: number, fieldName: 'approx_upset' | 'judgment_amount' | 'starting_bid' | 'bid_cap' | 'property_sold') => Promise<void>
  // Saved/favorite functionality
  isSaved?: boolean
  onToggleSaved?: (propertyId: number) => Promise<void>
  savedLoading?: boolean
  // Favorites functionality (separate from saved/kanban)
  isFavorited?: boolean
  onToggleFavorite?: (propertyId: number) => Promise<void>
  // Separate override props (for auction history)
  startingBidOverride?: number
  bidCapOverride?: number
  propertySoldOverride?: string | number
}

export function PropertyRow({
  property,
  tags = [],
  allTags = [],
  onOpenModal,
  onSkipTrace,
  onAddTag,
  onRemoveTag,
  skipTraceInProgress,
  onSaveOverride,
  onGetOverrideHistory,
  onRevertOverride,
  isSaved = false,
  onToggleSaved,
  savedLoading = false,
  isFavorited = false,
  onToggleFavorite,
  startingBidOverride,
  bidCapOverride,
  propertySoldOverride
}: PropertyRowProps) {
  console.log('PropertyRow rendered - override handlers:', {
    hasSaveOverride: !!onSaveOverride,
    hasGetHistory: !!onGetOverrideHistory,
    hasRevert: !!onRevertOverride,
    propertyId: property.id
  })
  const [localTracing, setLocalTracing] = useState(false)
  const [isTagsDropdownOpen, setIsTagsDropdownOpen] = useState(false)
  const [normalizedStatusHistory, setNormalizedStatusHistory] = useState<Array<{ date: string; status: string; originalStatus?: string }>>([])
  const tagsDropdownRef = useRef<HTMLDivElement>(null)

  // Bid tracking states
  const [editingBidField, setEditingBidField] = useState<string | null>(null) // 'starting_bid' | 'bid_cap' | 'property_sold'
  const [bidHistoryOpen, setBidHistoryOpen] = useState<string | null>(null)
  const [bidHistory, setBidHistory] = useState<Array<{
    id: number
    new_value: number | string
    created_at: string
  }>>([])
  const [bidInputValue, setBidInputValue] = useState('')

  // Normalize status history when property changes
  useEffect(() => {
    if (property.statusHistory && property.statusHistory.length > 0) {
      normalizeStatusHistory(property.statusHistory)
        .then(setNormalizedStatusHistory)
        .catch((err) => {
          console.error('Error normalizing status history:', err)
          setNormalizedStatusHistory([])
        })
    } else {
      setNormalizedStatusHistory([])
    }
  }, [property.statusHistory])

  // Close tags dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (tagsDropdownRef.current && !tagsDropdownRef.current.contains(event.target as Node)) {
        setIsTagsDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleAddTag = async (tagId: number) => {
    if (!onAddTag) return
    const propertyId = parseInt(property.id)
    await onAddTag(propertyId, tagId)
    setIsTagsDropdownOpen(false)
  }

  const handleRemoveTag = async (tagId: number) => {
    if (!onRemoveTag) return
    const propertyId = parseInt(property.id)
    await onRemoveTag(propertyId, tagId)
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  const handleCellClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    onOpenModal?.(property)
  }

  const handleSkipTraceClick = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (!onSkipTrace) return

    const propertyId = parseInt(property.id)
    setLocalTracing(true)

    try {
      const result = await onSkipTrace(propertyId)
      if (result.success) {
        // Keep showing loading state - parent component manages when to stop
        // Only stop if there was an error
        if (result.message?.includes('error') || result.message?.includes('failed')) {
          setLocalTracing(false)
        }
        // If job started successfully, keep localTracing true until data refreshes
      } else {
        setLocalTracing(false)
      }
    } catch {
      setLocalTracing(false)
    }
  }

  // Clear localTracing when property gets skip trace data
  useEffect(() => {
    if (property.hasSkipTrace && localTracing) {
      setLocalTracing(false)
    }
  }, [property.hasSkipTrace, localTracing])

  const isSkipTraceActive = localTracing || skipTraceInProgress

  // Favorite toggle handler
  const handleToggleFavorite = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (!onToggleSaved) return

    const propertyId = parseInt(property.id)
    try {
      await onToggleSaved(propertyId)
    } catch (err) {
      console.error('Error toggling favorite:', err)
    }
  }

  // Bid tracking helper functions
  const handleBidFieldClick = async (fieldName: 'starting_bid' | 'bid_cap' | 'property_sold', e: React.MouseEvent) => {
    e.stopPropagation()
    if (!onGetOverrideHistory) return

    const propertyId = parseInt(property.id)
    try {
      const history = await onGetOverrideHistory(propertyId, fieldName)
      setBidHistory(history)
      setBidHistoryOpen(fieldName)
    } catch (err) {
      console.error('Error fetching bid history:', err)
    }
  }

  const handleBidFieldEdit = (fieldName: 'starting_bid' | 'bid_cap' | 'property_sold', currentValue?: number | string) => {
    setEditingBidField(fieldName)
    setBidInputValue(currentValue !== undefined && currentValue !== null ? String(currentValue) : '')
    setBidHistoryOpen(null)
  }

  const handleBidSave = async (fieldName: 'starting_bid' | 'bid_cap' | 'property_sold') => {
    if (!onSaveOverride) return

    const propertyId = parseInt(property.id)
    let value: number | null = null
    let propertySoldDate: string | undefined

    if (fieldName === 'property_sold') {
      // For property_sold, parse the sale price from input
      if (bidInputValue.trim()) {
        value = parseFloat(bidInputValue.replace(/[$,]/g, ''))
        if (isNaN(value)) value = null
      }

      // Get the date input if provided, otherwise use current timestamp
      const dateInput = document.querySelector('input[type="date"]') as HTMLInputElement
      if (dateInput && dateInput.value) {
        propertySoldDate = new Date(dateInput.value).toISOString()
      } else {
        // Use current timestamp if no date provided
        propertySoldDate = new Date().toISOString()
      }
    } else {
      // For starting_bid and bid_cap, parse as number
      if (bidInputValue.trim()) {
        value = parseFloat(bidInputValue.replace(/[$,]/g, ''))
        if (isNaN(value)) value = null
      }
    }

    try {
      await onSaveOverride(propertyId, fieldName, value, undefined, propertySoldDate)
      setEditingBidField(null)
      setBidInputValue('')
      // Clear date input
      const dateInputElement = document.querySelector('input[type="date"]') as HTMLInputElement
      if (dateInputElement) {
        dateInputElement.value = ''
      }
    } catch (err) {
      console.error('Error saving bid field:', err)
    }
  }

  const handleBidRevert = async (fieldName: 'starting_bid' | 'bid_cap' | 'property_sold') => {
    if (!onRevertOverride) return

    const propertyId = parseInt(property.id)
    try {
      await onRevertOverride(propertyId, fieldName)
      setBidHistoryOpen(null)
    } catch (err) {
      console.error('Error reverting bid field:', err)
    }
  }

  const formatBidDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getCurrentBidValue = (fieldName: 'starting_bid' | 'bid_cap' | 'property_sold'): string => {
    switch (fieldName) {
      case 'starting_bid':
        return property.startingBidOverride ? formatCurrency(property.startingBidOverride) : '-'
      case 'bid_cap':
        return property.bidCapOverride ? formatCurrency(property.bidCapOverride) : '-'
      case 'property_sold':
        if (!property.propertySoldOverride) return '-'
        // If it's a number, display as currency (sale price)
        if (typeof property.propertySoldOverride === 'number') {
          return formatCurrency(property.propertySoldOverride)
        }
        // If it's a string that looks like a number, display as currency
        if (!isNaN(parseFloat(String(property.propertySoldOverride)))) {
          return formatCurrency(parseFloat(String(property.propertySoldOverride)))
        }
        // Otherwise it's a timestamp string
        return formatBidDate(String(property.propertySoldOverride))
      default:
        return '-'
    }
  }

  const getStatusConfig = () => {
    const status = property.status?.toLowerCase() || 'scheduled'
    // Handle combined statuses like "bankruptcy/adjourned"
    if (status.includes('bankruptcy')) {
      return { label: status.includes('/') ? status : 'Bankruptcy', color: 'text-purple-600 dark:text-purple-400', bgColor: 'bg-purple-100 dark:bg-purple-500/10' }
    } else if (status === 'scheduled') {
      return { label: 'Scheduled', color: 'text-blue-600 dark:text-blue-400', bgColor: 'bg-blue-100 dark:bg-blue-500/10' }
    } else if (status === 'adjourned') {
      return { label: 'Adjourned', color: 'text-yellow-600 dark:text-yellow-400', bgColor: 'bg-yellow-100 dark:bg-yellow-500/10' }
    } else if (status === 'sold') {
      return { label: 'Sold', color: 'text-emerald-600 dark:text-emerald-400', bgColor: 'bg-emerald-100 dark:bg-emerald-500/10' }
    } else if (status === 'canceled' || status === 'cancelled') {
      return { label: 'Canceled', color: 'text-red-600 dark:text-red-400', bgColor: 'bg-red-100 dark:bg-red-500/10' }
    } else if (status === 'borrower occupied') {
      return { label: 'Borrower Occupied', color: 'text-orange-600 dark:text-orange-400', bgColor: 'bg-orange-100 dark:bg-orange-500/10' }
    }
    return { label: status, color: 'text-gray-600 dark:text-gray-400', bgColor: 'bg-gray-200 dark:bg-gray-500/10' }
  }

  const statusConfig = getStatusConfig()

  // Spread calculation - use the pre-calculated spread from the hook (which uses higher of upset/judgment)
  const spreadPercent = property.spread.toFixed(1)
  const spreadColor = property.spread >= 30 ? 'text-emerald-400' : property.spread >= 10 ? 'text-yellow-500' : 'text-red-400'

  // Check if spread is 0 due to missing data (no zestimate and no ARV)
  const hasNoPricingData = !property.zestimate && (!property.estimatedARV || property.estimatedARV === 0)
  const spreadDisplay = hasNoPricingData ? 'N/A' : `+${spreadPercent}%`

  return (
    <tr className="group hover:bg-gray-100 dark:hover:bg-white/[0.02] transition-colors cursor-pointer">
      {/* Property */}
      <td className="p-4 md:sticky md:left-0 md:z-10 md:bg-white dark:md:bg-surface-dark/95 md:backdrop-blur-sm md:border-r md:border-gray-300 dark:md:border-border-dark md:group-hover:bg-gray-50 dark:md:group-hover:bg-surface-dark/95">
        <div className="flex items-center gap-4">
          <div className="relative">
            <div
              className="w-[60px] h-[60px] rounded-lg bg-cover bg-center shrink-0 cursor-pointer hover:opacity-80 transition-opacity hover:ring-2 hover:ring-primary/50"
              style={{ backgroundImage: `url('${property.image}')` }}
              onClick={(e) => {
                e.stopPropagation()
                onOpenModal?.(property)
              }}
              title="Click to view property details"
            />
            {/* Subtle overlay icon on hover to indicate clickability */}
            <div className="absolute inset-0 rounded-lg bg-black/0 hover:bg-black/20 transition-colors flex items-center justify-center opacity-0 hover:opacity-100 pointer-events-none">
              <span className="material-symbols-outlined text-white text-[24px]">visibility</span>
            </div>
          </div>
          {/* Vertical divider */}
          <div className="w-px h-12 bg-gray-300 dark:bg-border-dark self-center" />
          <div>
            {property.googleMapsUrl ? (
              <a
                href={property.googleMapsUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-900 dark:text-white font-medium hover:text-primary dark:hover:text-emerald-400 transition-colors"
                title="View on Google Maps"
              >
                {property.address}
              </a>
            ) : (
              <div className="text-gray-900 dark:text-white font-medium">{property.address}</div>
            )}
            <div className="text-gray-600 dark:text-gray-500 text-xs">{`${property.city}, ${property.state} ${property.zip}`}</div>
          </div>
        </div>
      </td>

      {/* Favorites (Star) */}
      <td className="p-4 text-center">
        <button
          type="button"
          onClick={async (e) => {
            e.stopPropagation()
            if (!onToggleFavorite) return
            const propertyId = parseInt(property.id)
            try {
              await onToggleFavorite(propertyId)
            } catch (err) {
              console.error('Error toggling favorite:', err)
            }
          }}
          className={`material-symbols-outlined text-[24px] transition-colors ${
            isFavorited
              ? 'text-yellow-400 fill-yellow-400'
              : 'text-gray-400 dark:text-gray-600 hover:text-yellow-400 dark:hover:text-yellow-400'
          }`}
          title={isFavorited ? 'Remove from favorites' : 'Add to favorites'}
        >
          star
        </button>
      </td>

      {/* County */}
      <td className="p-4">
        <span className="text-gray-700 dark:text-gray-400 text-sm">{property.county || '-'}</span>
      </td>

      {/* Auction Date */}
      <td className="p-4 text-gray-700 dark:text-gray-400 tabular-nums">
        {property.auctionDate}
      </td>

      {/* Zillow Link */}
      <td className="p-4 text-center">
        {property.zillowUrl ? (
          <a
            href={property.zillowUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
            title="View on Zillow"
          >
            <span className="material-symbols-outlined text-[20px]">open_in_new</span>
          </a>
        ) : (
          <span className="material-symbols-outlined text-gray-500 dark:text-gray-600 text-[20px]">link_off</span>
        )}
      </td>

      {/* Approx Upset */}
      <td className="p-4">
        {onSaveOverride && onGetOverrideHistory && onRevertOverride ? (
          <EditableCell
            value={property.approxUpset ?? null}
            overrideValue={property.approxUpsetOverride ?? null}
            propertyId={parseInt(property.id)}
            fieldName="approx_upset"
            propertyLabel={property.address}
            onSave={onSaveOverride}
            onGetHistory={onGetOverrideHistory}
            onRevert={onRevertOverride}
          />
        ) : (
          <span className="flex justify-center text-gray-700 dark:text-gray-400 tabular-nums py-2">
            {property.approxUpset ? formatCurrency(property.approxUpset) : '-'}
          </span>
        )}
      </td>

      {/* Approx. Judgment */}
      <td className="p-4">
        {onSaveOverride && onGetOverrideHistory && onRevertOverride ? (
          <EditableCell
            value={property.approxJudgment ?? null}
            overrideValue={property.approxJudgmentOverride ?? null}
            propertyId={parseInt(property.id)}
            fieldName="judgment_amount"
            propertyLabel={property.address}
            onSave={onSaveOverride}
            onGetHistory={onGetOverrideHistory}
            onRevert={onRevertOverride}
          />
        ) : (
          <span className="flex justify-center text-gray-700 dark:text-gray-400 tabular-nums py-2">
            {property.approxJudgment ? formatCurrency(property.approxJudgment) : '-'}
          </span>
        )}
      </td>

      {/* Zestimate */}
      <td className="p-4 text-center text-gray-700 dark:text-gray-400 tabular-nums">
        {property.zestimate ? formatCurrency(property.zestimate) : '-'}
      </td>

      {/* Spread */}
      <td className="p-4 text-center">
        <span className={`${hasNoPricingData ? 'text-gray-500' : spreadColor} font-medium tabular-nums`}>{spreadDisplay}</span>
      </td>

      {/* Tags */}
      <td className="p-4">
        <div className="relative" ref={tagsDropdownRef}>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation()
              setIsTagsDropdownOpen(!isTagsDropdownOpen)
            }}
            className="flex items-center gap-1.5 flex-wrap"
          >
            {tags.length > 0 ? (
              <div className="flex items-center gap-1.5 flex-wrap">
                {tags.map((tag) => (
                  <span
                    key={tag.id}
                    onClick={(e) => {
                      e.stopPropagation()
                      handleRemoveTag(tag.id)
                    }}
                    className="px-2 py-0.5 rounded text-xs font-medium text-white cursor-pointer hover:opacity-80 transition-opacity"
                    style={{ backgroundColor: tag.color }}
                    title={`Click to remove ${tag.name} tag`}
                  >
                    {tag.name}
                  </span>
                ))}
                <span className="material-symbols-outlined text-gray-500 dark:text-gray-500 text-[16px] hover:text-gray-700 dark:hover:text-gray-400">
                  expand_more
                </span>
              </div>
            ) : (
              <span className="material-symbols-outlined text-gray-500 dark:text-gray-600 text-[20px] hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">
                add_circle
              </span>
            )}
          </button>

          {isTagsDropdownOpen && (
            <div
              className="absolute z-50 mt-2 w-48 rounded-md shadow-lg bg-white dark:bg-surface-dark border border-gray-300 dark:border-border-dark py-1"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="px-3 py-2 text-xs text-gray-600 dark:text-gray-400 border-b border-gray-300 dark:border-border-dark">
                Add tag to property
              </div>
              {allTags.length === 0 ? (
                <div className="px-3 py-2 text-xs text-gray-500 dark:text-gray-500">No tags available</div>
              ) : (
                allTags
                  .filter((tag) => !tags.some((t) => t.id === tag.id))
                  .map((tag) => (
                    <button
                      key={tag.id}
                      type="button"
                      onClick={() => handleAddTag(tag.id)}
                      className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-white/[0.05] transition-colors flex items-center gap-2"
                    >
                      <span
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: tag.color }}
                      />
                      <span className="text-gray-800 dark:text-gray-300">{tag.name}</span>
                    </button>
                  ))
              )}
            </div>
          )}
        </div>
      </td>

      {/* Skip Trace */}
      <td className="p-4 text-center">
        {property.hasSkipTrace ? (
          <button
            type="button"
            onClick={handleCellClick}
            className="material-symbols-outlined text-emerald-600 dark:text-emerald-400 text-[18px] hover:text-emerald-700 dark:hover:text-emerald-300 transition-colors cursor-pointer"
            title="View skip trace data"
          >
            check_circle
          </button>
        ) : (
          <button
            type="button"
            onClick={handleSkipTraceClick}
            disabled={!onSkipTrace || isSkipTraceActive}
            className={`material-symbols-outlined text-[18px] transition-colors ${
              isSkipTraceActive
                ? 'text-yellow-600 dark:text-yellow-500 animate-spin'
                : onSkipTrace
                ? 'text-gray-500 dark:text-gray-500 hover:text-emerald-600 dark:hover:text-emerald-400 cursor-pointer'
                : 'text-gray-400 dark:text-gray-600 cursor-not-allowed'
            }`}
            title={
              isSkipTraceActive
                ? 'Skip trace in progress...'
                : onSkipTrace
                ? 'Click to start skip trace'
                : 'Skip trace not available'
            }
          >
            {isSkipTraceActive ? 'sync' : 'add_circle'}
          </button>
        )}
      </td>

      {/* Starting Bid */}
      <td className="p-4">
        {editingBidField === 'starting_bid' ? (
          <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
            <input
              type="text"
              value={bidInputValue}
              onChange={(e) => setBidInputValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleBidSave('starting_bid')
                if (e.key === 'Escape') {
                  setEditingBidField(null)
                  setBidInputValue('')
                }
              }}
              placeholder="$0"
              className="w-24 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              autoFocus
            />
            <button
              onClick={() => handleBidSave('starting_bid')}
              className="text-emerald-600 dark:text-emerald-400 hover:text-emerald-700"
            >
              ✓
            </button>
            <button
              onClick={() => {
                setEditingBidField(null)
                setBidInputValue('')
              }}
              className="text-red-600 dark:text-red-400 hover:text-red-700"
            >
              ✕
            </button>
          </div>
        ) : property.startingBidOverride ? (
          <div className="relative">
            <button
              onClick={(e) => handleBidFieldClick('starting_bid', e)}
              onDoubleClick={(e) => {
                e.stopPropagation()
                handleBidFieldEdit('starting_bid', property.startingBidOverride)
              }}
              className={`text-sm font-medium hover:text-blue-600 dark:hover:text-blue-400 transition-colors ${
                property.startingBidOverride
                  ? 'text-gray-900 dark:text-gray-100'
                  : 'text-gray-400 dark:text-gray-600'
              }`}
              title="Double-click to edit • Click for history"
            >
              {getCurrentBidValue('starting_bid')}
            </button>
            {bidHistoryOpen === 'starting_bid' && (
              <div className="absolute z-50 mt-2 w-48 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg">
                <div className="p-2">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-xs font-semibold text-gray-700 dark:text-gray-300">History</span>
                    <button
                      onClick={() => setBidHistoryOpen(null)}
                      className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                    >
                      ✕
                    </button>
                  </div>
                  {bidHistory.length > 0 ? (
                    <div className="max-h-40 overflow-y-auto">
                      {bidHistory.map((item) => (
                        <div
                          key={item.id}
                          className="flex justify-between items-center py-1 px-2 text-xs hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                        >
                          <span className="text-gray-900 dark:text-gray-100">
                            {typeof item.new_value === 'number' ? formatCurrency(item.new_value) : item.new_value}
                          </span>
                          <span className="text-gray-500 dark:text-gray-400 text-[10px]">
                            {formatBidDate(item.created_at)}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-gray-500 dark:text-gray-400 py-2">No history</p>
                  )}
                  {property.startingBidOverride && (
                    <button
                      onClick={() => handleBidRevert('starting_bid')}
                      className="w-full mt-2 text-xs text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 py-1 border-t border-gray-200 dark:border-gray-700"
                    >
                      Revert to original
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        ) : (
          <button
            onClick={(e) => {
              e.stopPropagation()
              handleBidFieldEdit('starting_bid', undefined)
            }}
            className="text-gray-400 dark:text-gray-600 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors text-sm"
            title="Add starting bid"
          >
            + Add
          </button>
        )}
      </td>

      {/* Bid Cap */}
      <td className="p-4">
        {editingBidField === 'bid_cap' ? (
          <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
            <input
              type="text"
              value={bidInputValue}
              onChange={(e) => setBidInputValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleBidSave('bid_cap')
                if (e.key === 'Escape') {
                  setEditingBidField(null)
                  setBidInputValue('')
                }
              }}
              placeholder="$0"
              className="w-24 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              autoFocus
            />
            <button
              onClick={() => handleBidSave('bid_cap')}
              className="text-emerald-600 dark:text-emerald-400 hover:text-emerald-700"
            >
              ✓
            </button>
            <button
              onClick={() => {
                setEditingBidField(null)
                setBidInputValue('')
              }}
              className="text-red-600 dark:text-red-400 hover:text-red-700"
            >
              ✕
            </button>
          </div>
        ) : property.bidCapOverride ? (
          <div className="relative">
            <button
              onClick={(e) => handleBidFieldClick('bid_cap', e)}
              onDoubleClick={(e) => {
                e.stopPropagation()
                handleBidFieldEdit('bid_cap', property.bidCapOverride)
              }}
              className={`text-sm font-medium hover:text-blue-600 dark:hover:text-blue-400 transition-colors ${
                property.bidCapOverride
                  ? 'text-gray-900 dark:text-gray-100'
                  : 'text-gray-400 dark:text-gray-600'
              }`}
              title="Double-click to edit • Click for history"
            >
              {getCurrentBidValue('bid_cap')}
            </button>
            {bidHistoryOpen === 'bid_cap' && (
              <div className="absolute z-50 mt-2 w-48 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg">
                <div className="p-2">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-xs font-semibold text-gray-700 dark:text-gray-300">History</span>
                    <button
                      onClick={() => setBidHistoryOpen(null)}
                      className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                    >
                      ✕
                    </button>
                  </div>
                  {bidHistory.length > 0 ? (
                    <div className="max-h-40 overflow-y-auto">
                      {bidHistory.map((item) => (
                        <div
                          key={item.id}
                          className="flex justify-between items-center py-1 px-2 text-xs hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                        >
                          <span className="text-gray-900 dark:text-gray-100">
                            {typeof item.new_value === 'number' ? formatCurrency(item.new_value) : item.new_value}
                          </span>
                          <span className="text-gray-500 dark:text-gray-400 text-[10px]">
                            {formatBidDate(item.created_at)}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-gray-500 dark:text-gray-400 py-2">No history</p>
                  )}
                  {property.bidCapOverride && (
                    <button
                      onClick={() => handleBidRevert('bid_cap')}
                      className="w-full mt-2 text-xs text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 py-1 border-t border-gray-200 dark:border-gray-700"
                    >
                      Revert to original
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        ) : (
          <button
            onClick={(e) => {
              e.stopPropagation()
              handleBidFieldEdit('bid_cap', undefined)
            }}
            className="text-gray-400 dark:text-gray-600 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors text-sm"
            title="Add bid cap"
          >
            + Add
          </button>
        )}
      </td>

      {/* Property Sold */}
      <td className="p-4">
        <div className="relative">
          {editingBidField === 'property_sold' ? (
            <div className="flex flex-col gap-2" onClick={(e) => e.stopPropagation()}>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500 dark:text-gray-400">Price:</span>
                <input
                  type="text"
                  value={bidInputValue}
                  onChange={(e) => setBidInputValue(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleBidSave('property_sold')
                    if (e.key === 'Escape') {
                      setEditingBidField(null)
                      setBidInputValue('')
                    }
                  }}
                  placeholder="$125,000"
                  className="w-28 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  autoFocus
                />
                <button
                  onClick={() => handleBidSave('property_sold')}
                  className="text-emerald-600 dark:text-emerald-400 hover:text-emerald-700"
                >
                  ✓
                </button>
                <button
                  onClick={() => {
                    setEditingBidField(null)
                    setBidInputValue('')
                  }}
                  className="text-red-600 dark:text-red-400 hover:text-red-700"
                >
                  ✕
                </button>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500 dark:text-gray-400">Date:</span>
                <input
                  type="date"
                  onChange={(e) => {
                    // Store the date for when saving
                    const dateInput = e.target.value
                    if (dateInput) {
                      e.target.dataset.dateValue = new Date(dateInput).toISOString()
                    }
                  }}
                  className="px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <span className="text-[10px] text-gray-400">(optional)</span>
              </div>
            </div>
          ) : property.propertySoldOverride ? (
            <>
              <button
                onClick={(e) => handleBidFieldClick('property_sold', e)}
                onDoubleClick={(e) => {
                  e.stopPropagation()
                  // Extract price from the override value
                  const priceMatch = String(property.propertySoldOverride).match(/^[\$]?([\d,]+)/)
                  const price = priceMatch ? parseFloat(priceMatch[1].replace(/,/g, '')) : 0
                  handleBidFieldEdit('property_sold', price)
                }}
                className="flex items-center gap-1 text-xs font-medium text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 transition-colors"
                title="Double-click to edit • Click for history"
              >
                <span className="material-symbols-outlined text-sm">check_circle</span>
                {/* Display price if it's a number, otherwise show the date */}
                {typeof property.propertySoldOverride === 'number' || !isNaN(parseFloat(String(property.propertySoldOverride))) ? formatCurrency(parseFloat(String(property.propertySoldOverride))) : formatBidDate(property.propertySoldOverride)}
              </button>
              {bidHistoryOpen === 'property_sold' && (
                <div className="absolute z-50 mt-2 w-56 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg">
                  <div className="p-2">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-xs font-semibold text-gray-700 dark:text-gray-300">History</span>
                      <button
                        onClick={() => setBidHistoryOpen(null)}
                        className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                      >
                        ✕
                      </button>
                    </div>
                    {bidHistory.length > 0 ? (
                      <div className="max-h-40 overflow-y-auto">
                        {bidHistory.map((item) => (
                          <div
                            key={item.id}
                            className="flex flex-col py-1 px-2 text-xs hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                          >
                            <div className="flex justify-between items-center">
                              <span className="text-emerald-600 dark:text-emerald-400 font-medium">
                                ✓ {typeof item.new_value === 'number' ? formatCurrency(item.new_value) : item.new_value}
                              </span>
                              <span className="text-gray-500 dark:text-gray-400 text-[10px]">
                                {formatBidDate(String(item.created_at))}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-gray-500 dark:text-gray-400 py-2">No history</p>
                    )}
                    <button
                      onClick={() => handleBidRevert('property_sold')}
                      className="w-full mt-2 text-xs text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 py-1 border-t border-gray-200 dark:border-gray-700"
                    >
                      Revert to original
                    </button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <button
              onClick={(e) => {
                e.stopPropagation()
                handleBidFieldEdit('property_sold', undefined)
              }}
              className="text-gray-400 dark:text-gray-600 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors text-sm"
              title="Mark as sold with price"
            >
              Mark Sold
            </button>
          )}
        </div>
      </td>

      {/* Status History */}
      <td className="p-4">
        {normalizedStatusHistory.length > 0 ? (
          <div className="flex flex-wrap gap-1">
            {(() => {
              // Count occurrences of each normalized status
              const statusCounts: Record<string, number> = {}
              normalizedStatusHistory.forEach(entry => {
                const status = entry.status
                statusCounts[status] = (statusCounts[status] || 0) + 1
              })

              // Get unique statuses in reverse order (most recent first)
              const uniqueStatuses = Array.from(new Set(
                normalizedStatusHistory.map(entry => entry.status)
              ))

              return uniqueStatuses.map((status, idx) => {
                const count = statusCounts[status]
                const label = count > 1 ? `${status} (${count})` : status
                const colorClass = getStatusColor(status)

                return (
                  <span
                    key={idx}
                    className={`px-2 py-0.5 rounded text-[10px] font-medium ${colorClass}`}
                    title={`Status history: ${status}`}
                  >
                    {label}
                  </span>
                )
              })
            })()}
          </div>
        ) : (
          <span className="text-gray-400 dark:text-gray-600 text-xs">-</span>
        )}
      </td>

      {/* Status */}
      <td className="p-4">
        <span className={`px-2 py-1 rounded text-xs font-medium ${statusConfig.color} ${statusConfig.bgColor}`}>
          {statusConfig.label}
        </span>
      </td>
    </tr>
  )
}
