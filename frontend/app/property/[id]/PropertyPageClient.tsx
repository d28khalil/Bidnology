'use client'

import { PropertyDetailModal } from '@/components/PropertyDetailModal'
import { transformPropertyToRow } from '@/lib/hooks/useProperties'
import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

interface PropertyPageClientProps {
  property: any
}

export function PropertyPageClient({ property }: PropertyPageClientProps) {
  const router = useRouter()
  const [isModalOpen, setIsModalOpen] = useState(true)

  // Transform property to match the modal's expected format
  const transformedProperty = transformPropertyToRow(property)

  return (
    <div className="min-h-screen bg-background-dark">
      {/* Header */}
      <div className="bg-white dark:bg-surface-dark border-b border-gray-200 dark:border-border-dark">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-4">
          <Link
            href="/"
            className="p-2 hover:bg-gray-100 dark:hover:bg-white/5 rounded-lg transition-colors"
          >
            <span className="material-symbols-outlined text-gray-600 dark:text-gray-400">
              arrow_back
            </span>
          </Link>
          <div>
            <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
              Property Details
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {property.property_address}, {property.city}, {property.state}
            </p>
          </div>
        </div>
      </div>

      {/* Property Modal rendered in place */}
      {isModalOpen && (
        <PropertyDetailModal
          property={transformedProperty}
          isOpen={isModalOpen}
          onClose={() => {
            setIsModalOpen(false)
            // Redirect back to home after closing
            router.replace('/')
          }}
        />
      )}
    </div>
  )
}
