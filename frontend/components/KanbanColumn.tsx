import { KanbanCard } from './KanbanCard'

interface KanbanColumnProps {
  title: string
  count: number
  status: string
  properties: Array<{
    id: string
    address: string
    city: string
    state: string
    image: string
    openingBid: number
    estimatedARV: number
    auctionDate: string
    tags: string[]
  }>
}

export function KanbanColumn({ title, count, status, properties }: KanbanColumnProps) {
  const getStatusColor = () => {
    switch (status) {
      case 'new':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/20'
      case 'researching':
        return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
      case 'under-contract':
        return 'bg-purple-500/10 text-purple-400 border-purple-500/20'
      case 'closed':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
      default:
        return 'bg-gray-500/10 text-gray-400 border-gray-500/20'
    }
  }

  return (
    <div className="kanban-column flex flex-col bg-column-bg border border-border-dark rounded-lg min-w-[320px] max-w-[320px]">
      {/* Column Header */}
      <div className="p-3 border-b border-border-dark">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-white font-medium text-sm">{title}</h3>
          <span className={`text-xs font-bold px-2 py-0.5 rounded border ${getStatusColor()}`}>
            {count}
          </span>
        </div>
        <div className="w-full bg-gray-800 h-1 rounded-full overflow-hidden">
          <div className="bg-primary h-full rounded-full" style={{ width: `${Math.min(count * 10, 100)}%` }} />
        </div>
      </div>

      {/* Column Cards */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3 max-h-[calc(100vh-320px)]">
        {properties.map((property) => (
          <KanbanCard key={property.id} property={property} />
        ))}
      </div>
    </div>
  )
}
