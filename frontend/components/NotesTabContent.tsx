'use client'

import { useState, useEffect } from 'react'
import { getAllUserNotes, type UserNote } from '@/lib/api/client'
import { createClient } from '@/utils/supabase/client'

interface NotesTabContentProps {
  userId: string
}

export function NotesTabContent({ userId }: NotesTabContentProps) {
  const [notes, setNotes] = useState<UserNote[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [properties, setProperties] = useState<Map<number, any>>(new Map())

  useEffect(() => {
    loadNotes()
  }, [userId])

  const loadNotes = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const userNotes = await getAllUserNotes(userId)
      setNotes(userNotes)

      // Fetch property details for each note
      const propertyIds = userNotes.map(note => note.property_id)
      if (propertyIds.length > 0) {
        const supabase = createClient()
        const { data: propertiesData } = await supabase
          .from('foreclosure_listings')
          .select('id, property_address, city, state, zip_code')
          .in('id', propertyIds)

        const propertyMap = new Map()
        propertiesData?.forEach(prop => {
          propertyMap.set(prop.id, prop)
        })
        setProperties(propertyMap)
      }
    } catch (err) {
      console.error('Error loading notes:', err)
      setError('Failed to load notes')
    } finally {
      setIsLoading(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-400">Loading notes...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-surface-dark border border-border-dark rounded-lg p-8 text-center">
        <p className="text-red-400">{error}</p>
        <button
          onClick={loadNotes}
          className="mt-4 px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg"
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">My Notes</h2>
          <p className="text-gray-400 mt-1">
            {notes.length} {notes.length === 1 ? 'note' : 'notes'} across {properties.size} {properties.size === 1 ? 'property' : 'properties'}
          </p>
        </div>
      </div>

      {notes.length === 0 ? (
        <div className="bg-surface-dark border border-border-dark rounded-lg p-12 text-center">
          <span className="material-symbols-outlined text-gray-500 text-5xl mb-4">note_add</span>
          <h3 className="text-lg font-medium text-white mb-2">No notes yet</h3>
          <p className="text-gray-400">
            Add notes to properties from the property detail modal. They will appear here.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {notes.map((note) => {
            const property = properties.get(note.property_id)
            return (
              <div
                key={note.id}
                className="bg-surface-dark border border-border-dark rounded-lg p-4 hover:border-border-dark/50 transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    {/* Property Address */}
                    {property && (
                      <div className="flex items-center gap-2 mb-3">
                        <span className="material-symbols-outlined text-primary text-[18px]">home</span>
                        <span className="text-sm font-medium text-white">
                          {property.property_address}, {property.city}, {property.state} {property.zip_code}
                        </span>
                      </div>
                    )}

                    {/* Note Content */}
                    <p className="text-gray-300 text-sm whitespace-pre-wrap break-words">
                      {note.note}
                    </p>

                    {/* Timestamps */}
                    <div className="mt-3 flex items-center gap-4 text-xs text-gray-500">
                      <span>Created: {formatDate(note.created_at)}</span>
                      {note.updated_at !== note.created_at && (
                        <span>Updated: {formatDate(note.updated_at)}</span>
                      )}
                    </div>
                  </div>

                  {/* View Property Button */}
                  {property && (
                    <a
                      href={`/?property=${note.property_id}`}
                      className="shrink-0 px-3 py-1.5 text-sm bg-primary/10 hover:bg-primary/20 text-primary border border-primary/30 rounded-lg transition-colors"
                    >
                      View Property
                    </a>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
