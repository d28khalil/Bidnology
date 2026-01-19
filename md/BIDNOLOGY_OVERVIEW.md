# Bidnology: Project Overview

## What is Bidnology?

**Bidnology** is an **AI-powered foreclosure investment platform** focused on **New Jersey sheriff sale properties**. The name combines "**Bid**" (auction bidding) + "**-nology**" (technology/knowledge) — essentially "the science/technology of smart bidding."

---

## Core Purpose

Bidnology helps real estate investors discover, analyze, and acquire foreclosure properties through data-driven insights. It solves the problem of **information asymmetry** in the foreclosure market, where valuable data is scattered across 16 different county websites with inconsistent formats.

---

## Key Features

### 1. Data Aggregation
- Scrapes foreclosure listings from **16 New Jersey counties**
- Monitors `salesweb.civilview.com` (official NJ Civil View foreclosure portal)
- Real-time change detection via `changedetection.io`
- Normalizes data across all counties into a unified schema

### 2. Property Enrichment
Integration with Zillow's API provides:
- Property details (beds, baths, sqft, Zestimate)
- Photo galleries and descriptions
- Comparable sales (ARV analysis)
- Price history
- Tax assessment records
- Climate and risk assessment
- Housing market trends
- Owner information

### 3. Deal Intelligence
- **Market Anomaly Detection**: Identifies unusual foreclosure patterns
- **Comparable Sales Analysis**: Determines After Repair Value (ARV)
- **Investment Strategies**: 6 different strategy frameworks
- **ML Ranking**: Machine learning-powered property scoring
- **Financial Analysis**: ROI, spreads, and profit margin calculations

### 4. Workflow Management
- **Kanban Pipeline**: `researching → analyzing → due_diligence → bidding → won/lost/archived`
- **Watchlist System**: Track properties with custom alerts
- **Notes & Collaboration**: Team collaboration tools
- **Portfolio Tracking**: Monitor investments across stages

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 14, React 18, TypeScript, Tailwind CSS, shadcn/ui |
| **Authentication** | Clerk |
| **Database** | Supabase (PostgreSQL) |
| **Backend API** | FastAPI (Python 3.12) |
| **Scraping** | Playwright (browser automation) |
| **AI Processing** | GPT-4o mini (data extraction from HTML) |
| **Infrastructure** | Docker, Coolify |
| **Monitoring** | changedetection.io webhooks |

---

## Supported New Jersey Counties

| County | ID |
|--------|-----|
| Atlantic | 1 |
| Bergen | 2 |
| Burlington | 3 |
| Camden | 6 |
| Cape May | 7 |
| Cumberland | 8 |
| Essex | 9 |
| Gloucester | 10 |
| Hudson | 15 |
| Hunterdon | 17 |
| Middlesex | 19 |
| Monmouth | 20 |
| Morris | 25 |
| Passaic | 32 |
| Salem | 52 |
| Union | 73 |

---

## Target Users

- **Real Estate Investors** — Individual and professional investors
- **Wholesalers** — Quick property flips
- **Landlords** — Rental property acquisitions
- **Contractors** — Fix-and-flip specialists
- **Real Estate Agents** — Working with investor clients

---

## Unique Value Proposition

1. **Comprehensive Coverage** — All NJ counties in one platform
2. **AI-Powered Insights** — Automated property analysis and scoring
3. **Real-Time Updates** — Instant notifications of new listings
4. **Professional Tools** — Institutional-grade analysis for individual investors
5. **Cost-Effective** — Minimal AI costs (~$3-5/month for all counties)

---

## Project Status

| Component | Status |
|-----------|--------|
| Data Pipeline & Scraping | ✅ Complete |
| Backend API (21+ endpoints) | ✅ Complete |
| Frontend UI & Feed | ✅ Complete |
| Authentication | 🟡 Partial |
| Mobile Optimization | 🟡 In Progress |

---

## The Name "Bidnology"

A clever portmanteau positioning the platform as an expert system for auction-based property investment — combining the act of **bidding** with **technology** and **knowledge**.
