// V1 API Client for Backend Integration
// Base URL: Coolify production (https://app.bidnology.com)
// Falls back to production URL if NEXT_PUBLIC_API_URL is not set

import type { SavedProperty } from '../types/property'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://app.bidnology.com'

/**
 * API Error class
 */
export class ApiError extends Error {
  constructor(public message: string, public status?: number) {
    super(message)
    this.name = 'ApiError'
  }
}

/**
 * Helper function to handle API responses
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = response.statusText
    try {
      const error = await response.json()
      errorMessage = error.detail || errorMessage
    } catch {
      // Use default error message
    }
    throw new ApiError(errorMessage, response.status)
  }
  return response.json()
}

/**
 * Get auth headers (for user-specific endpoints)
 */
function getHeaders(userId?: string): HeadersInit {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  }

  if (userId) {
    headers['X-User-ID'] = userId
  }

  return headers
}

// ============================================================================
// HEALTH & STATUS ENDPOINTS
// ============================================================================

export async function getHealth(): Promise<{ status: string }> {
  const response = await fetch(`${API_URL}/health`)
  return handleResponse<{ status: string }>(response)
}

export async function getDetailedStatus(): Promise<{
  status: string
  service: string
  running_scrapes: string[]
}> {
  const response = await fetch(`${API_URL}/`)
  return handleResponse(response)
}

export async function getScraperStatus(): Promise<{
  running_scrapes: Record<string, string>
  locked_counties: string[]
}> {
  const response = await fetch(`${API_URL}/status`)
  return handleResponse(response)
}

// ============================================================================
// PROPERTIES ENDPOINTS (Direct Supabase via enrichment routes)
// ============================================================================

export async function getProperties(params?: {
  county_id?: number
  limit?: number
  offset?: number
  property_status?: string
}): Promise<{ properties: any[] }> {
  // Note: V1 backend may need this endpoint added
  // For now, use enrichment status endpoint which returns properties
  const queryParams = new URLSearchParams()
  if (params?.county_id) queryParams.append('county_id', params.county_id.toString())
  if (params?.limit) queryParams.append('limit', params.limit.toString())
  if (params?.offset) queryParams.append('offset', params.offset.toString())

  const response = await fetch(
    `${API_URL}/api/enrichment/properties${queryParams.toString() ? `?${queryParams}` : ''}`
  )
  return handleResponse(response)
}

export async function getProperty(id: number): Promise<any> {
  const response = await fetch(`${API_URL}/api/enrichment/properties/${id}`)
  return handleResponse(response)
}

// ============================================================================
// ENRICHMENT ENDPOINTS
// ============================================================================

export async function triggerEnrichment(
  propertyId: number,
  userId?: string,
  endpoints?: string[]
): Promise<{
  property_id: number
  success: boolean
  status: string
  message: string
}> {
  const response = await fetch(`${API_URL}/api/enrichment/properties/${propertyId}/enrich`, {
    method: 'POST',
    headers: getHeaders(userId),
    body: JSON.stringify({ user_id: userId, endpoints }),
  })
  return handleResponse(response)
}

export async function getEnrichmentStatus(): Promise<{
  total: number
  pending: number
  auto_enriched: number
  fully_enriched: number
  failed: number
}> {
  const response = await fetch(`${API_URL}/api/enrichment/status`)
  return handleResponse(response)
}

// ============================================================================
// MARKET ANOMALY ENDPOINTS
// ============================================================================

export async function getMarketAnomalies(params?: {
  county_id?: number
  limit?: number
  only_anomalies?: boolean
}): Promise<{ anomalies: any[] }> {
  const queryParams = new URLSearchParams()
  if (params?.county_id) queryParams.append('county_id', params.county_id.toString())
  if (params?.limit) queryParams.append('limit', params.limit.toString())
  if (params?.only_anomalies !== undefined) queryParams.append('only_anomalies', params.only_anomalies.toString())

  const response = await fetch(
    `${API_URL}/api/deal-intelligence/market-anomalies${queryParams.toString() ? `?${queryParams}` : ''}`
  )
  return handleResponse(response)
}

export async function getPropertyAnomaly(propertyId: number): Promise<any> {
  const response = await fetch(`${API_URL}/api/deal-intelligence/market-anomalies/property/${propertyId}`)
  return handleResponse(response)
}

export async function analyzeMarketAnomaly(data: {
  property_id: number
  address: string
  list_price: number
  county_id?: number
}): Promise<any> {
  const response = await fetch(`${API_URL}/api/deal-intelligence/market-anomalies/analyze`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(data),
  })
  return handleResponse(response)
}

// ============================================================================
// COMPARABLE SALES ENDPOINTS
// ============================================================================

export async function getComparableSales(propertyId: number): Promise<any> {
  const response = await fetch(`${API_URL}/api/deal-intelligence/comparable-sales/${propertyId}`)
  return handleResponse(response)
}

export async function analyzeComparableSales(data: {
  property_id: number
  county_id?: number
}): Promise<any> {
  const response = await fetch(`${API_URL}/api/deal-intelligence/comparable-sales/analyze`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(data),
  })
  return handleResponse(response)
}

// ============================================================================
// SAVED PROPERTIES & KANBAN ENDPOINTS
// ============================================================================

export async function getSavedProperties(
  userId: string,
  kanbanStage?: string
): Promise<{ saved_properties: SavedProperty[] }> {
  const url = kanbanStage
    ? `${API_URL}/api/deal-intelligence/saved/${userId}?kanban_stage=${kanbanStage}`
    : `${API_URL}/api/deal-intelligence/saved/${userId}`

  const response = await fetch(url, { headers: getHeaders(userId) })
  return handleResponse(response)
}

export async function getKanbanBoard(userId: string): Promise<Record<string, any[]>> {
  const response = await fetch(
    `${API_URL}/api/deal-intelligence/saved/${userId}/kanban`,
    { headers: getHeaders(userId) }
  )
  return handleResponse(response)
}

export async function saveProperty(
  userId: string,
  propertyId: number,
  notes?: string,
  kanbanStage?: string
): Promise<any> {
  const response = await fetch(`${API_URL}/api/deal-intelligence/saved`, {
    method: 'POST',
    headers: getHeaders(userId),
    body: JSON.stringify({
      property_id: propertyId,
      notes,
      kanban_stage: kanbanStage || 'researching',
    }),
  })
  return handleResponse(response)
}

export async function unsaveProperty(userId: string, savedId: number): Promise<{ message: string }> {
  const response = await fetch(`${API_URL}/api/deal-intelligence/saved/${savedId}`, {
    method: 'DELETE',
    headers: getHeaders(userId),
  })
  return handleResponse(response)
}

export async function updateKanbanStage(
  userId: string,
  savedId: number,
  newStage: string
): Promise<any> {
  const response = await fetch(`${API_URL}/api/deal-intelligence/saved/stage`, {
    method: 'PUT',
    headers: getHeaders(userId),
    body: JSON.stringify({
      saved_id: savedId,
      new_stage: newStage,
    }),
  })
  return handleResponse(response)
}

export async function updatePropertyNotes(
  userId: string,
  savedId: number,
  notes: string
): Promise<any> {
  const response = await fetch(`${API_URL}/api/deal-intelligence/saved/${savedId}/notes`, {
    method: 'PUT',
    headers: getHeaders(userId),
    body: JSON.stringify({ notes }),
  })
  return handleResponse(response)
}

export async function getSavedStats(userId: string): Promise<any> {
  const response = await fetch(
    `${API_URL}/api/deal-intelligence/saved/${userId}/stats`,
    { headers: getHeaders(userId) }
  )
  return handleResponse(response)
}

// ============================================================================
// WATCHLIST & ALERTS ENDPOINTS
// ============================================================================

export async function getWatchlist(
  userId: string,
  priority?: string
): Promise<{ watchlist: any[] }> {
  const url = priority
    ? `${API_URL}/api/deal-intelligence/watchlist/${userId}?priority=${priority}`
    : `${API_URL}/api/deal-intelligence/watchlist/${userId}`

  const response = await fetch(url, { headers: getHeaders(userId) })
  return handleResponse(response)
}

export async function addToWatchlist(
  userId: string,
  propertyId: number,
  options?: {
    alert_on_price_change?: boolean
    alert_on_status_change?: boolean
    alert_on_new_comps?: boolean
    auction_alert_days?: number
    watch_notes?: string
    priority?: string
  }
): Promise<any> {
  const response = await fetch(`${API_URL}/api/deal-intelligence/watchlist`, {
    method: 'POST',
    headers: getHeaders(userId),
    body: JSON.stringify({
      property_id: propertyId,
      alert_on_price_change: options?.alert_on_price_change ?? true,
      alert_on_status_change: options?.alert_on_status_change ?? true,
      alert_on_new_comps: options?.alert_on_new_comps ?? false,
      auction_alert_days: options?.auction_alert_days ?? 7,
      watch_notes: options?.watch_notes,
      priority: options?.priority || 'normal',
    }),
  })
  return handleResponse(response)
}

export async function removeFromWatchlist(
  userId: string,
  propertyId: number
): Promise<{ message: string }> {
  const response = await fetch(`${API_URL}/api/deal-intelligence/watchlist/${propertyId}`, {
    method: 'DELETE',
    headers: getHeaders(userId),
  })
  return handleResponse(response)
}

export async function updateWatchlistEntry(
  userId: string,
  propertyId: number,
  updates: {
    alert_on_price_change?: boolean
    alert_on_status_change?: boolean
    alert_on_new_comps?: boolean
    auction_alert_days?: number
    watch_notes?: string
    priority?: string
  }
): Promise<any> {
  const response = await fetch(`${API_URL}/api/deal-intelligence/watchlist/${propertyId}`, {
    method: 'PUT',
    headers: getHeaders(userId),
    body: JSON.stringify(updates),
  })
  return handleResponse(response)
}

export async function getAlerts(
  userId: string,
  unreadOnly = false,
  limit = 50
): Promise<{ alerts: any[] }> {
  const response = await fetch(
    `${API_URL}/api/deal-intelligence/alerts/${userId}?unread_only=${unreadOnly}&limit=${limit}`,
    { headers: getHeaders(userId) }
  )
  return handleResponse(response)
}

export async function markAlertRead(userId: string, alertId: number): Promise<{ message: string }> {
  const response = await fetch(`${API_URL}/api/deal-intelligence/alerts/${alertId}/read`, {
    method: 'PUT',
    headers: getHeaders(userId),
  })
  return handleResponse(response)
}

export async function markAllAlertsRead(userId: string): Promise<{ marked_read: number }> {
  const response = await fetch(`${API_URL}/api/deal-intelligence/alerts/${userId}/read-all`, {
    method: 'PUT',
    headers: getHeaders(userId),
  })
  return handleResponse(response)
}

export async function deleteAlert(userId: string, alertId: number): Promise<{ message: string }> {
  const response = await fetch(`${API_URL}/api/deal-intelligence/alerts/${alertId}`, {
    method: 'DELETE',
    headers: getHeaders(userId),
  })
  return handleResponse(response)
}

// ============================================================================
// DEAL CRITERIA ENDPOINTS
// ============================================================================

export async function getDealCriteria(userId: string): Promise<any> {
  const response = await fetch(
    `${API_URL}/api/deal-intelligence/criteria/${userId}`,
    { headers: getHeaders(userId) }
  )
  return handleResponse(response)
}

export async function upsertDealCriteria(data: {
  user_id: string
  county_id?: number
  max_opening_bid?: number
  min_equity_spread?: number
  max_purchase_price?: number
  min_arv_spread?: number
  min_beds?: number
  max_beds?: number
  min_baths?: number
  min_sqft?: number
  property_types?: string[]
  sale_date_window_days?: number
  is_anomaly_only?: boolean
  counties?: number[]
  enable_alerts?: boolean
}): Promise<any> {
  const response = await fetch(`${API_URL}/api/deal-intelligence/criteria`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(data),
  })
  return handleResponse(response)
}

export async function getMatchingProperties(
  userId: string,
  category?: string,
  limit = 50
): Promise<any> {
  const url = category
    ? `${API_URL}/api/deal-intelligence/matches/${userId}?category=${category}&limit=${limit}`
    : `${API_URL}/api/deal-intelligence/matches/${userId}?limit=${limit}`

  const response = await fetch(url, { headers: getHeaders(userId) })
  return handleResponse(response)
}

export async function testPropertyMatch(userId: string, propertyId: number): Promise<any> {
  const response = await fetch(`${API_URL}/api/deal-intelligence/criteria/${userId}/test`, {
    method: 'POST',
    headers: getHeaders(userId),
    body: JSON.stringify({ property_id: propertyId }),
  })
  return handleResponse(response)
}

// ============================================================================
// DATA QUALITY ENDPOINTS
// ============================================================================

export async function getQualityScore(propertyId: number): Promise<any> {
  const response = await fetch(`${API_URL}/api/deal-intelligence/quality/${propertyId}`)
  return handleResponse(response)
}

export async function triggerQualityScoring(data: {
  property_id?: number
  property_ids?: number[]
}): Promise<any> {
  const response = await fetch(`${API_URL}/api/deal-intelligence/quality/score`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(data),
  })
  return handleResponse(response)
}

// ============================================================================
// NOTES & CHECKLIST ENDPOINTS
// ============================================================================

export async function getNotes(propertyId: number, noteType?: string): Promise<{ notes: any[] }> {
  const response = await fetch(
    `${API_URL}/api/deal-intelligence/notes/${propertyId}${noteType ? `?note_type=${noteType}` : ''}`
  )
  return handleResponse(response)
}

export async function addNote(
  userId: string,
  propertyId: number,
  content: string,
  noteType = 'general'
): Promise<any> {
  const response = await fetch(`${API_URL}/api/deal-intelligence/notes`, {
    method: 'POST',
    headers: getHeaders(userId),
    body: JSON.stringify({
      property_id: propertyId,
      content,
      note_type: noteType,
    }),
  })
  return handleResponse(response)
}

export async function updateNote(
  userId: string,
  noteId: number,
  content: string
): Promise<any> {
  const response = await fetch(`${API_URL}/api/deal-intelligence/notes/${noteId}`, {
    method: 'PUT',
    headers: getHeaders(userId),
    body: JSON.stringify({ content }),
  })
  return handleResponse(response)
}

export async function deleteNote(userId: string, noteId: number): Promise<{ message: string }> {
  const response = await fetch(`${API_URL}/api/deal-intelligence/notes/${noteId}`, {
    method: 'DELETE',
    headers: getHeaders(userId),
  })
  return handleResponse(response)
}

export async function getChecklist(propertyId: number, userId: string): Promise<any> {
  const response = await fetch(
    `${API_URL}/api/deal-intelligence/checklist/${propertyId}/${userId}`,
    { headers: getHeaders(userId) }
  )
  return handleResponse(response)
}

export async function updateChecklist(
  propertyId: number,
  userId: string,
  checklistItems: Record<string, boolean>
): Promise<any> {
  const response = await fetch(`${API_URL}/api/deal-intelligence/checklist/${propertyId}/${userId}`, {
    method: 'PUT',
    headers: getHeaders(userId),
    body: JSON.stringify({ checklist_items: checklistItems }),
  })
  return handleResponse(response)
}

export async function resetChecklist(propertyId: number, userId: string): Promise<any> {
  const response = await fetch(`${API_URL}/api/deal-intelligence/checklist/${propertyId}/${userId}/reset`, {
    method: 'POST',
    headers: getHeaders(userId),
  })
  return handleResponse(response)
}

// ============================================================================
// STREET VIEW ENDPOINT
// ============================================================================

export async function getStreetView(address: string, size = '600x400', headings?: string[]): Promise<any> {
  const response = await fetch(`${API_URL}/api/deal-intelligence/street-view`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ address, size, headings }),
  })
  return handleResponse(response)
}

// ============================================================================
// CSV EXPORT ENDPOINT
// ============================================================================

export async function exportCsv(data: {
  county_id?: number
  property_ids?: number[]
  columns?: string[]
}): Promise<Blob> {
  const response = await fetch(`${API_URL}/api/deal-intelligence/export/csv`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    throw new ApiError('Export failed', response.status)
  }

  return response.blob()
}

// ============================================================================
// TRACERFY SKIP TRACE ENDPOINTS
// ============================================================================

export async function triggerSkipTrace(
  propertyId: number,
  userId?: string
): Promise<{
  property_id: number
  success: boolean
  job_id?: string
  status: string
  message?: string
  data?: any
}> {
  const response = await fetch(`${API_URL}/api/enrichment/properties/${propertyId}/tracerfy`, {
    method: 'POST',
    headers: getHeaders(userId),
    body: JSON.stringify({ user_id: userId }),
  })
  return handleResponse(response)
}

export async function getTracerfyStatus(
  propertyId: number,
  jobId: string
): Promise<{
  job_id: string
  status: string
  data?: any
  error?: string
}> {
  const response = await fetch(
    `${API_URL}/api/enrichment/properties/${propertyId}/tracerfy/${jobId}`
  )
  return handleResponse(response)
}

export async function pollTracerfyResults(
  propertyId: number,
  jobId: string
): Promise<{
  property_id: number
  job_id: string
  status: string
  success: boolean
  data?: any
  message?: string
}> {
  const response = await fetch(
    `${API_URL}/api/enrichment/properties/${propertyId}/tracerfy/${jobId}/poll`,
    { method: 'POST' }
  )
  return handleResponse(response)
}

// ============================================================================
// USER NOTES ENDPOINTS
// ============================================================================

export interface UserNote {
  id: number
  user_id: string
  property_id: number
  note: string
  created_at: string
  updated_at: string
}

export async function getUserNote(
  propertyId: number,
  userId: string
): Promise<UserNote | null> {
  const response = await fetch(
    `${API_URL}/api/notes/property/${propertyId}?user_id=${encodeURIComponent(userId)}`
  )
  if (response.status === 404) return null
  return handleResponse<UserNote>(response)
}

export async function getAllUserNotes(
  userId: string,
  limit = 100,
  offset = 0
): Promise<UserNote[]> {
  const response = await fetch(
    `${API_URL}/api/notes/user/${encodeURIComponent(userId)}?limit=${limit}&offset=${offset}`
  )
  return handleResponse<UserNote[]>(response)
}

export async function createUserNote(
  propertyId: number,
  userId: string,
  note: string
): Promise<UserNote> {
  const response = await fetch(`${API_URL}/api/notes/?user_id=${encodeURIComponent(userId)}`, {
    method: 'POST',
    headers: getHeaders(userId),
    body: JSON.stringify({ property_id: propertyId, note })
  })
  return handleResponse<UserNote>(response)
}

export async function updateUserNote(
  noteId: number,
  userId: string,
  note: string
): Promise<UserNote> {
  const response = await fetch(`${API_URL}/api/notes/${noteId}?user_id=${encodeURIComponent(userId)}`, {
    method: 'PUT',
    headers: getHeaders(userId),
    body: JSON.stringify({ note })
  })
  return handleResponse<UserNote>(response)
}

export async function deleteUserNote(
  noteId: number,
  userId: string
): Promise<{ message: string }> {
  const response = await fetch(`${API_URL}/api/notes/${noteId}?user_id=${encodeURIComponent(userId)}`, {
    method: 'DELETE',
    headers: getHeaders(userId)
  })
  return handleResponse<{ message: string }>(response)
}

// ============================================================================
// USER TAGS ENDPOINTS
// ============================================================================

export interface UserTag {
  id: number
  user_id: string
  name: string
  color: string
  created_at: string
  updated_at: string
}

export async function getUserTags(userId: string): Promise<UserTag[]> {
  const response = await fetch(
    `${API_URL}/api/tags/?user_id=${encodeURIComponent(userId)}`
  )
  return handleResponse<UserTag[]>(response)
}

export async function createUserTag(
  userId: string,
  name: string,
  color: string = '#3B82F6'
): Promise<UserTag> {
  const response = await fetch(`${API_URL}/api/tags/?user_id=${encodeURIComponent(userId)}`, {
    method: 'POST',
    headers: getHeaders(userId),
    body: JSON.stringify({ name, color })
  })
  return handleResponse<UserTag>(response)
}

export async function updateUserTag(
  tagId: number,
  userId: string,
  name?: string,
  color?: string
): Promise<UserTag> {
  const response = await fetch(`${API_URL}/api/tags/${tagId}?user_id=${encodeURIComponent(userId)}`, {
    method: 'PUT',
    headers: getHeaders(userId),
    body: JSON.stringify({ name, color })
  })
  return handleResponse<UserTag>(response)
}

export async function deleteUserTag(
  tagId: number,
  userId: string
): Promise<{ message: string }> {
  const response = await fetch(`${API_URL}/api/tags/${tagId}?user_id=${encodeURIComponent(userId)}`, {
    method: 'DELETE',
    headers: getHeaders(userId)
  })
  return handleResponse<{ message: string }>(response)
}

export async function getPropertyTags(
  propertyId: number,
  userId: string
): Promise<UserTag[]> {
  const response = await fetch(
    `${API_URL}/api/tags/property/${propertyId}?user_id=${encodeURIComponent(userId)}`
  )
  return handleResponse<UserTag[]>(response)
}

export async function addTagToProperty(
  propertyId: number,
  tagId: number,
  userId: string
): Promise<UserTag> {
  const response = await fetch(`${API_URL}/api/tags/property?user_id=${encodeURIComponent(userId)}`, {
    method: 'POST',
    headers: getHeaders(userId),
    body: JSON.stringify({ property_id: propertyId, tag_id: tagId })
  })
  return handleResponse<UserTag>(response)
}

export async function removeTagFromProperty(
  propertyId: number,
  tagId: number,
  userId: string
): Promise<{ message: string }> {
  const response = await fetch(
    `${API_URL}/api/tags/property/${propertyId}/tag/${tagId}?user_id=${encodeURIComponent(userId)}`,
    {
      method: 'DELETE',
      headers: getHeaders(userId)
    }
  )
  return handleResponse<{ message: string }>(response)
}

export async function getPropertiesByTag(
  tagId: number,
  userId: string
): Promise<number[]> {
  const response = await fetch(
    `${API_URL}/api/tags/properties/by-tag/${tagId}?user_id=${encodeURIComponent(userId)}`
  )
  return handleResponse<number[]>(response)
}

// ============================================================================
// USER FAVORITES ENDPOINTS
// ============================================================================

export async function getUserFavorites(
  userId: string
): Promise<number[]> {
  const response = await fetch(
    `${API_URL}/api/favorites/user/${encodeURIComponent(userId)}`
  )
  return handleResponse<number[]>(response)
}

export async function addFavorite(
  userId: string,
  propertyId: number
): Promise<{ message: string }> {
  const response = await fetch(`${API_URL}/api/favorites`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ user_id: userId, property_id: propertyId })
  })
  return handleResponse<{ message: string }>(response)
}

export async function removeFavorite(
  userId: string,
  propertyId: number
): Promise<{ message: string }> {
  const response = await fetch(`${API_URL}/api/favorites`, {
    method: 'DELETE',
    headers: getHeaders(),
    body: JSON.stringify({ user_id: userId, property_id: propertyId })
  })
  return handleResponse<{ message: string }>(response)
}

// ============================================================================
// GPT DESCRIPTION REFINEMENT ENDPOINTS
// ============================================================================

export async function refineDescription(
  propertyId: number,
  description: string
): Promise<{
  refined_description: string
  property_id: number
}> {
  const response = await fetch('/api/refine-description', {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ property_id: propertyId, description }),
  })
  return handleResponse(response)
}
