'use client'

import { useState } from 'react'

interface PropertyListItemProps {
  property: {
    id: string
    address: string
    city: string
    state: string
    zip: string
    image: string
    auctionDate: string
    status?: string
    beds?: number
    baths?: number
    sqft?: number
    openingBid: number
    estimatedARV: number
    spread: number
    aiStatus: 'excellent' | 'good' | 'warning' | 'caution'
  }
  isSelected: boolean
  onSelect: () => void
}

function PropertyListItem({ property, isSelected, onSelect }: PropertyListItemProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  const getSpreadColor = () => {
    if (property.spread >= 30) return 'text-emerald-400'
    if (property.spread >= 20) return 'text-yellow-400'
    if (property.spread >= 10) return 'text-orange-400'
    return 'text-red-400'
  }

  const spreadColor = getSpreadColor()

  return (
    <div
      onClick={onSelect}
      className={`p-4 border-b border-border-dark cursor-pointer transition-all hover:bg-white/[0.02] ${
        isSelected ? 'bg-primary/10 border-l-4 border-l-primary' : 'border-l-4 border-l-transparent'
      }`}
    >
      <div className="flex items-start gap-4">
        {/* Thumbnail */}
        <div
          className="w-20 h-16 rounded bg-cover bg-center shrink-0"
          style={{ backgroundImage: `url('${property.image}')` }}
        />

        {/* Info */}
        <div className="flex-1 min-w-0">
          <h4 className="text-white font-medium text-sm leading-tight truncate">{property.address}</h4>
          <p className="text-gray-500 text-xs mt-1">
            {property.city}, {property.state} {property.zip}
          </p>
        </div>

        {/* Quick Stats */}
        <div className="flex items-center gap-4 text-sm">
          <div className="text-right">
            <div className="text-gray-500 text-xs">Bid</div>
            <div className="text-white font-medium">{formatCurrency(property.openingBid)}</div>
          </div>
          <div className="text-right">
            <div className="text-gray-500 text-xs">ARV</div>
            <div className="text-gray-300">{formatCurrency(property.estimatedARV)}</div>
          </div>
          <div className="text-right w-16">
            <div className="text-gray-500 text-xs">Spread</div>
            <div className={`${spreadColor} font-bold`}>+{property.spread.toFixed(1)}%</div>
          </div>
        </div>
      </div>
    </div>
  )
}

interface PropertySplitViewProps {
  properties: Array<{
    id: string
    address: string
    city: string
    state: string
    zip: string
    image: string
    auctionDate: string
    status?: string
    beds?: number
    baths?: number
    sqft?: number
    openingBid: number
    approxUpset?: number
    approxJudgment?: number
    estimatedARV: number
    spread: number
    aiConfidence: number
    aiStatus: 'excellent' | 'good' | 'warning' | 'caution'
    taxHistoryCount?: number
    taxHistoryData?: any[]
    comparablesCount?: number
    comparablesData?: any[]
    skipTraceData?: any
    streetViewImages?: any
    yearBuilt?: number
    lotSize?: number
    lastSoldDate?: string
    lastSoldPrice?: number
    zestimateLow?: number
    zestimateHigh?: number
    rentZestimate?: number
    climateRisk?: any
    ownerInfo?: any
  }>
}

export function PropertySplitView({ properties }: PropertySplitViewProps) {
  const [selectedId, setSelectedId] = useState<string | null>(properties[0]?.id || null)

  const selectedProperty = properties.find(p => p.id === selectedId)

  if (!selectedProperty) {
    return (
      <div className="bg-surface-dark border border-border-dark rounded-lg p-12 text-center">
        <p className="text-gray-400">No properties to display</p>
      </div>
    )
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  const getSpreadConfig = () => {
    if (selectedProperty.spread >= 40) return { color: 'text-emerald-400', bgColor: 'bg-emerald-500', label: 'Excellent Deal' }
    if (selectedProperty.spread >= 30) return { color: 'text-emerald-400', bgColor: 'bg-emerald-500/80', label: 'Hot Deal' }
    if (selectedProperty.spread >= 20) return { color: 'text-yellow-400', bgColor: 'bg-yellow-500/80', label: 'Good Spread' }
    if (selectedProperty.spread >= 10) return { color: 'text-orange-400', bgColor: 'bg-orange-500/80', label: 'Moderate' }
    return { color: 'text-red-400', bgColor: 'bg-red-500/80', label: 'Low Spread' }
  }

  const spreadConfig = getSpreadConfig()

  const potentialEquity = selectedProperty.estimatedARV - selectedProperty.openingBid

  return (
    <div className="bg-surface-dark border border-border-dark rounded-lg overflow-hidden shadow-xl flex h-[calc(100vh-240px)]">
      {/* Left Panel - Property List */}
      <div className="w-[400px] border-r border-border-dark flex flex-col bg-background-dark">
        <div className="p-4 border-b border-border-dark">
          <h3 className="text-white font-semibold">Properties ({properties.length})</h3>
        </div>
        <div className="flex-1 overflow-y-auto">
          {properties.map((property) => (
            <PropertyListItem
              key={property.id}
              property={property}
              isSelected={selectedId === property.id}
              onSelect={() => setSelectedId(property.id)}
            />
          ))}
        </div>
      </div>

      {/* Right Panel - Property Details */}
      <div className="flex-1 overflow-y-auto">
        {/* Hero Image with Badges */}
        <div className="relative h-64 overflow-hidden">
          <img
            src={selectedProperty.image}
            alt={selectedProperty.address}
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />

          {/* Top Badges */}
          <div className="absolute top-4 left-4 flex gap-2">
            {selectedProperty.status && (
              <span className="px-3 py-1 rounded-lg bg-blue-500/20 text-blue-400 text-xs font-semibold border border-blue-500/20 backdrop-blur-sm">
                {selectedProperty.status}
              </span>
            )}
            {selectedProperty.spread >= 30 && (
              <span className="px-3 py-1 rounded-lg bg-gradient-to-r from-emerald-500 to-emerald-600 text-white text-xs font-bold flex items-center gap-1">
                <span className="material-symbols-outlined text-[14px]">local_fire_department</span>
                {spreadConfig.label}
              </span>
            )}
          </div>

          {/* Bottom Info */}
          <div className="absolute bottom-4 left-4 right-4">
            <h2 className="text-white text-xl font-bold">{selectedProperty.address}</h2>
            <p className="text-gray-300 text-sm mt-1">
              {selectedProperty.city}, {selectedProperty.state} {selectedProperty.zip}
            </p>
          </div>
        </div>

        {/* Details Content */}
        <div className="p-6 space-y-6">
          {/* Key Financials */}
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-background-dark border border-border-dark rounded-lg p-4">
              <div className="text-gray-500 text-xs mb-1">Opening Bid</div>
              <div className="text-white font-bold text-lg">{formatCurrency(selectedProperty.openingBid)}</div>
            </div>
            <div className="bg-background-dark border border-border-dark rounded-lg p-4">
              <div className="text-gray-500 text-xs mb-1">Est. ARV</div>
              <div className="text-gray-300 text-lg">{formatCurrency(selectedProperty.estimatedARV)}</div>
              {selectedProperty.zestimateLow && selectedProperty.zestimateHigh && (
                <div className="text-gray-500 text-xs mt-1">
                  {formatCurrency(selectedProperty.zestimateLow)} - {formatCurrency(selectedProperty.zestimateHigh)}
                </div>
              )}
            </div>
            <div className="bg-background-dark border border-border-dark rounded-lg p-4">
              <div className="text-gray-500 text-xs mb-1">Potential Equity</div>
              <div className="text-emerald-400 font-bold text-lg">{formatCurrency(potentialEquity)}</div>
            </div>
            <div className="bg-background-dark border border-border-dark rounded-lg p-4">
              <div className="text-gray-500 text-xs mb-1">Spread</div>
              <div className={`${spreadConfig.color} font-bold text-lg`}>+{selectedProperty.spread.toFixed(1)}%</div>
            </div>
          </div>

          {/* Property Specs */}
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-background-dark border border-border-dark rounded-lg p-3">
              <div className="flex items-center gap-2 text-gray-400 text-xs mb-1">
                <span className="material-symbols-outlined text-[16px]">bed</span>
                Bedrooms
              </div>
              <div className="text-white font-semibold">{selectedProperty.beds ?? '-'}</div>
            </div>
            <div className="bg-background-dark border border-border-dark rounded-lg p-3">
              <div className="flex items-center gap-2 text-gray-400 text-xs mb-1">
                <span className="material-symbols-outlined text-[16px]">bathtub</span>
                Bathrooms
              </div>
              <div className="text-white font-semibold">{selectedProperty.baths ?? '-'}</div>
            </div>
            <div className="bg-background-dark border border-border-dark rounded-lg p-3">
              <div className="flex items-center gap-2 text-gray-400 text-xs mb-1">
                <span className="material-symbols-outlined text-[16px]">square_foot</span>
                Sq Ft
              </div>
              <div className="text-white font-semibold">{selectedProperty.sqft?.toLocaleString() ?? '-'}</div>
            </div>
            <div className="bg-background-dark border border-border-dark rounded-lg p-3">
              <div className="flex items-center gap-2 text-gray-400 text-xs mb-1">
                <span className="material-symbols-outlined text-[16px]">calendar_today</span>
                Year Built
              </div>
              <div className="text-white font-semibold">{selectedProperty.yearBuilt ?? '-'}</div>
            </div>
          </div>

          {/* Additional Financial Info */}
          <div className="grid grid-cols-3 gap-4">
            {selectedProperty.rentZestimate && (
              <div className="bg-background-dark border border-border-dark rounded-lg p-3">
                <div className="flex items-center gap-2 text-gray-400 text-xs mb-1">
                  <span className="material-symbols-outlined text-[16px]">payments</span>
                  Rent Estimate
                </div>
                <div className="text-white font-semibold">{formatCurrency(selectedProperty.rentZestimate)}/mo</div>
              </div>
            )}
            {selectedProperty.lastSoldPrice && (
              <div className="bg-background-dark border border-border-dark rounded-lg p-3">
                <div className="flex items-center gap-2 text-gray-400 text-xs mb-1">
                  <span className="material-symbols-outlined text-[16px]">sell</span>
                  Last Sold
                </div>
                <div className="text-white font-semibold">{formatCurrency(selectedProperty.lastSoldPrice)}</div>
                {selectedProperty.lastSoldDate && (
                  <div className="text-gray-500 text-xs">{selectedProperty.lastSoldDate}</div>
                )}
              </div>
            )}
            {selectedProperty.lotSize && (
              <div className="bg-background-dark border border-border-dark rounded-lg p-3">
                <div className="flex items-center gap-2 text-gray-400 text-xs mb-1">
                  <span className="material-symbols-outlined text-[16px]">landscape</span>
                  Lot Size
                </div>
                <div className="text-white font-semibold">{selectedProperty.lotSize.toLocaleString()} sqft</div>
              </div>
            )}
          </div>

          {/* Enrichment Data Summary */}
          <div className="space-y-3">
            <h3 className="text-white font-semibold">Enrichment Data</h3>
            <div className="flex flex-wrap gap-2">
              {(selectedProperty.taxHistoryCount ?? 0) > 0 && (
                <span className="px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 text-sm border border-emerald-500/20">
                  Tax History ({selectedProperty.taxHistoryCount ?? 0} yr)
                </span>
              )}
              {selectedProperty.comparablesCount && selectedProperty.comparablesCount > 0 && (
                <span className="px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 text-sm border border-emerald-500/20">
                  {selectedProperty.comparablesCount} Comps
                </span>
              )}
              {selectedProperty.skipTraceData && (
                <span className="px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 text-sm border border-emerald-500/20">
                  Skip Trace ✓
                </span>
              )}
              {selectedProperty.streetViewImages && (
                <span className="px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 text-sm border border-emerald-500/20">
                  Street View ✓
                </span>
              )}
            </div>
          </div>

          {/* Climate Risk (if available) */}
          {selectedProperty.climateRisk && (
            <div className="space-y-3">
              <h3 className="text-white font-semibold">Climate Risk</h3>
              <div className="grid grid-cols-3 gap-3">
                {selectedProperty.climateRisk.flood !== undefined && (
                  <div className="bg-background-dark border border-border-dark rounded-lg p-3">
                    <div className="flex items-center gap-2 text-gray-400 text-xs mb-1">
                      <span className="material-symbols-outlined text-[16px]">water</span>
                      Flood Risk
                    </div>
                    <div className={`font-semibold ${
                      selectedProperty.climateRisk.flood >= 80 ? 'text-red-400' :
                      selectedProperty.climateRisk.flood >= 50 ? 'text-orange-400' :
                      'text-emerald-400'
                    }`}>
                      {selectedProperty.climateRisk.flood}/100
                    </div>
                  </div>
                )}
                {selectedProperty.climateRisk.fire !== undefined && (
                  <div className="bg-background-dark border border-border-dark rounded-lg p-3">
                    <div className="flex items-center gap-2 text-gray-400 text-xs mb-1">
                      <span className="material-symbols-outlined text-[16px]">local_fire_department</span>
                      Fire Risk
                    </div>
                    <div className={`font-semibold ${
                      selectedProperty.climateRisk.fire >= 80 ? 'text-red-400' :
                      selectedProperty.climateRisk.fire >= 50 ? 'text-orange-400' :
                      'text-emerald-400'
                    }`}>
                      {selectedProperty.climateRisk.fire}/100
                    </div>
                  </div>
                )}
                {selectedProperty.climateRisk.storm !== undefined && (
                  <div className="bg-background-dark border border-border-dark rounded-lg p-3">
                    <div className="flex items-center gap-2 text-gray-400 text-xs mb-1">
                      <span className="material-symbols-outlined text-[16px]">thunderstorm</span>
                      Storm Risk
                    </div>
                    <div className={`font-semibold ${
                      selectedProperty.climateRisk.storm >= 80 ? 'text-red-400' :
                      selectedProperty.climateRisk.storm >= 50 ? 'text-orange-400' :
                      'text-emerald-400'
                    }`}>
                      {selectedProperty.climateRisk.storm}/100
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Owner Info (if available) */}
          {selectedProperty.ownerInfo && (
            <div className="space-y-3">
              <h3 className="text-white font-semibold">Owner Information</h3>
              <div className="bg-background-dark border border-border-dark rounded-lg p-4">
                <div className="text-white">{selectedProperty.ownerInfo.name || 'N/A'}</div>
                {selectedProperty.ownerInfo.agent && (
                  <div className="text-gray-400 text-sm mt-1">Agent: {selectedProperty.ownerInfo.agent}</div>
                )}
              </div>
            </div>
          )}

          {/* Auction Details */}
          <div className="space-y-3">
            <h3 className="text-white font-semibold">Auction Details</h3>
            <div className="bg-background-dark border border-border-dark rounded-lg p-4 space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-400">Auction Date</span>
                <span className="text-white">{selectedProperty.auctionDate}</span>
              </div>
              {selectedProperty.approxUpset && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Approx Upset</span>
                  <span className="text-white">{formatCurrency(selectedProperty.approxUpset)}</span>
                </div>
              )}
              {selectedProperty.approxJudgment && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Approx Judgment</span>
                  <span className="text-white">{formatCurrency(selectedProperty.approxJudgment)}</span>
                </div>
              )}
            </div>
          </div>

          {/* AI Confidence */}
          <div className="pt-2">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400 text-sm">AI Confidence Score</span>
              <span className="text-white font-semibold">{selectedProperty.aiConfidence}</span>
            </div>
            <div className="w-full bg-gray-800 h-2 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  selectedProperty.aiConfidence >= 85 ? 'bg-gradient-to-r from-emerald-500 to-emerald-400' :
                  selectedProperty.aiConfidence >= 70 ? 'bg-gradient-to-r from-yellow-500 to-yellow-400' :
                  'bg-gradient-to-r from-red-500 to-red-400'
                }`}
                style={{ width: `${selectedProperty.aiConfidence}%` }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
