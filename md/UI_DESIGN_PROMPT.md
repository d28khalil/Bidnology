# Deal Intelligence Web App - UI Design Prompt for Stitch

---

## High-Level Concept

A sophisticated, data-driven real estate investment platform for sheriff sale and foreclosure property analysis. The app helps investors discover undervalued properties, track deals through a kanban workflow, collaborate with team members, and manage their investment portfolio with AI-powered insights.

---

## Vibe & Aesthetic

**Dark, Professional, Modern, Data-Rich**

- **Primary Mood**: Sophisticated fintech meets pro real estate tool
- **Visual Style**: Deep charcoal/black backgrounds (#0a0a0a, #141414), electric blue accents (#3b82f6), emerald green success indicators (#10b981), amber warning states (#f59e0b)
- **Typography**: Clean sans-serif (Inter or SF Pro) - highly readable at small sizes for dense data tables
- **Design Language**: Minimalist card layouts, subtle borders, glassmorphism overlays, smooth micro-interactions
- **Imagery**: Property photos with subtle overlays, data visualization with charts/graphs, map-based property views

---

## Core Features & Screens

### 1. **Dashboard / Homepage**
- Hero section with key metrics: Total Properties in Pipeline, Active Deals, Portfolio Value, Hot Deal Alerts
- Quick action cards: "Search Properties", "View Kanban", "Portfolio Summary"
- Recent activity feed with deal status updates
- Market anomaly highlights section with property cards

### 2. **Property Search & Discovery**
- Advanced filters sidebar: price range, county, property type, bedrooms/bathrooms, square footage, year built
- Map view toggle (map/list split view)
- Property cards showing: thumbnail, address, list price, estimated ARV, potential profit, hot deal indicators
- Save to watchlist button, quick-add to kanban

### 3. **Kanban Board (Deal Pipeline)**
- Columns: Researching → Analyzing → Due Diligence → Bidding → Won → Lost → Archived
- Draggable property cards with key info
- Stage badges with color coding
- Quick actions: add note, assign to user, share
- Filter by user, county, deal stage

### 4. **Property Detail View**
- Left column: Property image gallery (hero image + thumbnails)
- Center: Property details (address, specs, Zillow data integration)
- Right: Investment analysis panel (ARV, repair estimates, potential profit, comparable sales)
- Tabs below: Notes, Checklist, Activity Timeline, Comps Analysis, Renovation Estimates
- Collaboration: Share button, comments thread, @mentions

### 5. **Notes & Checklist**
- Rich text note editor per property
- Due diligence checklist with checkboxes (inspection complete, title search, liens verified, etc.)
- Notes timeline with user attribution and timestamps

### 6. **Portfolio Tracker**
- Grid/list view of acquired properties
- Purchase price vs current value, profit/loss calculations
- Property performance metrics (cash flow, ROI, equity)
- Filter by strategy type, county, acquisition date

### 7. **Investment Strategies**
- Strategy templates: Fix & Flip, Buy & Hold, Wholesale, BRRRR
- Strategy criteria builder: max purchase price, min ARV spread, target counties, property preferences
- Save and manage multiple strategies

### 8. **Watchlist & Alerts**
- Watched properties with price drop alerts
- New property matching criteria notifications
- Alert history and preferences management

### 9. **Team Collaboration**
- Share properties with team members
- Comments and discussions per property
- Activity feed showing team actions

### 10. **Settings (Admin)**
- Feature toggle switches per module
- County-level settings overrides
- User preference management

---

## UI Components & Patterns

### **Property Card**
```
┌─────────────────────────────────────┐
│ [Thumbnail]  🏷️ Hot Deal         │
│                                      │
│ 123 Main St, Jacksonville, FL       │
│ Listed: $95,000 | ARV: $185,000     │
│ Potential Profit: $52,000 (55%)     │
│                                      │
│ [View Details] [💾 Save] [👁️ Watch] │
└─────────────────────────────────────┘
```

### **Kanban Column Header**
```
┌─────────────────────────────────────┐
│ Analyzing         (12)    [↓]     │
│ ────────────────────────────────── │
└─────────────────────────────────────┘
```

### **Navigation**
- Sidebar navigation with icons and labels
- Active state highlighted with accent color
- Collapsible sections
- User avatar and settings in top-right

### **Buttons**
- Primary: Electric blue, rounded corners, subtle hover lift
- Secondary: Outlined, same blue border
- Destructive: Red/pink for delete/remove actions
- Icon-only buttons for quick actions

---

## Color Palette Specification

| Purpose | Color |
|---------|-------|
| Background (primary) | #0a0a0a |
| Background (secondary) | #141414 |
| Background (tertiary) | #1c1c1c |
| Card surface | #1e1e1e |
| Border | #2a2a2a |
| Primary accent | #3b82f6 |
| Primary hover | #2563eb |
| Success | #10b981 |
| Warning | #f59e0b |
| Error | #ef4444 |
| Text (primary) | #f5f5f5 |
| Text (secondary) | #a3a3a3 |
| Text (muted) | #737373 |

---

## Tech Stack Recommendations

### **Frontend Framework**
- **Next.js 14+** with App Router - SSR, API routes, excellent performance
- **shadcn/ui** - Modern component library built on Radix UI + Tailwind
- **Tailwind CSS** - Utility-first styling with custom dark mode config

### **State Management**
- **Zustand** - Lightweight, minimal boilerplate
- OR **TanStack Query (React Query)** - For server state caching and synchronization

### **Data Visualization**
- **Recharts** - Simple, responsive charts
- OR **TanStack Virtual** - For virtualized long lists

### **Maps**
- **Mapbox GL JS** - Customizable, dark mode support
- OR **Google Maps** with dark theme

### **Forms & Validation**
- **React Hook Form** + **Zod** - Type-safe validation
- **TanStack Table** - Powerful table component with sorting, filtering, pagination

### **Real-time Updates**
- **Supabase Realtime** - WebSocket for live collaboration
- OR **Pusher** - Alternative for real-time features

### **Charts & Analytics**
- **Recharts** - Line charts for price history, bar charts for portfolio stats
- **Trend Micro** - Small sparkline charts for property cards

### **Icons**
- **Lucide React** - Consistent icon set, tree-shakeable
- **Heroicons** - Alternative icon set

### **Date/Time**
- **date-fns** - Lightweight date formatting
- OR **Day.js** - Alternative date library

---

## Screen-by-Screen Build Order

### Phase 1: Core Structure
1. Layout with sidebar navigation and top header
2. Authentication pages (login/signup)
3. Dashboard home with metrics cards

### Phase 2: Property Discovery
4. Property search page with filters
5. Property card component
6. Property detail page with tabs

### Phase 3: Deal Management
7. Kanban board with drag-and-drop
8. Notes editor component
9. Checklist component

### Phase 4: Portfolio & Strategies
10. Portfolio tracker page
11. Investment strategies manager
12. Watchlist and alerts

### Phase 5: Collaboration
13. Comments/discussion component
14. Share properties modal
15. Activity feed

---

## Stitch Prompt - Starting Point

> Create a modern, dark-themed real estate investment dashboard for analyzing sheriff sale and foreclosure properties. The app has a sidebar navigation with these main sections: Dashboard, Properties, Kanban Board, Portfolio, Watchlist, and Settings.
>
> The design should use deep charcoal backgrounds (#0a0a0a) with electric blue accents (#3b82f6) and emerald green for success states. Use a clean sans-serif font like Inter. Property cards should display the address, list price, estimated after-repair value (ARV), and potential profit percentage. Include badges for "hot deal" indicators.
>
> On the dashboard, show metric cards at the top for Total Pipeline, Active Deals, and Portfolio Value. Below that, show a row of recently updated properties and a section for market anomalies.
>
> Use minimalist card layouts with subtle borders, glassmorphism effects, and smooth hover animations. Buttons should have rounded corners with a subtle lift effect on hover.

---

## Sub-Prompts for Iteration

### After initial design:
> "Add a kanban board page with 5 columns: Researching, Analyzing, Due Diligence, Bidding, and Won. Property cards should be draggable between columns. Each card shows the property address, a small thumbnail, price, and stage badge."

### For property detail:
> "Property detail page should have a 3-column layout: left column for image gallery, center for property specs and Zillow data, right for investment analysis panel. Below, add 5 tabs: Notes, Checklist, Timeline, Comps, and Renovation."

### For collaboration:
> "Add a share button that opens a modal to select team members. Include a comments section on property detail with @mentions and threaded discussions."

### For portfolio:
> "Portfolio page should show acquired properties in a table with columns for Property, Purchase Price, Current Value, Profit/Loss, Cash Flow, and ROI. Add summary cards at the top showing Total Invested, Total Value, and Total Return."

---

## Responsive Requirements

- Desktop: Full 3-column layouts, sidebar navigation
- Tablet: 2-column layouts, collapsible sidebar
- Mobile: Single column, bottom navigation bar, stacked cards

---

## Accessibility

- Focus states on all interactive elements
- Keyboard navigation support
- ARIA labels for icons and buttons
- High contrast for text (WCAG AA compliant)
- Touch targets minimum 44px

---

## Performance Considerations

- Lazy load images in property feeds
- Virtual scrolling for long lists (1000+ properties)
- Debounce search inputs (300ms delay)
- Cache API responses with TanStack Query
- Optimize images with WebP format

---

## Brand Elements to Consider

- App Name: **DealFlow** OR **SheriffIQ** OR **ForeclosureFinder**
- Logo: Simple, geometric house/chart icon
- Favicon: Mini property icon with upward trend arrow

---

## Data Visualization Needs

- Line charts: Property price history over time
- Bar charts: Monthly deal volume by county
- Pie charts: Portfolio distribution by strategy
- Sparklines: Mini trend indicators on property cards
- Progress bars: Due diligence checklist completion
- Heat maps: County-level deal density on map view

---

## Additional Notes for Stitch

- Prioritize readability of numerical data (prices, percentages)
- Use consistent formatting for currency ($95,000) and percentages (55%)
- Add subtle visual hierarchy with font weights and colors
- Include loading states and skeletons for async data
- Design empty states with helpful CTAs for all major sections
- Consider adding a "Quick Actions" floating action button for mobile
- Make the hot deal badge prominent with a pulsing animation
- Use tooltips for abbreviated metrics (ARV, ROI, BRRRR)
