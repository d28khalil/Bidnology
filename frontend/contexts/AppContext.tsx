'use client'

import { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import type { Property, PropertyFilters, Alert, SavedProperty, KanbanStage } from '@/lib/types/property'

interface AppContextValue {
  // Properties state
  properties: Property[]
  setProperties: (properties: Property[]) => void
  filteredProperties: Property[]
  setFilteredProperties: (properties: Property[]) => void

  // Filters
  filters: PropertyFilters
  setFilters: (filters: PropertyFilters) => void
  updateFilter: <K extends keyof PropertyFilters>(key: K, value: PropertyFilters[K]) => void

  // Loading states
  isLoading: boolean
  setIsLoading: (loading: boolean) => void

  // Alerts
  alerts: Alert[]
  setAlerts: (alerts: Alert[]) => void
  unreadAlertCount: number

  // Saved properties (for kanban)
  savedProperties: SavedProperty[]
  setSavedProperties: (saved: SavedProperty[]) => void

  // UI state
  selectedPropertyId: number | null
  setSelectedPropertyId: (id: number | null) => void
}

const AppContext = createContext<AppContextValue | undefined>(undefined)

export function AppProvider({ children }: { children: ReactNode }) {
  // Properties state
  const [properties, setProperties] = useState<Property[]>([])
  const [filteredProperties, setFilteredProperties] = useState<Property[]>([])

  // Saved properties (for kanban)
  const [savedProperties, setSavedProperties] = useState<SavedProperty[]>([])

  // Filters
  const [filters, setFilters] = useState<PropertyFilters>({})

  // Loading states
  const [isLoading, setIsLoading] = useState(false)

  // Alerts
  const [alerts, setAlerts] = useState<Alert[]>([])
  const unreadAlertCount = alerts.filter((a) => !a.is_read).length

  // UI state
  const [selectedPropertyId, setSelectedPropertyId] = useState<number | null>(null)

  // Update a single filter
  const updateFilter = useCallback(<K extends keyof PropertyFilters>(
    key: K,
    value: PropertyFilters[K]
  ) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
  }, [])

  return (
    <AppContext.Provider
      value={{
        // Properties
        properties,
        setProperties,
        filteredProperties,
        setFilteredProperties,

        // Filters
        filters,
        setFilters,
        updateFilter,

        // Loading
        isLoading,
        setIsLoading,

        // Alerts
        alerts,
        setAlerts,
        unreadAlertCount,

        // Saved properties
        savedProperties,
        setSavedProperties,

        // UI state
        selectedPropertyId,
        setSelectedPropertyId,
      }}
    >
      {children}
    </AppContext.Provider>
  )
}

export function useApp() {
  const context = useContext(AppContext)
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider')
  }
  return context
}
