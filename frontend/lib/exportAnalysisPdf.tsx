import {
  Document,
  Page,
  Text,
  View,
  StyleSheet,
  Image,
} from '@react-pdf/renderer'
import { saveAs } from 'file-saver'
import type { AnalysisData } from './AnalysisService'

const formatCurrency = (value: number): string => {
  if (value === undefined || value === null) return 'N/A'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

const formatNumber = (num: number | string): string => {
  if (num === undefined || num === null) return 'N/A'
  if (typeof num === 'string') return num
  return new Intl.NumberFormat('en-US').format(num)
}

const styles = StyleSheet.create({
  page: {
    padding: 30,
    backgroundColor: '#FFFFFF',
    fontFamily: 'Helvetica',
    fontSize: 10,
  },
  header: {
    marginBottom: 20,
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
    pageBreakInside: 'avoid',
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#1E3A8A',
    marginBottom: 10,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    borderBottom: '1pt solid #E5E7EB',
    paddingBottom: 5,
  },
  metricsGrid: {
    display: 'flex',
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    marginBottom: 15,
  },
  metricBox: {
    width: '48%',
    backgroundColor: '#F9FAFB',
    padding: 10,
    borderRadius: 4,
    border: '1pt solid #E5E7EB',
  },
  metricLabel: {
    fontSize: 8,
    color: '#6B7280',
    marginBottom: 3,
    textTransform: 'uppercase',
    letterSpacing: 0.3,
  },
  metricValue: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#111827',
  },
  metricSubtext: {
    fontSize: 8,
    color: '#9CA3AF',
    marginTop: 2,
  },
  table: {
    width: '100%',
    marginBottom: 10,
  },
  tableRow: {
    flexDirection: 'row',
    borderBottom: '1pt solid #E5E7EB',
  },
  tableHeader: {
    backgroundColor: '#F3F4F6',
    padding: 8,
    fontSize: 9,
    fontWeight: 'bold',
    color: '#374151',
    flex: 1,
  },
  tableCell: {
    padding: 8,
    fontSize: 9,
    color: '#111827',
    flex: 1,
  },
  strategyCard: {
    backgroundColor: '#F9FAFB',
    padding: 12,
    marginBottom: 10,
    borderRadius: 4,
    border: '1pt solid #E5E7EB',
  },
  strategyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  strategyName: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#111827',
  },
  strategyRank: {
    backgroundColor: '#1E3A8A',
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: 'bold',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 3,
  },
  riskBadge: {
    fontSize: 8,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 3,
    alignSelf: 'flex-start',
  },
  riskLow: {
    backgroundColor: '#D1FAE5',
    color: '#065F46',
  },
  riskMedium: {
    backgroundColor: '#FEF3C7',
    color: '#92400E',
  },
  riskHigh: {
    backgroundColor: '#FEE2E2',
    color: '#991B1B',
  },
  text: {
    fontSize: 9,
    color: '#374151',
    lineHeight: 1.5,
    marginBottom: 5,
  },
  bold: {
    fontWeight: 'bold',
  },
  greenText: {
    color: '#059669',
  },
  redText: {
    color: '#DC2626',
  },
  checklistItem: {
    flexDirection: 'row',
    marginBottom: 8,
    padding: 8,
    backgroundColor: '#F9FAFB',
    borderRadius: 4,
    border: '1pt solid #E5E7EB',
  },
  checklistCategory: {
    fontSize: 8,
    color: '#6B7280',
    marginBottom: 2,
    textTransform: 'uppercase',
  },
  scenarioCard: {
    backgroundColor: '#F9FAFB',
    padding: 12,
    marginBottom: 10,
    borderRadius: 4,
    border: '1pt solid #E5E7EB',
  },
  scenarioTitle: {
    fontSize: 11,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 8,
  },
  scenarioFinancials: {
    flexDirection: 'row',
    gap: 15,
    marginTop: 8,
    paddingTop: 8,
    borderTop: '1pt solid #E5E7EB',
  },
  financialItem: {
    flex: 1,
  },
  financialLabel: {
    fontSize: 8,
    color: '#6B7280',
    marginBottom: 2,
  },
  financialValue: {
    fontSize: 11,
    fontWeight: 'bold',
    color: '#111827',
  },
})

interface AnalysisPdfProps {
  data: AnalysisData
}

const AnalysisPdfDocument = ({ data }: AnalysisPdfProps) => (
  <Document>
    <Page size="A4" style={styles.page}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Forensic Property Analysis</Text>
        <Text style={styles.subtitle}>{data.property_address}</Text>
        <Text style={styles.subtitle}>Generated: {new Date().toLocaleDateString()}</Text>
      </View>

      {/* Key Metrics */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Property Overview</Text>
        <View style={styles.metricsGrid}>
          <View style={styles.metricBox}>
            <Text style={styles.metricLabel}>Structure</Text>
            <Text style={styles.metricValue}>{formatNumber(data.property_details.building_sqft)} sqft</Text>
            <Text style={styles.metricSubtext}>Built {data.property_details.year_built}</Text>
          </View>
          <View style={styles.metricBox}>
            <Text style={styles.metricLabel}>Lot Size</Text>
            <Text style={styles.metricValue}>{formatNumber(data.property_details.lot_size_sqft)} sqft</Text>
            <Text style={styles.metricSubtext}>{data.property_details.lot_dimensions}</Text>
          </View>
          <View style={styles.metricBox}>
            <Text style={styles.metricLabel}>Annual Taxes</Text>
            <Text style={styles.metricValue}>{formatCurrency(data.property_details.tax_amount)}</Text>
            <Text style={styles.metricSubtext}>Assessed: {formatCurrency(data.property_details.assessed_value)}</Text>
          </View>
          <View style={styles.metricBox}>
            <Text style={styles.metricLabel}>Zoning</Text>
            <Text style={styles.metricValue}>{data.zoning_analysis.current_zoning_designation}</Text>
            <Text style={styles.metricSubtext}>{data.market_analysis?.neighborhood_class_estimate || 'N/A'}</Text>
          </View>
        </View>
      </View>

      {/* Comprehensive Analysis */}
      {data.comprehensive_analysis && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Investment Analysis</Text>
          <Text style={styles.text}>
            <Text style={styles.bold}>Property Narrative:</Text> {data.comprehensive_analysis.property_narrative}
          </Text>
          <Text style={styles.text}>
            <Text style={styles.bold}>Investment Thesis:</Text> {data.comprehensive_analysis.investment_thesis}
          </Text>
          <Text style={styles.text}>
            <Text style={styles.bold}>Risk Assessment:</Text> {data.comprehensive_analysis.risk_assessment_detailed}
          </Text>
        </View>
      )}

      {/* Valuation & Rehab */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Valuation & Rehab Estimates</Text>
        <View style={styles.table}>
          <View style={styles.tableRow}>
            <Text style={styles.tableHeader}>Metric</Text>
            <Text style={styles.tableHeader}>Value</Text>
          </View>
          <View style={styles.tableRow}>
            <Text style={styles.tableCell}>Conservative ARV</Text>
            <Text style={[styles.tableCell, styles.bold]}>{formatCurrency(data.auction_price_analysis.property_worth_scenarios.conservative_scenario.estimate)}</Text>
          </View>
          <View style={styles.tableRow}>
            <Text style={styles.tableCell}>Optimistic ARV</Text>
            <Text style={[styles.tableCell, styles.bold]}>{formatCurrency(data.auction_price_analysis.property_worth_scenarios.optimistic_scenario.estimate)}</Text>
          </View>
          <View style={styles.tableRow}>
            <Text style={styles.tableCell}>Break-Even Point</Text>
            <Text style={styles.tableCell}>{data.auction_price_analysis.break_even_point}</Text>
          </View>
        </View>

        <Text style={[styles.text, styles.bold, { marginTop: 10, marginBottom: 5 }]}>Rehab Cost Matrix:</Text>
        {data.rehab_matrix && (
          <>
            <Text style={styles.text}>• Light Cosmetic: {formatCurrency(data.rehab_matrix.light_cosmetic.cost)} - {data.rehab_matrix.light_cosmetic.description}</Text>
            <Text style={styles.text}>• Moderate Update: {formatCurrency(data.rehab_matrix.moderate_update.cost)} - {data.rehab_matrix.moderate_update.description}</Text>
            <Text style={styles.text}>• Full Gut Reno: {formatCurrency(data.rehab_matrix.full_gut.cost)} - {data.rehab_matrix.full_gut.description}</Text>
          </>
        )}
      </View>

      {/* Zoning & Buildable Area */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Zoning & Buildable Area</Text>
        <Text style={styles.text}>
          <Text style={styles.bold}>Zone:</Text> {data.zoning_analysis.current_zoning_designation} | <Text style={styles.bold}>Status:</Text> {data.zoning_analysis.conforming_status}
        </Text>
        <Text style={styles.text}>
          <Text style={styles.bold}>Min Lot:</Text> {formatNumber(data.zoning_analysis.bulk_and_setback_requirements.min_lot_size.value)} {data.zoning_analysis.bulk_and_setback_requirements.min_lot_size.unit}
        </Text>
        <Text style={styles.text}>
          <Text style={styles.bold}>Max Coverage:</Text> {data.zoning_analysis.bulk_and_setback_requirements.max_building_coverage}
        </Text>
        <Text style={styles.text}>
          <Text style={styles.bold}>Setbacks:</Text> {data.zoning_analysis.bulk_and_setback_requirements.setbacks}
        </Text>
        {data.zoning_analysis.buildable_area_analysis && (
          <Text style={[styles.text, { marginTop: 5, backgroundColor: '#F3F4F6', padding: 8, borderRadius: 4 }]}>
            <Text style={styles.bold}>Buildable Area Analysis:</Text> {data.zoning_analysis.buildable_area_analysis}
          </Text>
        )}
      </View>

      {/* Investment Strategies */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Strategic Recommendations</Text>
        {data.investment_strategies_ranked.map((strategy) => (
          <View style={styles.strategyCard} key={strategy.rank}>
            <View style={styles.strategyHeader}>
              <Text style={styles.strategyName}>{strategy.strategy}</Text>
              <Text style={styles.strategyRank}>#{strategy.rank}</Text>
            </View>
            <Text style={styles.text}>{strategy.explanation}</Text>
            <View style={styles.metricsGrid}>
              <View style={styles.metricBox}>
                <Text style={styles.metricLabel}>Break-Even Offer</Text>
                <Text style={styles.metricValue}>{formatCurrency(strategy.break_even_offer)}</Text>
              </View>
              <View style={styles.metricBox}>
                <Text style={styles.metricLabel}>Est. Profit</Text>
                <Text style={[styles.metricValue, strategy.est_profit_potential > 0 ? styles.greenText : styles.redText]}>
                  {formatCurrency(strategy.est_profit_potential)}
                </Text>
              </View>
            </View>
            <View style={[styles.riskBadge, strategy.risk_level.toLowerCase().includes('low') ? styles.riskLow : strategy.risk_level.toLowerCase().includes('high') ? styles.riskHigh : styles.riskMedium]}>
              <Text style={{ fontSize: 8 }}>{strategy.risk_level} RISK</Text>
            </View>
          </View>
        ))}
      </View>

      {/* Highest & Best Use Scenarios */}
      {data.highest_best_use_scenarios && data.highest_best_use_scenarios.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Highest & Best Use Scenarios</Text>
          {data.highest_best_use_scenarios.map((scenario, idx) => (
            <View style={styles.scenarioCard} key={idx}>
              <Text style={styles.scenarioTitle}>{scenario.scenario}</Text>
              <Text style={styles.text}>
                <Text style={styles.bold}>Pros:</Text> {scenario.pros}
              </Text>
              <Text style={styles.text}>
                <Text style={styles.bold}>Cons:</Text> {scenario.cons}
              </Text>
              <Text style={styles.text}>
                <Text style={styles.bold}>Risk:</Text> {scenario.risk}
              </Text>
              {scenario.financials && (
                <View style={styles.scenarioFinancials}>
                  <View style={styles.financialItem}>
                    <Text style={styles.financialLabel}>Est. Rehab</Text>
                    <Text style={styles.financialValue}>{formatCurrency(scenario.financials.est_rehab_cost)}</Text>
                  </View>
                  <View style={styles.financialItem}>
                    <Text style={styles.financialLabel}>Est. ARV</Text>
                    <Text style={styles.financialValue}>{formatCurrency(scenario.financials.est_arv)}</Text>
                  </View>
                  <View style={styles.financialItem}>
                    <Text style={styles.financialLabel}>Est. Profit</Text>
                    <Text style={[styles.financialValue, scenario.financials.est_profit > 0 ? styles.greenText : styles.redText]}>
                      {formatCurrency(scenario.financials.est_profit)}
                    </Text>
                  </View>
                  <View style={styles.financialItem}>
                    <Text style={styles.financialLabel}>ROI</Text>
                    <Text style={[styles.financialValue, scenario.financials.est_profit > 0 ? styles.greenText : styles.redText]}>
                      {scenario.financials.roi_percentage}
                    </Text>
                  </View>
                </View>
              )}
            </View>
          ))}
        </View>
      )}

      {/* Rental Analysis */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Rental Analysis</Text>
        <View style={styles.metricsGrid}>
          <View style={styles.metricBox}>
            <Text style={styles.metricLabel}>Est. Monthly Rent</Text>
            <Text style={styles.metricValue}>{formatCurrency(data.rental_analysis.estimated_monthly_rent.low)} - {formatCurrency(data.rental_analysis.estimated_monthly_rent.high)}</Text>
          </View>
          <View style={styles.metricBox}>
            <Text style={styles.metricLabel}>Section 8 FMR</Text>
            <Text style={styles.metricValue}>{formatCurrency(data.rental_analysis.section_8_fmr)}</Text>
          </View>
          <View style={styles.metricBox}>
            <Text style={styles.metricLabel}>Gross Yield</Text>
            <Text style={styles.metricValue}>{data.rental_analysis.gross_yield_percentage}</Text>
          </View>
          <View style={styles.metricBox}>
            <Text style={styles.metricLabel}>Demand</Text>
            <Text style={styles.metricValue}>{data.rental_analysis.rental_demand_rating}</Text>
          </View>
        </View>
      </View>

      {/* Verification Checklist */}
      {data.verification_checklist && data.verification_checklist.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Municipal Verification Checklist</Text>
          {data.verification_checklist.map((item, idx) => (
            <View style={styles.checklistItem} key={idx}>
              <View style={{ flex: 1 }}>
                <Text style={styles.checklistCategory}>{item.category}</Text>
                <Text style={styles.text}>{item.item}</Text>
                <Text style={[styles.text, { color: '#6B7280', fontSize: 8 }]}>Action: {item.action_needed}</Text>
              </View>
            </View>
          ))}
        </View>
      )}

      {/* Auction Analysis */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Auction Price Analysis</Text>
        <Text style={styles.text}>
          <Text style={styles.bold}>Upset Amount:</Text> {formatCurrency(data.auction_price_analysis.upset_amount)}
        </Text>
        <Text style={styles.text}>
          <Text style={styles.bold}>Max Bid Calculation:</Text> {data.auction_price_analysis.max_bid_calculation}
        </Text>
        <Text style={styles.text}>
          <Text style={styles.bold}>Analysis Notes:</Text> {data.auction_price_analysis.analysis_notes}
        </Text>
      </View>

      {/* Footer */}
      <View style={{ marginTop: 20, paddingTop: 15, borderTop: '1pt solid #E5E7EB' }}>
        <Text style={[styles.text, { textAlign: 'center', color: '#9CA3AF' }]}>
          Generated by Bidnology AI • {new Date().toLocaleString()}
        </Text>
      </View>
    </Page>
  </Document>
)

export const exportAnalysisPdf = async (data: AnalysisData) => {
  const { pdf } = await import('@react-pdf/renderer')
  const doc = pdf(<AnalysisPdfDocument data={data} />)
  const blob = await doc.toBlob()

  const address = data.property_address.replace(/[^a-z0-9]/gi, '_').substring(0, 30)
  saveAs(blob, `Bidnology_Analysis_${address}_${Date.now()}.pdf`)
}
