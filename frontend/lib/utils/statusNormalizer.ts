'use client'

/**
 * Status Normalizer using GPT-4o
 * Normalizes inconsistent status labels into standardized formats
 */

// Cache for normalized statuses to avoid repeated API calls
const statusCache = new Map<string, string>()

// Standard status categories for matching
const STANDARD_PATTERNS = {
  SCHEDULED: ['scheduled', 'scheduled for sale', 'set for sale'],
  RESCHEDULED: ['rescheduled', 'continued', 'reset', 'new sale date'],
  ADJOURNED_DEFENDANT: ['adjourned - defendant', 'defendant adjourned', 'adjourned defendant', 'defendant request'],
  ADJOURNED_PLAINTIFF: ['adjourned - plaintiff', 'plaintiff adjourned', 'plaintiff request'],
  ADJOURNED_COURT: ['adjourned by court', 'court adjourned', 'administrative'],
  CANCELLED: ['cancelled', 'canceled', 'withdrawn', 'removed', 'pulled'],
  SOLD: ['sold', 'sold to plaintiff', 'sold to third party', 'purchased'],
  BANKRUPTCY: ['bankruptcy', 'bankrupt', 'chapter 7', 'chapter 13', 'stay of sale'],
  SETTLED: ['settled', 'stipulation', 'agreement'],
  NO_SALE: ['no sale', 'not sold', 'passed'],
}

/**
 * Quick normalization using pattern matching (no API call)
 */
function quickNormalize(status: string): string | null {
  if (!status) return null
  const normalized = status.toLowerCase().trim()

  for (const [category, patterns] of Object.entries(STANDARD_PATTERNS)) {
    for (const pattern of patterns) {
      if (normalized.includes(pattern)) {
        // Return standardized label
        switch (category) {
          case 'SCHEDULED':
            return 'Scheduled'
          case 'RESCHEDULED':
            return 'Rescheduled'
          case 'ADJOURNED_DEFENDANT':
            return 'Adjourned (Defendant)'
          case 'ADJOURNED_PLAINTIFF':
            return 'Adjourned (Plaintiff)'
          case 'ADJOURNED_COURT':
            return 'Adjourned (Court)'
          case 'CANCELLED':
            return 'Cancelled'
          case 'SOLD':
            return 'Sold'
          case 'BANKRUPTCY':
            return 'Bankruptcy'
          case 'SETTLED':
            return 'Settled'
          case 'NO_SALE':
            return 'No Sale'
        }
      }
    }
  }

  return null
}

/**
 * Normalize a status label using GPT-4o
 * Falls back to pattern matching for common cases
 */
export async function normalizeStatus(
  status: string,
  options?: { useGPT?: boolean; apiKey?: string }
): Promise<string> {
  // Handle undefined/null status early
  if (!status) {
    return ''
  }

  // Check cache first
  if (statusCache.has(status)) {
    return statusCache.get(status)!
  }

  // Try quick pattern matching first (no API call needed)
  const quickResult = quickNormalize(status)
  if (quickResult) {
    statusCache.set(status, quickResult)
    return quickResult
  }

  // If GPT is disabled or no API key, return original
  if (options?.useGPT === false || !options?.apiKey) {
    // Clean up the original status slightly
    const cleaned = status
      .trim()
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ')
    statusCache.set(status, cleaned)
    return cleaned
  }

  // Use GPT-4o for complex cases
  try {
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${options.apiKey}`,
      },
      body: JSON.stringify({
        model: 'gpt-4o',
        messages: [
          {
            role: 'system',
            content: `You normalize foreclosure auction status labels into standardized formats.

Standard categories to use:
- "Scheduled" - Property is scheduled for auction
- "Rescheduled" - Auction date was changed to a new date
- "Adjourned (Defendant)" - Delayed by defendant request
- "Adjourned (Plaintiff)" - Delayed by plaintiff request
- "Adjourned (Court)" - Delayed by court/administrative decision
- "Cancelled" - Sale was cancelled or withdrawn
- "Sold" - Property was sold
- "Bankruptcy" - Bankruptcy filing/stay
- "Settled" - Case was settled out of court
- "No Sale" - No sale occurred

Return ONLY the standardized label, nothing else. Be concise but accurate.`,
          },
          {
            role: 'user',
            content: `Normalize this auction status: "${status}"`,
          },
        ],
        temperature: 0.1,
        max_tokens: 50,
      }),
    })

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`)
    }

    const data = await response.json()
    const normalized = data.choices[0]?.message?.content?.trim() || status

    statusCache.set(status, normalized)
    return normalized
  } catch (error) {
    console.warn('GPT normalization failed, using original:', error)
    // Fallback to capitalizing each word
    const cleaned = status
      .trim()
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ')
    statusCache.set(status, cleaned)
    return cleaned
  }
}

/**
 * Normalize an entire status history array
 */
export async function normalizeStatusHistory(
  statusHistory: Array<{ date: string; status: string }>,
  options?: { useGPT?: boolean; apiKey?: string }
): Promise<Array<{ date: string; status: string; originalStatus?: string }>> {
  // Normalize all statuses in parallel, filtering out entries with no status
  const normalizedEntries = await Promise.all(
    statusHistory
      .filter(entry => entry.status) // Filter out entries with undefined/null status
      .map(async (entry) => {
        const normalizedStatus = await normalizeStatus(entry.status, options)
        return {
          date: entry.date,
          status: normalizedStatus,
          originalStatus: entry.status !== normalizedStatus ? entry.status : undefined,
        }
      })
  )

  return normalizedEntries
}

/**
 * Get a color class for a normalized status
 */
export function getStatusColor(status: string): string {
  if (!status) return 'text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-500/10'
  const normalized = status.toLowerCase()

  if (normalized.includes('sold')) {
    return 'text-emerald-600 dark:text-emerald-400 bg-emerald-100 dark:bg-emerald-500/10'
  }
  if (normalized.includes('adjourned') || normalized.includes('defendant')) {
    return 'text-yellow-600 dark:text-yellow-400 bg-yellow-100 dark:bg-yellow-500/10'
  }
  if (normalized.includes('scheduled')) {
    return 'text-blue-600 dark:text-blue-400 bg-blue-100 dark:bg-blue-500/10'
  }
  if (normalized.includes('rescheduled')) {
    return 'text-purple-600 dark:text-purple-400 bg-purple-100 dark:bg-purple-500/10'
  }
  if (normalized.includes('cancel') || normalized.includes('withdrawn')) {
    return 'text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-500/10'
  }
  if (normalized.includes('bankrupt') || normalized.includes('stay')) {
    return 'text-purple-600 dark:text-purple-400 bg-purple-100 dark:bg-purple-500/10'
  }
  if (normalized.includes('settled') || normalized.includes('stipulation')) {
    return 'text-teal-600 dark:text-teal-400 bg-teal-100 dark:bg-teal-500/10'
  }
  if (normalized.includes('no sale') || normalized.includes('not sold')) {
    return 'text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-500/10'
  }

  // Default
  return 'text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-500/10'
}

/**
 * Clear the status cache (useful for testing)
 */
export function clearStatusCache(): void {
  statusCache.clear()
}

/**
 * Get cache size
 */
export function getStatusCacheSize(): number {
  return statusCache.size
}
