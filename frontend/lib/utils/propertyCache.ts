'use client'

import { Property } from '@/lib/types/property'

const CACHE_PREFIX = 'bidnology_properties_'
const CACHE_VERSION = 'v1'
const DEFAULT_CACHE_TTL = 5 * 60 * 1000 // 5 minutes default TTL

interface CacheEntry {
  version: string
  timestamp: number
  ttl: number
  data: Property[]
  count: number
  metadata: {
    queryKey: string
    county_id?: number
    state?: string
    city?: string
    property_status?: string
    min_upset_price?: number
    max_upset_price?: number
    search?: string
  }
}

/**
 * Generate a cache key from query parameters
 */
export function generateCacheKey(options: {
  county_id?: number
  state?: string
  city?: string
  property_status?: string
  min_upset_price?: number
  max_upset_price?: number
  search?: string
  order_by?: string
  order?: 'asc' | 'desc' | null
  limit?: number
  offset?: number
}): string {
  // Create a deterministic key from the options
  const keyParts = [
    options.county_id ?? 'all',
    options.state?.toLowerCase() ?? 'all',
    options.city?.toLowerCase() ?? 'all',
    options.property_status ?? 'all',
    options.min_upset_price ?? 'all',
    options.max_upset_price ?? 'all',
    options.search?.toLowerCase() ?? 'all',
    options.order_by ?? 'default',
    options.order ?? 'default',
  ]

  // For live feed vs auction history, we use different keys
  // Live feed: upcoming auctions only
  // Auction history: past auctions only
  const suffix = options.limit === 1000 ? 'live' : 'history'

  return `${CACHE_PREFIX}${CACHE_VERSION}_${suffix}_${keyParts.join('_')}`
}

/**
 * Check if cached data is valid and not expired
 */
function isCacheValid(entry: CacheEntry): boolean {
  // Check version match
  if (entry.version !== CACHE_VERSION) {
    return false
  }

  // Check if expired
  const now = Date.now()
  const age = now - entry.timestamp
  return age < entry.ttl
}

/**
 * Get cached properties for a given query
 */
export function getCachedProperties(
  cacheKey: string
): { properties: Property[]; count: number } | null {
  if (typeof window === 'undefined') {
    return null
  }

  try {
    const cached = localStorage.getItem(cacheKey)
    if (!cached) {
      return null
    }

    const entry: CacheEntry = JSON.parse(cached)

    // Validate cache
    if (!isCacheValid(entry)) {
      // Remove expired cache
      localStorage.removeItem(cacheKey)
      return null
    }

    return {
      properties: entry.data,
      count: entry.count,
    }
  } catch (error) {
    console.error('Error reading from cache:', error)
    return null
  }
}

/**
 * Cache properties with a TTL
 */
export function setCachedProperties(
  cacheKey: string,
  properties: Property[],
  count: number,
  ttl: number = DEFAULT_CACHE_TTL,
  metadata?: CacheEntry['metadata']
): void {
  if (typeof window === 'undefined') {
    return
  }

  try {
    const entry: CacheEntry = {
      version: CACHE_VERSION,
      timestamp: Date.now(),
      ttl,
      data: properties,
      count,
      metadata: metadata || {
        queryKey: cacheKey,
      },
    }

    localStorage.setItem(cacheKey, JSON.stringify(entry))
  } catch (error) {
    // Handle quota exceeded error
    if (error instanceof Error && error.name === 'QuotaExceededError') {
      console.warn('LocalStorage quota exceeded, clearing old cache entries')
      clearOldCacheEntries()
      // Try again
      try {
        localStorage.setItem(cacheKey, JSON.stringify({
          version: CACHE_VERSION,
          timestamp: Date.now(),
          ttl,
          data: properties,
          count,
          metadata: metadata || { queryKey: cacheKey },
        }))
      } catch (retryError) {
        console.error('Failed to cache properties after cleanup:', retryError)
      }
    } else {
      console.error('Error caching properties:', error)
    }
  }
}

/**
 * Clear cache for a specific key
 */
export function clearCacheKey(cacheKey: string): void {
  if (typeof window === 'undefined') {
    return
  }

  try {
    localStorage.removeItem(cacheKey)
  } catch (error) {
    console.error('Error clearing cache key:', error)
  }
}

/**
 * Clear all property cache entries
 */
export function clearAllPropertyCache(): void {
  if (typeof window === 'undefined') {
    return
  }

  try {
    const keys = Object.keys(localStorage)
    keys.forEach(key => {
      if (key.startsWith(CACHE_PREFIX)) {
        localStorage.removeItem(key)
      }
    })
  } catch (error) {
    console.error('Error clearing all cache:', error)
  }
}

/**
 * Clear old/expired cache entries to free up space
 */
export function clearOldCacheEntries(): void {
  if (typeof window === 'undefined') {
    return
  }

  try {
    const keys = Object.keys(localStorage)
    const now = Date.now()

    keys.forEach(key => {
      if (key.startsWith(CACHE_PREFIX)) {
        try {
          const cached = localStorage.getItem(key)
          if (cached) {
            const entry: CacheEntry = JSON.parse(cached)
            // Remove if expired or old version
            if (entry.version !== CACHE_VERSION || (now - entry.timestamp) > entry.ttl) {
              localStorage.removeItem(key)
            }
          }
        } catch {
          // Remove corrupted entries
          localStorage.removeItem(key)
        }
      }
    })
  } catch (error) {
    console.error('Error clearing old cache entries:', error)
  }
}

/**
 * Get cache size in bytes (approximate)
 */
export function getCacheSize(): number {
  if (typeof window === 'undefined') {
    return 0
  }

  try {
    let size = 0
    const keys = Object.keys(localStorage)

    keys.forEach(key => {
      if (key.startsWith(CACHE_PREFIX)) {
        const item = localStorage.getItem(key)
        if (item) {
          size += key.length + item.length
        }
      }
    })

    return size
  } catch (error) {
    return 0
  }
}

/**
 * Get cache info for debugging
 */
export function getCacheInfo(): Array<{ key: string; size: number; age: number; itemCount: number }> {
  if (typeof window === 'undefined') {
    return []
  }

  try {
    const info: Array<{ key: string; size: number; age: number; itemCount: number }> = []
    const keys = Object.keys(localStorage)
    const now = Date.now()

    keys.forEach(key => {
      if (key.startsWith(CACHE_PREFIX)) {
        const item = localStorage.getItem(key)
        if (item) {
          try {
            const entry: CacheEntry = JSON.parse(item)
            info.push({
              key: key.replace(CACHE_PREFIX, ''),
              size: key.length + item.length,
              age: now - entry.timestamp,
              itemCount: entry.data.length,
            })
          } catch {
            // Skip corrupted entries
          }
        }
      }
    })

    return info.sort((a, b) => b.age - a.age)
  } catch (error) {
    return []
  }
}

/**
 * Prefetch/cache multiple queries in the background
 */
export async function prefetchProperties(
  queries: Array<{
    options: Parameters<typeof generateCacheKey>[0]
    fetchFn: () => Promise<{ properties: Property[]; count: number }>
  }>,
  ttl: number = DEFAULT_CACHE_TTL
): Promise<void> {
  if (typeof window === 'undefined') {
    return
  }

  // Clear old cache before prefetching
  clearOldCacheEntries()

  // Fetch all queries in parallel
  await Promise.all(
    queries.map(async ({ options, fetchFn }) => {
      const cacheKey = generateCacheKey(options)

      // Skip if already cached and valid
      const existing = getCachedProperties(cacheKey)
      if (existing) {
        return
      }

      try {
        const result = await fetchFn()
        setCachedProperties(cacheKey, result.properties, result.count, ttl)
      } catch (error) {
        console.error('Error prefetching properties:', error)
      }
    })
  )
}
