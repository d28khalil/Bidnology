'use client'

import { useState, useEffect, useCallback } from 'react'
import { useUser } from '@/contexts/UserContext'
import {
  getUserTags,
  createUserTag,
  updateUserTag,
  deleteUserTag,
  getPropertyTags as getPropertyTagsApi,
  addTagToProperty as addTagToPropertyApi,
  removeTagFromProperty as removeTagFromPropertyApi,
  getPropertiesByTag as getPropertiesByTagApi,
  type UserTag
} from '@/lib/api/client'

interface UseTagsReturn {
  tags: UserTag[]
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
  createTag: (name: string, color?: string) => Promise<UserTag | null>
  updateTag: (tagId: number, name?: string, color?: string) => Promise<UserTag | null>
  deleteTag: (tagId: number) => Promise<boolean>
  getPropertyTags: (propertyId: number) => Promise<UserTag[]>
  addTagToProperty: (propertyId: number, tagId: number) => Promise<UserTag | null>
  removeTagFromProperty: (propertyId: number, tagId: number) => Promise<boolean>
  getPropertiesByTag: (tagId: number) => Promise<number[]>
}

export function useTags(): UseTagsReturn {
  const { userId } = useUser()
  const [tags, setTags] = useState<UserTag[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchTags = useCallback(async () => {
    if (!userId) {
      setTags([])
      return
    }

    setIsLoading(true)
    setError(null)
    try {
      const data = await getUserTags(userId)
      setTags(data)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch tags')
      console.error('Error fetching tags:', err)
    } finally {
      setIsLoading(false)
    }
  }, [userId])

  // Fetch tags on mount or when userId changes
  useEffect(() => {
    fetchTags()
  }, [fetchTags])

  const createTag = useCallback(async (name: string, color = '#3B82F6'): Promise<UserTag | null> => {
    if (!userId) return null

    setIsLoading(true)
    setError(null)
    try {
      const newTag = await createUserTag(userId, name, color)
      setTags(prev => [...prev, newTag])
      return newTag
    } catch (err: any) {
      setError(err.message || 'Failed to create tag')
      console.error('Error creating tag:', err)
      return null
    } finally {
      setIsLoading(false)
    }
  }, [userId])

  const updateTag = useCallback(async (tagId: number, name?: string, color?: string): Promise<UserTag | null> => {
    if (!userId) return null

    setIsLoading(true)
    setError(null)
    try {
      const updatedTag = await updateUserTag(tagId, userId, name, color)
      setTags(prev => prev.map(tag => tag.id === tagId ? updatedTag : tag))
      return updatedTag
    } catch (err: any) {
      setError(err.message || 'Failed to update tag')
      console.error('Error updating tag:', err)
      return null
    } finally {
      setIsLoading(false)
    }
  }, [userId])

  const deleteTag = useCallback(async (tagId: number): Promise<boolean> => {
    if (!userId) return false

    setIsLoading(true)
    setError(null)
    try {
      await deleteUserTag(tagId, userId)
      setTags(prev => prev.filter(tag => tag.id !== tagId))
      return true
    } catch (err: any) {
      setError(err.message || 'Failed to delete tag')
      console.error('Error deleting tag:', err)
      return false
    } finally {
      setIsLoading(false)
    }
  }, [userId])

  const getPropertyTags = useCallback(async (propertyId: number): Promise<UserTag[]> => {
    if (!userId) return []

    try {
      return await getPropertyTagsApi(propertyId, userId)
    } catch (err: any) {
      console.error('Error fetching property tags:', err)
      return []
    }
  }, [userId])

  const addTagToPropertyFn = useCallback(async (propertyId: number, tagId: number): Promise<UserTag | null> => {
    if (!userId) return null

    try {
      const tag = await addTagToPropertyApi(propertyId, tagId, userId)
      return tag
    } catch (err: any) {
      console.error('Error adding tag to property:', err)
      return null
    }
  }, [userId])

  const removeTagFromPropertyFn = useCallback(async (propertyId: number, tagId: number): Promise<boolean> => {
    if (!userId) return false

    try {
      await removeTagFromPropertyApi(propertyId, tagId, userId)
      return true
    } catch (err: any) {
      console.error('Error removing tag from property:', err)
      return false
    }
  }, [userId])

  const getPropertiesByTagFn = useCallback(async (tagId: number): Promise<number[]> => {
    if (!userId) return []

    try {
      return await getPropertiesByTagApi(tagId, userId)
    } catch (err: any) {
      console.error('Error fetching properties by tag:', err)
      return []
    }
  }, [userId])

  return {
    tags,
    isLoading,
    error,
    refetch: fetchTags,
    createTag,
    updateTag,
    deleteTag,
    getPropertyTags,
    addTagToProperty: addTagToPropertyFn,
    removeTagFromProperty: removeTagFromPropertyFn,
    getPropertiesByTag: getPropertiesByTagFn,
  }
}
