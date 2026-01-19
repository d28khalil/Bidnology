interface StatsCardProps {
  title: string
  value: string
  change: string
  changeType: 'positive' | 'negative' | 'neutral'
  progress: number
  icon: string
  color: string
  active?: boolean
  onClick?: () => void
}

export function StatsCard({ title, value, change, changeType, progress, icon, color, active, onClick }: StatsCardProps) {
  const colorClasses = {
    primary: 'text-primary bg-primary/10 border-primary/30',
    emerald: 'text-emerald-500 bg-emerald-500/10 border-emerald-500/30',
    orange: 'text-orange-500 bg-orange-500/10 border-orange-500/30',
  }

  const getChangeIcon = () => {
    if (changeType === 'positive') return 'trending_up'
    if (changeType === 'negative') return 'trending_down'
    return 'priority_high'
  }

  return (
    <div
      onClick={onClick}
      className={`bg-white dark:bg-surface-dark border rounded-lg p-5 flex flex-col gap-3 relative overflow-hidden group transition-all cursor-pointer ${
        active ? 'border-orange-500 shadow-lg shadow-orange-500/20' : 'border-gray-200 dark:border-border-dark hover:border-gray-400 dark:hover:border-gray-500'
      }`}
    >
      {/* Background Icon */}
      <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
        <span className={`material-symbols-outlined text-6xl ${colorClasses[color as keyof typeof colorClasses]?.split(' ')[0] || color}`}>
          {icon}
        </span>
      </div>

      {/* Active Indicator Badge */}
      {active && (
        <div className="absolute top-3 right-3 flex items-center gap-1 bg-orange-500/20 border border-orange-500/50 rounded-full px-2 py-1">
          <span className="material-symbols-outlined text-orange-500 text-sm">check_circle</span>
          <span className="text-orange-500 text-xs font-medium">Active</span>
        </div>
      )}

      {/* Title */}
      <p className="text-gray-600 dark:text-gray-400 text-sm font-medium">{title}</p>

      {/* Value and Change */}
      <div className="flex items-end gap-3">
        <p className="text-3xl font-bold text-gray-900 dark:text-white tracking-tight tabular-nums">{value}</p>
        <span className={`text-sm font-medium mb-1 px-1.5 py-0.5 rounded flex items-center ${
          changeType === 'positive' ? 'text-emerald-600 dark:text-emerald-500 bg-emerald-100 dark:bg-emerald-500/10' :
          changeType === 'negative' ? 'text-red-600 dark:text-red-500 bg-red-100 dark:bg-red-500/10' :
          'text-orange-600 dark:text-orange-400 bg-orange-100 dark:bg-orange-500/10'
        }`}>
          <span className="material-symbols-outlined text-sm mr-0.5">{getChangeIcon()}</span>
          {change}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-gray-200 dark:bg-gray-800 h-1 rounded-full mt-2 overflow-hidden">
        <div className={`${colorClasses[color as keyof typeof colorClasses]?.split(' ')[0]?.replace('text-', 'bg-') || 'bg-primary'} h-full rounded-full transition-all duration-500`} style={{ width: `${progress}%` }} />
      </div>

      {/* Hover hint for clickable cards - dark mode only */}
      {onClick && (
        <div className="absolute inset-0 dark:bg-white/5 opacity-0 dark:group-hover:opacity-100 transition-opacity pointer-events-none rounded-lg" />
      )}
    </div>
  )
}
