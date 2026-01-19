interface KanbanCardProps {
  property: {
    id: string
    address: string
    city: string
    state: string
    image: string
    openingBid: number
    estimatedARV: number
    auctionDate: string
    tags: string[]
  }
}

export function KanbanCard({ property }: KanbanCardProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  const spread = ((property.estimatedARV - property.openingBid) / property.estimatedARV * 100).toFixed(1)

  return (
    <div className="bg-column-bg border border-border-dark rounded-lg p-4 cursor-pointer hover:border-gray-600 transition-all group">
      {/* Property Image */}
      <div className="relative aspect-video rounded-md overflow-hidden mb-3 bg-surface-dark">
        <div
          className="w-full h-full bg-cover bg-center opacity-90 group-hover:opacity-100 transition-opacity"
          style={{ backgroundImage: `url('${property.image}')` }}
        />
        {/* Badges */}
        <div className="absolute top-2 right-2 flex gap-1">
          {property.tags.map((tag) => (
            <span
              key={tag}
              className="bg-black/60 backdrop-blur text-white text-[10px] px-1.5 py-0.5 rounded border border-white/10"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>

      {/* Address */}
      <h4 className="text-white font-medium text-sm mb-1 leading-tight">{property.address}</h4>
      <p className="text-gray-500 text-xs mb-3">{`${property.city}, ${property.state}`}</p>

      {/* Metrics */}
      <div className="space-y-2 mb-3">
        <div className="flex justify-between items-center">
          <span className="text-gray-500 text-xs">Opening Bid</span>
          <span className="text-white text-sm font-medium">{formatCurrency(property.openingBid)}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-500 text-xs">Est. ARV</span>
          <span className="text-gray-400 text-sm">{formatCurrency(property.estimatedARV)}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-500 text-xs">Spread</span>
          <span className="text-emerald-400 text-sm font-medium">+{spread}%</span>
        </div>
      </div>

      {/* Auction Date */}
      <div className="flex items-center gap-1.5 text-xs text-gray-400 pt-2 border-t border-border-dark">
        <span className="material-symbols-outlined text-[14px]">schedule</span>
        {property.auctionDate}
      </div>
    </div>
  )
}
