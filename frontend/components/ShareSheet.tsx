'use client'

import { useState } from 'react'
import { QRCodeSVG } from 'qrcode.react'
import { exportPropertyPdf, PropertyPdfData } from '@/lib/exportPropertyPdf'

interface ShareSheetProps {
  property: {
    id: string
    address: string
    city: string
    state: string
    zip: string
    auctionDate: string
    openingBid: number
    approxUpset?: number
    approxJudgment?: number
    estimatedARV?: number
    zestimate?: number
    rentZestimate?: number
    spread: number
    beds?: number
    baths?: number
    sqft?: number
    yearBuilt?: number
    propertyType?: string
    apn?: string
    status?: string
    description?: string
    sheriff_number?: string
    plaintiff?: string
    plaintiff_attorney?: string
    defendant?: string
    skipTraceData?: any
    refined_description?: string
    statusHistory?: Array<{
      status: string
      date: string
      notes?: string
    }>
    tags?: Array<{ name: string; color: string }>
    notes?: Array<{ note: string; created_at: string }>
  }
  isOpen: boolean
  onClose: () => void
  onShareComplete?: (type: 'copied' | 'shared' | 'qr' | 'pdf') => void
}

export function ShareSheet({ property, isOpen, onClose, onShareComplete }: ShareSheetProps) {
  const [showQR, setShowQR] = useState(false)
  const [feedback, setFeedback] = useState<'copied' | 'shared' | 'pdf' | null>(null)
  const [isPdfGenerating, setIsPdfGenerating] = useState(false)

  if (!isOpen) return null

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  // Generate shareable URL with property ID
  const getShareableUrl = () => {
    // Use bidnology.com as the base URL, fallback to current origin for development
    const baseUrl = 'https://bidnology.com'
    return `${baseUrl}/property/${property.id}`
  }

  // Generate Google Maps URL for the property address
  const getGoogleMapsUrl = () => {
    const address = `${property.address}, ${property.city}, ${property.state} ${property.zip}`
    return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(address)}`
  }

  // Generate Zillow URL for the property address
  const getZillowUrl = () => {
    const address = `${property.address}, ${property.city}, ${property.state} ${property.zip}`
    return `https://www.zillow.com/homes/${encodeURIComponent(address)}_rb/`
  }

  // Generate formatted content with all property details
  const getShareContent = (): { title: string; text: string } => {
    const url = getShareableUrl()
    const googleMapsUrl = getGoogleMapsUrl()
    const zillowUrl = getZillowUrl()
    const address = `${property.address}, ${property.city}, ${property.state} ${property.zip}`

    let text = `PROPERTY REPORT\n${address}\n`
    text += `Generated: ${new Date().toLocaleDateString()}\n\n`

    // Status
    if (property.status) {
      text += `Status: ${property.status.toUpperCase()}\n\n`
    }

    // Property Information
    text += `PROPERTY INFORMATION\n`
    text += `${address}\n\n`

    // Property Stats
    if (property.beds) text += `Bedrooms: ${property.beds}\n`
    if (property.baths) text += `Bathrooms: ${property.baths}\n`
    if (property.sqft) text += `Square Feet: ${property.sqft.toLocaleString()}\n`
    if (property.yearBuilt) text += `Year Built: ${property.yearBuilt}\n`
    if (property.apn) text += `APN: ${property.apn}\n`
    if (property.propertyType) text += `Property Type: ${property.propertyType}\n`
    text += `\n`

    // Description
    if (property.description) {
      text += `DESCRIPTION\n${property.description}\n\n`
    }

    // AI-Refined Description
    if (property.refined_description) {
      text += `AI-REFINED DESCRIPTION\n${property.refined_description}\n\n`
    }

    // Auction Details
    text += `AUCTION DETAILS\n`
    text += `Auction Date: ${property.auctionDate} (Status: ${property.status || 'Active'})\n`
    text += `Opening Bid: ${formatCurrency(property.openingBid)}\n`
    if (property.approxUpset) text += `Approx Upset: ${formatCurrency(property.approxUpset)}\n`
    if (property.approxJudgment) text += `Approx Judgment: ${formatCurrency(property.approxJudgment)}\n`
    if (property.zestimate) text += `Zestimate: ${formatCurrency(property.zestimate)} (Zillow)\n`
    if (property.rentZestimate) text += `Rent Zestimate: ${formatCurrency(property.rentZestimate)}\n`
    if (property.estimatedARV) text += `Est. ARV: ${formatCurrency(property.estimatedARV)} (Projected)\n`
    text += `Spread: +${property.spread.toFixed(1)}% (ROI)\n\n`

    // Legal Parties
    if (property.sheriff_number || property.plaintiff || property.plaintiff_attorney || property.defendant) {
      text += `LEGAL PARTIES\n`
      if (property.sheriff_number) text += `Sheriff #: ${property.sheriff_number}\n`
      if (property.plaintiff) text += `Plaintiff: ${property.plaintiff}\n`
      if (property.plaintiff_attorney) text += `Plaintiff Attorney: ${property.plaintiff_attorney}\n`
      if (property.defendant) text += `Defendant: ${property.defendant}\n`
      text += `\n`
    }

    // Status History
    if (property.statusHistory && property.statusHistory.length > 0) {
      text += `STATUS HISTORY\n`
      property.statusHistory.forEach((entry, i) => {
        text += `${i + 1}. ${entry.status} - ${entry.date}\n`
        if (entry.notes) text += `   ${entry.notes}\n`
      })
      text += `\n`
    }

    // Owner Contact Information
    if (property.skipTraceData?.owners?.length > 0) {
      text += `OWNER CONTACT INFORMATION\n`
      property.skipTraceData.owners.forEach((owner: any, idx: number) => {
        text += `Owner ${idx + 1}:\n`
        if (owner.name) text += `  Name: ${owner.name}\n`
        if (owner.phones?.length > 0) text += `  Phones: ${owner.phones.join(', ')}\n`
        if (owner.emails?.length > 0) text += `  Emails: ${owner.emails.join(', ')}\n`
      })
      text += `\n`
    }

    // Quick Links
    text += `QUICK LINKS\n`
    text += `Google Maps: ${googleMapsUrl}\n`
    text += `Zillow: ${zillowUrl}\n`
    text += `Property Link: ${url}\n`

    return {
      title: `${property.address} - Auction ${property.auctionDate} | Bidnology`,
      text,
    }
  }

  const handleExportPdf = async () => {
    setIsPdfGenerating(true)
    try {
      await exportPropertyPdf(property as PropertyPdfData)
      setFeedback('pdf')
      onShareComplete?.('pdf')
      setTimeout(() => {
        setFeedback(null)
        onClose()
      }, 1500)
    } catch (error) {
      console.error('Failed to generate PDF:', error)
    } finally {
      setIsPdfGenerating(false)
    }
  }

  const handleShare = async () => {
    const { title, text } = getShareContent()
    const url = getShareableUrl()

    // Check if Web Share API is supported (mobile devices)
    if (navigator.share) {
      try {
        await navigator.share({
          title,
          text,
          url,
        })
        setFeedback('shared')
        onShareComplete?.('shared')
        setTimeout(() => {
          setFeedback(null)
          onClose()
        }, 1500)
      } catch (err) {
        if ((err as Error).name !== 'AbortError') {
          console.error('Error sharing:', err)
        }
      }
    } else {
      // Fallback: copy to clipboard
      try {
        await navigator.clipboard.writeText(text)
        setFeedback('copied')
        onShareComplete?.('copied')
        setTimeout(() => setFeedback(null), 2000)
      } catch (err) {
        console.error('Failed to copy to clipboard:', err)
      }
    }
  }

  const handleCopyLink = async () => {
    const url = getShareableUrl()
    try {
      await navigator.clipboard.writeText(url)
      setFeedback('copied')
      onShareComplete?.('copied')
      setTimeout(() => setFeedback(null), 2000)
    } catch (err) {
      console.error('Failed to copy link:', err)
    }
  }

  const handleCopyQR = async () => {
    setShowQR(true)
    onShareComplete?.('qr')
  }

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="w-full max-w-md bg-[#1a2332] border border-border-dark rounded-xl shadow-2xl animate-in fade-in zoom-in duration-200">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border-dark">
          <h3 className="text-lg font-semibold text-white">Share Property</h3>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-white rounded-lg hover:bg-white/5 transition-colors"
          >
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4">
          {/* Preview */}
          <div className="bg-[#0F1621] rounded-lg p-3 border border-border-dark">
            <div className="text-xs text-gray-500 mb-1">Share Preview:</div>
            <div className="max-h-48 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-transparent hover:scrollbar-thumb-gray-500">
              <div className="text-xs text-gray-300 whitespace-pre-wrap font-mono break-all pr-2">
                {getShareContent().text}
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="space-y-2">
            <button
              onClick={handleShare}
              disabled={!!feedback || isPdfGenerating}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary hover:bg-primary/90 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {feedback === 'shared' ? (
                <>
                  <span className="material-symbols-outlined text-[18px]">check_circle</span>
                  <span>Shared!</span>
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-[18px]">share</span>
                  <span>Share</span>
                </>
              )}
            </button>

            <button
              onClick={handleExportPdf}
              disabled={isPdfGenerating || !!feedback}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isPdfGenerating ? (
                <>
                  <span className="material-symbols-outlined text-[18px] animate-spin">refresh</span>
                  <span>Generating PDF...</span>
                </>
              ) : feedback === 'pdf' ? (
                <>
                  <span className="material-symbols-outlined text-[18px]">check_circle</span>
                  <span>PDF Downloaded!</span>
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-[18px]">picture_as_pdf</span>
                  <span>Export PDF Report</span>
                </>
              )}
            </button>

            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={handleCopyLink}
                disabled={isPdfGenerating}
                className="flex items-center justify-center gap-2 px-4 py-3 bg-surface-dark hover:bg-white/5 text-gray-300 hover:text-white border border-border-dark rounded-lg font-medium transition-colors disabled:opacity-50"
              >
                <span className="material-symbols-outlined text-[18px]">link</span>
                <span>Copy Link</span>
              </button>

              <button
                onClick={handleCopyQR}
                disabled={isPdfGenerating}
                className="flex items-center justify-center gap-2 px-4 py-3 bg-surface-dark hover:bg-white/5 text-gray-300 hover:text-white border border-border-dark rounded-lg font-medium transition-colors disabled:opacity-50"
              >
                <span className="material-symbols-outlined text-[18px]">qr_code</span>
                <span>QR Code</span>
              </button>
            </div>
          </div>
        </div>

        {/* QR Code Modal */}
        {showQR && (
          <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <div className="bg-[#1a2332] border border-border-dark rounded-xl p-6 max-w-sm w-full animate-in fade-in zoom-in duration-200">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-lg font-semibold text-white">QR Code</h4>
                <button
                  onClick={() => setShowQR(false)}
                  className="p-1 text-gray-400 hover:text-white rounded-lg hover:bg-white/5"
                >
                  <span className="material-symbols-outlined">close</span>
                </button>
              </div>

              <div className="flex flex-col items-center gap-4">
                <div className="bg-white p-4 rounded-lg">
                  <QRCodeSVG
                    value={getShareableUrl()}
                    size={200}
                    level="M"
                    includeMargin={true}
                  />
                </div>
                <p className="text-sm text-gray-400 text-center">
                  Scan to view property details
                </p>
                <button
                  onClick={async () => {
                    const svg = document.querySelector('#qr-code-svg') as SVGSVGElement
                    if (svg) {
                      const svgData = new XMLSerializer().serializeToString(svg)
                      const canvas = document.createElement('canvas')
                      const ctx = canvas.getContext('2d')
                      const img = new Image()
                      img.setAttribute('src', 'data:image/svg+xml;base64,' + btoa(svgData))
                      img.onload = () => {
                        canvas.width = 400
                        canvas.height = 400
                        ctx?.drawImage(img, 0, 0, 400, 400)
                        const pngUrl = canvas.toDataURL('image/png')
                        const downloadLink = document.createElement('a')
                        downloadLink.href = pngUrl
                        downloadLink.download = `property-${property.id}-qr.png`
                        downloadLink.click()
                      }
                    }
                  }}
                  className="w-full px-4 py-2 bg-surface-dark hover:bg-white/5 text-gray-300 hover:text-white border border-border-dark rounded-lg font-medium transition-colors"
                >
                  Download QR Code
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Hidden SVG for QR download */}
        <div className="hidden">
          <QRCodeSVG
            id="qr-code-svg"
            value={getShareableUrl()}
            size={400}
            level="M"
            includeMargin={true}
          />
        </div>
      </div>
    </div>
  )
}
