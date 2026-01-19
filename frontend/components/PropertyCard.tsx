interface PropertyCardProps {
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
    approxUpset?: number
    approxJudgment?: number
    zestimate?: number
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
    climateRisk?: {
      flood?: number
      fire?: number
      storm?: number
    }
    ownerInfo?: {
      name?: string
      agent?: string
    }
  }
  onOpenModal?: () => void
}

export function PropertyCard({ property, onOpenModal }: PropertyCardProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  // Check if spread is 0 due to missing data (no zestimate and no ARV)
  const hasNoPricingData = (!property.zestimate || property.zestimate === 0) && (!property.estimatedARV || property.estimatedARV === 0)

  // Get spread color for heat-map styling
  const getSpreadConfig = () => {
    if (hasNoPricingData) return { color: 'text-gray-400', bgColor: 'bg-gray-500/80', label: 'No Data', glow: '' }
    if (property.spread >= 40) return { color: 'text-emerald-300', bgColor: 'bg-emerald-500', label: 'Excellent', glow: 'shadow-emerald-500/50' }
    if (property.spread >= 30) return { color: 'text-emerald-400', bgColor: 'bg-emerald-500/90', label: 'Hot Deal', glow: 'shadow-emerald-500/30' }
    if (property.spread >= 20) return { color: 'text-yellow-400', bgColor: 'bg-yellow-500/80', label: 'Good', glow: 'shadow-yellow-500/20' }
    if (property.spread >= 10) return { color: 'text-orange-400', bgColor: 'bg-orange-500/80', label: 'Moderate', glow: '' }
    return { color: 'text-red-400', bgColor: 'bg-red-500/80', label: 'Low', glow: '' }
  }

  const spreadConfig = getSpreadConfig()
  const spreadDisplay = hasNoPricingData ? 'N/A' : `+${property.spread.toFixed(1)}%`

  // Get status styling
  const getStatusConfig = () => {
    const status = property.status?.toLowerCase() || 'scheduled'
    if (status === 'scheduled') return { label: 'Scheduled', color: 'text-blue-400', bgColor: 'bg-blue-500/10', borderColor: 'border-blue-500/30' }
    if (status === 'adjourned') return { label: 'Adjourned', color: 'text-yellow-400', bgColor: 'bg-yellow-500/10', borderColor: 'border-yellow-500/30' }
    if (status === 'sold') return { label: 'Sold', color: 'text-emerald-400', bgColor: 'bg-emerald-500/10', borderColor: 'border-emerald-500/30' }
    if (status === 'canceled' || status === 'cancelled') return { label: 'Canceled', color: 'text-red-400', bgColor: 'bg-red-500/10', borderColor: 'border-red-500/30' }
    return { label: status, color: 'text-gray-400', bgColor: 'bg-gray-500/10', borderColor: 'border-gray-500/30' }
  }

  const statusConfig = getStatusConfig()

  // Calculate tax appreciation (compare most recent to oldest)
  const getTaxAppreciation = () => {
    if (!property.taxHistoryData || property.taxHistoryData.length < 2) return null
    const sorted = [...property.taxHistoryData].sort((a, b) => {
      const aTime = typeof a.time === 'string' ? a.time : (a.time?.toString() || '')
      const bTime = typeof b.time === 'string' ? b.time : (b.time?.toString() || '')
      return aTime.localeCompare(bTime)
    })
    const oldest = sorted[0]?.tax?.assessment
    const newest = sorted[sorted.length - 1]?.tax?.assessment
    if (!oldest || !newest) return null
    const percentChange = ((newest - oldest) / oldest) * 100
    return {
      percent: percentChange.toFixed(1),
      isPositive: percentChange > 0,
      oldest,
      newest,
    }
  }

  const taxAppreciation = getTaxAppreciation()

  // Calculate average comp price
  const getCompStats = () => {
    if (!property.comparablesData || property.comparablesData.length === 0) return null
    const prices = property.comparablesData
      .map(c => c.price || c.unformattedPrice)
      .filter(p => p && typeof p === 'number')
    if (prices.length === 0) return null
    const avg = prices.reduce((sum, p) => sum + p, 0) / prices.length
    const min = Math.min(...prices)
    const max = Math.max(...prices)
    return { avg, min, max, count: prices.length }
  }

  const compStats = getCompStats()

  // Calculate potential equity
  const potentialEquity = property.estimatedARV - property.openingBid

  // Calculate days until auction
  const getDaysUntilAuction = () => {
    const auctionDate = new Date(property.auctionDate)
    const today = new Date()
    const diffTime = auctionDate.getTime() - today.getTime()
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    return diffDays
  }

  const daysUntil = getDaysUntilAuction()
  const isUrgent = daysUntil >= 0 && daysUntil <= 7

  return (
    <div
      onClick={onOpenModal}
      className="bg-surface-dark border border-border-dark rounded-xl overflow-hidden hover:border-primary/50 transition-all cursor-pointer group shadow-lg hover:shadow-primary/10 flex flex-col h-full"
    >
      {/* Image with Overlay Badges */}
      <div className="relative aspect-video overflow-hidden">
        <img
          src={property.image}
          alt={property.address}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
        />

        {/* Top Left - Status Badge */}
        <div className="absolute top-3 left-3 flex flex-col gap-2">
          <span className={`px-2.5 py-1 rounded-lg text-xs font-semibold ${statusConfig.color} ${statusConfig.bgColor} border ${statusConfig.borderColor} backdrop-blur-sm shadow-lg`}>
            {statusConfig.label}
          </span>
          {isUrgent && (
            <span className="px-2.5 py-1 rounded-lg text-xs font-bold bg-red-500 text-white border border-red-400 backdrop-blur-sm shadow-lg flex items-center gap-1">
              <span className="material-symbols-outlined text-[12px]">schedule</span>
              {daysUntil === 0 ? 'Today' : daysUntil === 1 ? 'Tomorrow' : `${daysUntil} days`}
            </span>
          )}
        </div>

        {/* Top Right - Spread Badge - More Prominent */}
        <div className="absolute top-3 right-3">
          <div className={`${spreadConfig.bgColor} ${spreadConfig.glow} shadow-xl backdrop-blur-sm px-3 py-2 rounded-lg border border-white/10`}>
            <div className="text-white/90 text-[10px] font-medium uppercase tracking-wider">Equity Spread</div>
            <div className={`text-2xl font-bold ${spreadConfig.color} leading-none`}>
              {spreadDisplay}
            </div>
            {!hasNoPricingData && property.spread >= 30 && (
              <div className="text-white/90 text-[10px] font-semibold mt-0.5 flex items-center gap-0.5">
                <span className="material-symbols-outlined text-[10px]">local_fire_department</span>
                {spreadConfig.label}
              </div>
            )}
          </div>
        </div>

        {/* Bottom - Quick Stats Bar */}
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 via-black/60 to-transparent p-4">
          <div className="flex items-center justify-between text-white">
            <div className="flex items-center gap-4 text-sm">
              {property.beds && (
                <span className="flex items-center gap-1">
                  <span className="material-symbols-outlined text-[16px] text-gray-300">bed</span>
                  {property.beds}
                </span>
              )}
              {property.baths && (
                <span className="flex items-center gap-1">
                  <span className="material-symbols-outlined text-[16px] text-gray-300">bathtub</span>
                  {property.baths}
                </span>
              )}
              {property.sqft && (
                <span className="flex items-center gap-1">
                  <span className="material-symbols-outlined text-[16px] text-gray-300">square_foot</span>
                  {property.sqft.toLocaleString()}
                </span>
              )}
            </div>
            <div className={`text-xs font-medium px-2 py-1 rounded ${isUrgent ? 'bg-red-500/80 text-white' : 'bg-black/50 text-gray-300'} backdrop-blur-sm border border-white/10`}>
              {property.auctionDate}
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4 flex-1 flex flex-col">
        {/* Address */}
        <div>
          <h3 className="text-white font-semibold text-base leading-tight group-hover:text-primary transition-colors">
            {property.address}
          </h3>
          <p className="text-gray-500 text-sm mt-1">
            {property.city}, {property.state} {property.zip}
          </p>
        </div>

        {/* Deal Analysis Section - Highlighted */}
        <div className="bg-gradient-to-br from-primary/5 to-background-dark border border-primary/20 rounded-xl p-4 space-y-3">
          <div className="flex items-center gap-2 text-primary text-xs font-semibold uppercase tracking-wider">
            <span className="material-symbols-outlined text-[16px]">analytics</span>
            Deal Analysis
          </div>

          {/* Main Metrics - 3 Column */}
          <div className="grid grid-cols-3 gap-3">
            {/* Opening Bid */}
            <div className="text-center">
              <div className="text-gray-500 text-[10px] uppercase tracking-wide mb-1">Opening Bid</div>
              <div className="text-white font-bold text-base">{formatCurrency(property.openingBid)}</div>
            </div>

            {/* ARV - Highlighted */}
            <div className="text-center bg-primary/10 rounded-lg py-2 px-1">
              <div className="text-primary text-[10px] uppercase tracking-wide mb-1 font-semibold">Est. ARV</div>
              <div className="text-primary font-bold text-lg">{formatCurrency(property.estimatedARV)}</div>
              {property.zestimateLow && property.zestimateHigh && (
                <div className="text-gray-500 text-[9px] mt-0.5">
                  {formatCurrency(property.zestimateLow)} - {formatCurrency(property.zestimateHigh)}
                </div>
              )}
            </div>

            {/* Potential Equity */}
            <div className="text-center">
              <div className="text-gray-500 text-[10px] uppercase tracking-wide mb-1">Equity</div>
              <div className={`font-bold text-base ${potentialEquity > 0 ? 'text-emerald-400' : 'text-gray-400'}`}>
                {formatCurrency(Math.abs(potentialEquity))}
              </div>
            </div>
          </div>

          {/* Additional Cost Basis */}
          {(property.approxUpset || property.approxJudgment) && (
            <div className="pt-2 border-t border-primary/10 flex items-center justify-between text-xs">
              <span className="text-gray-500">Cost Basis</span>
              <span className="text-gray-300">
                {formatCurrency(Math.max(property.approxUpset || 0, property.approxJudgment || 0, property.openingBid))}
              </span>
            </div>
          )}
        </div>

        {/* Property Specs Row */}
        {(property.beds || property.baths || property.sqft || property.yearBuilt) && (
          <div className="flex items-center justify-between bg-background-dark border border-border-dark rounded-lg px-3 py-2">
            <div className="flex items-center gap-3 text-sm text-gray-400">
              {property.beds !== undefined && (
                <span className="flex items-center gap-1">
                  <span className="material-symbols-outlined text-[16px]">bed</span>
                  <span className="text-white">{property.beds} bd</span>
                </span>
              )}
              {property.baths !== undefined && (
                <span className="flex items-center gap-1">
                  <span className="material-symbols-outlined text-[16px]">bathtub</span>
                  <span className="text-white">{property.baths} ba</span>
                </span>
              )}
              {property.sqft && (
                <span className="flex items-center gap-1">
                  <span className="material-symbols-outlined text-[16px]">square_foot</span>
                  <span className="text-white">{property.sqft.toLocaleString()}</span>
                </span>
              )}
              {property.yearBuilt && (
                <span className="flex items-center gap-1">
                  <span className="material-symbols-outlined text-[16px]">calendar_today</span>
                  <span className="text-white">{property.yearBuilt}</span>
                </span>
              )}
            </div>
          </div>
        )}

        {/* Additional Financial Info */}
        <div className="grid grid-cols-2 gap-2">
          {property.rentZestimate && (
            <div className="flex items-center justify-between bg-background-dark border border-border-dark rounded-lg px-3 py-2">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[16px] text-gray-500">payments</span>
                <span className="text-gray-400 text-xs">Rent Est.</span>
              </div>
              <span className="text-white text-sm font-semibold">{formatCurrency(property.rentZestimate)}/mo</span>
            </div>
          )}
          {property.lastSoldPrice && (
            <div className="flex items-center justify-between bg-background-dark border border-border-dark rounded-lg px-3 py-2">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[16px] text-gray-500">sell</span>
                <span className="text-gray-400 text-xs">Last Sold</span>
              </div>
              <div className="text-right">
                <div className="text-white text-sm font-semibold">{formatCurrency(property.lastSoldPrice)}</div>
                {property.lastSoldDate && (
                  <div className="text-gray-500 text-[10px]">{property.lastSoldDate}</div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Enrichment Data - Compact */}
        <div className="space-y-2">
          {/* Tax History Trend */}
          {taxAppreciation && (
            <div className={`flex items-center justify-between bg-background-dark border rounded-lg px-3 py-2 ${taxAppreciation.isPositive ? 'border-emerald-500/20' : 'border-red-500/20'}`}>
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[16px] text-gray-500">receipt_long</span>
                <span className="text-gray-400 text-xs">Tax Trend ({property.taxHistoryCount}y)</span>
              </div>
              <div className={`text-xs font-semibold flex items-center gap-1 ${taxAppreciation.isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
                <span className="material-symbols-outlined text-[14px]">
                  {taxAppreciation.isPositive ? 'trending_up' : 'trending_down'}
                </span>
                {taxAppreciation.isPositive ? '+' : ''}{taxAppreciation.percent}%
              </div>
            </div>
          )}

          {/* Comparables Summary */}
          {compStats && (
            <div className="flex items-center justify-between bg-background-dark border border-border-dark rounded-lg px-3 py-2">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[16px] text-gray-500">compare_arrows</span>
                <span className="text-gray-400 text-xs">{compStats.count} Comps</span>
              </div>
              <div className="text-white text-xs font-semibold">Avg: {formatCurrency(compStats.avg)}</div>
            </div>
          )}

          {/* Enrichment Status Badges - Compact */}
          <div className="flex items-center gap-1.5 flex-wrap">
            {(property.taxHistoryCount ?? 0) > 0 && (
              <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 text-[10px] font-medium border border-emerald-500/20">
                Tax ✓
              </span>
            )}
            {compStats && compStats.count > 0 && (
              <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 text-[10px] font-medium border border-emerald-500/20">
                Comps ✓
              </span>
            )}
            {property.skipTraceData && (
              <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 text-[10px] font-medium border border-emerald-500/20">
                Skip Trace ✓
              </span>
            )}
            {property.streetViewImages && (
              <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 text-[10px] font-medium border border-emerald-500/20">
                Street View ✓
              </span>
            )}
          </div>
        </div>

        {/* Spacer to push AI confidence to bottom */}
        <div className="flex-1"></div>

        {/* AI Confidence Indicator - Compact */}
        <div className="pt-3 border-t border-border-dark">
          <div className="flex items-center justify-between mb-1">
            <span className="text-gray-500 text-[10px] uppercase tracking-wide">AI Confidence</span>
            <span className={`text-[10px] font-bold uppercase ${
              property.aiStatus === 'excellent' ? 'text-emerald-400' :
              property.aiStatus === 'good' ? 'text-emerald-400' :
              property.aiStatus === 'warning' ? 'text-yellow-400' :
              'text-red-400'
            }`}>
              {property.aiStatus}
            </span>
          </div>
          <div className="w-full bg-gray-800 h-1 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                property.aiConfidence >= 85 ? 'bg-gradient-to-r from-emerald-600 to-emerald-400' :
                property.aiConfidence >= 70 ? 'bg-gradient-to-r from-yellow-600 to-yellow-400' :
                'bg-gradient-to-r from-red-600 to-red-400'
              }`}
              style={{ width: `${property.aiConfidence}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
