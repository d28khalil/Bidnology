'use client'

import { useState, useRef, useEffect } from 'react'

interface EditableCellProps {
  value: number | null
  overrideValue: number | null
  propertyId: number
  fieldName: 'approx_upset' | 'judgment_amount' | 'starting_bid' | 'bid_cap' | 'property_sold'
  propertyLabel: string
  onSave: (propertyId: number, fieldName: 'approx_upset' | 'judgment_amount' | 'starting_bid' | 'bid_cap' | 'property_sold', newValue: number | null, notes?: string, propertySoldDate?: string) => Promise<void>
  onGetHistory: (propertyId: number, fieldName: 'approx_upset' | 'judgment_amount' | 'starting_bid' | 'bid_cap' | 'property_sold') => Promise<Array<{
    id: number
    original_value: number | null
    new_value: number | string
    previous_spread: number | null
    notes: string | null
    created_at: string
  }>>
  onRevert: (propertyId: number, fieldName: 'approx_upset' | 'judgment_amount' | 'starting_bid' | 'bid_cap' | 'property_sold') => Promise<void>
}

export function EditableCell({
  value,
  overrideValue,
  propertyId,
  fieldName,
  propertyLabel,
  onSave,
  onGetHistory,
  onRevert
}: EditableCellProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [isHistoryOpen, setIsHistoryOpen] = useState(false)
  const [editValue, setEditValue] = useState<string>('')
  const [isSaving, setIsSaving] = useState(false)
  const [history, setHistory] = useState<Array<{
    id: number
    original_value: number | null
    new_value: number | string
    previous_spread: number | null
    notes: string | null
    created_at: string
  }>>([])
  const historyRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const displayValue = overrideValue !== null ? overrideValue : value
  const hasOverride = overrideValue !== null

  const formatCurrency = (val: number | null) => {
    if (val === null || val === undefined) return '-'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(val)
  }

  const formatSpread = (spread: number | null) => {
    if (spread === null) return 'N/A'
    return `+${spread.toFixed(1)}%`
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const handleSave = async () => {
    console.log('handleSave called:', { editValue, propertyId, fieldName })
    const numValue = parseFloat(editValue.replace(/[$,]/g, ''))
    console.log('Parsed numValue:', numValue, 'isNaN:', isNaN(numValue))
    if (isNaN(numValue)) {
      console.log('Returning early - NaN')
      return
    }

    setIsSaving(true)
    try {
      console.log('Calling onSave with:', propertyId, fieldName, numValue)
      await onSave(propertyId, fieldName, numValue)
      console.log('Save successful!')
      setIsEditing(false)
    } catch (err) {
      console.error('Failed to save override:', err)
    } finally {
      setIsSaving(false)
    }
  }

  const handleRevert = async () => {
    setIsSaving(true)
    try {
      await onRevert(propertyId, fieldName)
      setIsHistoryOpen(false)
    } catch (err) {
      console.error('Failed to revert:', err)
    } finally {
      setIsSaving(false)
    }
  }

  const handleClick = async () => {
    console.log('EditableCell clicked:', { propertyId, fieldName, hasOverride, userId: 'should come from API' })
    // If no override exists, go directly to edit mode
    if (!hasOverride) {
      console.log('Starting edit mode for:', displayValue)
      setEditValue(displayValue !== null ? displayValue.toString() : '')
      setIsEditing(true)
    } else {
      // If override exists, show history
      if (isHistoryOpen) {
        setIsHistoryOpen(false)
        return
      }
      try {
        console.log('Fetching history for:', propertyId, fieldName)
        const historyData = await onGetHistory(propertyId, fieldName)
        console.log('History data:', historyData)
        setHistory(historyData)
        setIsHistoryOpen(true)
      } catch (err) {
        console.error('Failed to fetch history:', err)
      }
    }
  }

  // Close history when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (historyRef.current && !historyRef.current.contains(event.target as Node)) {
        setIsHistoryOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Focus input when editing starts
  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [isEditing])

  return (
    <div className="relative">
      {/* Display value */}
      {!isEditing ? (
        <button
          onClick={handleClick}
          className={`
            relative group py-2 px-3 rounded transition-all duration-200 w-full text-center
            ${hasOverride
              ? 'hover:bg-yellow-100 dark:hover:bg-yellow-500/20 text-gray-700 dark:text-gray-300 hover:text-yellow-800 dark:hover:text-yellow-300'
              : 'hover:bg-gray-100 dark:hover:bg-white/5 text-gray-700 dark:text-gray-300'
            }
          `}
        >
          <span className="font-medium tabular-nums">{formatCurrency(displayValue)}</span>
          {hasOverride && (
            <span className="material-symbols-outled absolute right-1 top-1/2 -translate-y-1/2 text-[14px] text-yellow-600 dark:text-yellow-400 opacity-0 group-hover:opacity-100 transition-opacity">
              edit
            </span>
          )}

          {/* Edit tooltip on hover */}
          {!isHistoryOpen && (
            <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10 pointer-events-none">
              {hasOverride ? 'Click for history' : 'Click to edit'}
            </div>
          )}
        </button>
      ) : (
        /* Inline edit mode */
        <div className="flex items-center gap-2 py-1 px-2 bg-white dark:bg-surface-dark rounded border-2 border-primary">
          <span className="text-gray-500">$</span>
          <input
            ref={inputRef}
            type="text"
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSave()
              if (e.key === 'Escape') setIsEditing(false)
            }}
            className="w-24 bg-transparent outline-none tabular-nums text-gray-900 dark:text-white"
          />
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="p-1 text-green-600 hover:text-green-700 disabled:opacity-50"
            title="Save (Enter)"
          >
            <span className="material-symbols-outlined text-[18px]">check</span>
          </button>
          <button
            onClick={() => setIsEditing(false)}
            className="p-1 text-red-600 hover:text-red-700"
            title="Cancel (Esc)"
          >
            <span className="material-symbols-outlined text-[18px]">close</span>
          </button>
        </div>
      )}

      {/* History dropdown */}
      {isHistoryOpen && !isEditing && (
        <div
          ref={historyRef}
          className="absolute z-50 mt-1 w-72 bg-white dark:bg-surface-dark border border-gray-200 dark:border-border-dark rounded-lg shadow-lg"
        >
          <div className="p-3 border-b border-gray-200 dark:border-border-dark">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold text-gray-900 dark:text-white">Edit History</h4>
              <button
                onClick={() => {
                  setIsHistoryOpen(false)
                  setEditValue(displayValue !== null ? displayValue.toString() : '')
                  setIsEditing(true)
                }}
                className="text-xs text-primary hover:underline"
              >
                New Edit
              </button>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{propertyLabel}</p>
          </div>

          <div className="max-h-64 overflow-y-auto">
            {history.length === 0 ? (
              <div className="p-4 text-center text-sm text-gray-500 dark:text-gray-400">
                No edit history yet
              </div>
            ) : (
              <div className="divide-y divide-gray-200 dark:divide-border-dark">
                {history.map((item) => (
                  <div key={item.id} className="p-3 hover:bg-gray-50 dark:hover:bg-white/5">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 mb-1">
                          <span className="material-symbols-outlined text-[12px]">schedule</span>
                          {formatDate(item.created_at)}
                        </div>
                        <div className="space-y-1">
                          {item.original_value !== null && (
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-gray-600 dark:text-gray-400 line-through">
                                {formatCurrency(item.original_value)}
                              </span>
                            </div>
                          )}
                          <div className="flex items-center justify-between text-sm font-medium text-emerald-600 dark:text-emerald-400">
                            <span>{typeof item.new_value === 'number' ? formatCurrency(item.new_value) : item.new_value}</span>
                            <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
                          </div>
                          {item.previous_spread !== null && (
                            <div className="flex items-center gap-2 text-xs mt-1 pt-1 border-t border-gray-200 dark:border-border-dark">
                              <span className="text-gray-500 dark:text-gray-400">Spread:</span>
                              <span className={`font-medium ${
                                item.previous_spread >= 30 ? 'text-emerald-600 dark:text-emerald-400' :
                                item.previous_spread >= 10 ? 'text-yellow-600 dark:text-yellow-400' :
                                'text-red-600 dark:text-red-400'
                              }`}>
                                {formatSpread(item.previous_spread)}
                              </span>
                            </div>
                          )}
                          {item.notes && (
                            <div className="text-xs text-gray-500 dark:text-gray-400 italic mt-1">
                              "{item.notes}"
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {hasOverride && (
            <div className="p-3 border-t border-gray-200 dark:border-border-dark">
              <button
                onClick={handleRevert}
                disabled={isSaving}
                className="w-full py-2 px-3 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 rounded transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                <span className="material-symbols-outlined text-[16px]">restore</span>
                Revert to Original
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
