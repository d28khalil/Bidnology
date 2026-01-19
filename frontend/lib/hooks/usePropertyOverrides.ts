'use client'

import { useCallback } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://app.bidnology.com'

type OverrideFieldName = 'approx_upset' | 'judgment_amount' | 'starting_bid' | 'bid_cap' | 'property_sold'

interface OverrideValue {
  id: number
  property_id: number
  field_name: OverrideFieldName
  original_value: number | null
  new_value: number | string  // Can be number (price) or string (date timestamp)
  previous_spread: number | null
  notes: string | null
  created_at: string
}

export function usePropertyOverrides(userId: string | null) {
  // Get all overrides for a property
  const getPropertyOverrides = useCallback(async (propertyId: number) => {
    if (!userId) return null
    try {
      const response = await fetch(
        `${API_URL}/api/property-overrides/property/${propertyId}?user_id=${encodeURIComponent(userId)}`
      )
      if (!response.ok) return null
      return await response.json()
    } catch (err) {
      console.error('Error fetching property overrides:', err)
      return null
    }
  }, [userId])

  // Get the latest override for a specific field
  const getOverride = useCallback(async (
    propertyId: number,
    fieldName: OverrideFieldName
  ): Promise<OverrideValue | null> => {
    if (!userId) return null
    try {
      const response = await fetch(
        `${API_URL}/api/property-overrides/property/${propertyId}/history/${fieldName}?user_id=${encodeURIComponent(userId)}`
      )
      if (!response.ok) return null
      const history: OverrideValue[] = await response.json()
      return history.length > 0 ? history[0] : null
    } catch (err) {
      console.error('Error fetching override:', err)
      return null
    }
  }, [userId])

  // Save a new override
  const saveOverride = useCallback(async (
    propertyId: number,
    fieldName: OverrideFieldName,
    newValue: number | null,
    notes?: string,
    propertySoldDate?: string
  ): Promise<void> => {
    if (!userId) throw new Error('Not authenticated')
    const response = await fetch(`${API_URL}/api/property-overrides/?user_id=${encodeURIComponent(userId)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        property_id: propertyId,
        field_name: fieldName,
        new_value: newValue,
        notes: notes,
        property_sold_date: propertySoldDate
      })
    })
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to save override')
    }
  }, [userId])

  // Get override history for a field
  const getOverrideHistory = useCallback(async (
    propertyId: number,
    fieldName: OverrideFieldName
  ): Promise<OverrideValue[]> => {
    if (!userId) throw new Error('Not authenticated')
    const response = await fetch(
      `${API_URL}/api/property-overrides/property/${propertyId}/history/${fieldName}?user_id=${encodeURIComponent(userId)}`
    )
    if (!response.ok) throw new Error('Failed to fetch history')
    return await response.json()
  }, [userId])

  // Revert a field to original value
  const revertOverride = useCallback(async (
    propertyId: number,
    fieldName: OverrideFieldName
  ): Promise<void> => {
    if (!userId) throw new Error('Not authenticated')
    const response = await fetch(
      `${API_URL}/api/property-overrides/property/${propertyId}/field/${fieldName}?user_id=${encodeURIComponent(userId)}`,
      { method: 'DELETE' }
    )
    if (!response.ok) throw new Error('Failed to revert override')
  }, [userId])

  return {
    getPropertyOverrides,
    getOverride,
    saveOverride,
    getOverrideHistory,
    revertOverride
  }
}
