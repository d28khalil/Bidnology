'use client'

import { useState, useCallback, useEffect } from 'react'
import { useUser } from '@/contexts/UserContext'
import { getUserFavorites, addFavorite, removeFavorite } from '@/lib/api/client'

export function useFavorites() {
  const { userId } = useUser()
  const [favoritePropertyIds, setFavoritePropertyIds] = useState<Set<number>>(new Set())
  const [loading, setLoading] = useState(false)

  // Load favorites for the current user
  const loadFavorites = useCallback(async () => {
    if (!userId) return

    setLoading(true)
    try {
      const favorites = await getUserFavorites(userId)
      setFavoritePropertyIds(new Set(favorites))
    } catch (err: any) {
      console.error('Error loading favorites:', err)
    } finally {
      setLoading(false)
    }
  }, [userId])

  // Check if a property is favorited
  const isFavorited = useCallback((propertyId: number): boolean => {
    return favoritePropertyIds.has(propertyId)
  }, [favoritePropertyIds])

  // Add to favorites - optimistic update
  const addToFavorites = useCallback(async (propertyId: number) => {
    if (!userId) {
      throw new Error('User not authenticated')
    }

    // Optimistic: add to UI immediately
    setFavoritePropertyIds(prev => new Set(prev).add(propertyId))

    try {
      await addFavorite(userId, propertyId)
    } catch (err: any) {
      // Revert on error
      console.error('Error adding favorite:', err)
      setFavoritePropertyIds(prev => {
        const newSet = new Set(prev)
        newSet.delete(propertyId)
        return newSet
      })
      throw err
    }
  }, [userId])

  // Remove from favorites - optimistic update
  const removeFromFavorites = useCallback(async (propertyId: number) => {
    if (!userId) {
      throw new Error('User not authenticated')
    }

    // Optimistic: remove from UI immediately
    setFavoritePropertyIds(prev => {
      const newSet = new Set(prev)
      newSet.delete(propertyId)
      return newSet
    })

    try {
      await removeFavorite(userId, propertyId)
    } catch (err: any) {
      // Revert on error
      console.error('Error removing favorite:', err)
      setFavoritePropertyIds(prev => new Set(prev).add(propertyId))
      throw err
    }
  }, [userId])

  // Toggle favorite/unfavorite
  const toggleFavorite = useCallback(async (propertyId: number) => {
    if (isFavorited(propertyId)) {
      await removeFromFavorites(propertyId)
    } else {
      await addToFavorites(propertyId)
    }
  }, [isFavorited, addToFavorites, removeFromFavorites])

  // Load favorites on mount
  useEffect(() => {
    loadFavorites()
  }, [loadFavorites])

  return {
    favoritePropertyIds,
    loading,
    isFavorited,
    addToFavorites,
    removeFromFavorites,
    toggleFavorite,
    reload: loadFavorites
  }
}
