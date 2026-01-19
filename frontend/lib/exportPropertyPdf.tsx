import {
  Document,
  Page,
  Text,
  View,
  StyleSheet,
} from '@react-pdf/renderer'
import { saveAs } from 'file-saver'

export interface PropertyPdfData {
  id: string
  address: string
  city: string
  state: string
  zip: string
  apn?: string
  image?: string
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
  aiConfidence?: number
  status?: string
  description?: string
  refined_description?: string
  sheriff_number?: string
  plaintiff?: string
  plaintiff_attorney?: string
  defendant?: string
  skipTraceData?: any
  statusHistory?: Array<{
    status: string
    date: string
    notes?: string
  }>
  tags?: Array<{ name: string; color: string }>
  notes?: Array<{ note: string; created_at: string }>
}

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

interface AuctionDataRow {
  item: string
  amount: string
  notes: string
  highlight?: boolean
}

const styles = StyleSheet.create({
  page: {
    padding: 30,
    backgroundColor: '#FFFFFF',
    fontFamily: 'Helvetica',
  },
  header: {
    marginBottom: 25,
    paddingBottom: 15,
    borderBottom: '2pt solid #1E3A8A',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1E3A8A',
    marginBottom: 5,
  },
  subtitle: {
    fontSize: 11,
    color: '#6B7280',
  },
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#1E3A8A',
    marginBottom: 10,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  sectionUnderline: {
    height: 1,
    backgroundColor: '#1E3A8A',
    marginBottom: 12,
  },
  address: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 8,
  },
  statusBadge: {
    backgroundColor: '#1E3A8A',
    color: '#FFFFFF',
    fontSize: 8,
    fontWeight: 'bold',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 3,
    textTransform: 'uppercase',
    alignSelf: 'flex-start',
    marginBottom: 10,
  },
  label: {
    fontSize: 9,
    color: '#6B7280',
    marginBottom: 2,
  },
  value: {
    fontSize: 10,
    color: '#111827',
    marginBottom: 8,
  },
  keyValueRow: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  key: {
    fontSize: 9,
    color: '#6B7280',
    width: 120,
  },
  val: {
    fontSize: 10,
    color: '#111827',
    flex: 1,
  },
  table: {
    width: '100%',
    marginBottom: 10,
  },
  tableHeader: {
    backgroundColor: '#F5F7FA',
    flexDirection: 'row',
  },
  tableHeaderCell: {
    padding: 8,
    fontSize: 9,
    fontWeight: 'bold',
    color: '#374151',
    borderRight: '1pt solid #E5E7EB',
  },
  tableRow: {
    flexDirection: 'row',
    borderBottom: '1pt solid #F3F4F6',
  },
  tableRowAlt: {
    flexDirection: 'row',
    backgroundColor: '#FAFAFA',
    borderBottom: '1pt solid #F3F4F6',
  },
  tableCell: {
    padding: 8,
    fontSize: 9,
    color: '#111827',
    borderRight: '1pt solid #E5E7EB',
  },
  highlight: {
    color: '#22C55E',
    fontWeight: 'bold',
  },
  note: {
    fontSize: 8,
    color: '#6B7280',
  },
  divider: {
    height: 8,
  },
  footer: {
    position: 'absolute',
    bottom: 20,
    left: 30,
    right: 30,
    borderTop: '1pt solid #E5E7EB',
    paddingTop: 8,
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  footerText: {
    fontSize: 8,
    color: '#9CA3AF',
  },
  link: {
    color: '#1E3A8A',
    textDecoration: 'underline',
  },
  tag: {
    backgroundColor: '#E5E7EB',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 3,
    fontSize: 8,
    marginRight: 5,
    marginBottom: 5,
  },
  ownerCard: {
    backgroundColor: '#FAFAFA',
    padding: 12,
    borderRadius: 4,
    marginBottom: 10,
  },
  ownerTitle: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 6,
  },
  ownerContact: {
    fontSize: 9,
    color: '#374151',
    marginBottom: 3,
  },
})

interface PropertyPdfProps {
  property: PropertyPdfData
}

const PropertyPdfDocument: React.FC<{ property: PropertyPdfData }> = ({ property }) => {
  const googleMapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${property.address}, ${property.city}, ${property.state} ${property.zip}`)}`
  const zillowUrl = `https://www.zillow.com/homes/${encodeURIComponent(`${property.address}, ${property.city}, ${property.state} ${property.zip}`)}_rb/`

  // Prepare auction table data
  const auctionData: AuctionDataRow[] = [
    { item: 'Auction Date', amount: property.auctionDate, notes: property.status || 'Active' },
    { item: 'Opening Bid', amount: formatCurrency(property.openingBid), notes: '-' },
  ]

  if (property.approxUpset) auctionData.push({ item: 'Approx Upset', amount: formatCurrency(property.approxUpset), notes: '-' })
  if (property.approxJudgment) auctionData.push({ item: 'Approx Judgment', amount: formatCurrency(property.approxJudgment), notes: '-' })
  if (property.zestimate) auctionData.push({ item: 'Zestimate', amount: formatCurrency(property.zestimate), notes: 'Zillow' })
  if (property.estimatedARV) auctionData.push({ item: 'Est. ARV', amount: formatCurrency(property.estimatedARV), notes: 'Projected' })
  auctionData.push({ item: 'Spread', amount: `+${property.spread.toFixed(1)}%`, notes: 'ROI', highlight: true })

  return (
    <Document>
      <Page size="A4" style={styles.page}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>PROPERTY REPORT</Text>
          <Text style={styles.subtitle}>{`${property.address}, ${property.city}`}</Text>
          <Text style={styles.footerText}>{new Date().toLocaleDateString()}</Text>
        </View>

        {/* Property Information */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Property Information</Text>
          <View style={styles.sectionUnderline} />

          <Text style={styles.address}>{`${property.address}\n${property.city}, ${property.state} ${property.zip}`}</Text>

          {property.status && (
            <View style={styles.statusBadge}>
              <Text>{property.status.toUpperCase()}</Text>
            </View>
          )}

          {/* Property Stats */}
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginBottom: 15 }}>
            <View style={{ width: '50%', marginBottom: 10 }}>
              <Text style={styles.label}>Bedrooms</Text>
              <Text style={styles.value}>{property.beds ?? '-'}</Text>
            </View>
            <View style={{ width: '50%', marginBottom: 10 }}>
              <Text style={styles.label}>Bathrooms</Text>
              <Text style={styles.value}>{property.baths ?? '-'}</Text>
            </View>
            <View style={{ width: '50%', marginBottom: 10 }}>
              <Text style={styles.label}>Square Feet</Text>
              <Text style={styles.value}>{property.sqft?.toLocaleString() ?? '-'}</Text>
            </View>
            <View style={{ width: '50%', marginBottom: 10 }}>
              <Text style={styles.label}>Year Built</Text>
              <Text style={styles.value}>{property.yearBuilt ?? '-'}</Text>
            </View>
          </View>

          {property.apn && (
            <View style={styles.keyValueRow}>
              <Text style={styles.key}>APN:</Text>
              <Text style={styles.val}>{property.apn}</Text>
            </View>
          )}

          {property.propertyType && (
            <View style={styles.keyValueRow}>
              <Text style={styles.key}>Property Type:</Text>
              <Text style={styles.val}>{property.propertyType}</Text>
            </View>
          )}
        </View>

        {/* Description */}
        {property.description && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Description</Text>
            <View style={styles.sectionUnderline} />
            <Text style={styles.value}>{property.description}</Text>

            {/* Refined Description */}
            {property.refined_description && (
              <>
                <View style={styles.sectionUnderline} />
                <Text style={[styles.value, { marginTop: 8, fontWeight: 'bold', color: '#1E3A8A' }]}>AI-Refined Version</Text>
                <Text style={[styles.value, { backgroundColor: '#F0F9FF', padding: 8, borderRadius: 4 }]}>{property.refined_description}</Text>
              </>
            )}
          </View>
        )}

        {/* Auction Details */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Auction Details</Text>
          <View style={styles.sectionUnderline} />

          <View style={styles.tableHeader}>
            <Text style={[styles.tableHeaderCell, { flex: 1 }]}>Item</Text>
            <Text style={[styles.tableHeaderCell, { flex: 1 }]}>Amount / Date</Text>
            <Text style={[styles.tableHeaderCell, { flex: 1 }]}>Notes</Text>
          </View>
          {auctionData.map((row, i) => {
            const amountStyle = row.highlight ? [styles.tableCell, { flex: 1 }, styles.highlight] : [styles.tableCell, { flex: 1 }]
            return (
              <View key={i} style={i % 2 === 0 ? styles.tableRow : styles.tableRowAlt}>
                <Text style={[styles.tableCell, { flex: 1 }]}>{row.item}</Text>
                <Text style={amountStyle}>{row.amount}</Text>
                <Text style={[styles.tableCell, { flex: 1 }, styles.note]}>{row.notes}</Text>
              </View>
            )
          })}
        </View>

        {/* Legal Parties */}
        {(property.sheriff_number || property.plaintiff || property.plaintiff_attorney || property.defendant) && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Legal Parties</Text>
            <View style={styles.sectionUnderline} />

            {property.sheriff_number && (
              <View style={styles.keyValueRow}>
                <Text style={styles.key}>Sheriff #:</Text>
                <Text style={styles.val}>{property.sheriff_number}</Text>
              </View>
            )}
            {property.plaintiff && (
              <View style={styles.keyValueRow}>
                <Text style={styles.key}>Plaintiff:</Text>
                <Text style={styles.val}>{property.plaintiff}</Text>
              </View>
            )}
            {property.plaintiff_attorney && (
              <View style={styles.keyValueRow}>
                <Text style={styles.key}>Plaintiff Attorney:</Text>
                <Text style={styles.val}>{property.plaintiff_attorney}</Text>
              </View>
            )}
            {property.defendant && (
              <View style={styles.keyValueRow}>
                <Text style={styles.key}>Defendant:</Text>
                <Text style={styles.val}>{property.defendant}</Text>
              </View>
            )}
          </View>
        )}

        {/* Status History */}
        {property.statusHistory && property.statusHistory.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Status History</Text>
            <View style={styles.sectionUnderline} />

            {property.statusHistory.map((entry, i) => (
              <View key={i} style={{ marginBottom: 10 }}>
                <View style={styles.keyValueRow}>
                  <Text style={[styles.key, { fontWeight: 'bold' }]}>{i + 1}.</Text>
                  <Text style={[styles.val, { fontWeight: 'bold' }]}>{entry.status}</Text>
                  <Text style={styles.note}>{entry.date}</Text>
                </View>
                {entry.notes && (
                  <Text style={[styles.value, { color: '#6B7280', fontSize: 8 }]}>{entry.notes}</Text>
                )}
              </View>
            ))}
          </View>
        )}

        {/* Owner Contact Info */}
        {property.skipTraceData?.owners?.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Owner Contact Information</Text>
            <View style={styles.sectionUnderline} />

            {property.skipTraceData.owners.map((owner: any, idx: number) => (
              <View key={idx} style={styles.ownerCard}>
                <Text style={styles.ownerTitle}>Owner {idx + 1}</Text>
                {owner.name && (
                  <Text style={styles.ownerContact}>Name: {owner.name}</Text>
                )}
                {owner.phones?.length > 0 && (
                  <Text style={styles.ownerContact}>Phones: {owner.phones.join(', ')}</Text>
                )}
                {owner.emails?.length > 0 && (
                  <Text style={styles.ownerContact}>Emails: {owner.emails.join(', ')}</Text>
                )}
              </View>
            ))}
          </View>
        )}

        {/* Quick Links */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Quick Links</Text>
          <View style={styles.sectionUnderline} />

          <View style={styles.keyValueRow}>
            <Text style={styles.key}>Google Maps:</Text>
            <Text style={styles.val}>{googleMapsUrl}</Text>
          </View>
          <View style={styles.keyValueRow}>
            <Text style={styles.key}>Zillow:</Text>
            <Text style={styles.val}>{zillowUrl}</Text>
          </View>
        </View>

        <View style={styles.divider} />
      </Page>
    </Document>
  )
}

export async function exportPropertyPdf(property: PropertyPdfData): Promise<void> {
  const { pdf } = await import('@react-pdf/renderer')
  const blob = await pdf(<PropertyPdfDocument property={property} />).toBlob()

  const fileName = `Property Report - ${property.address.replace(/[^a-z0-9]/gi, '-')} - ${property.auctionDate}.pdf`
  saveAs(blob, fileName)
}
