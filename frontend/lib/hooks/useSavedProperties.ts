'use client'

import { useState, useCallback, useEffect } from 'react'
import { useUser } from '@/contexts/UserContext'
import { getSavedProperties, saveProperty, unsaveProperty } from '@/lib/api/client'
import type { SavedProperty } from '@/lib/types/property'

export function useSavedProperties() {
  const { userId } = useUser()
  const [savedProperties, setSavedProperties] = useState<SavedProperty[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load saved properties for the current user
  const loadSavedProperties = useCallback(async () => {
    if (!userId) return

    setLoading(true)
    setError(null)
    try {
      const result = await getSavedProperties(userId)
      setSavedProperties(result.saved_properties || [])
    } catch (err: any) {
      setError(err.message || 'Failed to load saved properties')
      console.error('Error loading saved properties:', err)
    } finally {
      setLoading(false)
    }
  }, [userId])

  // Check if a property is saved
  const isPropertySaved = useCallback((propertyId: number): boolean => {
    return savedProperties.some(sp => sp.property_id === propertyId)
  }, [savedProperties])

  // Get the saved ID for a property (needed to unsave)
  const getSavedId = useCallback((propertyId: number): number | null => {
    const saved = savedProperties.find(sp => sp.property_id === propertyId)
    return saved?.id || null
  }, [savedProperties])

  // Save a property - optimistic update
  const savePropertyToList = useCallback(async (propertyId: number) => {
    if (!userId) {
      throw new Error('User not authenticated')
    }

    // Check if already saved
    if (isPropertySaved(propertyId)) {
      return { alreadySaved: true }
    }

    // Optimistic: create a temporary saved property object
    const tempSaved: SavedProperty = {
      id: Date.now(), // temporary ID
      user_id: userId,
      property_id: propertyId,
      kanban_stage: 'researching',
      saved_at: new Date().toISOString(),
      stage_updated_at: new Date().toISOString(),
      foreclosure_listings: undefined, // Will be populated on reload
    }

    // Update UI immediately
    setSavedProperties(prev => [...prev, tempSaved])

    try {
      // Make API call in background
      const result = await saveProperty(userId, propertyId)
      // Replace temp with real data
      setSavedProperties(prev => prev.map(sp => sp.id === tempSaved.id ? result : sp))
      return { success: true }
    } catch (err: any) {
      // Revert on error
      console.error('Error saving property:', err)
      setSavedProperties(prev => prev.filter(sp => sp.id !== tempSaved.id))
      throw err
    }
  }, [userId, isPropertySaved])

  // Unsave a property - optimistic update
  const unsavePropertyFromList = useCallback(async (propertyId: number) => {
    if (!userId) {
      throw new Error('User not authenticated')
    }

    const saved = savedProperties.find(sp => sp.property_id === propertyId)
    if (!saved) {
      return { notSaved: true }
    }

    // Optimistic: remove from UI immediately
    setSavedProperties(prev => prev.filter(sp => sp.property_id !== propertyId))

    try {
      // Make API call in background
      await unsaveProperty(userId, saved.id)
      return { success: true }
    } catch (err: any) {
      // Revert on error
      console.error('Error unsaving property:', err)
      setSavedProperties(prev => [...prev, saved])
      throw err
    }
  }, [userId, savedProperties])

  // Toggle save/unsave
  const toggleSaved = useCallback(async (propertyId: number) => {
    if (isPropertySaved(propertyId)) {
      return await unsavePropertyFromList(propertyId)
    } else {
      return await savePropertyToList(propertyId)
    }
  }, [isPropertySaved, unsavePropertyFromList, savePropertyToList])

  // Load saved properties on mount
  useEffect(() => {
    loadSavedProperties()
  }, [loadSavedProperties])

  return {
    savedProperties,
    loading,
    savedLoading: false, // Always false since we use optimistic updates
    error,
    isPropertySaved,
    savePropertyToList,
    unsavePropertyFromList,
    toggleSaved,
    reload: loadSavedProperties
  }
}
