/**
 * RefinedReport Component
 *
 * Beautiful UI for displaying forensic real estate analysis results.
 * Enhanced with comprehensive analysis, verification checklist, and print support.
 *
 * Based on Integration Kit from app (3).zip and enhanced with app (10).zip features
 */

import React from "react";
import type { AnalysisData } from "@/lib/AnalysisService";

const formatCurrency = (amount: number) => {
  if (amount === undefined || amount === null) return "N/A";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(amount);
};

const formatNumber = (num: number | string) => {
  if (num === undefined || num === null) return "N/A";
  if (typeof num === "string") return num;
  return new Intl.NumberFormat("en-US").format(num);
};

interface RefinedReportProps {
  data: AnalysisData;
}

export const RefinedReport: React.FC<RefinedReportProps> = ({ data }) => {
  if (!data) return null;

  const {
    auction_price_analysis,
    zoning_analysis,
    property_details,
    investment_strategies_ranked,
    highest_best_use_scenarios,
    rental_analysis,
    market_analysis,
    rehab_matrix,
    comprehensive_analysis,
    verification_checklist,
  } = data;

  const maxBid = auction_price_analysis?.max_bid_calculation
    ? parseFloat(auction_price_analysis.max_bid_calculation.replace(/[^0-9.-]+/g, "")) || 0
    : 0;
  const upset = auction_price_analysis?.upset_amount || 0;
  const isProfitable = maxBid > upset;

  return (
    <div className="font-sans text-gray-900 dark:text-white space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-500">
      {/* Header Section */}
      <div className="border-b border-gray-300 dark:border-gray-700 pb-6">
        <h2 className="text-3xl font-semibold text-white tracking-tight mb-2">
          {data.property_address}
        </h2>
        <div className="flex flex-wrap gap-4 text-sm text-gray-500 dark:text-gray-400 font-mono">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-sm">pin_drop</span>
            <span>
              Block/Lot:{" "}
              <span className="text-white font-medium">
                {property_details?.parcel_id || "N/A"}
              </span>
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-sm">apartment</span>
            <span>
              Details:{" "}
              <span className="text-white font-medium">
                {property_details?.year_built || "N/A"} |{" "}
                {formatNumber(property_details?.building_sqft || "N/A")} sqft
              </span>
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-sm">home</span>
            <span>
              Class:{" "}
              <span className="text-white font-medium">
                {market_analysis?.neighborhood_class_estimate || "N/A"}
              </span>
            </span>
          </div>
        </div>
      </div>

      {/* Comprehensive Analysis (Narrative) */}
      {comprehensive_analysis && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-gray-100/30 dark:bg-gray-800/30 p-5 rounded-lg border border-gray-300 dark:border-gray-600/50">
            <h3 className="text-sm font-bold uppercase tracking-widest mb-3 text-gray-500 dark:text-gray-400 flex items-center gap-2">
              <span className="material-symbols-outlined text-base">menu_book</span>
              Property Narrative
            </h3>
            <p className="text-sm leading-7 text-gray-500 dark:text-gray-400 whitespace-pre-wrap text-justify">
              {comprehensive_analysis.property_narrative}
            </p>
          </div>
          <div className="bg-gray-100/30 dark:bg-gray-800/30 p-5 rounded-lg border border-gray-300 dark:border-gray-600/50">
            <h3 className="text-sm font-bold uppercase tracking-widest mb-3 text-gray-500 dark:text-gray-400 flex items-center gap-2">
              <span className="material-symbols-outlined text-base">business_center</span>
              Investment Thesis
            </h3>
            <p className="text-sm leading-7 text-gray-500 dark:text-gray-400 whitespace-pre-wrap text-justify">
              {comprehensive_analysis.investment_thesis}
            </p>
            <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
              <div className="text-[10px] font-bold text-red-400 uppercase tracking-wider mb-1">
                Risk Assessment
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 leading-5">
                {comprehensive_analysis.risk_assessment_detailed}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Executive Summary / Recommendation */}
      <div
        className={`p-5 border-l-4 ${
          isProfitable
            ? "border-emerald-500 bg-emerald-500/5"
            : "border-red-500 bg-red-500/5"
        }`}
      >
        <h3 className="text-xs font-bold uppercase tracking-widest mb-2 text-gray-500 dark:text-gray-400">
          Executive Summary
        </h3>
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div className="flex-1">
            <span
              className={`text-xl font-semibold block mb-2 ${
                isProfitable ? "text-emerald-400" : "text-red-400"
              }`}
            >
              {isProfitable
                ? "Recommendation: Potentially Profitable"
                : "Recommendation: High Risk / Negative Margin"}
            </span>
            <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed max-w-3xl whitespace-pre-wrap">
              {auction_price_analysis.analysis_notes}
            </p>
          </div>
          <div className="text-left md:text-right bg-gray-50/50 dark:bg-gray-900/50 p-3 rounded border border-gray-300 dark:border-gray-600/50 min-w-[200px]">
            <div className="text-[10px] text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
              Max Allowable Bid
            </div>
            <div className="text-2xl font-bold text-white tracking-tight">
              {auction_price_analysis.max_bid_calculation}
            </div>
            <div className="text-[10px] text-gray-500 dark:text-gray-400 mt-1">
              Based on 70% ARV Rule
            </div>
          </div>
        </div>
      </div>

      {/* Property Abstract Grid */}
      <div>
        <h3 className="text-lg font-medium text-white mb-4 border-b border-gray-300 dark:border-gray-600/50 pb-2 flex items-center gap-2">
          <span className="material-symbols-outlined text-sm text-gray-500 dark:text-gray-400">description</span>
          Property Abstract
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-y-6 gap-x-4 bg-gray-100/30 dark:bg-gray-800/30 p-4 rounded-lg border border-gray-300 dark:border-gray-600/50">
          <div>
            <div className="text-[10px] text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
              Lot Size
            </div>
            <div className="text-base text-white font-mono">
              {formatNumber(property_details?.lot_size_sqft || "N/A")} sqft
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              {property_details?.lot_dimensions || "N/A"}
            </div>
          </div>
          <div>
            <div className="text-[10px] text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
              Structure
            </div>
            <div className="text-base text-white font-mono">
              {formatNumber(property_details?.building_sqft || "N/A")} sqft
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              Built {property_details?.year_built || "N/A"}
            </div>
          </div>
          <div>
            <div className="text-[10px] text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
              Flood Zone
            </div>
            <div
              className={`text-base font-mono ${
                property_details?.flood_zone?.includes("X")
                  ? "text-white"
                  : "text-amber-400"
              }`}
            >
              {property_details?.flood_zone || "N/A"}
            </div>
          </div>
          <div>
            <div className="text-[10px] text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
              Annual Taxes
            </div>
            <div className="text-base text-white font-mono">
              {formatCurrency(property_details?.tax_amount || 0)}
            </div>
          </div>
          <div>
            <div className="text-[10px] text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
              Zoning Code
            </div>
            <div className="text-base text-white font-mono">
              {zoning_analysis?.current_zoning_designation || "N/A"}
            </div>
          </div>
          <div>
            <div className="text-[10px] text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
              Conforming Status
            </div>
            <div
              className={`text-base font-mono ${
                zoning_analysis?.conforming_status?.toLowerCase().includes("non")
                  ? "text-red-400"
                  : "text-emerald-400"
              }`}
            >
              {zoning_analysis?.conforming_status || "N/A"}
            </div>
          </div>
          <div>
            <div className="text-[10px] text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
              School Rating
            </div>
            <div className="text-base text-white font-mono">
              {market_analysis?.school_district_rating || "N/A"}
            </div>
          </div>
          <div>
            <div className="text-[10px] text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
              Market Velocity
            </div>
            <div className="text-base text-white font-mono">
              {market_analysis?.est_days_on_market || "N/A"}
            </div>
          </div>
        </div>
      </div>

      {/* Financial Analysis Table */}
      <div>
        <h3 className="text-lg font-medium text-white mb-4 border-b border-gray-300 dark:border-gray-600/50 pb-2 flex items-center gap-2">
          <span className="material-symbols-outlined text-sm text-gray-500 dark:text-gray-400">attach_money</span>
          Financial & Rehab Analysis
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-6">
          {/* Financials */}
          <div className="overflow-hidden border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-100/30 dark:bg-gray-800/30">
            <table className="w-full text-sm text-left">
              <thead className="bg-gray-200 dark:bg-gray-700/50 text-gray-500 dark:text-gray-400 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="px-4 py-3 font-medium">Valuation Metric</th>
                  <th className="px-4 py-3 font-medium text-right">Value</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/50">
                <tr>
                  <td className="px-4 py-3 font-medium text-white">
                    Conservative ARV
                  </td>
                  <td className="px-4 py-3 text-right text-gray-900 dark:text-white font-mono">
                    {formatCurrency(
                      auction_price_analysis.property_worth_scenarios
                        .conservative_scenario.estimate
                    )}
                  </td>
                </tr>
                <tr>
                  <td className="px-4 py-3 font-medium text-white">
                    Optimistic ARV
                  </td>
                  <td className="px-4 py-3 text-right text-gray-900 dark:text-white font-mono">
                    {formatCurrency(
                      auction_price_analysis.property_worth_scenarios
                        .optimistic_scenario.estimate
                    )}
                  </td>
                </tr>
                <tr>
                  <td className="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">
                    Break-Even Point
                  </td>
                  <td className="px-4 py-3 text-right text-white font-mono">
                    {auction_price_analysis.break_even_point}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Rehab Matrix */}
          <div className="overflow-hidden border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-100/30 dark:bg-gray-800/30">
            <table className="w-full text-sm text-left">
              <thead className="bg-gray-200 dark:bg-gray-700/50 text-gray-500 dark:text-gray-400 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="px-4 py-3 font-medium">Rehab Level</th>
                  <th className="px-4 py-3 font-medium text-right">
                    Est. Budget
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/50">
                <tr className="group hover:bg-gray-200 dark:bg-gray-700/20 transition-colors">
                  <td className="px-4 py-3">
                    <div className="font-medium text-white flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-emerald-400" />
                      Light Cosmetic
                    </div>
                    <div className="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">
                      {rehab_matrix?.light_cosmetic?.description}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right text-gray-900 dark:text-white font-mono">
                    {rehab_matrix
                      ? formatCurrency(rehab_matrix.light_cosmetic.cost)
                      : "N/A"}
                  </td>
                </tr>
                <tr className="group hover:bg-gray-200 dark:bg-gray-700/20 transition-colors">
                  <td className="px-4 py-3">
                    <div className="font-medium text-white flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-amber-400" />
                      Moderate Update
                    </div>
                    <div className="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">
                      {rehab_matrix?.moderate_update?.description}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right text-gray-900 dark:text-white font-mono">
                    {rehab_matrix
                      ? formatCurrency(rehab_matrix.moderate_update.cost)
                      : "N/A"}
                  </td>
                </tr>
                <tr className="group hover:bg-gray-200 dark:bg-gray-700/20 transition-colors">
                  <td className="px-4 py-3">
                    <div className="font-medium text-white flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-red-400" />
                      Full Gut / Reno
                    </div>
                    <div className="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">
                      {rehab_matrix?.full_gut?.description}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right text-gray-900 dark:text-white font-mono">
                    {rehab_matrix
                      ? formatCurrency(rehab_matrix.full_gut.cost)
                      : "N/A"}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Rental & Market Intelligence */}
      {rental_analysis && (
        <div>
          <h3 className="text-lg font-medium text-white mb-4 border-b border-gray-300 dark:border-gray-600/50 pb-2 flex items-center gap-2">
            <span className="material-symbols-outlined text-sm text-gray-500 dark:text-gray-400">trending_up</span>
            Rental Intelligence & Exit Strategy
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-100/30 dark:bg-gray-800/30 p-4 rounded-lg border border-gray-300 dark:border-gray-600/50">
              <div className="text-[10px] text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
                Monthly Rent Range
              </div>
              <div className="text-xl font-mono text-white">
                {formatCurrency(rental_analysis.estimated_monthly_rent.low)} -{" "}
                {formatCurrency(rental_analysis.estimated_monthly_rent.high)}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">Market Rate</div>
            </div>
            <div className="bg-gray-100/30 dark:bg-gray-800/30 p-4 rounded-lg border border-gray-300 dark:border-gray-600/50">
              <div className="text-[10px] text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
                Section 8 FMR
              </div>
              <div className="text-xl font-mono text-white">
                {formatCurrency(rental_analysis.section_8_fmr)}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Guaranteed Income Potential
              </div>
            </div>
            <div className="bg-gray-100/30 dark:bg-gray-800/30 p-4 rounded-lg border border-gray-300 dark:border-gray-600/50">
              <div className="text-[10px] text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
                Projected Gross Yield
              </div>
              <div className="text-xl font-mono text-emerald-400">
                {rental_analysis.gross_yield_percentage}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Based on Upset Price
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Zoning & Usage */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <h3 className="text-lg font-medium text-white mb-4 border-b border-gray-300 dark:border-gray-600/50 pb-2 flex items-center gap-2">
            <span className="material-symbols-outlined text-sm text-gray-500 dark:text-gray-400">straighten</span>
            Zoning & Bulk Regulations
          </h3>
          <div className="bg-gray-100/30 dark:bg-gray-800/30 rounded-lg border border-gray-300 dark:border-gray-600/50 p-5">
            <ul className="space-y-4 text-sm">
              <li className="flex justify-between border-b border-gray-300 dark:border-gray-600/30 pb-2">
                <span className="text-gray-500 dark:text-gray-400">Min Lot Size</span>
                <span className="text-white text-right font-mono">
                  {formatNumber(
                    zoning_analysis?.bulk_and_setback_requirements?.min_lot_size
                      ?.value || 0
                  )}{" "}
                  {
                    zoning_analysis?.bulk_and_setback_requirements?.min_lot_size
                      ?.unit || ""
                  }
                </span>
              </li>
              <li className="flex justify-between border-b border-gray-300 dark:border-gray-600/30 pb-2">
                <span className="text-gray-500 dark:text-gray-400">Max Building Coverage</span>
                <span className="text-white text-right font-mono">
                  {zoning_analysis?.bulk_and_setback_requirements
                    ?.max_building_coverage || "N/A"}
                </span>
              </li>
              <li className="flex flex-col gap-1 border-b border-gray-300 dark:border-gray-600/30 pb-2">
                <span className="text-gray-500 dark:text-gray-400">Required Setbacks</span>
                <span className="text-white font-mono text-right">
                  {zoning_analysis?.bulk_and_setback_requirements?.setbacks || "N/A"}
                </span>
              </li>
            </ul>
            {/* Buildable Area Analysis */}
            {zoning_analysis?.buildable_area_analysis && (
              <div className="mt-4 p-3 bg-gray-200 dark:bg-gray-700/50 rounded-lg border border-gray-300 dark:border-gray-600/30">
                <div className="text-[10px] text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
                  Buildable Footprint Analysis
                </div>
                <p className="text-sm text-gray-900 dark:text-white/90 leading-relaxed">
                  {zoning_analysis.buildable_area_analysis}
                </p>
              </div>
            )}
          </div>
        </div>
        <div>
          <h3 className="text-lg font-medium text-white mb-4 border-b border-gray-300 dark:border-gray-600/50 pb-2 flex items-center gap-2">
            <span className="material-symbols-outlined text-sm text-gray-500 dark:text-gray-400">calculate</span>
            Highest & Best Use Analysis
          </h3>
          <div className="space-y-4">
            {highest_best_use_scenarios?.map((scenario, i) => (
              <div
                key={i}
                className="bg-gray-100/30 dark:bg-gray-800/30 p-4 rounded-lg border border-gray-300 dark:border-gray-600/50"
              >
                <div className="flex justify-between items-start mb-2">
                  <span className="font-semibold text-white text-sm">
                    {scenario.scenario}
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400 border border-gray-300 dark:border-gray-600 uppercase tracking-wider">
                    {scenario.risk} Risk
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-4 text-xs mt-3 mb-4">
                  <div>
                    <span className="font-bold text-gray-500 dark:text-gray-400 block mb-1">
                      Pros
                    </span>
                    <p className="text-emerald-400/90 leading-relaxed whitespace-pre-wrap">
                      {scenario.pros}
                    </p>
                  </div>
                  <div>
                    <span className="font-bold text-gray-500 dark:text-gray-400 block mb-1">
                      Cons
                    </span>
                    <p className="text-red-400/90 leading-relaxed whitespace-pre-wrap">
                      {scenario.cons}
                    </p>
                  </div>
                </div>
                {scenario.financials && (
                  <div className="grid grid-cols-4 gap-2 pt-3 border-t border-gray-300 dark:border-gray-600/30 bg-black/20 -mx-4 -mb-4 p-3 px-4">
                    <div>
                      <div className="text-[9px] text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-0.5">
                        Est. Cost
                      </div>
                      <div className="text-xs font-mono text-white">
                        {formatCurrency(scenario.financials.est_rehab_cost)}
                      </div>
                    </div>
                    <div>
                      <div className="text-[9px] text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-0.5">
                        Est. ARV
                      </div>
                      <div className="text-xs font-mono text-white">
                        {formatCurrency(scenario.financials.est_arv)}
                      </div>
                    </div>
                    <div>
                      <div className="text-[9px] text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-0.5">
                        Est. Profit
                      </div>
                      <div
                        className={`text-xs font-mono ${
                          scenario.financials.est_profit > 0
                            ? "text-emerald-400"
                            : "text-red-400"
                        }`}
                      >
                        {formatCurrency(scenario.financials.est_profit)}
                      </div>
                    </div>
                    <div>
                      <div className="text-[9px] text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-0.5">
                        ROI
                      </div>
                      <div
                        className={`text-xs font-mono ${
                          scenario.financials.est_profit > 0
                            ? "text-emerald-400"
                            : "text-red-400"
                        }`}
                      >
                        {scenario.financials.roi_percentage}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Strategies List */}
      <div>
        <h3 className="text-lg font-medium text-white mb-4 border-b border-gray-300 dark:border-gray-600/50 pb-2 flex items-center gap-2">
          <span className="material-symbols-outlined text-sm text-gray-500 dark:text-gray-400">dashboard</span>
          Strategic Recommendations & Break-Even Analysis
        </h3>
        <div className="space-y-4">
          {investment_strategies_ranked?.map((strat, idx) => (
            <div
              key={idx}
              className="flex flex-col md:flex-row gap-4 p-5 bg-gray-100/30 dark:bg-gray-800/30 rounded-lg border border-gray-300 dark:border-gray-600/50 items-start hover:bg-gray-100/50 dark:hover:bg-gray-800/50 transition-colors"
            >
              <span className="flex-shrink-0 w-8 h-8 rounded bg-gray-200 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-sm flex items-center justify-center font-bold text-gray-500 dark:text-gray-400 font-mono mt-1">
                0{idx + 1}
              </span>
              <div className="flex-1">
                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-2 mb-2">
                  <h4 className="font-bold text-white text-base">
                    {strat.strategy}
                  </h4>
                  {(strat.est_profit_potential !== undefined || strat.break_even_offer !== undefined) && (
                    <div className="text-right">
                      <div className="text-[10px] text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Break-Even Offer
                      </div>
                      <div className="font-mono text-white font-medium">
                        {strat.break_even_offer !== undefined ? formatCurrency(strat.break_even_offer) : "N/A"}
                      </div>
                    </div>
                  )}
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400 leading-7 whitespace-pre-wrap mb-3">
                  {strat.explanation}
                </p>
                {strat.est_profit_potential !== undefined && (
                  <div className="flex items-center gap-2 text-xs bg-gray-200 dark:bg-gray-700/50 p-2 rounded border border-gray-300 dark:border-gray-600/30 w-fit">
                    <span className="material-symbols-outlined text-sm text-emerald-400">trending_up</span>
                    <span className="text-gray-500 dark:text-gray-400">Est. Profit Potential:</span>
                    <span className="text-emerald-400 font-mono">{formatCurrency(strat.est_profit_potential)}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Municipal Verification Checklist */}
      {verification_checklist && verification_checklist.length > 0 && (
        <div>
          <h3 className="text-lg font-medium text-white mb-4 border-b border-gray-300 dark:border-gray-600/50 pb-2 flex items-center gap-2">
            <span className="material-symbols-outlined text-sm text-gray-500 dark:text-gray-400">fact_check</span>
            Municipal Verification Checklist
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {verification_checklist.map((item, i) => (
              <div
                key={i}
                className="flex items-start gap-3 p-3 bg-gray-100/30 dark:bg-gray-800/30 rounded-lg border border-gray-300 dark:border-gray-600/50"
              >
                <div className="mt-0.5">
                  <span className="material-symbols-outlined text-sm text-primary opacity-70">
                    check_circle
                  </span>
                </div>
                <div>
                  <div className="text-[10px] text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-0.5">
                    {item.category}
                  </div>
                  <div className="text-sm text-white font-medium mb-1">{item.item}</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">{item.action_needed}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
