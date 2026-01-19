'use client'

import { useState, useCallback, useRef, useEffect } from 'react'
import { triggerSkipTrace, pollTracerfyResults } from '@/lib/api/client'
import { createClient } from '@/utils/supabase/client'

interface SkipTraceState {
  isTracing: boolean
  status: string | null
  error: string | null
}

interface UseSkipTraceResult {
  traceProperty: (propertyId: number) => Promise<{ success: boolean; message?: string; jobId?: string }>
  state: SkipTraceState
  onDataUpdate?: (propertyId: number) => void
}

/**
 * Hook for triggering and monitoring Tracerfy skip trace operations
 * Handles the async job submission and optional polling for results
 * Uses Supabase realtime for live updates when skip trace completes
 */
export function useSkipTrace(userId?: string, onDataUpdate?: (propertyId: number) => void): UseSkipTraceResult {
  const [isTracing, setIsTracing] = useState(false)
  const [status, setStatus] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Track active jobs to avoid duplicate polling
  const activeJobs = useRef<Set<number>>(new Set())

  // Track completed jobs for realtime updates
  const pendingPropertyIds = useRef<Set<number>>(new Set())

  // Store onDataUpdate in a ref to avoid dependency issues
  const onDataUpdateRef = useRef(onDataUpdate)
  onDataUpdateRef.current = onDataUpdate

  // Set up Supabase realtime subscription for skip trace updates
  useEffect(() => {
    const supabase = createClient()
    const channel = supabase
      .channel('skip-trace-updates')
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'zillow_enrichment',
          filter: 'skip_tracing->>isnull.false'
        },
        (payload) => {
          const newRecord = payload.new as any
          const propertyId = newRecord.property_id

          // Check if this is a property we're waiting for
          if (pendingPropertyIds.current.has(propertyId)) {
            // Check if skip trace data is now available
            if (newRecord.skip_tracing) {
              console.log(`Skip trace completed for property ${propertyId}`)
              pendingPropertyIds.current.delete(propertyId)
              setIsTracing(false)
              activeJobs.current.delete(propertyId)
              setStatus('completed')

              // Trigger data update callback
              if (onDataUpdateRef.current) {
                onDataUpdateRef.current(propertyId)
              }
            }
          }
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [])

  const traceProperty = useCallback(async (propertyId: number) => {
    // Prevent duplicate requests
    if (activeJobs.current.has(propertyId)) {
      return { success: false, message: 'Skip trace already in progress' }
    }

    setIsTracing(true)
    setStatus('submitting')
    setError(null)
    activeJobs.current.add(propertyId)
    pendingPropertyIds.current.add(propertyId)

    try {
      // Submit the skip trace job
      const result = await triggerSkipTrace(propertyId, userId)

      if (!result.success) {
        setError(result.message || 'Failed to submit skip trace')
        setIsTracing(false)
        activeJobs.current.delete(propertyId)
        pendingPropertyIds.current.delete(propertyId)
        return { success: false, message: result.message }
      }

      setStatus('submitted')

      // If job was immediately completed, return success
      if (result.status === 'completed' && result.data) {
        setStatus('completed')
        setIsTracing(false)
        activeJobs.current.delete(propertyId)
        pendingPropertyIds.current.delete(propertyId)
        // Trigger data update callback for immediate completion
        if (onDataUpdateRef.current) {
          onDataUpdateRef.current(propertyId)
        }
        return { success: true, message: 'Skip trace completed', jobId: result.job_id }
      }

      // For pending jobs, start polling in background
      if (result.job_id) {
        setStatus('processing')

        // Poll for results in background (fire and forget)
        pollJob(result.job_id, propertyId).catch(err => {
          console.error('Polling error:', err)
        })

        return { success: true, message: 'Skip trace started', jobId: result.job_id }
      }

      // If we got here, the API returned success but no job_id and status wasn't 'completed'
      // This is an unexpected state - keep tracing active and wait for realtime update
      setStatus('processing')
      console.log('Skip trace submitted without job_id, waiting for realtime update')

      // Don't set isTracing to false - wait for realtime or timeout
      return { success: true, message: 'Skip trace submitted' }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      setError(errorMessage)
      setIsTracing(false)
      activeJobs.current.delete(propertyId)
      pendingPropertyIds.current.delete(propertyId)
      return { success: false, message: errorMessage }
    }
  }, [userId])

  // Background polling function (fallback if realtime doesn't work)
  const pollJob = async (jobId: string, propertyId: number) => {
    const maxAttempts = 20
    const pollInterval = 3000 // 3 seconds

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        const result = await pollTracerfyResults(propertyId, jobId)

        if (result.status === 'completed') {
          setStatus('completed')
          setIsTracing(false)
          activeJobs.current.delete(propertyId)
          pendingPropertyIds.current.delete(propertyId)

          // Trigger data update callback if realtime didn't catch it
          if (onDataUpdateRef.current) {
            onDataUpdateRef.current(propertyId)
          }
          return
        }

        if (result.status === 'failed') {
          setError(result.message || 'Skip trace failed')
          setIsTracing(false)
          activeJobs.current.delete(propertyId)
          pendingPropertyIds.current.delete(propertyId)
          return
        }

        // Still processing, wait and retry
        await new Promise(resolve => setTimeout(resolve, pollInterval))
      } catch (err) {
        console.error(`Polling attempt ${attempt + 1} failed:`, err)
        await new Promise(resolve => setTimeout(resolve, pollInterval))
      }
    }

    // Max attempts reached
    setError('Skip trace timed out')
    setIsTracing(false)
    activeJobs.current.delete(propertyId)
    pendingPropertyIds.current.delete(propertyId)
  }

  return {
    traceProperty,
    state: { isTracing, status, error }
  }
}
