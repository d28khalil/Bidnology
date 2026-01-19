'use client'

import { useState, useEffect, useRef } from 'react'
import { getUserNote, createUserNote, updateUserNote, deleteUserNote, type UserNote } from '@/lib/api/client'

interface PropertyNotesProps {
  propertyId: number
  userId: string
}

export function PropertyNotes({ propertyId, userId }: PropertyNotesProps) {
  const [note, setNote] = useState<UserNote | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [content, setContent] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Load note on mount
  useEffect(() => {
    loadNote()
  }, [propertyId, userId])

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current && isEditing) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px'
    }
  }, [content, isEditing])

  const loadNote = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await getUserNote(propertyId, userId)
      setNote(data)
      setContent(data?.note || '')
    } catch (err) {
      console.error('Error loading note:', err)
      setError('Failed to load note')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSave = async () => {
    if (!content.trim()) return

    setIsSaving(true)
    setError(null)

    try {
      if (note) {
        // Update existing note
        const updated = await updateUserNote(note.id, userId, content)
        setNote(updated)
      } else {
        // Create new note
        const created = await createUserNote(propertyId, userId, content)
        setNote(created)
      }
      setIsEditing(false)
    } catch (err) {
      console.error('Error saving note:', err)
      setError('Failed to save note')
    } finally {
      setIsSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!note) return

    setIsSaving(true)
    setError(null)

    try {
      await deleteUserNote(note.id, userId)
      setNote(null)
      setContent('')
      setIsEditing(false)
    } catch (err) {
      console.error('Error deleting note:', err)
      setError('Failed to delete note')
    } finally {
      setIsSaving(false)
    }
  }

  const handleCancel = () => {
    setContent(note?.note || '')
    setIsEditing(false)
  }

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-surface-dark border border-gray-300 dark:border-border-dark rounded-lg p-4">
        <div className="flex items-center gap-3 text-gray-600 dark:text-gray-400">
          <div className="w-4 h-4 border-2 border-gray-400 dark:border-gray-600 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm">Loading notes...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-surface-dark border border-gray-300 dark:border-border-dark rounded-lg overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-300 dark:border-border-dark flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-gray-600 dark:text-gray-400 text-[20px]">edit_note</span>
          <h3 className="font-medium text-gray-900 dark:text-white">My Notes</h3>
        </div>
        {!isEditing && note && (
          <button
            onClick={() => setIsEditing(true)}
            className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
            title="Edit note"
          >
            <span className="material-symbols-outlined text-[20px]">edit</span>
          </button>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        {error && (
          <div className="mb-3 p-2 bg-red-100 dark:bg-red-500/10 border border-red-300 dark:border-red-500/30 rounded text-red-700 dark:text-red-400 text-sm">
            {error}
          </div>
        )}

        {isEditing ? (
          // Edit mode
          <div className="flex flex-col gap-3">
            <textarea
              ref={textareaRef}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Add your private notes about this property..."
              className="w-full min-h-[100px] bg-gray-100 dark:bg-background-dark border border-gray-300 dark:border-border-dark rounded-lg p-3 text-sm text-gray-900 dark:text-gray-200 placeholder-gray-500 focus:outline-none focus:border-primary resize-none"
              disabled={isSaving}
            />

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-500">
                <span>{content.length} characters</span>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={handleCancel}
                  disabled={isSaving}
                  className="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-200 dark:hover:bg-white/5 rounded transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDelete}
                  disabled={isSaving || !note}
                  className="px-3 py-1.5 text-sm text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 hover:bg-red-100 dark:hover:bg-red-500/10 rounded transition-colors disabled:opacity-50"
                  title="Delete note"
                >
                  <span className="material-symbols-outlined text-[18px]">delete</span>
                </button>
                <button
                  onClick={handleSave}
                  disabled={isSaving || !content.trim()}
                  className="px-4 py-1.5 text-sm bg-primary hover:bg-primary/90 text-white rounded transition-colors disabled:opacity-50 flex items-center gap-2"
                >
                  {isSaving ? (
                    <>
                      <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <span className="material-symbols-outlined text-[18px]">save</span>
                      Save
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        ) : (
          // View mode
          <div>
            {note ? (
              <div className="group relative">
                <p className="text-gray-700 dark:text-gray-300 text-sm whitespace-pre-wrap">{note.note}</p>
                <div className="mt-3 flex items-center gap-3 text-xs text-gray-500 dark:text-gray-500">
                  <span>Last updated {new Date(note.updated_at).toLocaleDateString()}</span>
                </div>
              </div>
            ) : (
              <div className="text-center py-6">
                <span className="material-symbols-outlined text-gray-400 dark:text-gray-600 text-[32px] mb-2">note_add</span>
                <p className="text-gray-600 dark:text-gray-500 text-sm mb-3">No notes yet</p>
                <button
                  onClick={() => setIsEditing(true)}
                  className="px-4 py-2 text-sm bg-primary hover:bg-primary/90 text-white rounded transition-colors"
                >
                  Add Note
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
