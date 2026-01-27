/**
 * Shared API Key Utility
 *
 * Provides robust API key retrieval with localStorage fallback.
 * Used by both CopilotWidget and AnalysisService.
 */

const LOCAL_STORAGE_KEY = 'gemini_api_key'

/**
 * Get API key from environment variables or localStorage
 * Falls back to localStorage if env vars are not available
 */
export function getApiKey(): string {
  // 1. Try standard process.env (Node/Webpack/CRA/Next.js)
  try {
    if (typeof process !== 'undefined' && process.env) {
      if (process.env.NEXT_PUBLIC_API_KEY) {
        console.log('[ApiKey] Found NEXT_PUBLIC_API_KEY')
        return process.env.NEXT_PUBLIC_API_KEY
      }
      if (process.env.API_KEY) {
        console.log('[ApiKey] Found API_KEY')
        return process.env.API_KEY
      }
      if (process.env.REACT_APP_API_KEY) {
        console.log('[ApiKey] Found REACT_APP_API_KEY')
        return process.env.REACT_APP_API_KEY
      }
      console.log('[ApiKey] process.env exists but no API key found')
    }
  } catch (e) {
    console.log('[ApiKey] process is not defined')
  }

  // 2. Try Vite import.meta.env
  try {
    // @ts-ignore - import.meta is not typed in Next.js
    const meta: any = import.meta
    if (typeof meta !== 'undefined' && meta.env) {
      if (meta.env.VITE_API_KEY) {
        console.log('[ApiKey] Found VITE_API_KEY')
        return meta.env.VITE_API_KEY
      }
      if (meta.env.API_KEY) {
        console.log('[ApiKey] Found import.meta.env.API_KEY')
        return meta.env.API_KEY
      }
    }
  } catch (e) {
    console.log('[ApiKey] import.meta is not defined')
  }

  // 3. Fall back to localStorage
  try {
    if (typeof localStorage !== 'undefined') {
      const storedKey = localStorage.getItem(LOCAL_STORAGE_KEY)
      if (storedKey) {
        console.log('[ApiKey] Found key in localStorage')
        return storedKey
      }
      console.log('[ApiKey] localStorage exists but no key found')
    }
  } catch (e) {
    console.log('[ApiKey] localStorage is not available')
  }

  console.log('[ApiKey] No API key found anywhere')
  return ''
}

/**
 * Save API key to localStorage
 */
export function saveApiKey(key: string): void {
  try {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(LOCAL_STORAGE_KEY, key.trim())
    }
  } catch (e) {
    console.error('Failed to save API key to localStorage:', e)
  }
}

/**
 * Clear API key from localStorage
 */
export function clearApiKey(): void {
  try {
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem(LOCAL_STORAGE_KEY)
    }
  } catch (e) {
    console.error('Failed to clear API key from localStorage:', e)
  }
}

/**
 * Check if API key is configured
 */
export function hasApiKey(): boolean {
  return getApiKey().length > 0
}
