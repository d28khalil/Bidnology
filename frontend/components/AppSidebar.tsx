'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useEffect, useRef } from 'react'

const navItems = [
  { href: '/', label: 'Live Feed', icon: 'table_chart', activePattern: '^/$' },
  { href: '/auction-history', label: 'Auction History', icon: 'history', activePattern: '^/auction-history' },
]

interface AppSidebarProps {
  isMobileMenuOpen?: boolean
  onMobileMenuClose?: () => void
}

export function AppSidebar({ isMobileMenuOpen = false, onMobileMenuClose }: AppSidebarProps) {
  const pathname = usePathname()
  const previousPathname = useRef(pathname)

  const isActive = (pattern: string) => {
    return new RegExp(pattern).test(pathname)
  }

  // Close mobile menu when route changes (but not on initial render)
  useEffect(() => {
    if (previousPathname.current !== pathname && isMobileMenuOpen) {
      onMobileMenuClose?.()
    }
    previousPathname.current = pathname
  }, [pathname, isMobileMenuOpen])

  return (
    <>
      {/* Mobile Overlay */}
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onMobileMenuClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed lg:sticky inset-y-0 left-0 z-50
          h-screen w-full lg:w-20 xl:w-64
          flex flex-col
          border-r border-gray-200 dark:border-border-dark
          bg-white dark:bg-background-dark
          shrink-0
          transition-transform duration-300 ease-in-out
          ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        {/* Logo */}
        <div className="h-16 flex items-center justify-between lg:justify-center xl:justify-start xl:px-6 border-b border-gray-200 dark:border-border-dark shrink-0 px-4">
          <div className="flex items-center gap-2 text-primary">
            <span className="material-symbols-outlined text-3xl">token</span>
            <span className="text-xl font-bold tracking-tight lg:hidden xl:block text-gray-900 dark:text-white">
              Bidnology
            </span>
          </div>
          {/* Close button - mobile only */}
          <button
            onClick={onMobileMenuClose}
            className="lg:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-white/5 transition-colors"
            aria-label="Close menu"
          >
            <span className="material-symbols-outlined text-gray-600 dark:text-gray-400 text-[24px]">close</span>
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-6 px-2 xl:px-4 gap-2 flex flex-col">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => onMobileMenuClose?.()}
              className={`flex items-center gap-3 px-3 py-3 rounded-lg transition-colors group ${
                isActive(item.activePattern)
                  ? 'bg-primary/20 text-primary border border-primary/30'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/5 border border-transparent'
              }`}
            >
              <span className="material-symbols-outlined text-[24px]">{item.icon}</span>
              <span className="text-sm font-medium lg:hidden xl:block">{item.label}</span>
            </Link>
          ))}
        </nav>
      </aside>
    </>
  )
}
