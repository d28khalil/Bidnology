'use client'

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useUser } from '@/contexts/UserContext'
import { useTheme } from '@/contexts/ThemeContext'

interface HeaderProps {
  searchQuery?: string
  onSearchChange?: (query: string) => void
  onMobileMenuToggle?: () => void
}

export function Header({ searchQuery: externalSearchQuery, onSearchChange, onMobileMenuToggle }: HeaderProps) {
  // Use internal state if no external state provided (for standalone usage)
  const [internalSearchQuery, setInternalSearchQuery] = useState('')
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false)
  const userMenuRef = useRef<HTMLDivElement>(null)
  const router = useRouter()
  const { user, userId, isAuthenticated, isLoaded, signOut } = useUser()
  const { theme, toggleTheme } = useTheme()

  // Get the base URL for redirects
  const baseUrl = typeof window !== 'undefined' ? window.location.origin : ''
  const signInUrl = `https://bidnology.com/login?redirect_url=${encodeURIComponent(baseUrl + '/')}`
  const signUpUrl = `https://bidnology.com/signup?redirect_url=${encodeURIComponent(baseUrl + '/')}`

  const searchQuery = externalSearchQuery ?? internalSearchQuery
  const setSearchQuery = onSearchChange ?? setInternalSearchQuery

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setIsUserMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSignOut = async () => {
    await signOut()
    // After sign out, Clerk will redirect back to the home page automatically
    router.push('/')
  }

  // Get user email or display name - only when authenticated
  const userDisplay = isAuthenticated && user?.email ? user.email.split('@')[0] : null
  const userInitial = userDisplay ? userDisplay.charAt(0).toUpperCase() : null

  return (
    <header className="h-16 flex items-center justify-between px-4 lg:px-6 border-b border-gray-200 dark:border-border-dark bg-white/95 dark:bg-background-dark/95 backdrop-blur z-20">
      {/* Left: Mobile Menu Button + Search */}
      <div className="flex items-center gap-3 flex-1">
        {/* Mobile Menu Button */}
        {onMobileMenuToggle && (
          <button
            onClick={onMobileMenuToggle}
            className="lg:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-white/5 transition-colors"
            aria-label="Toggle menu"
          >
            <span className="material-symbols-outlined text-gray-600 dark:text-gray-400 text-[24px]">menu</span>
          </button>
        )}

        {/* Search - centered on desktop, takes remaining space on mobile */}
        <div className="relative group w-full max-w-xl">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400 group-focus-within:text-primary transition-colors">
            <span className="material-symbols-outlined text-[20px]">search</span>
          </div>
          <input
            type="text"
            placeholder="Search address"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-none rounded-lg leading-5 bg-white dark:bg-surface-dark text-gray-900 dark:text-gray-300 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-primary focus:bg-gray-50 dark:focus:bg-background-dark sm:text-sm transition-all shadow-sm dark:shadow-inner"
          />
        </div>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-3">
        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-white/5 cursor-pointer transition-colors group"
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
          <span className="material-symbols-outlined text-gray-500 dark:text-gray-400 group-hover:text-primary dark:group-hover:text-primary text-[20px] transition-colors">
            {theme === 'dark' ? 'light_mode' : 'dark_mode'}
          </span>
        </button>
        {!isLoaded ? (
          /* Loading state - small spinner */
          <div className="w-20 h-8 flex items-center justify-center">
            <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : isAuthenticated ? (
          /* User Profile */
          <div className="relative" ref={userMenuRef}>
            <button
              onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 cursor-pointer transition-colors"
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-primary to-purple-500 flex items-center justify-center text-white">
                {userInitial || <span className="material-symbols-outlined text-[18px]">person</span>}
              </div>
              <div className="hidden sm:block text-left">
                <p className="text-sm font-medium text-white">{userDisplay}</p>
              </div>
              <span className="material-symbols-outlined text-gray-400 text-[20px]">
                {isUserMenuOpen ? 'expand_less' : 'expand_more'}
              </span>
            </button>

            {/* User Dropdown Menu */}
            {isUserMenuOpen && (
              <div className="absolute right-0 top-full mt-2 w-48 bg-surface-dark border border-border-dark rounded-lg shadow-xl z-50">
                <div className="py-1">
                  <div className="px-4 py-2 border-b border-border-dark">
                    <p className="text-sm font-medium text-white">{user?.email}</p>
                  </div>
                  <button
                    onClick={handleSignOut}
                    className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-400 hover:text-white hover:bg-white/5 transition-colors text-left"
                  >
                    <span className="material-symbols-outlined text-[18px]">logout</span>
                    Sign Out
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          /* Sign In and Sign Up Buttons - redirect to Clerk Hosted Pages on custom domain */
          <div className="flex items-center gap-2">
            <a
              href={signInUrl}
              className="flex items-center gap-2 px-4 py-2 border border-primary text-primary rounded-lg hover:bg-primary/10 transition-colors font-medium text-sm"
            >
              <span className="material-symbols-outlined text-[18px]">login</span>
              <span className="hidden sm:inline">Sign In</span>
            </a>
            <a
              href={signUpUrl}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors font-medium text-sm"
            >
              <span className="material-symbols-outlined text-[18px]">person_add</span>
              <span className="hidden sm:inline">Sign Up</span>
            </a>
          </div>
        )}
      </div>
    </header>
  )
}
