'use client'

import { useState, useMemo, useRef, useEffect } from 'react'
import { AppSidebar } from '@/components/AppSidebar'
import { Header } from '@/components/Header'
import { StatsCard } from '@/components/StatsCard'
import { PropertyRow } from '@/components/PropertyRow'
import { PropertyDetailModal } from '@/components/PropertyDetailModal'
import { useProperties, transformPropertyToRow } from '@/lib/hooks/useProperties'
import { useSkipTrace } from '@/lib/hooks/useSkipTrace'
import { useTags } from '@/lib/hooks/useTags'
import { usePropertyOverrides } from '@/lib/hooks/usePropertyOverrides'
import { useSavedProperties } from '@/lib/hooks/useSavedProperties'
import { useFavorites } from '@/lib/hooks/useFavorites'
import { useUser } from '@/contexts/UserContext'
import { Property } from '@/lib/types/property'
import { supabase } from '@/lib/supabase/client'
import { getPropertyTags, addTagToProperty, removeTagFromProperty, getAllUserNotes, type UserTag } from '@/lib/api/client'

// NJ Counties list (only counties with data in database)
const NJ_COUNTIES = [
  'Atlantic', 'Bergen', 'Burlington', 'Camden', 'Cape May',
  'Cumberland', 'Essex', 'Gloucester', 'Hudson', 'Hunterdon',
  'Middlesex', 'Monmouth', 'Morris', 'Passaic', 'Salem', 'Union'
]

const DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

const SPREAD_OPTIONS = [
  { label: 'All', value: 'all' },
  { label: '30%+', value: '30plus' },
  { label: '20%+', value: '20plus' },
  { label: '10%+', value: '10plus' },
]

const STATUS_OPTIONS = [
  'Scheduled',
  'Adjourned',
  'Bankruptcy',
  'Sold',
  'Canceled',
  'Borrower Occupied',
]

const STATUS_HISTORY_OPTIONS = [
  'Scheduled',
  'Scheduled (2)',
  'Scheduled (3+)',
  'Rescheduled',
  'Rescheduled (2)',
  'Rescheduled (3+)',
  'Adjourned (Defendant)',
  'Adjourned (Defendant) (2)',
  'Adjourned (Defendant) (3+)',
  'Adjourned (Plaintiff)',
  'Adjourned (Plaintiff) (2)',
  'Adjourned (Plaintiff) (3+)',
  'Adjourned (Court)',
  'Adjourned (Court) (2)',
  'Adjourned (Court) (3+)',
  'Cancelled',
  'Cancelled (2)',
  'Cancelled (3+)',
  'Sold',
  'Sold (2)',
  'Sold (3+)',
  'Bankruptcy',
  'Bankruptcy (2)',
  'Bankruptcy (3+)',
  'Settled',
  'Settled (2)',
  'Settled (3+)',
  'No Sale',
  'No Sale (2)',
  'No Sale (3+)',
]


interface HomePageClientProps {
  initialData: {
    properties: Property[]
    count: number
  }
}

export function HomePageClient({ initialData }: HomePageClientProps) {
  // Mobile menu state
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  // Sort orders for columns: 'desc', 'asc', or null (no sort)
  const [auctionDateOrder, setAuctionDateOrder] = useState<'desc' | 'asc' | null>('desc')
  const [upsetOrder, setUpsetOrder] = useState<'desc' | 'asc' | null>(null)
  const [judgmentOrder, setJudgmentOrder] = useState<'desc' | 'asc' | null>(null)
  const [zestimateOrder, setZestimateOrder] = useState<'desc' | 'asc' | null>(null)
  const [spreadOrder, setSpreadOrder] = useState<'desc' | 'asc' | null>(null)

  // Helper: set one column's sort order and reset all others
  const setColumnSort = (column: 'auctionDate' | 'upset' | 'judgment' | 'zestimate' | 'spread', order: 'desc' | 'asc' | null) => {
    setAuctionDateOrder(column === 'auctionDate' ? order : null)
    setUpsetOrder(column === 'upset' ? order : null)
    setJudgmentOrder(column === 'judgment' ? order : null)
    setZestimateOrder(column === 'zestimate' ? order : null)
    setSpreadOrder(column === 'spread' ? order : null)
  }

  // Helper: cycle through sort states (null -> desc -> asc -> null)
  const cycleSort = (current: 'desc' | 'asc' | null) => {
    if (current === null) return 'desc'
    if (current === 'desc') return 'asc'
    return null
  }

  // Filter states
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [selectedCounties, setSelectedCounties] = useState<string[]>([])
  const [selectedDaysOfWeek, setSelectedDaysOfWeek] = useState<string[]>([])
  const [spreadFilter, setSpreadFilter] = useState<string>('all')
  const [selectedStatuses, setSelectedStatuses] = useState<string[]>([])
  const [selectedStatusHistory, setSelectedStatusHistory] = useState<string[]>([])
  const [selectedTagId, setSelectedTagId] = useState<number | null>(null)
  const [hasNotesOnly, setHasNotesOnly] = useState(false)
  const [auctionsTodayOnly, setAuctionsTodayOnly] = useState(false)
  const [favoritesOnly, setFavoritesOnly] = useState(false)

  // Price range filters
  const [judgmentRangeEnabled, setJudgmentRangeEnabled] = useState(false)
  const [judgmentMin, setJudgmentMin] = useState('')
  const [judgmentMax, setJudgmentMax] = useState('')
  const [upsetRangeEnabled, setUpsetRangeEnabled] = useState(false)
  const [upsetMin, setUpsetMin] = useState('')
  const [upsetMax, setUpsetMax] = useState('')

  // User and tags hooks
  const { userId } = useUser()
  const { tags, refetch: refetchTags, createTag } = useTags()
  const { getOverride, saveOverride, getOverrideHistory, revertOverride } = usePropertyOverrides(userId)
  const { isPropertySaved, toggleSaved, savedLoading } = useSavedProperties()
  const { isFavorited, toggleFavorite, favoritePropertyIds } = useFavorites()
  const [propertyTagsMap, setPropertyTagsMap] = useState<Record<number, UserTag[]>>({})
  const [propertyOverridesMap, setPropertyOverridesMap] = useState<Record<number, {
    approxUpsetOverride?: number
    approxJudgmentOverride?: number
    startingBidOverride?: number
    bidCapOverride?: number
    propertySoldOverride?: string | number  // Can be timestamp string or sale price number
  }>>({})
  const [propertiesWithNotes, setPropertiesWithNotes] = useState<Set<number>>(new Set())
  const [isCreateTagModalOpen, setIsCreateTagModalOpen] = useState(false)
  const [newTagName, setNewTagName] = useState('')
  const [newTagColor, setNewTagColor] = useState('#3B82F6')

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(100)
  const ITEMS_PER_PAGE_OPTIONS = [100, 500, 1000]

  // UI states
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedProperty, setSelectedProperty] = useState<ReturnType<typeof transformPropertyToRow> | null>(null)
  const exportDropdownRef = useRef<HTMLDivElement>(null)
  const [isExportDropdownOpen, setIsExportDropdownOpen] = useState(false)
  const scrollableContainerRef = useRef<HTMLDivElement>(null)

  // Filter dropdown refs
  const countyDropdownRef = useRef<HTMLDivElement>(null)
  const dayDropdownRef = useRef<HTMLDivElement>(null)
  const statusDropdownRef = useRef<HTMLDivElement>(null)
  const tagsDropdownRef = useRef<HTMLDivElement>(null)
  const statusHistoryDropdownRef = useRef<HTMLDivElement>(null)
  const sortOrderDropdownRef = useRef<HTMLDivElement>(null)
  const itemsPerPageDropdownRef = useRef<HTMLDivElement>(null)
  const priceRangeDropdownRef = useRef<HTMLDivElement>(null)
  const [isCountyDropdownOpen, setIsCountyDropdownOpen] = useState(false)
  const [isDayDropdownOpen, setIsDayDropdownOpen] = useState(false)
  const [isStatusDropdownOpen, setIsStatusDropdownOpen] = useState(false)
  const [isStatusHistoryDropdownOpen, setIsStatusHistoryDropdownOpen] = useState(false)
  const [isTagsDropdownOpen, setIsTagsDropdownOpen] = useState(false)
  const [isSortOrderDropdownOpen, setIsSortOrderDropdownOpen] = useState(false)
  const [isItemsPerPageDropdownOpen, setIsItemsPerPageDropdownOpen] = useState(false)
  const [isPriceRangeDropdownOpen, setIsPriceRangeDropdownOpen] = useState(false)

  // Toggle functions for filters
  const toggleCounty = (county: string) => {
    setSelectedCounties(prev =>
      prev.includes(county)
        ? prev.filter(c => c !== county)
        : [...prev, county]
    )
  }

  const toggleDayOfWeek = (day: string) => {
    setSelectedDaysOfWeek(prev =>
      prev.includes(day)
        ? prev.filter(d => d !== day)
        : [...prev, day]
    )
  }

  const toggleStatus = (status: string) => {
    setSelectedStatuses(prev =>
      prev.includes(status)
        ? prev.filter(s => s !== status)
        : [...prev, status]
    )
  }

  const toggleStatusHistory = (status: string) => {
    setSelectedStatusHistory(prev =>
      prev.includes(status)
        ? prev.filter(s => s !== status)
        : [...prev, status]
    )
  }

  const clearAllFilters = () => {
    setSearchQuery('')
    setSelectedCounties([])
    setSelectedDaysOfWeek([])
    setSpreadFilter('all')
    setSelectedStatuses([])
    setSelectedStatusHistory([])
    setSelectedTagId(null)
    setHasNotesOnly(false)
    setAuctionsTodayOnly(false)
    setFavoritesOnly(false)
    setJudgmentRangeEnabled(false)
    setJudgmentMin('')
    setJudgmentMax('')
    setUpsetRangeEnabled(false)
    setUpsetMin('')
    setUpsetMax('')
    setCurrentPage(1)
    setItemsPerPage(100)
  }

  // Fetch property tags for all visible properties
  useEffect(() => {
    if (!userId || properties.length === 0) return

    const fetchAllPropertyTags = async () => {
      const tagsMap: Record<number, UserTag[]> = {}
      for (const property of properties) {
        try {
          const propId = typeof property.id === 'number' ? property.id : Number(property.id)
          const tags = await getPropertyTags(propId, userId)
          if (tags.length > 0) {
            tagsMap[propId] = tags
          }
        } catch (error) {
          console.error(`Error fetching tags for property ${property.id}:`, error)
        }
      }
      setPropertyTagsMap(tagsMap)
    }

    fetchAllPropertyTags()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId])

  // Handler to add tag to property
  const handleAddTagToProperty = async (propertyId: number, tagId: number) => {
    if (!userId) return
    try {
      await addTagToProperty(propertyId, tagId, userId)
      // Refresh property tags
      const tags = await getPropertyTags(propertyId, userId)
      setPropertyTagsMap(prev => ({
        ...prev,
        [propertyId]: tags
      }))
    } catch (error) {
      console.error('Error adding tag to property:', error)
    }
  }

  // Handler to remove tag from property
  const handleRemoveTagFromProperty = async (propertyId: number, tagId: number) => {
    if (!userId) return
    try {
      await removeTagFromProperty(propertyId, tagId, userId)
      // Refresh property tags
      const tags = await getPropertyTags(propertyId, userId)
      setPropertyTagsMap(prev => {
        const newMap = { ...prev }
        if (tags.length === 0) {
          delete newMap[propertyId]
        } else {
          newMap[propertyId] = tags
        }
        return newMap
      })
    } catch (error) {
      console.error('Error removing tag from property:', error)
    }
  }

  // Handler to create new tag
  const handleCreateTag = async () => {
    if (!userId || !newTagName.trim()) return
    const result = await createTag(newTagName.trim(), newTagColor)
    if (result) {
      setNewTagName('')
      setNewTagColor('#3B82F6')
      setIsCreateTagModalOpen(false)
      refetchTags()
    }
  }

  // Handler to save property override
  const handleSaveOverride = async (propertyId: number, fieldName: 'approx_upset' | 'judgment_amount' | 'starting_bid' | 'bid_cap' | 'property_sold', newValue: number | null, notes?: string, propertySoldDate?: string) => {
    if (!userId) return
    try {
      await saveOverride(propertyId, fieldName, newValue, notes, propertySoldDate)
      // Update the override map with the new value
      if (fieldName === 'property_sold' && propertySoldDate) {
        setPropertyOverridesMap(prev => ({
          ...prev,
          [propertyId]: {
            ...prev[propertyId],
            propertySoldOverride: propertySoldDate
          }
        }))
      } else if (fieldName === 'starting_bid' && newValue !== null) {
        setPropertyOverridesMap(prev => ({
          ...prev,
          [propertyId]: {
            ...prev[propertyId],
            startingBidOverride: newValue
          }
        }))
      } else if (fieldName === 'bid_cap' && newValue !== null) {
        setPropertyOverridesMap(prev => ({
          ...prev,
          [propertyId]: {
            ...prev[propertyId],
            bidCapOverride: newValue
          }
        }))
      } else if (fieldName === 'approx_upset' && newValue !== null) {
        setPropertyOverridesMap(prev => ({
          ...prev,
          [propertyId]: {
            ...prev[propertyId],
            approxUpsetOverride: newValue
          }
        }))
      } else if (fieldName === 'judgment_amount' && newValue !== null) {
        setPropertyOverridesMap(prev => ({
          ...prev,
          [propertyId]: {
            ...prev[propertyId],
            approxJudgmentOverride: newValue
          }
        }))
      }
      // If the modal is open for this property, refresh it to show the new spread
      if (isModalOpen && selectedProperty && (typeof selectedProperty.id === 'number' ? selectedProperty.id : Number(selectedProperty.id)) === propertyId) {
        await handlePropertyUpdate(propertyId)
      }
    } catch (error) {
      console.error('Error saving override:', error)
      throw error
    }
  }

  // Handler to get override history
  const handleGetOverrideHistory = async (propertyId: number, fieldName: 'approx_upset' | 'judgment_amount' | 'starting_bid' | 'bid_cap' | 'property_sold') => {
    if (!userId) return []
    try {
      return await getOverrideHistory(propertyId, fieldName)
    } catch (error) {
      console.error('Error getting override history:', error)
      return []
    }
  }

  // Handler to revert override
  const handleRevertOverride = async (propertyId: number, fieldName: 'approx_upset' | 'judgment_amount' | 'starting_bid' | 'bid_cap' | 'property_sold') => {
    if (!userId) return
    try {
      await revertOverride(propertyId, fieldName)
      // Remove the override from the map
      setPropertyOverridesMap(prev => {
        const newMap = { ...prev }
        if (fieldName === 'approx_upset') {
          delete newMap[propertyId]?.approxUpsetOverride
        } else if (fieldName === 'judgment_amount') {
          delete newMap[propertyId]?.approxJudgmentOverride
        } else if (fieldName === 'starting_bid') {
          delete newMap[propertyId]?.startingBidOverride
        } else if (fieldName === 'bid_cap') {
          delete newMap[propertyId]?.bidCapOverride
        } else if (fieldName === 'property_sold') {
          delete newMap[propertyId]?.propertySoldOverride
        }
        // Clean up empty entries
        if (!newMap[propertyId]?.approxUpsetOverride &&
            !newMap[propertyId]?.approxJudgmentOverride &&
            !newMap[propertyId]?.startingBidOverride &&
            !newMap[propertyId]?.bidCapOverride &&
            !newMap[propertyId]?.propertySoldOverride) {
          delete newMap[propertyId]
        }
        return newMap
      })
      // If the modal is open for this property, refresh it to show the updated spread
      if (isModalOpen && selectedProperty && (typeof selectedProperty.id === 'number' ? selectedProperty.id : Number(selectedProperty.id)) === propertyId) {
        await handlePropertyUpdate(propertyId)
      }
    } catch (error) {
      console.error('Error reverting override:', error)
      throw error
    }
  }

  // Helper function to change page and scroll to top
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    // Scroll the container to top
    if (scrollableContainerRef.current) {
      scrollableContainerRef.current.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }

  // Scroll to top when page or items per page changes
  useEffect(() => {
    if (scrollableContainerRef.current) {
      scrollableContainerRef.current.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }, [currentPage, itemsPerPage])

  // Check if any filters are active
  const hasActiveFilters = searchQuery.trim() !== '' ||
    selectedCounties.length > 0 ||
    selectedDaysOfWeek.length > 0 ||
    spreadFilter !== 'all' ||
    selectedStatuses.length > 0 ||
    selectedStatusHistory.length > 0 ||
    selectedTagId !== null ||
    hasNotesOnly ||
    favoritesOnly ||
    (judgmentRangeEnabled && (judgmentMin || judgmentMax)) ||
    (upsetRangeEnabled && (upsetMin || upsetMax))

  // CSV Export function
  const exportToCSV = async (propertiesToExport: ReturnType<typeof transformPropertyToRow>[]) => {
    const { normalizeStatus, normalizeStatusHistory } = await import('@/lib/utils/statusNormalizer')

    const headers = [
      'Address', 'City', 'State', 'ZIP', 'County',
      'Auction Date', 'Day of Week', 'Status',
      'Status History',
      'Opening Bid', 'Approx Upset', 'Approx Judgment',
      'Zestimate', 'Est. ARV', 'Spread %',
      'Beds', 'Baths', 'Sqft',
      'Zillow Link'
    ]

    // Normalize all statuses and status histories
    const rows = await Promise.all(propertiesToExport.map(async (p) => {
      const normalizedStatus = await normalizeStatus(p.status || '')
      const normalizedHistory = p.statusHistory
        ? await normalizeStatusHistory(p.statusHistory)
        : []

      // Format status history as a readable string
      const historyString = normalizedHistory
        .map(h => `${h.status}${h.originalStatus ? ` (${h.originalStatus})` : ''}`)
        .join('; ')

      return [
        p.address,
        p.city,
        p.state,
        p.zip,
        p.county || '',
        p.auctionDate,
        p.dayOfWeek || '',
        normalizedStatus,
        historyString,
        p.openingBid.toString(),
        p.approxUpset?.toString() || '',
        p.approxJudgment?.toString() || '',
        p.zestimate?.toString() || '',
        p.estimatedARV.toString(),
        p.spread.toFixed(1),
        p.beds?.toString() || '',
        p.baths?.toString() || '',
        p.sqft?.toString() || '',
        p.zillowUrl || ''
      ]
    }))

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `properties_${new Date().toISOString().slice(0, 10)}.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    setIsExportDropdownOpen(false)
  }

  // Use initial server-fetched data, then let the hook manage updates
  // Fetch all properties with a large limit for client-side pagination
  // Determine which column to sort by (spread is client-side only)
  const activeSortColumn =
    upsetOrder ? 'upset' :
    judgmentOrder ? 'judgment' :
    zestimateOrder ? 'zestimate' :
    auctionDateOrder ? 'auctionDate' :
    null

  const activeSortOrder =
    activeSortColumn === 'upset' ? upsetOrder :
    activeSortColumn === 'judgment' ? judgmentOrder :
    activeSortColumn === 'zestimate' ? zestimateOrder :
    auctionDateOrder

  const { properties, count, isLoading, error, refetch, updateProperty, isFromCache } = useProperties({
    order_by: activeSortColumn === 'auctionDate' ? 'sale_date' :
              activeSortColumn === 'upset' ? 'approx_upset' :
              activeSortColumn === 'judgment' ? 'judgment_amount' :
              activeSortColumn === 'zestimate' ? 'zillow_enrichment!left(zestimate)' :
              undefined,
    order: activeSortOrder,
    limit: 10000,  // Large limit to fetch all properties for client-side pagination
    initialData,
  })

  // Fetch property overrides for all visible properties
  useEffect(() => {
    if (!userId || properties.length === 0) return

    const fetchAllPropertyOverrides = async () => {
      const overridesMap: Record<number, {
        approxUpsetOverride?: number
        approxJudgmentOverride?: number
        startingBidOverride?: number
        bidCapOverride?: number
        propertySoldOverride?: string | number  // Can be timestamp string or sale price number
      }> = {}
      for (const property of properties) {
        try {
          const propId = typeof property.id === 'number' ? property.id : Number(property.id)
          const upsetOverride = await getOverride(propId, 'approx_upset')
          const judgmentOverride = await getOverride(propId, 'judgment_amount')
          const startingBidOverride = await getOverride(propId, 'starting_bid')
          const bidCapOverride = await getOverride(propId, 'bid_cap')
          const propertySoldOverride = await getOverride(propId, 'property_sold')

          if (upsetOverride || judgmentOverride || startingBidOverride || bidCapOverride || propertySoldOverride) {
            overridesMap[propId] = {
              approxUpsetOverride: typeof upsetOverride?.new_value === 'number' ? upsetOverride?.new_value : undefined,
              approxJudgmentOverride: typeof judgmentOverride?.new_value === 'number' ? judgmentOverride?.new_value : undefined,
              startingBidOverride: typeof startingBidOverride?.new_value === 'number' ? startingBidOverride?.new_value : undefined,
              bidCapOverride: typeof bidCapOverride?.new_value === 'number' ? bidCapOverride?.new_value : undefined,
              propertySoldOverride: propertySoldOverride?.new_value,
            }
          }
        } catch (error) {
          console.error(`Error fetching overrides for property ${property.id}:`, error)
        }
      }
      setPropertyOverridesMap(overridesMap)
    }

    fetchAllPropertyOverrides()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId, getOverride, properties])

  // Fetch user notes to build set of properties with notes
  useEffect(() => {
    if (!userId || properties.length === 0) return

    const fetchAllUserNotes = async () => {
      try {
        const notes = await getAllUserNotes(userId, 1000)
        const propIdsWithNotes = new Set(
          notes.map(note => note.property_id)
        )
        setPropertiesWithNotes(propIdsWithNotes)
      } catch (error) {
        console.error('Error fetching user notes:', error)
      }
    }

    fetchAllUserNotes()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId, properties])

  // Callback to update property data and refresh modal if open
  const handlePropertyUpdate = async (propertyId: number) => {
    console.log('handlePropertyUpdate called for property', propertyId)

    // Update the properties array
    await updateProperty(propertyId)

    // If modal is open and the updated property matches, fetch fresh data for modal
    if (selectedProperty && parseInt(selectedProperty.id) === propertyId) {
      console.log('Modal is open for this property, fetching fresh data...')

      // Add a small delay to ensure database has committed the transaction
      // Then retry a few times to get the updated skip trace data
      let data = null
      let error = null
      let retries = 0
      const maxRetries = 5
      const delay = 1000 // 1 second between retries

      while (retries < maxRetries && (!data || !data.zillow_enrichment?.[0]?.skip_tracing)) {
        if (retries > 0) {
          console.log(`Retry ${retries}/${maxRetries}: Waiting ${delay}ms for skip trace data...`)
          await new Promise(resolve => setTimeout(resolve, delay))
        }

        const result = await supabase
          .from('foreclosure_listings')
          .select('id, property_id, sheriff_number, case_number, property_address, city, state, zip_code, county_name, sale_date, sale_time, court_name, property_status, status_detail, opening_bid, approx_upset, judgment_amount, minimum_bid, sale_price, plaintiff, plaintiff_attorney, defendant, property_type, lot_size, filing_date, judgment_date, writ_date, sale_terms, attorney_notes, general_notes, description, details_url, data_source_url, zillow_zpid, zillow_enrichment_status, zillow_enriched_at, zillow_enrichment!left(zpid, zestimate, zestimate_low, zestimate_high, bedrooms, bathrooms, sqft, year_built, lot_size, property_type, last_sold_date, last_sold_price, images, tax_assessment, tax_assessment_year, tax_billed, walk_score, transit_score, bike_score, tax_history, price_history, zestimate_history, climate_risk, comps, similar_properties, nearby_properties, skip_tracing), created_at, updated_at')
          .eq('id', propertyId)
          .single()

        data = result.data
        error = result.error

        if (error) {
          console.error('Error fetching updated property:', error)
          retries++
          continue
        }

        if (data?.zillow_enrichment?.[0]?.skip_tracing) {
          console.log('Found skip trace data!', data.zillow_enrichment[0].skip_tracing)
          break
        }

        retries++
      }

      console.log('Final fetch result - skip_tracing:', data?.zillow_enrichment?.[0]?.skip_tracing)

      if (data && !error) {
        const propId = typeof data.id === 'number' ? data.id : Number(data.id)
        const overrides = propertyOverridesMap[propId]
        const transformed = transformPropertyToRow(data, overrides)
        console.log('Transformed property has skipTraceData:', !!transformed.skipTraceData)
        setSelectedProperty(transformed)
      }
    } else {
      console.log('Modal not open or different property, skipping refresh')
    }
  }

  // Skip trace hook - pass custom update callback that also refreshes modal
  const { traceProperty, state: skipTraceState } = useSkipTrace(undefined, handlePropertyUpdate)

  // Track which specific property is currently being traced (for per-row loading state)
  const [tracingPropertyId, setTracingPropertyId] = useState<number | null>(null)

  // Wrapper for traceProperty that tracks which property is being traced
  const handleSkipTrace = async (propertyId: number) => {
    setTracingPropertyId(propertyId)
    const result = await traceProperty(propertyId)
    if (!result.success) {
      setTracingPropertyId(null)
    }
    return result
  }

  // Handler to toggle property saved/favorite status
  const handleToggleSaved = async (propertyId: number) => {
    if (!userId) return
    try {
      await toggleSaved(propertyId)
    } catch (err: any) {
      console.error('Error toggling saved status:', err)
    }
  }

  // Clear tracingPropertyId when skip trace completes (hook's isTracing becomes false)
  useEffect(() => {
    if (!skipTraceState.isTracing && tracingPropertyId !== null) {
      setTracingPropertyId(null)
    }
  }, [skipTraceState.isTracing, tracingPropertyId])

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (exportDropdownRef.current && !exportDropdownRef.current.contains(event.target as Node)) {
        setIsExportDropdownOpen(false)
      }
      if (countyDropdownRef.current && !countyDropdownRef.current.contains(event.target as Node)) {
        setIsCountyDropdownOpen(false)
      }
      if (dayDropdownRef.current && !dayDropdownRef.current.contains(event.target as Node)) {
        setIsDayDropdownOpen(false)
      }
      if (statusDropdownRef.current && !statusDropdownRef.current.contains(event.target as Node)) {
        setIsStatusDropdownOpen(false)
      }
      if (statusHistoryDropdownRef.current && !statusHistoryDropdownRef.current.contains(event.target as Node)) {
        setIsStatusHistoryDropdownOpen(false)
      }
      if (tagsDropdownRef.current && !tagsDropdownRef.current.contains(event.target as Node)) {
        setIsTagsDropdownOpen(false)
      }
      if (sortOrderDropdownRef.current && !sortOrderDropdownRef.current.contains(event.target as Node)) {
        setIsSortOrderDropdownOpen(false)
      }
      if (itemsPerPageDropdownRef.current && !itemsPerPageDropdownRef.current.contains(event.target as Node)) {
        setIsItemsPerPageDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Transform backend properties to UI format and apply client-side filters
  const rowProperties = useMemo(() => {
    const transformed = properties.map(p => {
      const propId = typeof p.id === 'number' ? p.id : Number(p.id)
      // Get override values for this property
      const overrides = propertyOverridesMap[propId]
      // Pass overrides to transformPropertyToRow so spread is recalculated correctly
      const transformed = transformPropertyToRow(p, overrides)
      return transformed
    })

    // Prepare search query for case-insensitive matching
    const searchLower = searchQuery.trim().toLowerCase()

    let filtered = transformed.filter(property => {
      // Filter by search query (address, city, state, zip)
      if (searchLower) {
        const searchableText = `${property.address} ${property.city} ${property.state} ${property.zip}`.toLowerCase()
        if (!searchableText.includes(searchLower)) {
          return false
        }
      }

      // Filter by county - check if the county name contains any of the selected counties
      if (selectedCounties.length > 0 && property.county) {
        const countyLower = property.county.toLowerCase()
        const matchesCounty = selectedCounties.some(selectedCounty =>
          countyLower.includes(selectedCounty.toLowerCase())
        )
        if (!matchesCounty) {
          return false
        }
      }

      // Filter by day of week
      if (selectedDaysOfWeek.length > 0) {
        // If days are selected, property MUST have a matching dayOfWeek
        if (!property.dayOfWeek || !selectedDaysOfWeek.includes(property.dayOfWeek)) {
          return false
        }
      }

      // Filter by spread
      if (spreadFilter !== 'all') {
        const spreadThreshold = spreadFilter === '30plus' ? 30 : spreadFilter === '20plus' ? 20 : 10
        if (property.spread < spreadThreshold) {
          return false
        }
      }

      // Filter by status - handle combined statuses like "bankruptcy/adjourned"
      if (selectedStatuses.length > 0 && property.status) {
        const propertyStatus = property.status.toLowerCase()

        // Check if this is a combined status (contains "/")
        if (propertyStatus.includes('/')) {
          // Split combined status and check if any part matches selected statuses
          const statusParts = propertyStatus.split('/').map(s => s.trim().toLowerCase())
          const normalizedSelected = selectedStatuses.map(s => s.toLowerCase())

          // Check if any selected status matches any part of the combined status
          const matches = statusParts.some(part =>
            normalizedSelected.some(selected =>
              part.includes(selected) || selected.includes(part)
            )
          )

          if (!matches) {
            return false
          }
        } else {
          // Normal exact match for single status
          if (!selectedStatuses.some(selected =>
            propertyStatus === selected.toLowerCase() ||
            propertyStatus.includes(selected.toLowerCase())
          )) {
            return false
          }
        }
      }

      // Filter by status history - check if property's status history badges match selected filters
      if (selectedStatusHistory.length > 0 && property.statusHistory && property.statusHistory.length > 0) {
        // Helper function to normalize status for filtering
        const normalizeForFilter = (status: string): string => {
          const s = status.toLowerCase().trim()
          // Map common original patterns to normalized versions
          if (s.includes('defendant') && s.includes('adjourned')) return 'adjourned (defendant)'
          if (s.includes('plaintiff') && s.includes('adjourned')) return 'adjourned (plaintiff)'
          if (s.includes('court') && s.includes('adjourned')) return 'adjourned (court)'
          if (s.includes('rescheduled') || s.includes('continued') || s.includes('reset')) return 'rescheduled'
          if (s.includes('cancel')) return 'cancelled'
          if (s.includes('sold')) return 'sold'
          if (s.includes('bankrupt')) return 'bankruptcy'
          if (s.includes('settled') || s.includes('stipulation')) return 'settled'
          if (s.includes('no sale') || s.includes('not sold')) return 'no sale'
          if (s.includes('scheduled')) return 'scheduled'
          return s
        }

        // Count occurrences of each normalized status in history
        const statusCounts: Record<string, number> = {}
        property.statusHistory.forEach(entry => {
          if (entry.status) {
            const normalized = normalizeForFilter(entry.status)
            statusCounts[normalized] = (statusCounts[normalized] || 0) + 1
          }
        })

        // Create badge labels that match what's displayed in the UI
        const historyBadges = property.statusHistory
          .filter(entry => entry.status)
          .map(entry => {
            const normalized = normalizeForFilter(entry.status || '')
            const count = statusCounts[normalized] || 1
            // Capitalize first letter for display
            const displayStatus = normalized.charAt(0).toUpperCase() + normalized.slice(1)
            return count > 1 ? `${displayStatus} (${count})` : displayStatus
          })

        // Check if any selected status history filter matches any badge
        const hasMatchingBadge = selectedStatusHistory.some(selected => {
          const selectedLower = selected.toLowerCase()

          // For filters with counts like "Scheduled (2)", match exactly
          if (selected.includes(' (2)')) {
            return historyBadges.some(badge =>
              badge.toLowerCase() === selectedLower
            )
          }
          // For filters with "3+" like "Scheduled (3+)", match any with count >= 3
          if (selected.includes(' (3+)')) {
            const baseStatus = selected.replace(' (3+)', '').toLowerCase()
            return Object.entries(statusCounts).some(([status, count]) =>
              status === baseStatus && count >= 3
            )
          }
          // For base status filters (no count), match any with that status
          return historyBadges.some(badge =>
            badge.toLowerCase() === selectedLower ||
            badge.toLowerCase().startsWith(selectedLower + ' (')
          )
        })

        if (!hasMatchingBadge) {
          return false
        }
      }

      // Filter by tag
      if (selectedTagId !== null) {
        const propId = typeof property.id === 'number' ? property.id : Number(property.id)
        const propTags = propertyTagsMap[propId] || []
        if (!propTags.some(tag => tag.id === selectedTagId)) {
          return false
        }
      }

      // Filter by notes
      if (hasNotesOnly) {
        const propId = typeof property.id === 'number' ? property.id : Number(property.id)
        if (!propertiesWithNotes.has(propId)) {
          return false
        }
      }

      // Filter by favorites
      if (favoritesOnly) {
        const propId = typeof property.id === 'number' ? property.id : Number(property.id)
        if (!isFavorited(propId)) {
          return false
        }
      }

      // Filter by auctions today
      if (auctionsTodayOnly) {
        const today = new Date()
        const auctionDate = new Date(property.auctionDate)
        const isToday = (
          auctionDate.getDate() === today.getDate() &&
          auctionDate.getMonth() === today.getMonth() &&
          auctionDate.getFullYear() === today.getFullYear()
        )
        if (!isToday) {
          return false
        }
      }

      // Filter by judgment price range
      if (judgmentRangeEnabled && (judgmentMin || judgmentMax)) {
        const judgmentAmount = property.approxJudgment || 0
        if (judgmentMin && judgmentAmount < parseFloat(judgmentMin)) {
          return false
        }
        if (judgmentMax && judgmentAmount > parseFloat(judgmentMax)) {
          return false
        }
      }

      // Filter by upset price range
      if (upsetRangeEnabled && (upsetMin || upsetMax)) {
        const upsetAmount = property.approxUpset || 0
        if (upsetMin && upsetAmount < parseFloat(upsetMin)) {
          return false
        }
        if (upsetMax && upsetAmount > parseFloat(upsetMax)) {
          return false
        }
      }

      // LIVE FEED: Exclude properties with past auction dates
      // Auction History (past auctions) is shown on /auction-history page
      const today = new Date()
      today.setHours(0, 0, 0, 0) // Reset to midnight for fair comparison
      const auctionDate = new Date(property.auctionDate)
      if (auctionDate < today) {
        return false
      }

      return true
    })

    // Client-side sorting for spread (calculated field)
    if (spreadOrder) {
      filtered.sort((a, b) => {
        return spreadOrder === 'desc' ? b.spread - a.spread : a.spread - b.spread
      })
    }

    return filtered
  }, [properties, searchQuery, selectedCounties, selectedDaysOfWeek, spreadFilter, selectedStatuses, selectedStatusHistory, selectedTagId, propertyTagsMap, propertyOverridesMap, propertiesWithNotes, hasNotesOnly, auctionsTodayOnly, spreadOrder, favoritesOnly, isFavorited, judgmentRangeEnabled, judgmentMin, judgmentMax, upsetRangeEnabled, upsetMin, upsetMax])

  // Paginated properties for display
  const paginatedProperties = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage
    const endIndex = startIndex + itemsPerPage
    return rowProperties.slice(startIndex, endIndex)
  }, [rowProperties, currentPage])

  // Calculate stats from all properties
  const stats = useMemo(() => {
    const avgSpread = rowProperties.length > 0
      ? rowProperties.reduce((sum, p) => sum + p.spread, 0) / rowProperties.length
      : 0

    const today = new Date()
    const auctionsToday = rowProperties.filter(p => {
      const auctionDate = new Date(p.auctionDate)
      return (
        auctionDate.getDate() === today.getDate() &&
        auctionDate.getMonth() === today.getMonth() &&
        auctionDate.getFullYear() === today.getFullYear()
      )
    }).length

    return {
      total: count,
      showing: rowProperties.length,
      avgSpread: avgSpread.toFixed(1),
      auctionsToday,
    }
  }, [rowProperties, count])

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1)
  }, [searchQuery, selectedCounties, selectedDaysOfWeek, spreadFilter, selectedStatuses, selectedTagId, hasNotesOnly, favoritesOnly, judgmentRangeEnabled, judgmentMin, judgmentMax, upsetRangeEnabled, upsetMin, upsetMax])

  const handleOpenModal = (property: ReturnType<typeof transformPropertyToRow>) => {
    setSelectedProperty(property)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setSelectedProperty(null)
  }

  return (
    <div className="h-screen flex overflow-hidden bg-gray-50 dark:bg-background-dark">
      <AppSidebar
        isMobileMenuOpen={isMobileMenuOpen}
        onMobileMenuClose={() => setIsMobileMenuOpen(false)}
      />

      <main className="flex-1 flex flex-col h-full relative overflow-hidden">
        <Header
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          onMobileMenuToggle={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        />

        {/* Dashboard Content */}
        <div ref={scrollableContainerRef} className="flex-1 overflow-y-auto p-3 lg:p-8 scroll-smooth">
          <div className="flex flex-col gap-3 lg:gap-6">
            {/* Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <StatsCard
                title="Total Properties"
                value={`${stats.showing.toLocaleString()} / ${stats.total.toLocaleString()}`}
                change={isLoading ? '...' : 'Showing / Total'}
                changeType="positive"
                progress={100}
                icon="verified"
                color="primary"
              />
              <StatsCard
                title="Avg. Equity Spread"
                value={`${stats.avgSpread}%`}
                change={isLoading ? '...' : 'Updated now'}
                changeType="positive"
                progress={Math.min(100, parseFloat(stats.avgSpread) * 2)}
                icon="monetization_on"
                color="emerald"
              />
              <StatsCard
                title="Auctions (24h)"
                value={stats.auctionsToday.toString()}
                change={isLoading ? '...' : 'Today'}
                changeType="neutral"
                progress={85}
                icon="gavel"
                color="orange"
                active={auctionsTodayOnly}
                onClick={() => setAuctionsTodayOnly(!auctionsTodayOnly)}
              />
            </div>

            {/* Cache Indicator */}
            {isFromCache && !isLoading && (
              <div className="flex items-center justify-end">
                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-200 dark:border-emerald-500/30 rounded-lg text-xs font-medium text-emerald-700 dark:text-emerald-400">
                  <span className="material-symbols-outlined text-[14px]">cached</span>
                  Loaded from cache
                </span>
              </div>
            )}

            {/* Filter Bar */}
            <div className="bg-white dark:bg-surface-dark border border-gray-200 dark:border-border-dark rounded-lg p-3 md:p-4 min-h-[52px] md:min-h-[60px]">
              <div className="flex flex-wrap items-center gap-2 md:gap-3 overflow-x-auto md:overflow-visible pb-2 md:pb-0 -mx-1 md:mx-0 px-1 md:px-0 snap-x">
                {/* County Filter */}
                    <div className="relative shrink-0 snap-start" ref={countyDropdownRef}>
                      <button
                        onClick={() => setIsCountyDropdownOpen(!isCountyDropdownOpen)}
                        className={`bg-white dark:bg-surface-dark border ${selectedCounties.length > 0 ? 'border-primary' : 'border-gray-300 dark:border-border-dark'} hover:border-gray-400 dark:hover:border-gray-500 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white px-2 py-1.5 md:px-3 rounded-lg text-xs md:text-sm font-medium flex items-center gap-0.5 md:gap-1.5 transition-colors whitespace-nowrap min-w-[80px] md:min-w-[100px]`}
                      >
                        <span className="material-symbols-outlined text-[16px] md:text-[18px] shrink-0">location_city</span>
                        <span className="inline">County</span>
                        <span className={`text-primary text-[10px] md:text-xs ${selectedCounties.length > 0 ? 'opacity-100' : 'opacity-0'} transition-opacity`}>( {selectedCounties.length} )</span>
                        <span className="material-symbols-outlined text-[14px] md:text-[16px] transition-transform shrink-0 ml-auto">{isCountyDropdownOpen ? 'expand_less' : 'expand_more'}</span>
                      </button>

                      {isCountyDropdownOpen && (
                        <>
                          {/* Mobile backdrop */}
                          <div
                            className="fixed inset-0 bg-black/60 z-40 md:hidden"
                            onClick={() => setIsCountyDropdownOpen(false)}
                          />
                          <div className="fixed bottom-0 left-0 right-0 md:absolute md:top-full md:left-0 md:right-auto md:bottom-auto md:mt-2 bg-white dark:bg-surface-dark border border-gray-200 dark:border-border-dark md:rounded-lg rounded-t-2xl shadow-xl z-50 md:w-64 md:max-h-80 max-h-[60vh] overflow-y-auto animate-in slide-in-from-bottom md:animate-in fade-in zoom-in duration-200">
                            {/* Header for mobile */}
                            <div className="sticky top-0 bg-white dark:bg-surface-dark border-b border-gray-200 dark:border-border-dark p-4 flex items-center justify-between md:hidden">
                              <h3 className="text-gray-900 dark:text-gray-900 dark:text-white font-semibold">Select Counties</h3>
                              <button
                                onClick={() => setIsCountyDropdownOpen(false)}
                                className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                              >
                                <span className="material-symbols-outlined">close</span>
                              </button>
                            </div>
                            <div className="p-2 md:p-2 grid grid-cols-2 gap-1">
                              {NJ_COUNTIES.map(county => (
                                <button
                                  key={county}
                                  onClick={() => toggleCounty(county)}
                                  className={`px-2 py-2 md:py-1.5 rounded text-xs font-medium text-left transition-colors ${
                                    selectedCounties.includes(county)
                                      ? 'bg-primary text-white'
                                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5'
                                  }`}
                                >
                                  <span className="flex items-center gap-1.5">
                                    <span className="material-symbols-outlined text-[14px]">
                                      {selectedCounties.includes(county) ? 'check_box' : 'check_box_outline_blank'}
                                    </span>
                                    {county}
                                  </span>
                                </button>
                              ))}
                            </div>
                            {/* Done button for mobile */}
                            <div className="sticky bottom-0 bg-white dark:bg-surface-dark border-t border-gray-200 dark:border-border-dark p-4 md:hidden">
                              <button
                                onClick={() => setIsCountyDropdownOpen(false)}
                                className="w-full py-3 bg-primary text-white rounded-lg font-medium"
                              >
                                Done
                              </button>
                            </div>
                          </div>
                        </>
                      )}
                    </div>

                    {/* Day of Week Filter */}
                    <div className="relative shrink-0 snap-start" ref={dayDropdownRef}>
                      <button
                        onClick={() => setIsDayDropdownOpen(!isDayDropdownOpen)}
                        className={`bg-white dark:bg-surface-dark border ${selectedDaysOfWeek.length > 0 ? 'border-primary' : 'border-gray-300 dark:border-border-dark'} hover:border-gray-400 dark:hover:border-gray-500 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white px-2 py-1.5 md:px-3 rounded-lg text-xs md:text-sm font-medium flex items-center gap-0.5 md:gap-1.5 transition-colors whitespace-nowrap min-w-[80px] md:min-w-[110px]`}
                      >
                        <span className="material-symbols-outlined text-[16px] md:text-[18px] shrink-0">event</span>
                        <span className="inline">Auction Day</span>
                        <span className={`text-primary text-[10px] md:text-xs ${selectedDaysOfWeek.length > 0 ? 'opacity-100' : 'opacity-0'} transition-opacity`}>( {selectedDaysOfWeek.length} )</span>
                        <span className="material-symbols-outlined text-[14px] md:text-[16px] transition-transform shrink-0 ml-auto">{isDayDropdownOpen ? 'expand_less' : 'expand_more'}</span>
                      </button>

                      {isDayDropdownOpen && (
                        <>
                          {/* Mobile backdrop */}
                          <div
                            className="fixed inset-0 bg-black/60 z-40 md:hidden"
                            onClick={() => setIsDayDropdownOpen(false)}
                          />
                          <div className="fixed bottom-0 left-0 right-0 md:absolute md:top-full md:left-0 md:right-auto md:bottom-auto md:mt-2 bg-white dark:bg-surface-dark border border-gray-200 dark:border-border-dark md:rounded-lg rounded-t-2xl shadow-xl z-50 md:w-48 animate-in slide-in-from-bottom md:animate-in fade-in zoom-in duration-200">
                            {/* Header for mobile */}
                            <div className="sticky top-0 bg-white dark:bg-surface-dark border-b border-gray-200 dark:border-border-dark p-4 flex items-center justify-between md:hidden">
                              <h3 className="text-gray-900 dark:text-gray-900 dark:text-white font-semibold">Select Days</h3>
                              <button
                                onClick={() => setIsDayDropdownOpen(false)}
                                className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                              >
                                <span className="material-symbols-outlined">close</span>
                              </button>
                            </div>
                            <div className="p-2 md:p-2 flex flex-col gap-1">
                              {DAYS_OF_WEEK.map(day => (
                                <button
                                  key={day}
                                  onClick={() => toggleDayOfWeek(day)}
                                  className={`px-3 py-2 md:py-1.5 rounded text-xs font-medium text-left transition-colors ${
                                    selectedDaysOfWeek.includes(day)
                                      ? 'bg-primary text-white'
                                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5'
                                  }`}
                                >
                                  <span className="flex items-center gap-1.5">
                                    <span className="material-symbols-outlined text-[14px]">
                                      {selectedDaysOfWeek.includes(day) ? 'check_box' : 'check_box_outline_blank'}
                                    </span>
                                    {day}
                                  </span>
                                </button>
                              ))}
                            </div>
                            {/* Done button for mobile */}
                            <div className="sticky bottom-0 bg-white dark:bg-surface-dark border-t border-gray-200 dark:border-border-dark p-4 md:hidden">
                              <button
                                onClick={() => setIsDayDropdownOpen(false)}
                                className="w-full py-3 bg-primary text-white rounded-lg font-medium"
                              >
                                Done
                              </button>
                            </div>
                          </div>
                        </>
                      )}
                    </div>

                    {/* Spread Filter */}
                    <div className="flex items-center gap-0.5 md:gap-2 bg-white dark:bg-surface-dark border border-gray-200 dark:border-border-dark rounded-lg px-1.5 md:px-3 py-1.5 shrink-0">
                      <span className="material-symbols-outlined text-gray-600 dark:text-gray-400 text-[14px] md:text-[18px]">trending_up</span>
                      <span className="text-gray-600 dark:text-gray-400 text-[10px] md:text-sm inline">Spread:</span>
                      {SPREAD_OPTIONS.map(option => (
                        <button
                          key={option.value}
                          onClick={() => setSpreadFilter(option.value)}
                          className={`px-1 md:px-2 py-1 rounded text-[10px] md:text-xs font-medium transition-colors ${
                            spreadFilter === option.value
                              ? 'bg-primary text-white'
                              : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
                          }`}
                        >
                          {option.label === 'All' ? 'All' : option.label.replace('+', '')}
                        </button>
                      ))}
                    </div>

                    {/* Status Filter */}
                    <div className="relative shrink-0 snap-start" ref={statusDropdownRef}>
                      <button
                        onClick={() => setIsStatusDropdownOpen(!isStatusDropdownOpen)}
                        className={`bg-white dark:bg-surface-dark border ${selectedStatuses.length > 0 ? 'border-primary' : 'border-gray-300 dark:border-border-dark'} hover:border-gray-400 dark:hover:border-gray-500 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white px-2 py-1.5 md:px-3 rounded-lg text-xs md:text-sm font-medium flex items-center gap-0.5 md:gap-1.5 transition-colors whitespace-nowrap min-w-[80px] md:min-w-[90px]`}
                      >
                        <span className="material-symbols-outlined text-[16px] md:text-[18px] shrink-0">label</span>
                        <span className="inline">Status</span>
                        <span className={`text-primary text-[10px] md:text-xs ${selectedStatuses.length > 0 ? 'opacity-100' : 'opacity-0'} transition-opacity`}>( {selectedStatuses.length} )</span>
                        <span className="material-symbols-outlined text-[14px] md:text-[16px] transition-transform shrink-0 ml-auto">{isStatusDropdownOpen ? 'expand_less' : 'expand_more'}</span>
                      </button>

                      {isStatusDropdownOpen && (
                        <>
                          {/* Mobile backdrop */}
                          <div
                            className="fixed inset-0 bg-black/60 z-40 md:hidden"
                            onClick={() => setIsStatusDropdownOpen(false)}
                          />
                          <div className="fixed bottom-0 left-0 right-0 md:absolute md:top-full md:left-0 md:right-auto md:bottom-auto md:mt-2 bg-white dark:bg-surface-dark border border-gray-200 dark:border-border-dark md:rounded-lg rounded-t-2xl shadow-xl z-50 md:w-48 animate-in slide-in-from-bottom md:animate-in fade-in zoom-in duration-200">
                            {/* Header for mobile */}
                            <div className="sticky top-0 bg-white dark:bg-surface-dark border-b border-gray-200 dark:border-border-dark p-4 flex items-center justify-between md:hidden">
                              <h3 className="text-gray-900 dark:text-white font-semibold">Select Status</h3>
                              <button
                                onClick={() => setIsStatusDropdownOpen(false)}
                                className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                              >
                                <span className="material-symbols-outlined">close</span>
                              </button>
                            </div>
                            <div className="p-2 md:p-2 flex flex-col gap-1">
                              {STATUS_OPTIONS.map(status => (
                                <button
                                  key={status}
                                  onClick={() => toggleStatus(status)}
                                  className={`px-3 py-2 md:py-1.5 rounded text-xs font-medium text-left transition-colors ${
                                    selectedStatuses.includes(status)
                                      ? 'bg-primary text-white'
                                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5'
                                  }`}
                                >
                                  <span className="flex items-center gap-1.5">
                                    <span className="material-symbols-outlined text-[14px]">
                                      {selectedStatuses.includes(status) ? 'check_box' : 'check_box_outline_blank'}
                                    </span>
                                    {status}
                                  </span>
                                </button>
                              ))}
                            </div>
                            {/* Done button for mobile */}
                            <div className="sticky bottom-0 bg-white dark:bg-surface-dark border-t border-gray-200 dark:border-border-dark p-4 md:hidden">
                              <button
                                onClick={() => setIsStatusDropdownOpen(false)}
                                className="w-full py-3 bg-primary text-white rounded-lg font-medium"
                              >
                                Done
                              </button>
                            </div>
                          </div>
                        </>
                      )}
                    </div>

                    {/* Status History Filter */}
                    <div className="relative shrink-0 snap-start" ref={statusHistoryDropdownRef}>
                      <button
                        onClick={() => setIsStatusHistoryDropdownOpen(!isStatusHistoryDropdownOpen)}
                        className={`bg-white dark:bg-surface-dark border ${selectedStatusHistory.length > 0 ? 'border-primary' : 'border-gray-300 dark:border-border-dark'} hover:border-gray-400 dark:hover:border-gray-500 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white px-2 py-1.5 md:px-3 rounded-lg text-xs md:text-sm font-medium flex items-center gap-0.5 md:gap-1.5 transition-colors whitespace-nowrap min-w-[80px] md:min-w-[110px]`}
                      >
                        <span className="material-symbols-outlined text-[16px] md:text-[18px] shrink-0">history</span>
                        <span className="inline">Status History</span>
                        <span className={`text-primary text-[10px] md:text-xs ${selectedStatusHistory.length > 0 ? 'opacity-100' : 'opacity-0'} transition-opacity`}>( {selectedStatusHistory.length} )</span>
                        <span className="material-symbols-outlined text-[14px] md:text-[16px] transition-transform shrink-0 ml-auto">{isStatusHistoryDropdownOpen ? 'expand_less' : 'expand_more'}</span>
                      </button>

                      {isStatusHistoryDropdownOpen && (
                        <>
                          {/* Mobile backdrop */}
                          <div
                            className="fixed inset-0 bg-black/60 z-40 md:hidden"
                            onClick={() => setIsStatusHistoryDropdownOpen(false)}
                          />
                          <div className="fixed bottom-0 left-0 right-0 md:absolute md:top-full md:left-0 md:right-auto md:bottom-auto md:mt-2 bg-white dark:bg-surface-dark border border-gray-200 dark:border-border-dark md:rounded-lg rounded-t-2xl shadow-xl z-50 md:w-56 md:max-h-80 max-h-[60vh] overflow-y-auto animate-in slide-in-from-bottom md:animate-in fade-in zoom-in duration-200">
                            {/* Header for mobile */}
                            <div className="sticky top-0 bg-white dark:bg-surface-dark border-b border-gray-200 dark:border-border-dark p-4 flex items-center justify-between md:hidden">
                              <h3 className="text-gray-900 dark:text-white font-semibold">Select Status History</h3>
                              <button
                                onClick={() => setIsStatusHistoryDropdownOpen(false)}
                                className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                              >
                                <span className="material-symbols-outlined">close</span>
                              </button>
                            </div>
                            <div className="p-2 md:p-2 flex flex-col gap-1">
                              {STATUS_HISTORY_OPTIONS.map(status => (
                                <button
                                  key={status}
                                  onClick={() => toggleStatusHistory(status)}
                                  className={`px-3 py-2 md:py-1.5 rounded text-xs font-medium text-left transition-colors ${
                                    selectedStatusHistory.includes(status)
                                      ? 'bg-primary text-white'
                                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5'
                                  }`}
                                >
                                  <span className="flex items-center gap-1.5">
                                    <span className="material-symbols-outlined text-[14px]">
                                      {selectedStatusHistory.includes(status) ? 'check_box' : 'check_box_outline_blank'}
                                    </span>
                                    {status}
                                  </span>
                                </button>
                              ))}
                            </div>
                            {/* Done button for mobile */}
                            <div className="sticky bottom-0 bg-white dark:bg-surface-dark border-t border-gray-200 dark:border-border-dark p-4 md:hidden">
                              <button
                                onClick={() => setIsStatusHistoryDropdownOpen(false)}
                                className="w-full py-3 bg-primary text-white rounded-lg font-medium"
                              >
                                Done
                              </button>
                            </div>
                          </div>
                        </>
                      )}
                    </div>

                    {/* Tags Filter */}
                    <div className="relative shrink-0 snap-start" ref={tagsDropdownRef}>
                      <button
                        onClick={() => setIsTagsDropdownOpen(!isTagsDropdownOpen)}
                        className={`bg-white dark:bg-surface-dark border ${selectedTagId !== null ? 'border-primary' : 'border-gray-300 dark:border-border-dark'} hover:border-gray-400 dark:hover:border-gray-500 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white px-2 py-1.5 md:px-3 rounded-lg text-xs md:text-sm font-medium flex items-center gap-0.5 md:gap-1.5 transition-colors whitespace-nowrap min-w-[80px] md:min-w-[85px]`}
                      >
                        <span className="material-symbols-outlined text-[16px] md:text-[18px] shrink-0">sell</span>
                        <span className="inline">Tags</span>
                        <span className={`text-primary text-[10px] md:text-xs ${selectedTagId !== null ? 'opacity-100' : 'opacity-0'} transition-opacity`}>•</span>
                        <span className="material-symbols-outlined text-[14px] md:text-[16px] transition-transform shrink-0 ml-auto">{isTagsDropdownOpen ? 'expand_less' : 'expand_more'}</span>
                      </button>

                      {isTagsDropdownOpen && (
                        <>
                          {/* Mobile backdrop */}
                          <div
                            className="fixed inset-0 bg-black/60 z-40 md:hidden"
                            onClick={() => setIsTagsDropdownOpen(false)}
                          />
                          <div className="fixed bottom-0 left-0 right-0 md:absolute md:top-full md:left-0 md:right-auto md:bottom-auto md:mt-2 bg-white dark:bg-surface-dark border border-gray-200 dark:border-border-dark md:rounded-lg rounded-t-2xl shadow-xl z-50 md:w-64 md:max-h-80 max-h-[60vh] overflow-y-auto animate-in slide-in-from-bottom md:animate-in fade-in zoom-in duration-200">
                            {/* Header for mobile */}
                            <div className="sticky top-0 bg-white dark:bg-surface-dark border-b border-gray-200 dark:border-border-dark p-4 flex items-center justify-between md:hidden">
                              <h3 className="text-gray-900 dark:text-white font-semibold">Filter by Tags</h3>
                              <button
                                onClick={() => setIsTagsDropdownOpen(false)}
                                className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                              >
                                <span className="material-symbols-outlined">close</span>
                              </button>
                            </div>
                            <div className="p-2 md:p-2 flex flex-col gap-1">
                              <button
                                onClick={() => setSelectedTagId(null)}
                                className={`px-3 py-2 md:py-1.5 rounded text-xs font-medium text-left transition-colors ${
                                  selectedTagId === null
                                    ? 'bg-primary text-white'
                                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5'
                                }`}
                              >
                                <span className="flex items-center gap-1.5">
                                  <span className="material-symbols-outlined text-[14px]">
                                    {selectedTagId === null ? 'check_box' : 'check_box_outline_blank'}
                                  </span>
                                  All Properties
                                </span>
                              </button>
                              {tags.map(tag => (
                                <button
                                  key={tag.id}
                                  onClick={() => setSelectedTagId(tag.id)}
                                  className={`px-3 py-2 md:py-1.5 rounded text-xs font-medium text-left transition-colors ${
                                    selectedTagId === tag.id
                                      ? 'bg-primary text-white'
                                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5'
                                  }`}
                                >
                                  <span className="flex items-center gap-1.5">
                                    <span className="material-symbols-outlined text-[14px]">
                                      {selectedTagId === tag.id ? 'check_box' : 'check_box_outline_blank'}
                                    </span>
                                    <span
                                      className="w-2 h-2 rounded-full"
                                      style={{ backgroundColor: tag.color }}
                                    />
                                    {tag.name}
                                  </span>
                                </button>
                              ))}
                              {tags.length === 0 && (
                                <div className="px-3 py-4 text-gray-500 text-xs text-center">
                                  No tags yet. Create one to get started!
                                </div>
                              )}
                              {/* Create tag button for desktop */}
                              <button
                                onClick={() => { setIsCreateTagModalOpen(true); setIsTagsDropdownOpen(false); }}
                                className="hidden md:flex w-full px-3 py-2 rounded-lg text-sm font-medium items-center gap-2 text-emerald-400 hover:bg-emerald-500/10 transition-colors"
                              >
                                <span className="material-symbols-outlined text-[16px]">add</span>
                                Create New Tag
                              </button>
                            </div>
                            {/* Create tag button for mobile */}
                            <div className="sticky bottom-0 bg-white dark:bg-surface-dark border-t border-gray-200 dark:border-border-dark p-4 md:hidden">
                              <button
                                onClick={() => { setIsCreateTagModalOpen(true); setIsTagsDropdownOpen(false); }}
                                className="w-full py-3 bg-emerald-500 text-white rounded-lg font-medium flex items-center justify-center gap-2"
                              >
                                <span className="material-symbols-outlined">add</span>
                                Create New Tag
                              </button>
                            </div>
                          </div>
                        </>
                      )}
                    </div>

                    {/* Notes Filter */}
                    <button
                      onClick={() => setHasNotesOnly(!hasNotesOnly)}
                      className={`bg-white dark:bg-surface-dark border ${hasNotesOnly ? 'border-primary' : 'border-gray-300 dark:border-border-dark'} hover:border-gray-400 dark:hover:border-gray-500 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white px-2 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-colors whitespace-nowrap min-w-[75px]`}
                      title={hasNotesOnly ? 'Show all properties' : 'Show only properties with notes'}
                    >
                      <span className="material-symbols-outlined text-[16px] shrink-0">
                        {hasNotesOnly ? 'check_box' : 'check_box_outline_blank'}
                      </span>
                      <span className="inline">Notes</span>
                      <span className={`text-primary text-[10px] ${hasNotesOnly ? 'opacity-100' : 'opacity-0'} transition-opacity ml-auto`}>•</span>
                    </button>

                    {/* Favorites Filter */}
                    <button
                      onClick={() => setFavoritesOnly(!favoritesOnly)}
                      className={`bg-white dark:bg-surface-dark border ${favoritesOnly ? 'border-yellow-400' : 'border-gray-300 dark:border-border-dark'} hover:border-gray-400 dark:hover:border-gray-500 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white px-2 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-colors whitespace-nowrap min-w-[90px]`}
                      title={favoritesOnly ? 'Show all properties' : 'Show only favorites'}
                    >
                      <span className={`material-symbols-outlined text-[16px] shrink-0 ${favoritesOnly ? 'text-yellow-400' : ''}`}>
                        star
                      </span>
                      <span className="inline">Favorites</span>
                      <span className={`text-yellow-400 text-[10px] ${favoritesOnly ? 'opacity-100' : 'opacity-0'} transition-opacity ml-auto`}>•</span>
                    </button>

                    {/* Price Range Filter - Combined */}
                    <div className="relative shrink-0 snap-start" ref={priceRangeDropdownRef}>
                      <button
                        onClick={() => setIsPriceRangeDropdownOpen(!isPriceRangeDropdownOpen)}
                        className={`bg-white dark:bg-surface-dark border ${((judgmentRangeEnabled && (judgmentMin || judgmentMax)) || (upsetRangeEnabled && (upsetMin || upsetMax))) ? 'border-primary' : 'border-gray-300 dark:border-border-dark'} hover:border-gray-400 dark:hover:border-gray-500 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white px-2 py-1.5 md:px-3 rounded-lg text-xs md:text-sm font-medium flex items-center gap-0.5 md:gap-1.5 transition-colors whitespace-nowrap min-w-[90px] md:min-w-[100px]`}
                      >
                        <span className="material-symbols-outlined text-[16px] md:text-[18px] shrink-0">attach_money</span>
                        <span className="inline">Price Range</span>
                        <span className={`text-primary text-[10px] md:text-xs ${((judgmentRangeEnabled && (judgmentMin || judgmentMax)) || (upsetRangeEnabled && (upsetMin || upsetMax))) ? 'opacity-100' : 'opacity-0'} transition-opacity`}>•</span>
                        <span className="material-symbols-outlined text-[14px] md:text-[16px] transition-transform shrink-0 ml-auto">{isPriceRangeDropdownOpen ? 'expand_less' : 'expand_more'}</span>
                      </button>

                      {isPriceRangeDropdownOpen && (
                        <>
                          <div
                            className="fixed inset-0 bg-black/60 z-40 md:hidden"
                            onClick={() => setIsPriceRangeDropdownOpen(false)}
                          />
                          <div className="fixed bottom-0 left-0 right-0 md:absolute md:top-full md:left-0 md:right-auto md:bottom-auto md:mt-2 bg-white dark:bg-surface-dark border border-gray-200 dark:border-border-dark md:rounded-lg rounded-t-2xl shadow-xl z-50 md:w-80 animate-in slide-in-from-bottom md:animate-in fade-in zoom-in duration-200">
                            <div className="sticky top-0 bg-white dark:bg-surface-dark border-b border-gray-200 dark:border-border-dark p-4 flex items-center justify-between md:hidden">
                              <h3 className="text-gray-900 dark:text-white font-semibold">Price Range Filters</h3>
                              <button
                                onClick={() => setIsPriceRangeDropdownOpen(false)}
                                className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                              >
                                <span className="material-symbols-outlined">close</span>
                              </button>
                            </div>
                            <div className="p-4 md:p-3 flex flex-col gap-4 max-h-[70vh] overflow-y-auto">

                              {/* Judgment Price Section */}
                              <div className="flex flex-col gap-3 pb-3 border-b border-gray-200 dark:border-border-dark">
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center gap-2">
                                    <span className="material-symbols-outlined text-primary">gavel</span>
                                    <span className="text-sm font-medium text-gray-900 dark:text-white">Judgment Price</span>
                                  </div>
                                  <button
                                    onClick={() => setJudgmentRangeEnabled(!judgmentRangeEnabled)}
                                    className={`w-12 h-6 rounded-full transition-colors ${judgmentRangeEnabled ? 'bg-primary' : 'bg-gray-300 dark:bg-gray-600'}`}
                                  >
                                    <div className={`w-5 h-5 bg-white rounded-full shadow-md transition-transform ${judgmentRangeEnabled ? 'translate-x-6' : 'translate-x-0.5'}`} />
                                  </button>
                                </div>
                                {judgmentRangeEnabled && (
                                  <div className="flex gap-2">
                                    <div className="flex-1 flex flex-col gap-1.5">
                                      <label className="text-xs text-gray-600 dark:text-gray-400">Min</label>
                                      <input
                                        type="number"
                                        value={judgmentMin}
                                        onChange={(e) => setJudgmentMin(e.target.value)}
                                        placeholder="No min"
                                        className="w-full px-3 py-2 bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-border-dark rounded-lg text-sm text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary"
                                      />
                                    </div>
                                    <div className="flex-1 flex flex-col gap-1.5">
                                      <label className="text-xs text-gray-600 dark:text-gray-400">Max</label>
                                      <input
                                        type="number"
                                        value={judgmentMax}
                                        onChange={(e) => setJudgmentMax(e.target.value)}
                                        placeholder="No max"
                                        className="w-full px-3 py-2 bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-border-dark rounded-lg text-sm text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary"
                                      />
                                    </div>
                                  </div>
                                )}
                              </div>

                              {/* Upset Price Section */}
                              <div className="flex flex-col gap-3">
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center gap-2">
                                    <span className="material-symbols-outlined text-primary">payments</span>
                                    <span className="text-sm font-medium text-gray-900 dark:text-white">Upset Price</span>
                                  </div>
                                  <button
                                    onClick={() => setUpsetRangeEnabled(!upsetRangeEnabled)}
                                    className={`w-12 h-6 rounded-full transition-colors ${upsetRangeEnabled ? 'bg-primary' : 'bg-gray-300 dark:bg-gray-600'}`}
                                  >
                                    <div className={`w-5 h-5 bg-white rounded-full shadow-md transition-transform ${upsetRangeEnabled ? 'translate-x-6' : 'translate-x-0.5'}`} />
                                  </button>
                                </div>
                                {upsetRangeEnabled && (
                                  <div className="flex gap-2">
                                    <div className="flex-1 flex flex-col gap-1.5">
                                      <label className="text-xs text-gray-600 dark:text-gray-400">Min</label>
                                      <input
                                        type="number"
                                        value={upsetMin}
                                        onChange={(e) => setUpsetMin(e.target.value)}
                                        placeholder="No min"
                                        className="w-full px-3 py-2 bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-border-dark rounded-lg text-sm text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary"
                                      />
                                    </div>
                                    <div className="flex-1 flex flex-col gap-1.5">
                                      <label className="text-xs text-gray-600 dark:text-gray-400">Max</label>
                                      <input
                                        type="number"
                                        value={upsetMax}
                                        onChange={(e) => setUpsetMax(e.target.value)}
                                        placeholder="No max"
                                        className="w-full px-3 py-2 bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-border-dark rounded-lg text-sm text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary"
                                      />
                                    </div>
                                  </div>
                                )}
                              </div>

                            </div>
                            <div className="sticky bottom-0 bg-white dark:bg-surface-dark border-t border-gray-200 dark:border-border-dark p-4 md:hidden">
                              <button
                                onClick={() => setIsPriceRangeDropdownOpen(false)}
                                className="w-full py-3 bg-primary text-white rounded-lg font-medium"
                              >
                                Done
                              </button>
                            </div>
                          </div>
                        </>
                      )}
                    </div>

                    {/* Sort Order Filter - Mobile only */}
                    <div className="relative shrink-0 snap-start md:hidden" ref={sortOrderDropdownRef}>
                      <button
                        onClick={() => setIsSortOrderDropdownOpen(!isSortOrderDropdownOpen)}
                        className={`bg-white dark:bg-surface-dark border ${auctionDateOrder ? 'border-primary' : 'border-gray-300 dark:border-border-dark'} hover:border-gray-400 dark:hover:border-gray-500 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white px-2 py-1.5 rounded-lg text-xs font-medium flex items-center gap-0.5 transition-colors whitespace-nowrap`}
                      >
                        <span className="material-symbols-outlined text-[16px]">sort</span>
                        <span className="inline">Order</span>
                        <span className={`material-symbols-outlined text-[14px] transition-transform ${isSortOrderDropdownOpen ? 'rotate-180' : ''}`}>expand_more</span>
                      </button>

                      {isSortOrderDropdownOpen && (
                        <>
                          {/* Mobile backdrop */}
                          <div
                            className="fixed inset-0 bg-black/60 z-40"
                            onClick={() => setIsSortOrderDropdownOpen(false)}
                          />
                          <div className="fixed bottom-0 left-0 right-0 bg-white dark:bg-surface-dark border border-gray-200 dark:border-border-dark rounded-t-2xl shadow-xl z-50 animate-in slide-in-from-bottom duration-200">
                            {/* Header for mobile */}
                            <div className="sticky top-0 bg-white dark:bg-surface-dark border-b border-gray-200 dark:border-border-dark p-4 flex items-center justify-between">
                              <h3 className="text-gray-900 dark:text-white font-semibold">Sort by Auction Date</h3>
                              <button
                                onClick={() => setIsSortOrderDropdownOpen(false)}
                                className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                              >
                                <span className="material-symbols-outlined">close</span>
                              </button>
                            </div>
                            <div className="p-2 flex flex-col gap-1">
                              <button
                                onClick={() => { setAuctionDateOrder('desc'); setIsSortOrderDropdownOpen(false); }}
                                className={`px-3 py-3 rounded text-xs font-medium text-left transition-colors ${
                                  auctionDateOrder === 'desc'
                                    ? 'bg-primary text-white'
                                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5'
                                }`}
                              >
                                <span className="flex items-center gap-2">
                                  <span className="material-symbols-outlined text-[18px]">arrow_downward</span>
                                  <span>Descending</span>
                                  <span className="text-gray-500 text-[10px] ml-auto">Newest first</span>
                                </span>
                              </button>
                              <button
                                onClick={() => { setAuctionDateOrder('asc'); setIsSortOrderDropdownOpen(false); }}
                                className={`px-3 py-3 rounded text-xs font-medium text-left transition-colors ${
                                  auctionDateOrder === 'asc'
                                    ? 'bg-primary text-white'
                                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5'
                                }`}
                              >
                                <span className="flex items-center gap-2">
                                  <span className="material-symbols-outlined text-[18px]">arrow_upward</span>
                                  <span>Ascending</span>
                                  <span className="text-gray-500 text-[10px] ml-auto">Oldest first</span>
                                </span>
                              </button>
                              <button
                                onClick={() => { setAuctionDateOrder(null); setIsSortOrderDropdownOpen(false); }}
                                className={`px-3 py-3 rounded text-xs font-medium text-left transition-colors ${
                                  auctionDateOrder === null
                                    ? 'bg-primary text-white'
                                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5'
                                }`}
                              >
                                <span className="flex items-center gap-2">
                                  <span className="material-symbols-outlined text-[18px]">remove</span>
                                  <span>Normal</span>
                                  <span className="text-gray-500 text-[10px] ml-auto">Default order</span>
                                </span>
                              </button>
                            </div>
                            {/* Done button for mobile */}
                            <div className="sticky bottom-0 bg-white dark:bg-surface-dark border-t border-border-dark p-4">
                              <button
                                onClick={() => setIsSortOrderDropdownOpen(false)}
                                className="w-full py-3 bg-primary text-white rounded-lg font-medium"
                              >
                                Done
                              </button>
                            </div>
                          </div>
                        </>
                      )}
                    </div>

                    {/* Divider */}
                    <div className="w-px h-8 bg-border-dark hidden sm:block" />

                    {/* Export Button */}
                    <div className="relative shrink-0 snap-start order-2" ref={exportDropdownRef}>
                      <button
                        onClick={() => setIsExportDropdownOpen(!isExportDropdownOpen)}
                        className="bg-white dark:bg-surface-dark border border-gray-200 dark:border-gray-300 dark:border-border-dark hover:border-gray-400 dark:hover:border-gray-500 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white px-2 py-1.5 md:px-3 rounded-lg text-xs md:text-sm font-medium flex items-center gap-0.5 md:gap-1.5 transition-colors whitespace-nowrap"
                      >
                        <span className="material-symbols-outlined text-[16px] md:text-[18px]">download</span>
                        <span className="inline">Export</span>
                        <span className={`material-symbols-outlined text-[14px] md:text-[16px] transition-transform ${isExportDropdownOpen ? 'rotate-180' : ''}`}>expand_more</span>
                      </button>

                      {isExportDropdownOpen && (
                        <>
                          {/* Mobile backdrop */}
                          <div
                            className="fixed inset-0 bg-black/60 z-40 md:hidden"
                            onClick={() => setIsExportDropdownOpen(false)}
                          />
                          <div className="fixed bottom-0 left-0 right-0 md:absolute md:top-full md:right-0 md:left-auto md:bottom-auto md:mt-2 bg-white dark:bg-surface-dark border border-gray-200 dark:border-border-dark md:rounded-lg rounded-t-2xl shadow-xl z-50 md:w-48 animate-in slide-in-from-bottom md:animate-in fade-in zoom-in duration-200">
                            {/* Header for mobile */}
                            <div className="sticky top-0 bg-white dark:bg-surface-dark border-b border-gray-200 dark:border-border-dark p-4 flex items-center justify-between md:hidden">
                              <h3 className="text-gray-900 dark:text-white font-semibold">Export</h3>
                              <button
                                onClick={() => setIsExportDropdownOpen(false)}
                                className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                              >
                                <span className="material-symbols-outlined">close</span>
                              </button>
                            </div>
                            <div className="p-1">
                              <button
                                onClick={async () => await exportToCSV(rowProperties)}
                                className="w-full flex items-center gap-2 px-3 py-3 md:py-2 hover:bg-white/5 rounded cursor-pointer transition-colors text-left"
                              >
                                <span className="material-symbols-outlined text-gray-400 text-[18px]">filter_list</span>
                                <div className="flex flex-col">
                                  <span className="text-sm text-gray-300">Showing ({rowProperties.length})</span>
                                  <span className="text-xs text-gray-500">Filtered results</span>
                                </div>
                              </button>
                              <button
                                onClick={async () => await exportToCSV(properties.map(p => {
                                  const propId = typeof p.id === 'number' ? p.id : Number(p.id)
                                  const overrides = propertyOverridesMap[propId]
                                  return transformPropertyToRow(p, overrides)
                                }))}
                                className="w-full flex items-center gap-2 px-3 py-3 md:py-2 hover:bg-white/5 rounded cursor-pointer transition-colors text-left"
                              >
                                <span className="material-symbols-outlined text-gray-400 text-[18px]">download</span>
                                <div className="flex flex-col">
                                  <span className="text-sm text-gray-300">All ({initialData.properties.length})</span>
                                  <span className="text-xs text-gray-500">All properties</span>
                                </div>
                              </button>
                            </div>
                          </div>
                        </>
                      )}
                    </div>

                    {/* Clear Filters Button (after Export on desktop only) */}
                    {hasActiveFilters && (
                      <button
                        onClick={clearAllFilters}
                        className="bg-red-500/20 border border-red-500/50 text-red-400 hover:bg-red-500/30 px-2 py-1.5 md:px-3 rounded-lg text-xs md:text-sm font-medium flex items-center gap-0.5 md:gap-1 transition-colors shrink-0 snap-start whitespace-nowrap md:order-1"
                      >
                        <span className="material-symbols-outlined text-[16px] md:text-[18px]">filter_alt_off</span>
                        <span className="inline">Clear</span>
                      </button>
                    )}
                  </div>
                </div>

            {/* Loading State */}
            {isLoading && properties.length === 0 && (
              <div className="bg-white dark:bg-surface-dark border border-gray-200 dark:border-border-dark rounded-lg p-12 text-center">
                <div className="flex flex-col items-center gap-4">
                  <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                  <p className="text-gray-400">Loading properties...</p>
                </div>
              </div>
            )}

            {/* Error State */}
            {error && !isLoading && (
              <div className="bg-surface-dark border border-red-500/30 rounded-lg p-12 text-center">
                <div className="flex flex-col items-center gap-4">
                  <span className="material-symbols-outlined text-red-500 text-4xl">error</span>
                  <p className="text-red-400">Failed to load properties: {error}</p>
                  <button
                    onClick={() => refetch()}
                    className="px-4 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors"
                  >
                    Retry
                  </button>
                </div>
              </div>
            )}

            {/* Empty State */}
            {!isLoading && !error && rowProperties.length === 0 && (
              <div className="bg-white dark:bg-surface-dark border border-gray-200 dark:border-border-dark rounded-lg p-12 text-center">
                <div className="flex flex-col items-center gap-4">
                  <span className="material-symbols-outlined text-gray-500 text-4xl">search_off</span>
                  <p className="text-gray-400">No properties found</p>
                </div>
              </div>
            )}

            {/* Data */}
            {!isLoading && !error && rowProperties.length > 0 && (
              <div className="bg-white dark:bg-surface-dark border border-gray-200 dark:border-border-dark rounded-lg overflow-hidden shadow-xl -mx-4 md:mx-0">
                <div className="overflow-auto max-h-[800px] px-4 md:px-0">
                  <table className="w-full table-fixed text-left border-collapse">
                  <thead className="sticky top-0 z-20">
                    <tr className="bg-gradient-to-r from-gray-100 to-gray-200 dark:from-surface-dark dark:to-[#1a1f2e] border-b-2 border-gray-300 dark:border-border-dark text-xs tracking-wider">
                        <th className="p-4 font-semibold text-gray-700 dark:text-gray-300 text-center uppercase md:sticky md:left-0 md:z-30 md:bg-gradient-to-r md:from-gray-100 md:to-gray-200 dark:md:from-surface-dark dark:md:to-[#1a1f2e] md:border-r md:border-gray-300 dark:md:border-border-dark" style={{ width: '350px' }}>Property</th>
                        <th className="p-4 font-semibold text-gray-700 dark:text-gray-300 text-center uppercase" style={{ width: '70px' }}>
                          <span className="material-symbols-outlined text-[20px]">star</span>
                        </th>
                        <th className="p-4 font-semibold text-gray-700 dark:text-gray-300 text-center uppercase" style={{ width: '120px' }}>County</th>
                        <th className="p-4 font-semibold text-gray-700 dark:text-gray-300 text-center" style={{ width: '130px' }}>
                          <div className="flex items-center justify-center gap-2">
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                setColumnSort('auctionDate', cycleSort(auctionDateOrder))
                              }}
                              className="flex items-center gap-2 hover:text-gray-900 dark:hover:text-white hover:bg-gray-300 dark:hover:bg-white/5 px-2 py-1 rounded transition-colors cursor-pointer"
                            >
                              <span className="uppercase">Auction Date</span>
                              <span className="material-symbols-outlined text-[14px]">
                                {auctionDateOrder === 'desc' ? 'arrow_downward' : auctionDateOrder === 'asc' ? 'arrow_upward' : 'sort'}
                              </span>
                            </button>
                          </div>
                        </th>
                        <th className="p-4 font-semibold text-gray-700 dark:text-gray-300 text-center uppercase" style={{ width: '90px' }}>Zillow</th>
                        <th className="p-4 font-semibold text-gray-700 dark:text-gray-300 text-center" style={{ width: '120px' }}>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              setColumnSort('upset', cycleSort(upsetOrder))
                            }}
                            className="flex items-center gap-2 justify-center hover:text-gray-900 dark:hover:text-white hover:bg-gray-300 dark:hover:bg-white/5 px-2 py-1 rounded transition-colors cursor-pointer w-full"
                          >
                            <span className="uppercase">Approx Upset</span>
                            <span className="material-symbols-outlined text-[14px]">
                              {upsetOrder === 'desc' ? 'arrow_downward' : upsetOrder === 'asc' ? 'arrow_upward' : 'sort'}
                            </span>
                          </button>
                        </th>
                        <th className="p-4 font-semibold text-gray-700 dark:text-gray-300 text-center" style={{ width: '140px' }}>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              setColumnSort('judgment', cycleSort(judgmentOrder))
                            }}
                            className="flex items-center gap-2 justify-center hover:text-gray-900 dark:hover:text-white hover:bg-gray-300 dark:hover:bg-white/5 px-2 py-1 rounded transition-colors cursor-pointer w-full"
                          >
                            <span className="uppercase">Approx. Judgment</span>
                            <span className="material-symbols-outlined text-[14px]">
                              {judgmentOrder === 'desc' ? 'arrow_downward' : judgmentOrder === 'asc' ? 'arrow_upward' : 'sort'}
                            </span>
                          </button>
                        </th>
                        <th className="p-4 font-semibold text-gray-700 dark:text-gray-300 text-center" style={{ width: '110px' }}>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              setColumnSort('zestimate', cycleSort(zestimateOrder))
                            }}
                            className="flex items-center gap-2 justify-center hover:text-gray-900 dark:hover:text-white hover:bg-gray-300 dark:hover:bg-white/5 px-2 py-1 rounded transition-colors cursor-pointer w-full"
                          >
                            <span className="uppercase">Zestimate</span>
                            <span className="material-symbols-outlined text-[14px]">
                              {zestimateOrder === 'desc' ? 'arrow_downward' : zestimateOrder === 'asc' ? 'arrow_upward' : 'sort'}
                            </span>
                          </button>
                        </th>
                        <th className="p-4 font-semibold text-gray-700 dark:text-gray-300 text-center" style={{ width: '100px' }}>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              setColumnSort('spread', cycleSort(spreadOrder))
                            }}
                            className="flex items-center gap-2 justify-center hover:text-gray-900 dark:hover:text-white hover:bg-gray-300 dark:hover:bg-white/5 px-2 py-1 rounded transition-colors cursor-pointer w-full"
                          >
                            <span className="uppercase">Spread</span>
                            <span className="material-symbols-outlined text-[14px]">
                              {spreadOrder === 'desc' ? 'arrow_downward' : spreadOrder === 'asc' ? 'arrow_upward' : 'sort'}
                            </span>
                          </button>
                        </th>
                        <th className="p-4 font-semibold text-gray-700 dark:text-gray-300 text-center uppercase" style={{ width: '80px' }}>Tags</th>
                        <th className="p-4 font-semibold text-gray-700 dark:text-gray-300 text-center uppercase" style={{ width: '110px' }}>Skip Trace</th>
                        <th className="p-4 font-semibold text-gray-700 dark:text-gray-300 text-center uppercase" style={{ width: '120px' }}>Starting Bid</th>
                        <th className="p-4 font-semibold text-gray-700 dark:text-gray-300 text-center uppercase" style={{ width: '120px' }}>Bid Cap</th>
                        <th className="p-4 font-semibold text-gray-700 dark:text-gray-300 text-center uppercase" style={{ width: '130px' }}>Property Sold</th>
                        <th className="p-4 font-semibold text-gray-700 dark:text-gray-300 text-center uppercase" style={{ width: '160px' }}>Status History</th>
                        <th className="p-4 font-semibold text-gray-700 dark:text-gray-300 text-center uppercase" style={{ width: '140px' }}>Current Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 dark:divide-border-dark text-sm">
                      {paginatedProperties.map((property) => (
                        <PropertyRow
                          key={property.id}
                          property={property}
                          tags={propertyTagsMap[typeof property.id === 'number' ? property.id : Number(property.id)] || []}
                          allTags={tags}
                          onOpenModal={() => handleOpenModal(property)}
                          onSkipTrace={handleSkipTrace}
                          onAddTag={handleAddTagToProperty}
                          onRemoveTag={handleRemoveTagFromProperty}
                          skipTraceInProgress={(typeof property.id === 'number' ? property.id : Number(property.id)) === tracingPropertyId}
                          onSaveOverride={handleSaveOverride}
                          onGetOverrideHistory={handleGetOverrideHistory}
                          onRevertOverride={handleRevertOverride}
                          isSaved={isPropertySaved(typeof property.id === 'number' ? property.id : Number(property.id))}
                          onToggleSaved={handleToggleSaved}
                          savedLoading={savedLoading}
                          isFavorited={isFavorited(typeof property.id === 'number' ? property.id : Number(property.id))}
                          onToggleFavorite={toggleFavorite}
                        />
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Pagination Controls */}
            {!isLoading && !error && rowProperties.length > 0 && (
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 md:gap-0 mt-4 bg-white dark:bg-surface-dark border border-gray-200 dark:border-border-dark rounded-lg p-3 md:p-4">
                {/* Showing info - compact on mobile */}
                <div className="text-xs md:text-sm text-gray-400 text-center md:text-left">
                  <span className="hidden sm:inline">
                    Showing {(currentPage - 1) * itemsPerPage + 1} to {Math.min(currentPage * itemsPerPage, rowProperties.length)} of {rowProperties.length} properties
                  </span>
                  <span className="sm:hidden">
                    {(currentPage - 1) * itemsPerPage + 1}-{Math.min(currentPage * itemsPerPage, rowProperties.length)} of {rowProperties.length}
                  </span>
                </div>

                {/* Pagination controls - stacked on mobile */}
                <div className="flex flex-col sm:flex-row items-center justify-center gap-2 sm:gap-3 w-full sm:w-auto">
                  {/* Page navigation buttons */}
                  <div className="flex items-center gap-1 sm:gap-2">
                    {/* Previous button - icon on mobile, text on desktop */}
                    <button
                      onClick={() => handlePageChange(Math.max(1, currentPage - 1))}
                      disabled={currentPage === 1}
                      className="px-2 sm:px-3 py-2 bg-white dark:bg-surface-dark border border-gray-200 dark:border-border-dark rounded-lg text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      <span className="material-symbols-outlined text-[18px] md:hidden">chevron_left</span>
                      <span className="hidden md:inline">Previous</span>
                    </button>

                    {/* Page numbers - show fewer on mobile */}
                    <div className="flex items-center gap-1">
                      {(() => {
                        const totalPages = Math.ceil(rowProperties.length / itemsPerPage)
                        const pageNumbers: (number | string)[] = []

                        // Show pages: always include 1, current page with neighbors, and last page
                        const startPage = Math.max(1, currentPage - 2)
                        const endPage = Math.min(totalPages, currentPage + 2)

                        // Always show first page
                        if (startPage > 1) {
                          pageNumbers.push(1)
                          if (startPage > 2) pageNumbers.push('...')
                        }

                        // Show pages around current (hide middle pages on mobile via CSS)
                        for (let i = startPage; i <= endPage; i++) {
                          pageNumbers.push(i)
                        }

                        // Always show last page
                        if (endPage < totalPages) {
                          if (endPage < totalPages - 1) pageNumbers.push('...')
                          pageNumbers.push(totalPages)
                        }

                        return pageNumbers.map((page, idx) =>
                          typeof page === 'string' ? (
                            <span key={`ellipsis-${idx}`} className="px-2 py-2 text-gray-500 hidden sm:inline">
                              {page}
                            </span>
                          ) : (
                            <button
                              key={page}
                              onClick={() => handlePageChange(page)}
                              className={`px-2 sm:px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                                currentPage === page
                                  ? 'bg-primary text-white'
                                  : 'bg-white dark:bg-surface-dark border border-gray-200 dark:border-border-dark text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:border-gray-500'
                              } ${Math.abs(page - currentPage) > 2 && page !== 1 && page !== totalPages ? 'hidden sm:inline-flex' : ''}`}
                            >
                              {page}
                            </button>
                          )
                        )
                      })()}
                    </div>

                    {/* Next button - icon on mobile, text on desktop */}
                    <button
                      onClick={() => handlePageChange(Math.min(Math.ceil(rowProperties.length / itemsPerPage), currentPage + 1))}
                      disabled={currentPage >= Math.ceil(rowProperties.length / itemsPerPage)}
                      className="px-2 sm:px-3 py-2 bg-white dark:bg-surface-dark border border-gray-200 dark:border-border-dark rounded-lg text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      <span className="material-symbols-outlined text-[18px] md:hidden">chevron_right</span>
                      <span className="hidden md:inline">Next</span>
                    </button>
                  </div>

                  {/* Items per page dropdown - full width on mobile */}
                  <div className="relative w-full sm:w-auto" ref={itemsPerPageDropdownRef}>
                    <button
                      onClick={() => setIsItemsPerPageDropdownOpen(!isItemsPerPageDropdownOpen)}
                      className="w-full sm:w-auto flex items-center justify-center gap-2 px-3 py-2 bg-white dark:bg-surface-dark border border-gray-200 dark:border-border-dark rounded-lg text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:border-gray-500 transition-colors"
                    >
                      <span className="material-symbols-outlined text-[18px]">density_small</span>
                      <span>{itemsPerPage}/page</span>
                      <svg
                        className={`w-4 h-4 transition-transform ${isItemsPerPageDropdownOpen ? 'rotate-180' : ''}`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                    {isItemsPerPageDropdownOpen && (
                      <div className="absolute bottom-full left-1/2 -translate-x-1/2 sm:left-auto sm:right-0 sm:translate-x-0 mb-2 bg-white dark:bg-surface-dark border border-gray-200 dark:border-border-dark rounded-lg shadow-xl z-50 min-w-[120px]">
                        {ITEMS_PER_PAGE_OPTIONS.map((option) => (
                          <button
                            key={option}
                            onClick={() => {
                              setItemsPerPage(option)
                              setCurrentPage(1)
                              setIsItemsPerPageDropdownOpen(false)
                            }}
                            className={`w-full px-4 py-2 text-left text-sm font-medium transition-colors first:rounded-t-lg last:rounded-b-lg hover:bg-primary/20 ${
                              itemsPerPage === option ? 'text-primary' : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                            }`}
                          >
                            {option}/page
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Property Detail Modal */}
      {selectedProperty && (
        <PropertyDetailModal
          property={selectedProperty}
          isOpen={isModalOpen}
          onClose={handleCloseModal}
          onSkipTrace={() => handleSkipTrace(parseInt(selectedProperty.id))}
          isSkipTraceInProgress={parseInt(selectedProperty.id) === tracingPropertyId}
        />
      )}

      {/* Create Tag Modal */}
      {isCreateTagModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/70 backdrop-blur-sm"
            onClick={() => setIsCreateTagModalOpen(false)}
          />
          {/* Modal */}
          <div className="relative bg-white dark:bg-surface-dark border border-gray-200 dark:border-border-dark rounded-xl shadow-2xl w-full max-w-md p-6 animate-in fade-in zoom-in duration-200">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-white">Create New Tag</h2>
              <button
                onClick={() => setIsCreateTagModalOpen(false)}
                className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors rounded-lg hover:bg-white/5"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <div className="space-y-4">
              {/* Tag Name */}
              <div>
                <label htmlFor="tagName" className="block text-sm font-medium text-gray-300 mb-2">
                  Tag Name
                </label>
                <input
                  id="tagName"
                  type="text"
                  value={newTagName}
                  onChange={(e) => setNewTagName(e.target.value)}
                  placeholder="e.g., Hot Lead, Review Later"
                  className="w-full px-4 py-2.5 bg-white/5 border border-border-dark rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors"
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && newTagName.trim()) {
                      handleCreateTag()
                    }
                  }}
                />
              </div>

              {/* Tag Color */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Tag Color
                </label>
                <div className="flex flex-wrap gap-2">
                  {[
                    '#3B82F6', // Blue
                    '#10B981', // Emerald
                    '#F59E0B', // Amber
                    '#EF4444', // Red
                    '#8B5CF6', // Purple
                    '#EC4899', // Pink
                    '#06B6D4', // Cyan
                    '#84CC16', // Lime
                  ].map((color) => (
                    <button
                      key={color}
                      type="button"
                      onClick={() => setNewTagColor(color)}
                      className={`w-8 h-8 rounded-full transition-all ${
                        newTagColor === color
                          ? 'ring-2 ring-white ring-offset-2 ring-offset-surface-dark scale-110'
                          : 'hover:scale-110'
                      }`}
                      style={{ backgroundColor: color }}
                      title={color}
                    />
                  ))}
                  <input
                    type="color"
                    value={newTagColor}
                    onChange={(e) => setNewTagColor(e.target.value)}
                    className="w-8 h-8 rounded-full overflow-hidden cursor-pointer"
                    title="Custom color"
                  />
                </div>
              </div>

              {/* Preview */}
              {(newTagName.trim() || newTagColor) && (
                <div className="pt-2">
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Preview
                  </label>
                  <span
                    className="inline-block px-3 py-1 rounded-md text-sm font-medium text-white"
                    style={{ backgroundColor: newTagColor }}
                  >
                    {newTagName.trim() || 'Tag Name'}
                  </span>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setIsCreateTagModalOpen(false)}
                className="flex-1 px-4 py-2.5 border border-border-dark rounded-lg text-gray-300 hover:text-white hover:bg-white/5 transition-colors font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateTag}
                disabled={!newTagName.trim()}
                className="flex-1 px-4 py-2.5 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                <span className="material-symbols-outlined text-[18px]">add</span>
                Create Tag
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
