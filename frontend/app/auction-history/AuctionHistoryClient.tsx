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
import { useFavorites } from '@/lib/hooks/useFavorites'
import { useUser } from '@/contexts/UserContext'
import { Property } from '@/lib/types/property'
import { supabase } from '@/lib/supabase/client'
import { getPropertyTags, addTagToProperty, removeTagFromProperty, getAllUserNotes, type UserTag } from '@/lib/api/client'

// NJ Counties list
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

const DATE_RANGE_OPTIONS = [
  { label: 'All Time', value: 'all' },
  { label: 'Last 30 Days', value: '30' },
  { label: 'Last 90 Days', value: '90' },
  { label: 'Last 6 Months', value: '180' },
  { label: 'Last Year', value: '365' },
]

interface AuctionHistoryClientProps {
  initialData: {
    properties: Property[]
    count: number
  }
}

export function AuctionHistoryClient({ initialData }: AuctionHistoryClientProps) {
  // Mobile menu state
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  // Sort orders for columns
  const [auctionDateOrder, setAuctionDateOrder] = useState<'desc' | 'asc' | null>(null)
  const [upsetOrder, setUpsetOrder] = useState<'desc' | 'asc' | null>(null)
  const [judgmentOrder, setJudgmentOrder] = useState<'desc' | 'asc' | null>(null)
  const [zestimateOrder, setZestimateOrder] = useState<'desc' | 'asc' | null>(null)
  const [spreadOrder, setSpreadOrder] = useState<'desc' | 'asc' | null>(null)

  const setColumnSort = (column: 'auctionDate' | 'upset' | 'judgment' | 'zestimate' | 'spread', order: 'desc' | 'asc' | null) => {
    setAuctionDateOrder(column === 'auctionDate' ? order : null)
    setUpsetOrder(column === 'upset' ? order : null)
    setJudgmentOrder(column === 'judgment' ? order : null)
    setZestimateOrder(column === 'zestimate' ? order : null)
    setSpreadOrder(column === 'spread' ? order : null)
  }

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
  const [dateRangeFilter, setDateRangeFilter] = useState<string>('all')
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
  const { isFavorited, toggleFavorite } = useFavorites()
  const { getOverride, saveOverride, getOverrideHistory, revertOverride } = usePropertyOverrides(userId)
  const [propertyTagsMap, setPropertyTagsMap] = useState<Record<number, UserTag[]>>({})
  const [propertyOverridesMap, setPropertyOverridesMap] = useState<Record<number, {
    approxUpsetOverride?: number
    approxJudgmentOverride?: number
    startingBidOverride?: number
    bidCapOverride?: number
    propertySoldOverride?: string | number
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
  const statusHistoryDropdownRef = useRef<HTMLDivElement>(null)
  const dateRangeDropdownRef = useRef<HTMLDivElement>(null)
  const tagsDropdownRef = useRef<HTMLDivElement>(null)
  const itemsPerPageDropdownRef = useRef<HTMLDivElement>(null)
  const priceRangeDropdownRef = useRef<HTMLDivElement>(null)
  const [isCountyDropdownOpen, setIsCountyDropdownOpen] = useState(false)
  const [isDayDropdownOpen, setIsDayDropdownOpen] = useState(false)
  const [isStatusDropdownOpen, setIsStatusDropdownOpen] = useState(false)
  const [isStatusHistoryDropdownOpen, setIsStatusHistoryDropdownOpen] = useState(false)
  const [isDateRangeDropdownOpen, setIsDateRangeDropdownOpen] = useState(false)
  const [isTagsDropdownOpen, setIsTagsDropdownOpen] = useState(false)
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
    setDateRangeFilter('all')
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

  // Use initial server-fetched data
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
    limit: 10000,
    initialData,
  })

  // AUCTION HISTORY: Filter for ONLY past auctions
  const rowProperties = useMemo(() => {
    const transformed = properties.map(p => {
      const propId = typeof p.id === 'number' ? p.id : Number(p.id)
      const overrides = propertyOverridesMap[propId]
      return transformPropertyToRow(p, overrides)
    })
    const searchLower = searchQuery.trim().toLowerCase()
    const today = new Date()
    today.setHours(0, 0, 0, 0)

    let filtered = transformed.filter(property => {
      // PAST AUCTIONS ONLY: Exclude today and future auctions
      const auctionDate = new Date(property.auctionDate)
      if (auctionDate >= today) {
        return false
      }

      // Date range filter
      if (dateRangeFilter !== 'all') {
        const daysBack = parseInt(dateRangeFilter)
        const cutoffDate = new Date(today)
        cutoffDate.setDate(cutoffDate.getDate() - daysBack)
        if (auctionDate < cutoffDate) {
          return false
        }
      }

      // Search query
      if (searchLower) {
        const searchableText = `${property.address} ${property.city} ${property.state} ${property.zip}`.toLowerCase()
        if (!searchableText.includes(searchLower)) {
          return false
        }
      }

      // County filter
      if (selectedCounties.length > 0 && property.county) {
        const countyLower = property.county.toLowerCase()
        const matchesCounty = selectedCounties.some(selectedCounty =>
          countyLower.includes(selectedCounty.toLowerCase())
        )
        if (!matchesCounty) {
          return false
        }
      }

      // Day of week filter
      if (selectedDaysOfWeek.length > 0) {
        if (!property.dayOfWeek || !selectedDaysOfWeek.includes(property.dayOfWeek)) {
          return false
        }
      }

      // Spread filter
      if (spreadFilter !== 'all') {
        const spreadThreshold = spreadFilter === '30plus' ? 30 : spreadFilter === '20plus' ? 20 : 10
        if (property.spread < spreadThreshold) {
          return false
        }
      }

      // Status filter
      if (selectedStatuses.length > 0 && property.status) {
        const propertyStatus = property.status.toLowerCase()
        if (propertyStatus.includes('/')) {
          const statusParts = propertyStatus.split('/').map(s => s.trim().toLowerCase())
          const normalizedSelected = selectedStatuses.map(s => s.toLowerCase())
          const matches = statusParts.some(part =>
            normalizedSelected.some(selected =>
              part.includes(selected) || selected.includes(part)
            )
          )
          if (!matches) {
            return false
          }
        } else {
          if (!selectedStatuses.some(selected =>
            propertyStatus === selected.toLowerCase() ||
            propertyStatus.includes(selected.toLowerCase())
          )) {
            return false
          }
        }
      }

      // Status History filter - check if property's status history badges match selected filters
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

      // Tag filter
      if (selectedTagId !== null) {
        const propId = typeof property.id === 'number' ? property.id : Number(property.id)
        const propTags = propertyTagsMap[propId] || []
        if (!propTags.some(tag => tag.id === selectedTagId)) {
          return false
        }
      }

      // Notes filter
      if (hasNotesOnly) {
        const propId = typeof property.id === 'number' ? property.id : Number(property.id)
        if (!propertiesWithNotes.has(propId)) {
          return false
        }
      }

      // Favorites filter
      if (favoritesOnly) {
        const propId = typeof property.id === 'number' ? property.id : Number(property.id)
        if (!isFavorited(propId)) {
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

      return true
    })

    // Client-side sorting for spread
    if (spreadOrder) {
      filtered.sort((a, b) => {
        return spreadOrder === 'desc' ? b.spread - a.spread : a.spread - b.spread
      })
    }

    return filtered
  }, [properties, searchQuery, selectedCounties, selectedDaysOfWeek, spreadFilter, selectedStatuses, selectedStatusHistory, selectedTagId, propertyTagsMap, propertiesWithNotes, hasNotesOnly, dateRangeFilter, spreadOrder, favoritesOnly, isFavorited, judgmentRangeEnabled, judgmentMin, judgmentMax, upsetRangeEnabled, upsetMin, upsetMax])

  // Paginated properties
  const paginatedProperties = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage
    const endIndex = startIndex + itemsPerPage
    return rowProperties.slice(startIndex, endIndex)
  }, [rowProperties, currentPage])

  // Calculate stats
  const stats = useMemo(() => {
    const avgSpread = rowProperties.length > 0
      ? rowProperties.reduce((sum, p) => sum + p.spread, 0) / rowProperties.length
      : 0

    const today = new Date()
    const past30Days = rowProperties.filter(p => {
      const auctionDate = new Date(p.auctionDate)
      const daysDiff = Math.floor((today.getTime() - auctionDate.getTime()) / (1000 * 60 * 60 * 24))
      return daysDiff <= 30
    }).length

    return {
      total: count,
      showing: rowProperties.length,
      avgSpread: avgSpread.toFixed(1),
      soldPast30Days: past30Days,
    }
  }, [rowProperties, count])

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1)
  }, [searchQuery, selectedCounties, selectedDaysOfWeek, spreadFilter, selectedStatuses, selectedTagId, hasNotesOnly, dateRangeFilter])

  // Fetch property tags
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
  }, [userId])

  // Fetch property overrides
  useEffect(() => {
    if (!userId || properties.length === 0) return

    const fetchAllPropertyOverrides = async () => {
      const overridesMap: typeof propertyOverridesMap = {}
      for (const property of properties) {
        try {
          const propId = typeof property.id === 'number' ? property.id : Number(property.id)
          const overrides = await Promise.all([
            getOverride(propId, 'starting_bid'),
            getOverride(propId, 'bid_cap'),
            getOverride(propId, 'approx_upset'),
            getOverride(propId, 'judgment_amount'),
            getOverride(propId, 'property_sold'),
          ])
          const [startingBidOverride, bidCapOverride, approxUpsetOverride, approxJudgmentOverride, propertySoldOverride] = overrides
          if (startingBidOverride || bidCapOverride || approxUpsetOverride || approxJudgmentOverride || propertySoldOverride) {
            overridesMap[propId] = {
              startingBidOverride: startingBidOverride?.new_value !== undefined ? Number(startingBidOverride.new_value) : undefined,
              bidCapOverride: bidCapOverride?.new_value !== undefined ? Number(bidCapOverride.new_value) : undefined,
              approxUpsetOverride: approxUpsetOverride?.new_value !== undefined ? Number(approxUpsetOverride.new_value) : undefined,
              approxJudgmentOverride: approxJudgmentOverride?.new_value !== undefined ? Number(approxJudgmentOverride.new_value) : undefined,
              propertySoldOverride: propertySoldOverride?.new_value ?? undefined,
            }
          }
        } catch (error) {
          console.error(`Error fetching overrides for property ${property.id}:`, error)
        }
      }
      setPropertyOverridesMap(overridesMap)
    }

    fetchAllPropertyOverrides()
  }, [userId])

  // Fetch user notes
  useEffect(() => {
    if (!userId || properties.length === 0) return

    const fetchAllUserNotes = async () => {
      try {
        const notes = await getAllUserNotes(userId, 1000)
        const propIdsWithNotes = new Set(notes.map(note => note.property_id))
        setPropertiesWithNotes(propIdsWithNotes)
      } catch (error) {
        console.error('Error fetching user notes:', error)
      }
    }

    fetchAllUserNotes()
  }, [userId])

  // Handler to add tag to property
  const handleAddTagToProperty = async (propertyId: number, tagId: number) => {
    if (!userId) return
    try {
      await addTagToProperty(propertyId, tagId, userId)
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

  // Handle page change
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    if (scrollableContainerRef.current) {
      scrollableContainerRef.current.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }

  // Scroll to top when page changes
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
    dateRangeFilter !== 'all' ||
    favoritesOnly ||
    (judgmentRangeEnabled && (judgmentMin || judgmentMax)) ||
    (upsetRangeEnabled && (upsetMin || upsetMax))

  // CSV Export
  const exportToCSV = async (propertiesToExport: ReturnType<typeof transformPropertyToRow>[]) => {
    const { normalizeStatus, normalizeStatusHistory } = await import('@/lib/utils/statusNormalizer')

    const headers = ['Address', 'City', 'State', 'ZIP', 'County', 'Auction Date', 'Day of Week', 'Status', 'Status History', 'Opening Bid', 'Approx Upset', 'Approx Judgment', 'Zestimate', 'Est. ARV', 'Spread %', 'Beds', 'Baths', 'Sqft', 'Zillow Link']

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
        p.address, p.city, p.state, p.zip, p.county || '',
        p.auctionDate, p.dayOfWeek || '', normalizedStatus, historyString,
        p.openingBid.toString(), p.approxUpset?.toString() || '',
        p.approxJudgment?.toString() || '', p.zestimate?.toString() || '',
        p.estimatedARV.toString(), p.spread.toFixed(1),
        p.beds?.toString() || '', p.baths?.toString() || '',
        p.sqft?.toString() || '', p.zillowUrl || ''
      ]
    }))

    const csvContent = [headers.join(','), ...rows.map(row => row.map(cell => `"${cell}"`).join(','))].join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `auction_history_${new Date().toISOString().slice(0, 10)}.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    setIsExportDropdownOpen(false)
  }

  // Property update handler
  const handlePropertyUpdate = async (propertyId: number) => {
    await updateProperty(propertyId)
    if (selectedProperty && parseInt(selectedProperty.id) === propertyId) {
      const result = await supabase.from('foreclosure_listings').select('*').eq('id', propertyId).single()
      if (result.data) {
        setSelectedProperty(transformPropertyToRow(result.data))
      }
    }
  }

  // Skip trace hook
  const { traceProperty, state: skipTraceState } = useSkipTrace(undefined, handlePropertyUpdate)
  const [tracingPropertyId, setTracingPropertyId] = useState<number | null>(null)

  const handleSkipTrace = async (propertyId: number) => {
    setTracingPropertyId(propertyId)
    const result = await traceProperty(propertyId)
    if (!result.success) {
      setTracingPropertyId(null)
    }
    return result
  }

  useEffect(() => {
    if (!skipTraceState.isTracing && tracingPropertyId !== null) {
      setTracingPropertyId(null)
    }
  }, [skipTraceState.isTracing, tracingPropertyId])

  // Close dropdowns on outside click
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
      if (dateRangeDropdownRef.current && !dateRangeDropdownRef.current.contains(event.target as Node)) {
        setIsDateRangeDropdownOpen(false)
      }
      if (tagsDropdownRef.current && !tagsDropdownRef.current.contains(event.target as Node)) {
        setIsTagsDropdownOpen(false)
      }
      if (itemsPerPageDropdownRef.current && !itemsPerPageDropdownRef.current.contains(event.target as Node)) {
        setIsItemsPerPageDropdownOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

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

        <div ref={scrollableContainerRef} className="flex-1 overflow-y-auto p-3 lg:p-8 scroll-smooth">
          <div className="max-w-[1600px] mx-auto flex flex-col gap-3 lg:gap-6">
            {/* Page Header */}
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Auction History</h1>
              </div>
            </div>

            {/* Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <StatsCard
                title="Total Properties"
                value={`${stats.showing.toLocaleString()} / ${stats.total.toLocaleString()}`}
                change={isLoading ? '...' : 'Showing / Total'}
                changeType="positive"
                progress={100}
                icon="history"
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
                title="Sold (30 Days)"
                value={stats.soldPast30Days.toString()}
                change={isLoading ? '...' : 'Past 30 days'}
                changeType="neutral"
                progress={85}
                icon="gavel"
                color="orange"
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
                {/* Clear Filters */}
                {hasActiveFilters && (
                  <button
                    onClick={clearAllFilters}
                    className="bg-red-500/20 border border-red-500/50 text-red-400 hover:bg-red-500/30 px-2 py-1.5 md:px-3 rounded-lg text-xs md:text-sm font-medium flex items-center gap-0.5 md:gap-1 transition-colors shrink-0 snap-start whitespace-nowrap"
                  >
                    <span className="material-symbols-outlined text-[16px] md:text-[18px]">filter_alt_off</span>
                    <span>Clear All</span>
                  </button>
                )}

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
                          <h3 className="text-gray-900 dark:text-white font-semibold">Select Counties</h3>
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

                {/* Day Filter */}
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
                      <div
                        className="fixed inset-0 bg-black/60 z-40 md:hidden"
                        onClick={() => setIsDayDropdownOpen(false)}
                      />
                      <div className="fixed bottom-0 left-0 right-0 md:absolute md:top-full md:left-0 md:right-auto md:bottom-auto md:mt-2 bg-white dark:bg-surface-dark border border-gray-200 dark:border-border-dark md:rounded-lg rounded-t-2xl shadow-xl z-50 md:w-48 animate-in slide-in-from-bottom md:animate-in fade-in zoom-in duration-200">
                        <div className="sticky top-0 bg-white dark:bg-surface-dark border-b border-gray-200 dark:border-border-dark p-4 flex items-center justify-between md:hidden">
                          <h3 className="text-gray-900 dark:text-white font-semibold">Select Days</h3>
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
                              className={`px-3 py-2 md:py-1.5 rounded text-xs font-medium text-left transition-colors flex items-center gap-2 ${
                                selectedDaysOfWeek.includes(day)
                                  ? 'bg-primary text-white'
                                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5'
                              }`}
                            >
                              <span className="material-symbols-outlined text-[14px]">
                                {selectedDaysOfWeek.includes(day) ? 'check_box' : 'check_box_outline_blank'}
                              </span>
                              {day}
                            </button>
                          ))}
                        </div>
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

              {/* Date Range Filter */}
              <div className="relative shrink-0 snap-start" ref={dateRangeDropdownRef}>
                <button
                  onClick={() => setIsDateRangeDropdownOpen(!isDateRangeDropdownOpen)}
                  className={`bg-white dark:bg-surface-dark border ${dateRangeFilter !== 'all' ? 'border-primary' : 'border-gray-300 dark:border-border-dark'} hover:border-gray-400 dark:hover:border-gray-500 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white px-2 py-1.5 md:px-3 rounded-lg text-xs md:text-sm font-medium flex items-center gap-0.5 md:gap-1.5 transition-colors whitespace-nowrap min-w-[80px] md:min-w-[100px]`}
                >
                  <span className="material-symbols-outlined text-[16px] md:text-[18px] shrink-0">calendar_month</span>
                  <span className="inline">Date Range</span>
                  <span className="material-symbols-outlined text-[14px] md:text-[16px] transition-transform shrink-0 ml-auto">{isDateRangeDropdownOpen ? 'expand_less' : 'expand_more'}</span>
                </button>
                {isDateRangeDropdownOpen && (
                  <div className="absolute top-full left-0 mt-2 w-48 bg-white dark:bg-surface-dark border border-gray-200 dark:border-border-dark rounded-lg shadow-xl z-50">
                    <div className="p-2">
                      {DATE_RANGE_OPTIONS.map(option => (
                        <button
                          key={option.value}
                          onClick={() => {
                            setDateRangeFilter(option.value)
                            setIsDateRangeDropdownOpen(false)
                          }}
                          className={`w-full text-left px-3 py-2 text-sm rounded-lg transition-colors ${
                            dateRangeFilter === option.value
                              ? 'bg-primary/20 text-primary dark:bg-primary/20 dark:text-primary'
                              : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5'
                          }`}
                        >
                          {option.label}
                        </button>
                      ))}
                    </div>
                  </div>
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
                  <span className="material-symbols-outlined text-[16px] md:text-[18px] shrink-0">fact_check</span>
                  <span className="inline">Status</span>
                  <span className={`text-primary text-[10px] md:text-xs ${selectedStatuses.length > 0 ? 'opacity-100' : 'opacity-0'} transition-opacity`}>( {selectedStatuses.length} )</span>
                  <span className="material-symbols-outlined text-[14px] md:text-[16px] transition-transform shrink-0 ml-auto">{isStatusDropdownOpen ? 'expand_less' : 'expand_more'}</span>
                </button>
                {isStatusDropdownOpen && (
                  <>
                    <div
                      className="fixed inset-0 bg-black/60 z-40 md:hidden"
                      onClick={() => setIsStatusDropdownOpen(false)}
                    />
                    <div className="fixed bottom-0 left-0 right-0 md:absolute md:top-full md:left-0 md:right-auto md:bottom-auto md:mt-2 bg-white dark:bg-surface-dark border border-gray-200 dark:border-border-dark md:rounded-lg rounded-t-2xl shadow-xl z-50 md:w-56 md:max-h-80 max-h-[60vh] overflow-y-auto animate-in slide-in-from-bottom md:animate-in fade-in zoom-in duration-200">
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
                            className={`px-3 py-2 md:py-1.5 rounded text-xs font-medium text-left transition-colors flex items-center gap-2 ${
                              selectedStatuses.includes(status)
                                ? 'bg-primary text-white'
                                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5'
                            }`}
                          >
                            <span className="material-symbols-outlined text-[14px]">
                              {selectedStatuses.includes(status) ? 'check_box' : 'check_box_outline_blank'}
                            </span>
                            {status}
                          </button>
                        ))}
                      </div>
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
                    <div
                      className="fixed inset-0 bg-black/60 z-40 md:hidden"
                      onClick={() => setIsStatusHistoryDropdownOpen(false)}
                    />
                    <div className="fixed bottom-0 left-0 right-0 md:absolute md:top-full md:left-0 md:right-auto md:bottom-auto md:mt-2 bg-white dark:bg-surface-dark border border-gray-200 dark:border-border-dark md:rounded-lg rounded-t-2xl shadow-xl z-50 md:w-56 md:max-h-80 max-h-[60vh] overflow-y-auto animate-in slide-in-from-bottom md:animate-in fade-in zoom-in duration-200">
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
                            className={`px-3 py-2 md:py-1.5 rounded text-xs font-medium text-left transition-colors flex items-center gap-2 ${
                              selectedStatusHistory.includes(status)
                                ? 'bg-primary text-white'
                                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5'
                            }`}
                          >
                            <span className="material-symbols-outlined text-[14px]">
                              {selectedStatusHistory.includes(status) ? 'check_box' : 'check_box_outline_blank'}
                            </span>
                            {status}
                          </button>
                        ))}
                      </div>
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
                  <span className="material-symbols-outlined text-[16px] md:text-[18px] shrink-0">label</span>
                  <span className="inline">Tags</span>
                  <span className={`material-symbols-outlined text-[14px] md:text-[16px] transition-transform ${isTagsDropdownOpen ? 'rotate-180' : ''}`}>expand_more</span>
                </button>
                {isTagsDropdownOpen && (
                  <div className="absolute top-full left-0 mt-2 w-56 max-h-64 overflow-y-auto bg-white dark:bg-surface-dark border border-gray-200 dark:border-border-dark rounded-lg shadow-xl z-50">
                    <div className="p-2">
                      <button
                        onClick={() => {
                          setSelectedTagId(null)
                          setIsTagsDropdownOpen(false)
                        }}
                        className={`w-full text-left px-3 py-2 text-sm rounded-lg transition-colors mb-1 ${
                          selectedTagId === null
                            ? 'bg-primary/20 text-primary dark:bg-primary/20 dark:text-primary'
                            : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5'
                        }`}
                      >
                        All Tags
                      </button>
                      {tags.map(tag => (
                        <button
                          key={tag.id}
                          onClick={() => {
                            setSelectedTagId(tag.id)
                            setIsTagsDropdownOpen(false)
                          }}
                          className={`w-full flex items-center gap-2 px-3 py-2 text-sm rounded-lg transition-colors ${
                            selectedTagId === tag.id
                              ? 'bg-primary/20 text-primary dark:bg-primary/20 dark:text-primary'
                              : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5'
                          }`}
                        >
                          <span className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: tag.color }} />
                          <span className="truncate">{tag.name}</span>
                        </button>
                      ))}
                      <div className="border-t border-gray-200 dark:border-border-dark mt-2 pt-2">
                        <button
                          onClick={() => {
                            setIsCreateTagModalOpen(true)
                            setIsTagsDropdownOpen(false)
                          }}
                          className="w-full flex items-center gap-2 px-3 py-2 text-sm text-primary hover:bg-gray-100 dark:hover:bg-white/5 rounded-lg"
                        >
                          <span className="material-symbols-outlined text-[18px]">add</span>
                          Create Tag
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Notes Toggle */}
              <button
                onClick={() => setHasNotesOnly(!hasNotesOnly)}
                className={`shrink-0 bg-white dark:bg-surface-dark border ${hasNotesOnly ? 'border-primary' : 'border-gray-300 dark:border-border-dark'} hover:border-gray-400 dark:hover:border-gray-500 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white px-2 py-1.5 md:px-3 rounded-lg text-xs md:text-sm font-medium flex items-center gap-0.5 md:gap-1.5 transition-colors whitespace-nowrap min-w-[75px]`}
              >
                <span className="material-symbols-outlined text-[16px] md:text-[18px] shrink-0">edit_note</span>
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
                <span>Favorites</span>
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

              {/* Export Dropdown */}
              <div className="relative shrink-0 snap-start ml-auto" ref={exportDropdownRef}>
                <button
                  onClick={async () => {
                    if (isExportDropdownOpen) {
                      await exportToCSV(rowProperties)
                    } else {
                      setIsExportDropdownOpen(true)
                    }
                  }}
                  className="bg-white dark:bg-surface-dark border border-gray-300 dark:border-border-dark hover:border-gray-400 dark:hover:border-gray-500 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white px-2 py-1.5 md:px-3 rounded-lg text-xs md:text-sm font-medium flex items-center gap-0.5 md:gap-1.5 transition-colors whitespace-nowrap"
                >
                  <span className="material-symbols-outlined text-[16px] md:text-[18px]">download</span>
                  <span className="inline">Export</span>
                </button>
              </div>
            </div>
          </div>

          {/* Loading State */}
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
              </div>
            ) : rowProperties.length === 0 ? (
              <div className="bg-white dark:bg-surface-dark rounded-xl border border-gray-200 dark:border-border-dark p-12 text-center">
                <span className="material-symbols-outlined text-6xl text-gray-400 dark:text-gray-600 mb-4">history</span>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">No Auction History Found</h3>
                <p className="text-gray-500 dark:text-gray-400 text-sm max-w-md mx-auto">
                  {hasActiveFilters
                    ? 'Try adjusting your filters to see more results.'
                    : 'Properties will appear here once their auction dates have passed.'}
                </p>
              </div>
            ) : (
              <>
                {/* Property Table */}
                <div className="bg-white dark:bg-surface-dark rounded-xl border border-gray-200 dark:border-border-dark overflow-hidden shadow-xl">
                  <div className="overflow-auto max-h-[800px] overflow-x-auto px-4 md:px-0">
                    <table className="w-full table-fixed text-left border-collapse">
                    <thead className="sticky top-0 z-20">
                      <tr className="bg-gradient-to-r from-gray-100 to-gray-200 dark:from-surface-dark dark:to-[#1a1f2e] border-b-2 border-gray-300 dark:border-border-dark text-xs tracking-wider">
                          <th className="p-4 font-semibold text-gray-700 dark:text-gray-300 text-center uppercase md:sticky md:left-0 md:z-30 md:bg-gradient-to-r md:from-gray-100 md:to-gray-200 dark:md:from-surface-dark dark:md:to-[#1a1f2e] md:border-r md:border-gray-300 dark:md:border-border-dark" style={{ width: '350px' }}>Property</th>
                          <th className="p-4 font-semibold text-gray-700 dark:text-gray-300 text-center uppercase" style={{ width: '70px' }}>
                            <span className="material-symbols-outlined text-[20px]">star</span>
                          </th>
                          <th className="p-4 font-semibold text-gray-700 dark:text-gray-300 text-center uppercase" style={{ width: '120px' }}>County</th>
                          <th className="p-4 font-semibold text-gray-700 dark:text-gray-300 text-center uppercase" style={{ width: '130px' }}>
                            <button
                              onClick={() => setColumnSort('auctionDate', cycleSort(auctionDateOrder))}
                              className="flex items-center justify-center gap-2 hover:text-gray-900 dark:hover:text-white hover:bg-gray-300 dark:hover:bg-white/5 px-2 py-1 rounded transition-colors cursor-pointer w-full"
                            >
                              <span className="uppercase">Auction Date</span>
                              <span className="material-symbols-outlined text-[14px]">
                                {auctionDateOrder === 'desc' ? 'arrow_downward' : auctionDateOrder === 'asc' ? 'arrow_upward' : 'sort'}
                              </span>
                            </button>
                          </th>
                          <th className="p-4 font-semibold text-gray-700 dark:text-gray-300 text-center uppercase" style={{ width: '90px' }}>Zillow</th>
                          <th className="p-4 font-semibold text-gray-700 dark:text-gray-300 text-center uppercase" style={{ width: '120px' }}>
                            <button
                              onClick={() => setColumnSort('upset', cycleSort(upsetOrder))}
                              className="flex items-center justify-center gap-2 hover:text-gray-900 dark:hover:text-white hover:bg-gray-300 dark:hover:bg-white/5 px-2 py-1 rounded transition-colors cursor-pointer w-full"
                            >
                              <span className="uppercase">Approx Upset</span>
                              <span className="material-symbols-outlined text-[14px]">
                                {upsetOrder === 'desc' ? 'arrow_downward' : upsetOrder === 'asc' ? 'arrow_upward' : 'sort'}
                              </span>
                            </button>
                          </th>
                          <th className="p-4 font-semibold text-gray-700 dark:text-gray-300 text-center uppercase" style={{ width: '140px' }}>
                            <button
                              onClick={() => setColumnSort('judgment', cycleSort(judgmentOrder))}
                              className="flex items-center justify-center gap-2 hover:text-gray-900 dark:hover:text-white hover:bg-gray-300 dark:hover:bg-white/5 px-2 py-1 rounded transition-colors cursor-pointer w-full"
                            >
                              <span className="uppercase">Approx Judgment</span>
                              <span className="material-symbols-outlined text-[14px]">
                                {judgmentOrder === 'desc' ? 'arrow_downward' : judgmentOrder === 'asc' ? 'arrow_upward' : 'sort'}
                              </span>
                            </button>
                          </th>
                          <th className="p-4 font-semibold text-gray-700 dark:text-gray-300 text-center uppercase" style={{ width: '110px' }}>
                            <button
                              onClick={() => setColumnSort('zestimate', cycleSort(zestimateOrder))}
                              className="flex items-center justify-center gap-2 hover:text-gray-900 dark:hover:text-white hover:bg-gray-300 dark:hover:bg-white/5 px-2 py-1 rounded transition-colors cursor-pointer w-full"
                            >
                              <span className="uppercase">Zestimate</span>
                              <span className="material-symbols-outlined text-[14px]">
                                {zestimateOrder === 'desc' ? 'arrow_downward' : zestimateOrder === 'asc' ? 'arrow_upward' : 'sort'}
                              </span>
                            </button>
                          </th>
                          <th className="p-4 font-semibold text-gray-700 dark:text-gray-300 text-center uppercase" style={{ width: '100px' }}>
                            <button
                              onClick={() => setColumnSort('spread', cycleSort(spreadOrder))}
                              className="flex items-center justify-center gap-2 hover:text-gray-900 dark:hover:text-white hover:bg-gray-300 dark:hover:bg-white/5 px-2 py-1 rounded transition-colors cursor-pointer w-full"
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
                      <tbody className="divide-y divide-gray-200 dark:divide-border-dark">
                        {paginatedProperties.map((property) => {
                          const propId = Number(property.id)
                          const overrides = propertyOverridesMap[propId]
                          return (
                            <PropertyRow
                              key={property.id}
                              property={property}
                              onOpenModal={handleOpenModal}
                              onAddTag={handleAddTagToProperty}
                              onRemoveTag={handleRemoveTagFromProperty}
                              tags={propertyTagsMap[propId] || []}
                              allTags={tags}
                              onSkipTrace={handleSkipTrace}
                              skipTraceInProgress={tracingPropertyId === propId && skipTraceState.isTracing}
                              onSaveOverride={handleSaveOverride}
                              onGetOverrideHistory={handleGetOverrideHistory}
                              onRevertOverride={handleRevertOverride}
                              startingBidOverride={overrides?.startingBidOverride}
                              bidCapOverride={overrides?.bidCapOverride}
                              propertySoldOverride={overrides?.propertySoldOverride}
                              isFavorited={isFavorited(propId)}
                              onToggleFavorite={toggleFavorite}
                            />
                          )
                        })}
                      </tbody>
                      </table>
                  </div>
                </div>

                {/* Pagination */}
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 sm:gap-6 pt-4">
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Showing {(currentPage - 1) * itemsPerPage + 1} to {Math.min(currentPage * itemsPerPage, rowProperties.length)} of {rowProperties.length} properties
                  </p>

                  {/* Page controls with items per page dropdown */}
                  <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 w-full sm:w-auto">
                    {/* Page buttons */}
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handlePageChange(Math.max(1, currentPage - 1))}
                        disabled={currentPage === 1}
                        className="px-2 sm:px-3 py-2 bg-white dark:bg-surface-dark border border-gray-200 dark:border-border-dark rounded-lg text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        <span className="material-symbols-outlined text-[18px] md:hidden">chevron_left</span>
                        <span className="hidden md:inline">Previous</span>
                      </button>

                      <span className="text-sm text-gray-500 dark:text-gray-400 px-2">
                        {currentPage} / {Math.ceil(rowProperties.length / itemsPerPage)}
                      </span>

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
                        <div className="absolute bottom-full left-0 sm:top-full sm:bottom-auto sm:left-auto sm:right-0 mb-2 sm:mb-0 sm:mt-2 w-32 bg-white dark:bg-surface-dark border border-gray-200 dark:border-border-dark rounded-lg shadow-xl z-50">
                          <div className="p-2">
                            {ITEMS_PER_PAGE_OPTIONS.map(option => (
                              <button
                                key={option}
                                onClick={() => {
                                  setItemsPerPage(option)
                                  setIsItemsPerPageDropdownOpen(false)
                                  setCurrentPage(1)
                                }}
                                className={`w-full text-left px-3 py-2 text-sm rounded-lg transition-colors ${
                                  itemsPerPage === option
                                    ? 'bg-primary/20 text-primary dark:bg-primary/20 dark:text-primary'
                                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5'
                                }`}
                              >
                                {option}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </>
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
        />
      )}

      {/* Create Tag Modal */}
      {isCreateTagModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-surface-dark border border-gray-200 dark:border-border-dark rounded-xl p-6 w-96">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Create New Tag</h3>
            <input
              type="text"
              value={newTagName}
              onChange={(e) => setNewTagName(e.target.value)}
              placeholder="Tag name"
              className="w-full px-4 py-2 text-gray-900 dark:text-white bg-gray-50 dark:bg-background-dark border border-gray-300 dark:border-border-dark rounded-lg mb-4 focus:outline-none focus:border-primary dark:focus:border-primary"
            />
            <div className="flex gap-2 mb-4">
              {['#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6'].map(color => (
                <button
                  key={color}
                  onClick={() => setNewTagColor(color)}
                  className={`w-8 h-8 rounded-full border-2 transition-all ${newTagColor === color ? 'border-gray-900 dark:border-white scale-110' : 'border-transparent'}`}
                  style={{ backgroundColor: color }}
                />
              ))}
            </div>
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setIsCreateTagModalOpen(false)}
                className="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateTag}
                className="px-4 py-2 text-sm font-medium text-white bg-primary hover:bg-primary/90 rounded-lg transition-colors"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
