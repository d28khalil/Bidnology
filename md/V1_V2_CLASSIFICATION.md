# V1 vs V2 Feature Classification

## Swagger API Tags

### V1 Tags (Core MVP Features)
- **Enrichment (V1)** - Zillow property enrichment (properties, status, templates, user prefs)
- **Deal Intelligence (V1)** - Market anomalies, comps, saved properties, kanban, watchlist, alerts, notes, checklist, deal criteria, data quality, street view, CSV export

### V2 Tags (Advanced Features)
- **Enrichment (V2)** - County-level settings settings
- **Deal Intelligence (V2)** - Portfolio tracking, team collaboration, investment strategies, renovation estimator, mobile push notifications

---

## Supabase Tables Classification

### V1 Core Tables (Active in MVP)

| Table | Purpose | Status |
|-------|---------|--------|
| `foreclosure_listings` | Raw foreclosure data | ✅ Core |
| `zillow_enrichment` | Enriched property data | ✅ Core |
| `nj_counties` | County reference | ✅ Core |
| `deal_features_admin_settings` | Feature toggles (V1: 6 features) | ✅ Core |
| `market_anomalies` | Price anomaly results | ✅ Core |
| `comparable_sales_analysis` | Comps analysis | ✅ Core |
| `saved_properties` | Saved + Kanban | ✅ Core |
| `user_watchlist` | Watchlist | ✅ Core |
| `user_alerts` | Alert queue | ✅ Core |
| `property_notes` | User notes | ✅ Core |
| `due_diligence_checklists` | Task tracking | ✅ Core |
| `user_deal_criteria` | Deal criteria matching | ✅ Core |

### V2 Only Tables (Rename with V2_ prefix when ready)

| Table Name | V2 Name (when implemented) | Feature | Reason for V2 |
|------------|---------------------------|---------|---------------|
| `deal_features_county_settings` | `V2_deal_features_county_settings` | County-level settings | Too complex for V1 MVP |
| `user_portfolio` | `V2_user_portfolio` | Portfolio tracking | Strays from core mission (acquired properties) |
| `shared_properties` | `V2_shared_properties` | Team collaboration | V2: Team collaboration |
| `property_comments` | `V2_property_comments` | Team collaboration | V2: Team collaboration |
| `mobile_push_tokens` | `V2_mobile_push_tokens` | Mobile notifications | V2: Mobile notifications |
| `push_notification_queue` | `V2_push_notification_queue` | Mobile notifications | V2: Mobile notifications |
| `investment_strategies` | `V2_investment_strategies` | Advanced features | V2: Advanced features |
| `renovation_estimates` | `V2_renovation_estimates` | Advanced features | V2: GPT-4o Vision feature |
| `deal_features_user_preferences` | `V2_deal_features_user_preferences` | County settings | Simplified to user_settings for V1 |

---

## API Endpoint Mapping

### V1 Endpoints (Core MVP)

#### Enrichment (V1)
- `GET /api/enrichment/status` - Enrichment statistics
- `GET /api/enrichment/properties/{id}` - Get property with enrichment
- `POST /api/enrichment/properties/{id}/enrich` - Trigger enrichment
- `GET /api/enrichment/properties/{id}/skip-trace` - Get skip trace data
- `POST /api/enrichment/properties/{id}/skip-trace` - Skip trace property
- `POST /api/enrichment/skip-trace/batch` - Batch skip trace
- `GET /api/enrichment/settings/admin` - Get admin settings
- `PUT /api/enrichment/settings/admin` - Update admin settings
- `GET /api/enrichment/settings/user/{user_id}` - List user preferences
- `GET /api/enrichment/settings/user/{user_id}/{county_id}/{state}` - Get user preferences
- `POST /api/enrichment/settings/user` - Create user preferences
- `PUT /api/enrichment/settings/user/{user_id}/{county_id}/{state}` - Update user preferences
- `DELETE /api/enrichment/settings/user/{user_id}/{county_id}/{state}` - Delete user preferences
- `GET /api/enrichment/settings/resolve/{county_id}/{state}` - Resolve settings
- `GET /api/enrichment/templates` - List templates
- `GET /api/enrichment/templates/{template_name}` - Get template
- `POST /api/enrichment/templates/apply` - Apply template

#### Deal Intelligence (V1)
- `GET /api/deal-intelligence/health` - Health check
- `GET /api/deal-intelligence/settings/admin` - Get admin feature settings
- `PUT /api/deal-intelligence/settings/admin` - Update admin feature settings
- `GET /api/deal-intelligence/settings/user/{user_id}` - Get user preferences
- `POST /api/deal-intelligence/settings/user` - Create user preferences
- `PUT /api/deal-intelligence/settings/user/{user_id}` - Update user preferences
- `DELETE /api/deal-intelligence/settings/user/{user_id}` - Delete user preferences
- `GET /api/deal-intelligence/market-anomalies` - Get anomalies
- `GET /api/deal-intelligence/market-anomalies/property/{id}` - Get property anomaly
- `POST /api/deal-intelligence/market-anomalies/analyze` - Analyze property
- `PUT /api/deal-intelligence/market-anomalies/{id}/verify` - Verify anomaly
- `GET /api/deal-intelligence/comparable-sales/{property_id}` - Get comps
- `POST /api/deal-intelligence/comparable-sales/analyze` - Analyze comps
- `GET /api/deal-intelligence/saved/{user_id}` - Get saved properties
- `POST /api/deal-intelligence/saved` - Save property
- `DELETE /api/deal-intelligence/saved/{id}` - Unsave property
- `PUT /api/deal-intelligence/saved/stage` - Move stage
- `GET /api/deal-intelligence/saved/{user_id}/kanban` - Get kanban board
- `PUT /api/deal-intelligence/saved/{saved_id}/notes` - Update notes
- `GET /api/deal-intelligence/saved/{user_id}/stats` - Get saved stats
- `POST /api/deal-intelligence/saved/bulk-update` - Bulk update stages
- `GET /api/deal-intelligence/watchlist/{user_id}` - Get watchlist
- `POST /api/deal-intelligence/watchlist` - Add to watchlist
- `DELETE /api/deal-intelligence/watchlist/{id}` - Remove from watchlist
- `PUT /api/deal-intelligence/watchlist/{id}` - Update watchlist entry
- `GET /api/deal-intelligence/alerts/{user_id}` - Get alerts
- `PUT /api/deal-intelligence/alerts/{id}/read` - Mark alert read
- `PUT /api/deal-intelligence/alerts/{user_id}/read-all` - Mark all alerts read
- `DELETE /api/deal-intelligence/alerts/{id}` - Delete alert
- `POST /api/deal-intelligence/checklist/{property_id}/{user_id}/reset` - Reset checklist
- `GET /api/deal-intelligence/criteria/{user_id}` - Get deal criteria
- `POST /api/deal-intelligence/criteria` - Save deal criteria
- `GET /api/deal-intelligence/matches/{user_id}` - Get matching properties
- `POST /api/deal-intelligence/criteria/{user_id}/test` - Test property match
- `GET /api/deal-intelligence/quality/{property_id}` - Get quality score
- `POST /api/deal-intelligence/quality/score` - Trigger quality scoring
- `GET /api/deal-intelligence/notes/{property_id}` - Get notes
- `POST /api/deal-intelligence/notes` - Add note
- `PUT /api/deal-intelligence/notes/{note_id}` - Update note
- `DELETE /api/deal-intelligence/notes/{note_id}` - Delete note
- `GET /api/deal-intelligence/checklist/{property_id}/{user_id}` - Get checklist
- `PUT /api/deal-intelligence/checklist/{property_id}/{user_id}` - Update checklist
- `POST /api/deal-intelligence/street-view` - Get Street View images
- `POST /api/deal-intelligence/export/csv` - Export to CSV

### V2 Endpoints (Advanced Features - Tag with Deal Intelligence (V2))

#### Enrichment (V2) - County Settings
- `GET /api/enrichment/settings/county` - List all county settings
- `GET /api/enrichment/settings/county/{county_id}/{state}` - Get county settings
- `POST /api/enrichment/settings/county` - Create county settings
- `PUT /api/enrichment/settings/county/{county_id}/{state}` - Update county settings
- `DELETE /api/enrichment/settings/county/{county_id}/{state}` - Delete county settings

#### Deal Intelligence (V2) - Investment Strategies
- `GET /api/deal-intelligence/strategies/{user_id}` - Get strategies
- `POST /api/deal-intelligence/strategies` - Create strategy
- `GET /api/deal-intelligence/strategies/{user_id}/{strategy_id}` - Get strategy
- `PUT /api/deal-intelligence/strategies/{strategy_id}` - Update strategy
- `DELETE /api/deal-intelligence/strategies/{strategy_id}` - Delete strategy
- `PUT /api/deal-intelligence/strategies/{strategy_id}/set-default` - Set default strategy
- `POST /api/deal-intelligence/strategies/{strategy_id}/evaluate/{property_id}` - Evaluate property

#### Deal Intelligence (V2) - Renovation Estimator
- `POST /api/deal-intelligence/renovation/estimate` - Create renovation estimate
- `GET /api/deal-intelligence/renovation/estimate/{property_id}` - Get renovation estimate
- `PUT /api/deal-intelligence/renovation/estimate/{estimate_id}` - Update renovation estimate

#### Deal Intelligence (V2) - Portfolio Tracking (Commented out in code)
- `GET /api/deal-intelligence/portfolio/{user_id}` - Get portfolio
- `GET /api/deal-intelligence/portfolio/{user_id}/summary` - Get portfolio summary
- `POST /api/deal-intelligence/portfolio` - Add to portfolio
- `GET /api/deal-intelligence/portfolio/entry/{entry_id}` - Get portfolio entry
- `PUT /api/deal-intelligence/portfolio/entry/{entry_id}` - Update portfolio entry
- `DELETE /api/deal-intelligence/portfolio/entry/{entry_id}` - Remove from portfolio

#### Deal Intelligence (V2) - Team Collaboration
- `POST /api/deal-intelligence/collaboration/share` - Share property
- `DELETE /api/deal-intelligence/collaboration/share/{share_id}` - Unshare property
- `GET /api/deal-intelligence/collaboration/shared-with-me/{user_id}` - Get shared with me
- `GET /api/deal-intelligence/collaboration/shared-by-me/{user_id}` - Get shared by me
- `POST /api/deal-intelligence/collaboration/comments` - Add comment
- `GET /api/deal-intelligence/collaboration/comments/{property_id}` - Get comments
- `PUT /api/deal-intelligence/collaboration/comments/{comment_id}` - Update comment
- `DELETE /api/deal-intelligence/collaboration/comments/{comment_id}` - Delete comment

#### Deal Intelligence (V2) - Mobile Push Notifications
- `POST /api/deal-intelligence/notifications/register` - Register device token
- `DELETE /api/deal-intelligence/notifications/token/{token_id}` - Unregister token
- `POST /api/deal-intelligence/notifications/create` - Create notification
- `PUT /api/deal-intelligence/notifications/token/{token_id}/preferences` - Update preferences
- `GET /api/deal-intelligence/notifications/{user_id}/history` - Get history
- `PUT /api/deal-intelligence/notifications/{notification_id}/opened` - Mark opened

---

## Implementation Notes

### For V1 Development:
1. Use only tables marked as **V1 Core**
2. Use only endpoints tagged with **Enrichment (V1)** or **Deal Intelligence (V1)**
3. County settings endpoints are V2 only - ignore for now
4. Portfolio, collaboration, investment strategies, renovation, mobile push are V2 only

### For V2 Development:
1. Create V2_ prefixed versions of V2-only tables
2. Uncomment portfolio endpoints (currently commented out with # V2 ONLY)
3. Add V2 tags to all V2 endpoints

---

## Migration Path (V1 → V2)

When ready to implement V2:
1. Create migration to rename tables with V2_ prefix
   - `deal_features_county_settings` → `V2_deal_features_county_settings`
   - `user_portfolio` → `V2_user_portfolio`
   - `shared_properties` → `V2_shared_properties`
   - `property_comments` → `V2_property_comments`
   - `mobile_push_tokens` → `V2_mobile_push_tokens`
   - `push_notification_queue` → `V2_push_notification_queue`
   - `investment_strategies` → `V2_investment_strategies`
   - `renovation_estimates` → `V2_renovation_estimates`
2. Update service layer to use V2_ prefixed tables
3. Add V2 tags to all V2 endpoints in route decorators
4. Update Swagger documentation with V2 tag descriptions
