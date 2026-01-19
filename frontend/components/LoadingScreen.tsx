'use client'

import { useEffect, useState } from 'react'

interface LoadingScreenProps {
  onComplete?: () => void
  duration?: number
}

export function LoadingScreen({ onComplete, duration = 2500 }: LoadingScreenProps) {
  const [progress, setProgress] = useState(0)
  const [pulse, setPulse] = useState(0)
  const [orbit, setOrbit] = useState(0)

  useEffect(() => {
    // Animate progress
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(progressInterval)
          setTimeout(() => onComplete?.(), 300)
          return 100
        }
        return prev + Math.random() * 15
      })
    }, 200)

    // Animate pulse effect
    const pulseInterval = setInterval(() => {
      setPulse((prev) => (prev + 1) % 360)
    }, 16)

    // Animate orbit
    const orbitInterval = setInterval(() => {
      setOrbit((prev) => (prev + 2) % 360)
    }, 16)

    return () => {
      clearInterval(progressInterval)
      clearInterval(pulseInterval)
      clearInterval(orbitInterval)
    }
  }, [onComplete])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#0F1621] overflow-hidden">
      {/* Animated background grid */}
      <div
        className="absolute inset-0 opacity-20"
        style={{
          backgroundImage: `
            linear-gradient(rgba(43, 108, 238, 0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(43, 108, 238, 0.1) 1px, transparent 1px)
          `,
          backgroundSize: '50px 50px',
          animation: 'gridMove 20s linear infinite',
        }}
      />

      {/* Floating particles */}
      {[...Array(20)].map((_, i) => (
        <div
          key={i}
          className="absolute w-1 h-1 bg-primary rounded-full opacity-60"
          style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
            animation: `float ${3 + Math.random() * 4}s ease-in-out infinite`,
            animationDelay: `${Math.random() * 2}s`,
          }}
        />
      ))}

      {/* Main content */}
      <div className="relative z-10 flex flex-col items-center gap-8">
        {/* Central logo with effects */}
        <div className="relative">
          {/* Outer rotating ring */}
          <div
            className="absolute inset-0 -m-8 border-2 border-primary/30 rounded-full"
            style={{
              transform: `rotate(${orbit}deg)`,
              transition: 'transform 0.1s linear',
            }}
          />

          {/* Middle rotating ring (opposite direction) */}
          <div
            className="absolute inset-0 -m-6 border border-dashed border-primary/50 rounded-full"
            style={{
              transform: `rotate(${-orbit * 1.5}deg)`,
              transition: 'transform 0.1s linear',
            }}
          />

          {/* Inner pulsing ring */}
          <div
            className="absolute inset-0 -m-4 border border-primary/70 rounded-full"
            style={{
              transform: `scale(${1 + Math.sin(pulse * Math.PI / 180) * 0.1})`,
              transition: 'transform 0.1s ease-out',
            }}
          />

          {/* Logo with glow */}
          <div className="relative flex items-center justify-center">
            <div
              className="absolute inset-0 bg-primary/20 blur-3xl rounded-full"
              style={{
                transform: `scale(${1 + Math.sin(pulse * Math.PI / 180) * 0.3})`,
                transition: 'transform 0.1s ease-out',
              }}
            />
            <span
              className="material-symbols-outlined text-7xl text-primary relative z-10"
              style={{
                transform: `scale(${1 + Math.sin(pulse * Math.PI / 180) * 0.1})`,
                transition: 'transform 0.1s ease-out',
              }}
            >
              token
            </span>
          </div>
        </div>

        {/* Bidnology text with reveal effect */}
        <div className="relative overflow-hidden">
          <div
            className="text-5xl font-bold tracking-tight text-white flex items-center gap-3"
            style={{
              opacity: Math.min(progress / 30, 1),
              transform: `translateY(${(100 - progress) * 0.5}px)`,
              transition: 'all 0.5s ease-out',
            }}
          >
            <span>Bidnology</span>
          </div>
        </div>

        {/* Progress bar */}
        <div className="w-64 space-y-2">
          <div className="h-1 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-primary via-purple-500 to-primary rounded-full transition-all duration-300 relative"
              style={{ width: `${progress}%` }}
            >
              <div
                className="absolute inset-0 bg-white/30 animate-shimmer"
                style={{
                  background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent)',
                  animation: 'shimmer 1.5s infinite',
                }}
              />
            </div>
          </div>
          <div className="flex justify-between text-xs text-gray-500">
            <span>Loading</span>
            <span>{Math.round(progress)}%</span>
          </div>
        </div>

        {/* Status messages */}
        <div
          className="text-sm text-gray-400 h-6"
          style={{
            opacity: progress > 50 ? 1 : 0,
            transition: 'opacity 0.5s ease-in-out',
          }}
        >
          {progress > 80 ? 'Almost there...' : progress > 50 ? 'Preparing your dashboard...' : 'Authenticating...'}
        </div>
      </div>

      {/* Scan line effect */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: 'linear-gradient(180deg, transparent 0%, rgba(43, 108, 238, 0.03) 50%, transparent 100%)',
          animation: 'scan 3s linear infinite',
        }}
      />

      {/* CSS animations */}
      <style jsx>{`
        @keyframes gridMove {
          0% {
            transform: translate(0, 0);
          }
          100% {
            transform: translate(50px, 50px);
          }
        }

        @keyframes float {
          0%, 100% {
            transform: translate(0, 0) scale(1);
            opacity: 0.6;
          }
          50% {
            transform: translate(${Math.random() * 100 - 50}px, ${Math.random() * 100 - 50}px) scale(1.5);
            opacity: 1;
          }
        }

        @keyframes shimmer {
          0% {
            transform: translateX(-100%);
          }
          100% {
            transform: translateX(100%);
          }
        }

        @keyframes scan {
          0% {
            transform: translateY(-100%);
          }
          100% {
            transform: translateY(100vh);
          }
        }
      `}</style>
    </div>
  )
}
