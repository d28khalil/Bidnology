'use client'

import { createContext, useContext, ReactNode, useState, useEffect, useRef } from 'react'
import { useAuth, useUser as useClerkUser } from '@clerk/nextjs'
import { LoadingScreen } from '@/components/LoadingScreen'

interface UserContextValue {
  user: { email: string | null | undefined } | null
  userId: string | null
  isAuthenticated: boolean
  isLoaded: boolean
  signOut: () => Promise<void>
}

const UserContext = createContext<UserContextValue | undefined>(undefined)

const LOADING_SCREEN_SHOWN = 'loading_screen_shown'
const OAUTH_REDIRECT_KEY = 'clerk_oauth_redirect'

export function UserProvider({ children }: { children: ReactNode }) {
  const { isLoaded, userId, signOut } = useAuth()
  const { user } = useClerkUser()
  const [showLoading, setShowLoading] = useState(false)

  // Track if this is the first render and if userId was present on mount
  const hasMountedRef = useRef(false)
  const hadUserIdOnMountRef = useRef(false)

  useEffect(() => {
    const hasShownLoading = sessionStorage.getItem(LOADING_SCREEN_SHOWN)
    const hasOAuthRedirect = sessionStorage.getItem(OAUTH_REDIRECT_KEY) === 'true'

    // First mount - capture if user is already logged in
    if (!hasMountedRef.current) {
      hasMountedRef.current = true
      hadUserIdOnMountRef.current = !!userId
      console.log('First mount - userId present:', !!userId, 'hasOAuthRedirect:', hasOAuthRedirect)
    }

    // Show loading screen if:
    // 1. Returning from OAuth redirect (early loading screen was shown)
    // 2. Haven't shown loading screen this session
    if (hasOAuthRedirect && !hasShownLoading) {
      console.log('Taking over from early loading screen')
      sessionStorage.setItem(LOADING_SCREEN_SHOWN, 'true')
      sessionStorage.removeItem(OAUTH_REDIRECT_KEY)

      // Remove the early loading screen
      const earlyLoading = document.getElementById('early-loading-screen')
      if (earlyLoading) {
        earlyLoading.remove()
      }

      // Show React loading screen
      setShowLoading(true)

      // Hide after animation
      setTimeout(() => {
        setShowLoading(false)
      }, 2500)
    }
  }, [isLoaded, userId])

  // Clear flag when user signs out
  useEffect(() => {
    if (!userId && isLoaded) {
      sessionStorage.removeItem(LOADING_SCREEN_SHOWN)
      sessionStorage.removeItem(OAUTH_REDIRECT_KEY)
    }
  }, [userId, isLoaded])

  // Create user object
  const userObj = user
    ? {
        email: user.primaryEmailAddress?.emailAddress,
      }
    : null

  // Show loading screen only for fresh logins
  if (showLoading) {
    return <LoadingScreen onComplete={() => setShowLoading(false)} />
  }

  return (
    <UserContext.Provider
      value={{
        user: userObj,
        userId: userId ?? null,
        isAuthenticated: !!userId,
        isLoaded,
        signOut,
      }}
    >
      {children}
    </UserContext.Provider>
  )
}

export function useUser() {
  const context = useContext(UserContext)
  if (context === undefined) {
    throw new Error('useUser must be used within a UserProvider')
  }
  return context
}
