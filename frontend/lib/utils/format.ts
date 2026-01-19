// Utility functions for formatting

/**
 * Format currency value
 */
export function formatCurrency(value: number | undefined | null): string {
  if (value === undefined || value === null) return '—'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

/**
 * Format number with commas
 */
export function formatNumber(value: number | undefined | null): string {
  if (value === undefined || value === null) return '—'
  return new Intl.NumberFormat('en-US').format(value)
}

/**
 * Format percentage
 */
export function formatPercent(value: number | undefined | null, decimals = 1): string {
  if (value === undefined || value === null) return '—%'
  return `${value.toFixed(decimals)}%`
}

/**
 * Format date
 */
export function formatDate(date: string | undefined | null): string {
  if (!date) return '—'
  try {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    }).format(new Date(date))
  } catch {
    return date
  }
}

/**
 * Format date with time
 */
export function formatDateTime(date: string | undefined | null): string {
  if (!date) return '—'
  try {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    }).format(new Date(date))
  } catch {
    return date
  }
}

/**
 * Format relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(date: string | undefined | null): string {
  if (!date) return '—'
  try {
    const now = new Date()
    const then = new Date(date)
    const diffMs = now.getTime() - then.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return formatDate(date)
  } catch {
    return date
  }
}

/**
 * Calculate equity spread
 */
export function calculateEquitySpread(openingBid: number, zestimate?: number | null): number {
  if (!zestimate) return 0
  return zestimate - openingBid
}

/**
 * Calculate equity spread percentage
 */
export function calculateEquitySpreadPercent(openingBid: number, zestimate?: number | null): number {
  if (!zestimate || openingBid === 0) return 0
  return ((zestimate - openingBid) / openingBid) * 100
}

/**
 * Get AI status config
 */
export function getAIStatusConfig(aiStatus?: string) {
  if (!aiStatus) {
    return {
      color: 'gray',
      bgColor: 'bg-gray-500/10',
      textColor: 'text-gray-400',
      icon: 'help_outline',
      label: 'Unknown',
    }
  }

  if (aiStatus === 'excellent' || aiStatus === 'good') {
    return {
      color: 'primary',
      bgColor: 'bg-primary/10',
      textColor: 'text-primary',
      icon: 'smart_toy',
      label: 'Good Data',
    }
  }

  if (aiStatus === 'warning') {
    return {
      color: 'yellow',
      bgColor: 'bg-yellow-500/10',
      textColor: 'text-yellow-400',
      icon: 'warning',
      label: 'Low Data',
    }
  }

  return {
    color: 'orange',
    bgColor: 'bg-orange-500/10',
    textColor: 'text-orange-400',
    icon: 'construction',
    label: 'Needs Data',
  }
}

/**
 * Get kanban stage config
 */
export function getKanbanStageConfig(stage: string) {
  const configs: Record<string, { label: string; color: string; bgColor: string; textColor: string }> = {
    researching: { label: 'Researching', color: 'gray', bgColor: 'bg-gray-500/10', textColor: 'text-gray-400' },
    analyzing: { label: 'Analyzing', color: 'blue', bgColor: 'bg-blue-500/10', textColor: 'text-blue-400' },
    due_diligence: { label: 'Due Diligence', color: 'yellow', bgColor: 'bg-yellow-500/10', textColor: 'text-yellow-400' },
    bidding: { label: 'Bidding', color: 'orange', bgColor: 'bg-orange-500/10', textColor: 'text-orange-400' },
    won: { label: 'Won', color: 'green', bgColor: 'bg-green-500/10', textColor: 'text-green-400' },
    lost: { label: 'Lost', color: 'red', bgColor: 'bg-red-500/10', textColor: 'text-red-400' },
    archived: { label: 'Archived', color: 'gray', bgColor: 'bg-gray-500/10', textColor: 'text-gray-500' },
  }

  return configs[stage] || configs.researching
}

/**
 * Get property status config
 */
export function getPropertyStatusConfig(status?: string) {
  if (!status) {
    return {
      label: 'Unknown',
      color: 'gray',
      bgColor: 'bg-gray-500/10',
      textColor: 'text-gray-400',
    }
  }

  const configs: Record<string, { label: string; color: string; bgColor: string; textColor: string }> = {
    scheduled: { label: 'Scheduled', color: 'blue', bgColor: 'bg-blue-500/10', textColor: 'text-blue-400' },
    adjourned: { label: 'Adjourned', color: 'yellow', bgColor: 'bg-yellow-500/10', textColor: 'text-yellow-400' },
    sold: { label: 'Sold', color: 'green', bgColor: 'bg-green-500/10', textColor: 'text-green-400' },
    cancelled: { label: 'Cancelled', color: 'red', bgColor: 'bg-red-500/10', textColor: 'text-red-400' },
    pending: { label: 'Pending', color: 'gray', bgColor: 'bg-gray-500/10', textColor: 'text-gray-400' },
  }

  return configs[status] || configs.pending
}

/**
 * Get alert type config
 */
export function getAlertTypeConfig(alertType: string) {
  const configs: Record<string, { icon: string; color: string; bgColor: string; textColor: string }> = {
    price_change: { icon: 'trending_down', color: 'green', bgColor: 'bg-green-500/10', textColor: 'text-green-400' },
    status_change: { icon: 'info', color: 'blue', bgColor: 'bg-blue-500/10', textColor: 'text-blue-400' },
    new_comps: { icon: 'analytics', color: 'purple', bgColor: 'bg-purple-500/10', textColor: 'text-purple-400' },
    auction_near: { icon: 'schedule', color: 'orange', bgColor: 'bg-orange-500/10', textColor: 'text-orange-400' },
  }

  return configs[alertType] || configs.status_change
}

/**
 * Get quality score config
 */
export function getQualityScoreConfig(score: number) {
  if (score >= 90) {
    return {
      label: 'Excellent',
      color: 'green',
      bgColor: 'bg-green-500/10',
      textColor: 'text-green-400',
      icon: 'check_circle',
    }
  }

  if (score >= 70) {
    return {
      label: 'Good',
      color: 'blue',
      bgColor: 'bg-blue-500/10',
      textColor: 'text-blue-400',
      icon: 'thumb_up',
    }
  }

  if (score >= 50) {
    return {
      label: 'Fair',
      color: 'yellow',
      bgColor: 'bg-yellow-500/10',
      textColor: 'text-yellow-400',
      icon: 'warning',
    }
  }

  return {
    label: 'Poor',
    color: 'red',
    bgColor: 'bg-red-500/10',
    textColor: 'text-red-400',
    icon: 'error',
  }
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}

/**
 * Get initials from name
 */
export function getInitials(name: string): string {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

/**
 * Calculate days until date
 */
export function daysUntil(date: string | undefined | null): number | null {
  if (!date) return null
  try {
    const now = new Date()
    const target = new Date(date)
    const diffMs = target.getTime() - now.getTime()
    return Math.ceil(diffMs / 86400000)
  } catch {
    return null
  }
}
