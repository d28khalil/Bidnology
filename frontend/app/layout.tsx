import type { Metadata } from 'next'
import { Manrope } from 'next/font/google'
import './globals.css'
import { ClerkProvider } from '@clerk/nextjs'
import dynamic from 'next/dynamic'

// Dynamically import providers to avoid hydration issues
const UserProvider = dynamic(() => import('@/contexts/UserContext').then(mod => ({ default: mod.UserProvider })), { ssr: false })
const AppProvider = dynamic(() => import('@/contexts/AppContext').then(mod => ({ default: mod.AppProvider })), { ssr: false })
const ThemeProvider = dynamic(() => import('@/contexts/ThemeContext').then(mod => ({ default: mod.ThemeProvider })), { ssr: false })
const CopilotWidget = dynamic(() => import('@/components/CopilotWidget').then(mod => ({ default: mod.CopilotWidget })), { ssr: false })

const manrope = Manrope({
  subsets: ['latin'],
  variable: '--font-manrope',
  display: 'swap',
})

// Validate Clerk environment variables
const clerkPublishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
if (typeof window === 'undefined' && !clerkPublishableKey) {
  console.warn('NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY is not defined')
}

export const metadata: Metadata = {
  title: 'Bidnology - NJ Sheriff Sales Intelligence',
  description: 'AI-powered foreclosure property analysis and deal tracking',
  icons: {
    icon: '/icon.png',
    shortcut: '/icon.png',
    apple: '/icon.png',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
        />
        {/* Swetrix Analytics */}
        <script src="https://swetrix.org/swetrix.js" defer></script>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              document.addEventListener('DOMContentLoaded', function() {
                swetrix.init('TFhHpjO2KcN6', {
                  apiURL: 'https://swetrixapi-pow8g0000o4gk008swg4wss8.emprezario.com/log',
                })
                swetrix.trackViews()
              })
            `,
          }}
        />
        <noscript>
          <img
            src="https://swetrixapi-pow8g0000o4gk008swg4wss8.emprezario.com/log/noscript?pid=TFhHpjO2KcN6"
            alt=""
            referrerPolicy="no-referrer-when-downgrade"
          />
        </noscript>
      </head>
      <body className={`${manrope.variable} font-display antialiased`}>
        {/* Inline script to show loading screen immediately during OAuth redirect */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                // Check if we're returning from OAuth redirect
                const urlParams = new URLSearchParams(window.location.search);
                const hasRedirect = urlParams.has('redirected') ||
                                   urlParams.has('redirect_url') ||
                                   document.referrer.includes('clerk.com') ||
                                   document.referrer.includes('accounts.google.com');
                const freshLogin = sessionStorage.getItem('clerk_oauth_redirect');

                if (hasRedirect || freshLogin === 'true') {
                  // Set flag for React to pick up
                  sessionStorage.setItem('clerk_oauth_redirect', 'true');

                  // Immediately inject loading screen
                  const loadingHTML = \`
                    <div id="early-loading-screen" style="
                      position: fixed;
                      inset: 0;
                      z-index: 9999;
                      display: flex;
                      align-items: center;
                      justify-content: center;
                      background: #0F1621;
                      font-family: 'Manrope', sans-serif;
                    ">
                      <div style="position: relative; z-index: 10; display: flex; flex-direction: column; align-items: center; gap: 2rem;">
                        <div style="position: relative;">
                          <div style="position: absolute; inset: -2rem; border: 2px solid rgba(43, 108, 238, 0.3); border-radius: 50%; animation: rotate 2s linear infinite;"></div>
                          <div style="position: absolute; inset: -1.5rem; border: 1px dashed rgba(43, 108, 238, 0.5); border-radius: 50%; animation: rotate 1.5s linear infinite reverse;"></div>
                          <div style="display: flex; align-items: center; justify-content: center;">
                            <span class="material-symbols-outlined" style="font-size: 4rem; color: rgb(43, 108, 238);">token</span>
                          </div>
                        </div>
                        <div style="font-size: 2.5rem; font-weight: bold; color: white;">Bidnology</div>
                        <div style="width: 16rem; height: 0.25rem; background: #1f2937; border-radius: 9999px; overflow: hidden;">
                          <div id="loading-progress" style="
                            height: 100%;
                            background: linear-gradient(90deg, rgb(43, 108, 238), rgb(168, 85, 247), rgb(43, 108, 238));
                            background-size: 200% 100%;
                            border-radius: 9999px;
                            animation: progress 2s ease-in-out infinite;
                          "></div>
                        </div>
                        <div style="font-size: 0.875rem; color: rgb(156, 163, 175);">Authenticating...</div>
                      </div>
                      <style>
                        @keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
                        @keyframes progress { 0% { width: 0%; } 50% { width: 70%; } 100% { width: 100%; } }
                      </style>
                    </div>
                  \`;

                  document.body.insertAdjacentHTML('afterbegin', loadingHTML);
                }
              })();
            `,
          }}
        />
        <ClerkProvider
          publishableKey={process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ?? ''}
        >
          <ThemeProvider>
            <UserProvider>
              <AppProvider>{children}</AppProvider>
            </UserProvider>
          </ThemeProvider>
          <CopilotWidget />
        </ClerkProvider>
      </body>
    </html>
  )
}
