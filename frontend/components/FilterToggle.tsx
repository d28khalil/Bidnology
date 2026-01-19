'use client'

interface FilterToggleProps {
  label: string
  description: string
  enabled: boolean
  onChange: (enabled: boolean) => void
  icon?: string
}

export function FilterToggle({ label, description, enabled, onChange, icon }: FilterToggleProps) {
  return (
    <div className="flex items-center justify-between p-4 rounded-lg bg-surface-dark border border-border-dark hover:border-gray-600 transition-colors">
      <div className="flex items-center gap-3">
        {icon && (
          <span className="material-symbols-outlined text-primary text-[24px]">{icon}</span>
        )}
        <div>
          <p className="text-white font-medium text-sm">{label}</p>
          <p className="text-gray-500 text-xs">{description}</p>
        </div>
      </div>
      <button
        onClick={() => onChange(!enabled)}
        className={`relative w-12 h-6 rounded-full transition-colors ${
          enabled ? 'bg-primary' : 'bg-gray-700'
        }`}
      >
        <span
          className={`absolute top-1 left-1 w-4 h-4 rounded-full bg-white transition-transform ${
            enabled ? 'translate-x-6' : ''
          }`}
        />
      </button>
    </div>
  )
}
