# Investment Metrics Calculation

**Version:** 1.0
**Date:** December 27, 2025

---

## Overview

This document defines the investment metrics calculated from Zillow enrichment data, including the formulas used and the configurable parameters.

---

## Table of Contents

- [Configurable Parameters](#configurable-parameters)
- [Core Metrics](#core-metrics)
- [Rental ROI Metrics](#rental-roi-metrics)
- [Flipping Metrics](#flipping-metrics)
- [Risk Metrics](#risk-metrics)
- [Score Calculations](#score-calculations)

---

## Configurable Parameters

All parameters are configurable per:
- **Admin** (global defaults)
- **County** (overrides by location)
- **User** (if allowed by admin)

### Parameter Table

| Parameter | Default | Description |
|-----------|---------|-------------|
| `inv_annual_appreciation` | 0.03 (3%) | Expected annual property value increase |
| `inv_mortgage_rate` | 0.045 (4.5%) | Annual mortgage interest rate |
| `inv_down_payment_rate` | 0.20 (20%) | Down payment as percentage of purchase price |
| `inv_insurance_rate` | 0.015 (1.5%) | Annual insurance as percentage of property value |
| `inv_loan_term_months` | 360 (30 years) | Mortgage loan term in months |
| `inv_maintenance_rate` | 0.10 (10%) | Annual maintenance as percentage of rent |
| `inv_property_mgmt_rate` | 0.10 (10%) | Annual property management as percentage of rent |
| `inv_property_tax_rate` | 0.012 (1.2%) | Annual property tax as percentage of value |
| `inv_vacancy_rate` | 0.05 (5%) | Vacancy rate (percentage of time unrented) |
| `inv_renovation_cost` | 25000 | Fixed renovation budget (for flips) |

### Parameter Sources

From `/custom_ae/searchbyaddress` API, these are passed as query params:

| API Parameter | Database Field | Default |
|---------------|----------------|---------|
| `v_aa` | `inv_annual_appreciation` | 0.03 |
| `v_cmr` | `inv_mortgage_rate` | 0.045 |
| `v_dpr` | `inv_down_payment_rate` | 0.20 |
| `v_ir` | `inv_insurance_rate` | 0.015 |
| `v_ltm` | `inv_loan_term_months` | 360 |
| `v_mr` | `inv_maintenance_rate` | 0.10 |
| `v_pmr` | `inv_property_mgmt_rate` | 0.10 |
| `v_ptr` | `inv_property_tax_rate` | 0.012 |
| `v_vr` | `inv_vacancy_rate` | 0.05 |
| `v_rc` | `inv_renovation_cost` | 25000 |

---

## Core Metrics

### 1. ARV (After Repair Value)

**Definition:** Estimated market value after repairs.

**Calculation:**
```python
def calculate_arv(comps: List[Dict]) -> Dict[str, float]:
    # Use only active listings (FOR_SALE status)
    active_comps = [c for c in comps if c.get("homeStatus") == "FOR_SALE"]

    if not active_comps:
        return None

    prices = [c["price"] for c in active_comps if c.get("price")]

    return {
        "arv_low": min(prices),          # Lowest comp
        "arv_high": max(prices),         # Highest comp
        "arv_median": median(prices),    # Median comp (primary ARV)
        "arv_avg": sum(prices) / len(prices)  # Average comp
    }
```

**Data Source:** `/similar` endpoint

---

### 2. Purchase Price

**Definition:** Current listing price or auction starting bid.

**Calculation:**
```python
purchase_price = property.get("Price") or property.get("zestimate")
```

**Data Source:** `/pro/byaddress` endpoint

---

### 3. Repair Estimate

**Definition:** Estimated cost to bring property to market condition.

**Calculation:**
```python
def estimate_repair_cost(
    year_built: int,
    sqft: int,
    image_count: int,
    fixed_budget: int
) -> int:
    # Base calculation from image analysis (TODO: implement AI vision)
    base_per_sqft = 10  # $10/sqft base assumption

    # Age factor
    age = 2025 - year_built
    age_factor = min(age * 0.5, 15)  # Max $15/sqft for age

    # Image quality factor (more images = better documented condition)
    image_factor = max(0, (50 - image_count) * 0.1)

    per_sqft = base_per_sqft + age_factor + image_factor

    # Use configured renovation cost as ceiling
    calculated = sqft * per_sqft

    return min(calculated, fixed_budget)
```

**Data Sources:** `/custom_ad/byzpid` (images), `/pro/byaddress` (year built, sqft)

---

## Rental ROI Metrics

### 4. Monthly Mortgage Payment

**Definition:** Principal and interest payment.

**Calculation:**
```python
def calculate_monthly_mortgage(
    purchase_price: float,
    down_payment_rate: float,
    annual_rate: float,
    loan_term_months: int
) -> float:
    # Loan amount
    down_payment = purchase_price * down_payment_rate
    principal = purchase_price - down_payment

    # Monthly interest rate
    monthly_rate = annual_rate / 12

    # Mortgage formula
    if monthly_rate == 0:
        return principal / loan_term_months

    payment = principal * (
        monthly_rate * (1 + monthly_rate) ** loan_term_months
    ) / ((1 + monthly_rate) ** loan_term_months - 1)

    return payment
```

**Parameters Used:**
- `inv_down_payment_rate`
- `inv_mortgage_rate`
- `inv_loan_term_months`

---

### 5. Monthly Expenses

**Definition:** Total monthly ownership costs.

**Calculation:**
```python
def calculate_monthly_expenses(
    purchase_price: float,
    monthly_mortgage: float,
    property_tax_rate: float,
    insurance_rate: float,
    maintenance_rate: float,
    property_mgmt_rate: float,
    vacancy_rate: float
) -> Dict[str, float]:
    # Annual expenses converted to monthly
    property_tax = (purchase_price * property_tax_rate) / 12
    insurance = (purchase_price * insurance_rate) / 12

    # Fixed expenses
    fixed = monthly_mortgage + property_tax + insurance

    # Variable expenses (percentage of monthly rent)
    # These are calculated per-property based on actual rent
    return {
        "mortgage": monthly_mortgage,
        "property_tax": property_tax,
        "insurance": insurance,
        "fixed_total": fixed,
        "maintenance_rate": maintenance_rate,
        "property_mgmt_rate": property_mgmt_rate,
        "vacancy_rate": vacancy_rate
    }
```

**Parameters Used:**
- `inv_property_tax_rate`
- `inv_insurance_rate`
- `inv_maintenance_rate`
- `inv_property_mgmt_rate`
- `inv_vacancy_rate`

---

### 6. Monthly Cash Flow

**Definition:** Net profit per month from rental.

**Calculation:**
```python
def calculate_monthly_cash_flow(
    monthly_rent: float,
    monthly_expenses: Dict,
    maintenance_rate: float,
    property_mgmt_rate: float,
    vacancy_rate: float
) -> float:
    # Variable expenses
    maintenance = monthly_rent * maintenance_rate
    property_mgmt = monthly_rent * property_mgmt_rate
    vacancy_loss = monthly_rent * vacancy_rate

    # Total expenses
    total_expenses = (
        monthly_expenses["mortgage"] +
        monthly_expenses["property_tax"] +
        monthly_expenses["insurance"] +
        maintenance +
        property_mgmt +
        vacancy_loss
    )

    return monthly_rent - total_expenses
```

**Data Source:** `/pro/byaddress` (rentZestimate)

---

### 7. Cash on Cash Return

**Definition:** Annual cash flow as percentage of initial cash invested.

**Calculation:**
```python
def calculate_cash_on_cash_return(
    monthly_cash_flow: float,
    purchase_price: float,
    down_payment_rate: float,
    closing_costs: float = 3000
) -> float:
    # Total initial cash investment
    down_payment = purchase_price * down_payment_rate
    total_cash = down_payment + closing_costs

    # Annual cash flow
    annual_cash_flow = monthly_cash_flow * 12

    # Cash on cash return
    if total_cash == 0:
        return 0

    return (annual_cash_flow / total_cash) * 100
```

---

### 8. Cap Rate

**Definition:** Net operating income as percentage of property value.

**Calculation:**
```python
def calculate_cap_rate(
    monthly_rent: float,
    purchase_price: float,
    property_tax_rate: float,
    insurance_rate: float,
    maintenance_rate: float,
    property_mgmt_rate: float,
    vacancy_rate: float
) -> float:
    # Annual rent adjusted for vacancy
    annual_rent = monthly_rent * 12 * (1 - vacancy_rate)

    # Annual operating expenses (excluding mortgage)
    property_tax = purchase_price * property_tax_rate
    insurance = purchase_price * insurance_rate
    maintenance = annual_rent * maintenance_rate
    property_mgmt = annual_rent * property_mgmt_rate

    total_expenses = property_tax + insurance + maintenance + property_mgmt

    # Net operating income
    noi = annual_rent - total_expenses

    # Cap rate
    if purchase_price == 0:
        return 0

    return (noi / purchase_price) * 100
```

---

### 9. Total Return (5-Year)

**Definition:** Total profit over 5 years including appreciation.

**Calculation:**
```python
def calculate_total_return_5yr(
    purchase_price: float,
    monthly_cash_flow: float,
    annual_appreciation: float
) -> float:
    # Annual cash flow
    annual_cash_flow = monthly_cash_flow * 12

    # 5-year cash flow total
    total_cash_flow = annual_cash_flow * 5

    # Appreciation over 5 years (compound)
    future_value = purchase_price * (1 + annual_appreciation) ** 5
    appreciation_gain = future_value - purchase_price

    # Total return
    total_return = total_cash_flow + appreciation_gain

    # As percentage of initial investment
    down_payment = purchase_price * 0.20  # Assuming 20% down
    return (total_return / down_payment) * 100
```

**Parameters Used:**
- `inv_annual_appreciation`
- `inv_down_payment_rate`

---

## Flipping Metrics

### 10. Maximum Allowable Offer (MAO)

**Definition:** Highest price to pay while hitting target ROI.

**Calculation:**
```python
def calculate_mao(
    arv: float,
    repair_cost: float,
    closing_costs: float = 10000,
    target_roi: float = 0.30,  # 30% profit margin
    carrying_months: int = 6,
    monthly_carrying: float = 1000
) -> float:
    # Total costs
    total_closing = closing_costs + (carrying_months * monthly_carrying)

    # Target profit
    target_profit = arv * target_roi

    # MAO formula
    mao = arv - repair_cost - total_closing - target_profit

    return max(0, mao)
```

---

### 11. Fix & Flip Profit

**Definition:** Expected profit from flipping.

**Calculation:**
```python
def calculate_flip_profit(
    purchase_price: float,
    arv: float,
    repair_cost: float,
    closing_costs: float = 10000,
    carrying_months: int = 6,
    monthly_carrying: float = 1000
) -> Dict[str, float]:
    # Total costs
    total_closing = closing_costs + (carrying_months * monthly_carrying)
    total_investment = purchase_price + repair_cost + total_closing

    # Profit
    profit = arv - total_investment

    # ROI
    roi = (profit / total_investment) * 100 if total_investment > 0 else 0

    return {
        "profit": profit,
        "roi_percent": roi,
        "total_investment": total_investment,
        "break_even_price": total_investment
    }
```

---

### 12. ARV Spread

**Definition:** Difference between ARV and purchase price.

**Calculation:**
```python
def calculate_arv_spread(purchase_price: float, arv: float) -> Dict[str, float]:
    spread = arv - purchase_price
    spread_pct = (spread / purchase_price) * 100 if purchase_price > 0 else 0

    return {
        "spread_amount": spread,
        "spread_percent": spread_pct
    }
```

---

## Risk Metrics

### 13. Price Volatility Score

**Definition:** How much the property's price has changed.

**Calculation:**
```python
def calculate_price_volatility(price_history: List[Dict]) -> float:
    if len(price_history) < 2:
        return 0

    # Calculate percentage changes
    changes = []
    for i in range(1, len(price_history)):
        prev_price = price_history[i-1].get("price", 0)
        curr_price = price_history[i].get("price", 0)

        if prev_price > 0:
            pct_change = abs((curr_price - prev_price) / prev_price)
            changes.append(pct_change)

    if not changes:
        return 0

    # Return standard deviation
    return statistics.stdev(changes)
```

**Data Source:** `/pricehistory` endpoint

---

### 14. Climate Risk Score

**Definition:** Composite risk from climate hazards.

**Calculation:**
```python
def calculate_climate_risk_score(climate_data: Dict) -> Dict[str, Any]:
    # Zillow returns scores (typically 0-10 scale)
    flood_risk = climate_data.get("flood", {}).get("riskScore", 0)
    fire_risk = climate_data.get("fire", {}).get("riskScore", 0)
    storm_risk = climate_data.get("storm", {}).get("riskScore", 0)

    # Composite score (average)
    composite = (flood_risk + fire_risk + storm_risk) / 3

    # Risk category
    if composite < 3:
        category = "Low"
    elif composite < 6:
        category = "Moderate"
    elif composite < 8:
        category = "High"
    else:
        category = "Severe"

    return {
        "composite_score": composite,
        "category": category,
        "flood_risk": flood_risk,
        "fire_risk": fire_risk,
        "storm_risk": storm_risk
    }
```

**Data Source:** `/climate` endpoint

---

### 15. Market Health Score

**Definition:** How healthy the local market is.

**Calculation:**
```python
def calculate_market_health_score(housing_market: Dict) -> Dict[str, Any]:
    # Get market indicators
    zhvi = housing_market.get("zhvi", 0)
    pct_change_1yr = housing_market.get("percentageChange", {}).get("1yr", 0)
    pct_change_5yr = housing_market.get("percentageChange", {}).get("5yr", 0)

    # Health factors
    appreciation_trend = 1 if pct_change_1yr > 0 else -1
    long_term_growth = 1 if pct_change_5yr > 0 else -1

    # Score (0-100)
    score = 50 + (pct_change_1yr * 10) + (pct_change_5yr * 2)
    score = max(0, min(100, score))

    # Category
    if score >= 70:
        category = "Hot"
    elif score >= 50:
        category = "Healthy"
    elif score >= 30:
        category = "Cooling"
    else:
        category = "Cold"

    return {
        "score": score,
        "category": category,
        "zhvi": zhvi,
        "appreciation_1yr": pct_change_1yr,
        "appreciation_5yr": pct_change_5yr
    }
```

**Data Source:** `/housing_market` endpoint

---

### 16. Location Score

**Definition:** Walkability and transit access.

**Calculation:**
```python
def calculate_location_score(walk_data: Dict) -> Dict[str, Any]:
    walk_score = walk_data.get("walkScore", 0)
    transit_score = walk_data.get("transitScore", 0)
    bike_score = walk_data.get("bikeScore", 0)

    # Weighted composite (walkability most important for rentals)
    composite = (walk_score * 0.5) + (transit_score * 0.3) + (bike_score * 0.2)

    # Desirability for renters
    if walk_score >= 80:
        renter_appeal = "Excellent"
    elif walk_score >= 60:
        renter_appeal = "Good"
    elif walk_score >= 40:
        renter_appeal = "Fair"
    else:
        renter_appeal = "Poor"

    return {
        "walk_score": walk_score,
        "transit_score": transit_score,
        "bike_score": bike_score,
        "composite_score": composite,
        "renter_appeal": renter_appeal
    }
```

**Data Source:** `/walk_transit_bike` endpoint

---

## Score Calculations

### Overall Investment Score

**Definition:** Combined score for ranking properties.

**Calculation:**
```python
def calculate_investment_score(metrics: Dict) -> Dict[str, Any]:
    scores = {}

    # Cash flow score (0-25 points)
    cash_flow = metrics.get("monthly_cash_flow", 0)
    if cash_flow > 500:
        scores["cash_flow"] = 25
    elif cash_flow > 200:
        scores["cash_flow"] = 15
    elif cash_flow > 0:
        scores["cash_flow"] = 5
    else:
        scores["cash_flow"] = 0

    # ARV spread score (0-25 points)
    arv_spread_pct = metrics.get("arv_spread_percent", 0)
    if arv_spread_pct > 50:
        scores["arv_spread"] = 25
    elif arv_spread_pct > 30:
        scores["arv_spread"] = 15
    elif arv_spread_pct > 10:
        scores["arv_spread"] = 5
    else:
        scores["arv_spread"] = 0

    # Market health score (0-25 points)
    market_health = metrics.get("market_health_score", 50)
    scores["market"] = min(25, market_health / 4)

    # Risk penalty (0-25 points, subtract for risk)
    climate_risk = metrics.get("climate_composite_score", 0)
    volatility = metrics.get("price_volatility", 0)
    risk_penalty = min(25, (climate_risk * 2) + (volatility * 50))
    scores["risk"] = 25 - risk_penalty

    # Total score
    total = sum(scores.values())

    # Grade
    if total >= 80:
        grade = "A"
    elif total >= 60:
        grade = "B"
    elif total >= 40:
        grade = "C"
    elif total >= 20:
        grade = "D"
    else:
        grade = "F"

    return {
        "total_score": total,
        "grade": grade,
        "breakdown": scores
    }
```

---

## Pre-Calculated Metrics (from API)

The `/custom_ae/searchbyaddress` endpoint returns pre-calculated metrics:

```json
{
  "rental_metrics": {
    "monthlyCashFlow": 1093.75,
    "cashOnCashReturn": 50.5,
    "capRate": 267.3,
    "roi": 50.5,
    "totalReturn5yr": 268.3
  }
}
```

When this endpoint is enabled, these values are used directly instead of recalculating.

---

## Formula Summary Table

| Metric | Formula | Key Inputs |
|--------|---------|------------|
| **ARV** | Median of active comps | `/similar` prices |
| **Monthly Mortgage** | P&I formula | Price, down %, rate, term |
| **Cash Flow** | Rent - All expenses | Rent, mortgage, taxes, insurance, etc. |
| **Cash on Cash** | (Annual CF / Cash Invested) × 100 | Cash flow, down payment |
| **Cap Rate** | (NOI / Value) × 100 | Rent, expenses, price |
| **MAO** | ARV - Repairs - Costs - Target Profit | ARV, repairs, target ROI |
| **Flip Profit** | ARV - (Price + Repairs + Costs) | ARV, price, repairs |
| **Volatility** | StdDev of price changes | `/pricehistory` |
| **Climate Risk** | Avg of hazard scores | `/climate` |
| **Investment Score** | Weighted sum of factors | All metrics |

---

## Example Calculation

**Input Property:**
- Address: 1875 AVONDALE Circle, Jacksonville, FL 32205
- Purchase Price: $3,000,000
- Rent Zestimate: $15,000/month
- ARV (median comp): $3,850,000
- Year Built: 1927
- Sqft: 7,526
- Comps: 20 active listings

**Parameters (Flipper template):**
- Down payment: 20%
- Mortgage rate: 4.5%
- Annual appreciation: 3%
- Renovation budget: $50,000

**Calculated Metrics:**

| Metric | Value |
|--------|-------|
| ARV | $3,850,000 |
| ARV Spread | $850,000 (28%) |
| Down Payment | $600,000 |
| Loan Amount | $2,400,000 |
| Monthly Mortgage | $12,146 |
| Monthly Property Tax | $3,000 |
| Monthly Insurance | $3,750 |
| Monthly Rent | $15,000 |
| Monthly Cash Flow | -$3,896 (negative, not a rental) |
| MAO (30% ROI) | $2,495,000 |
| Flip Profit | $735,000 |
| Flip ROI | 22% |
| Investment Grade | B |

**Conclusion:** Good flip candidate (high ARV spread), poor rental choice (negative cash flow).
