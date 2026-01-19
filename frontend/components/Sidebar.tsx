'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const navItems = [
  {
    section: 'Intelligence',
    items: [
      { href: '/', label: 'Live Feed', icon: 'table_chart', activePattern: '^/$' },
      { href: '/pipeline', label: 'Deal Pipeline', icon: 'view_kanban', activePattern: '^/pipeline' },
      { href: '/analytics', label: 'Analytics', icon: 'analytics', activePattern: '^/analytics' },
    ],
  },
  {
    section: 'System',
    items: [
      { href: '/documents', label: 'Documents', icon: 'folder_shared', activePattern: '^/documents' },
      { href: '/settings', label: 'Configuration', icon: 'settings_applications', activePattern: '^/settings' },
    ],
  },
]

export function Sidebar() {
  const pathname = usePathname()

  const isActive = (pattern: string) => {
    return new RegExp(pattern).test(pathname)
  }

  return (
    <aside className="w-20 lg:w-64 flex flex-col border-r border-border-dark bg-background-dark shrink-0 sticky top-0 h-screen overflow-hidden transition-all duration-300">
      {/* Logo */}
      <div className="h-16 flex items-center justify-center lg:justify-start lg:px-6 border-b border-border-dark">
        <div className="flex items-center gap-2 text-primary">
          <span className="material-symbols-outlined text-3xl">token</span>
          <span className="text-xl font-bold tracking-tight hidden lg:block text-white">
            Bidnology
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-6 px-2 lg:px-4 gap-2 flex flex-col">
        {navItems.map((section) => (
          <div key={section.section}>
            <div className="lg:px-2 pb-2">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider hidden lg:block">
                {section.section}
              </p>
            </div>
            {section.items.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors group ${
                  isActive(item.activePattern)
                    ? 'bg-primary/20 text-primary'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <span className="material-symbols-outlined">{item.icon}</span>
                <span className="text-sm font-medium hidden lg:block">{item.label}</span>
              </Link>
            ))}
          </div>
        ))}
      </nav>

      {/* User Profile */}
      <div className="p-4 border-t border-border-dark">
        <div className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 cursor-pointer">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-primary to-purple-500 flex items-center justify-center text-white">
            <span className="material-symbols-outlined text-[18px]">person</span>
          </div>
          <div className="hidden lg:block">
            <p className="text-sm font-medium text-white">User</p>
            <p className="text-xs text-gray-500">Admin</p>
          </div>
        </div>
      </div>
    </aside>
  )
}
