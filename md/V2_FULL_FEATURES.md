# V2 FULL FEATURES - Complete Deal Intelligence Platform

**Everything in V1 PLUS 8 additional advanced features**

---

## V2 = V1 + Advanced Features

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        V2: COMPLETE PLATFORM                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    V1 CORE (34 endpoints)                       │   │
│  │  • Property Feed • Auto-Enrichment • Deal Flags                │   │
│  │  • Saved + Kanban • Watchlist + Email Alerts                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              +                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    V2 ADDITIONS (39 endpoints)                  │   │
│  │  • Portfolio Tracking • Team Collaboration                     │   │
│  │  • Investment Strategies • Renovation Estimator                │   │
│  │  • SMS + Push Notifications • County Settings                  │   │
│  │  • Advanced Analytics                                          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│                           TOTAL: 73 ENDPOINTS                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## V2 Feature Set (14 Total Features)

| # | Feature | Description | Endpoints | Status |
|---|---------|-------------|-----------|--------|
| | **V1 Core (6 features)** | | | |
| 1 | Property Feed | Foreclosure listings with filters | 5 | ✅ Complete |
| 2 | Auto-Enrichment | Zillow data integration | 8 | ✅ Complete |
| 3 | Market Anomaly Detection | Price outlier flags | 4 | ✅ Complete |
| 4 | Comparable Sales | AI-powered ARV calculation | 3 | ✅ Complete |
| 5 | Saved + Kanban | Pipeline management | 5 | ✅ Complete |
| 6 | Watchlist + Alerts | Email notifications | 9 | ✅ Complete |
| | **V2 Additions (8 features)** | | | |
| 7 | **Portfolio Tracking** | Acquired properties management | 5 | ✅ Complete |
| 8 | **Team Collaboration** | Share, comments, permissions | 6 | ✅ Complete |
| 9 | **Investment Strategies** | Custom strategy templates | 6 | ✅ Complete |
| 10 | **Renovation Estimator** | GPT-4o Vision photo analysis | 3 | 🟡 Partial |
| 11 | **SMS Notifications** | Twilio text alerts | - | 🟡 TODO |
| 12 | **Push Notifications** | iOS/Android mobile alerts | 6 | ✅ Complete |
| 13 | **County Settings** | Per-county feature overrides | 5 | ✅ Complete |
| 14 | **ML Ranking** | Personalized property scoring | 7 | ✅ Complete |

**Total V2 Endpoints: 73**

---

## V2-Only Features (Detailed)

### 7. Portfolio Tracking ✅
**What it does:** Track acquired properties through rehab → rent/sold lifecycle

**Database:** `user_portfolio` table
**Service:** `portfolio_service.py`

**Endpoints:**
- `GET /api/deal-intelligence/portfolio/{user_id}` - Get portfolio
- `GET /api/deal-intelligence/portfolio/{user_id}/summary` - Get summary stats
- `POST /api/deal-intelligence/portfolio` - Add acquired property
- `PUT /api/deal-intelligence/portfolio/entry/{id}` - Update entry
- `DELETE /api/deal-intelligence/portfolio/entry/{id}` - Remove entry

**Portfolio Stages:**
- `under_repair` - Property being renovated
- `rented` - Tenant occupied
- `for_sale` - Listed for sale
- `under_contract` - Buyer found
- `sold` - Sale complete
- `held` - Long-term hold
- `lost` - Deal fell through

**Tracked Metrics:**
- Total invested (purchase + rehab)
- Current value
- ARV target vs actual
- ROI percent
- Sale price (when sold)
- Actual profit/loss

---

### 8. Team Collaboration ✅
**What it does:** Share properties with team, threaded comments

**Database:** `shared_properties`, `property_comments` tables
**Service:** `collaboration_service.py`

**Endpoints:**
- `POST /api/deal-intelligence/collaboration/share` - Share property
- `DELETE /api/deal-intelligence/collaboration/share/{id}` - Unshare
- `GET /api/deal-intelligence/collaboration/shared-with-me/{user_id}` - Properties shared with me
- `GET /api/deal-intelligence/collaboration/shared-by-me/{user_id}` - Properties I shared
- `POST /api/deal-intelligence/collaboration/comments` - Add comment
- `GET /api/deal-intelligence/collaboration/comments/{property_id}` - Get comments
- `PUT /api/deal-intelligence/collaboration/comments/{id}` - Update comment
- `DELETE /api/deal-intelligence/collaboration/comments/{id}` - Delete comment

**Permissions:**
- `view` - Can view property and analysis
- `edit` - Can add notes, move Kanban stage

**Comment Features:**
- Threaded replies (parent_comment_id)
- @mentions (future)
- Comment history
- Soft delete

---

### 9. Investment Strategies ✅
**What it does:** Custom strategy templates to auto-evaluate properties

**Database:** `investment_strategies` table
**Service:** `investment_service.py`

**Strategy Types:**
- `fix_and_flip` - Quick turnaround
- `buy_and_hold` - Rental property
- `wholesale` - Contract assignment
- `brrrr` - Buy, Rehab, Rent, Refinance, Repeat
- `value_add` - Add value through improvements
- `rental` - Long-term rental
- `multi_family` - 2-4 units
- `commercial` - Commercial properties

**Endpoints:**
- `GET /api/deal-intelligence/strategies/{user_id}` - List strategies
- `POST /api/deal-intelligence/strategies` - Create strategy
- `GET /api/deal-intelligence/strategies/{user_id}/{id}` - Get strategy
- `PUT /api/deal-intelligence/strategies/{id}` - Update strategy
- `DELETE /api/deal-intelligence/strategies/{id}` - Delete strategy
- `PUT /api/deal-intelligence/strategies/{id}/set-default` - Set as default
- `POST /api/deal-intelligence/strategies/{id}/evaluate/{property_id}` - Evaluate property

**Strategy Criteria:**
- `min_fix_and_flip_profit` - Minimum profit % for flips
- `max_purchase_price` - Maximum purchase price
- `min_arv_spread` - Minimum ARV spread
- `max_repair_cost` - Maximum rehab budget
- `max_holding_months` - Maximum hold time
- `min_cash_flow` - Minimum monthly cash flow
- `custom_criteria` - Custom JSON criteria

**Property Evaluation:**
```json
{
  "strategy_id": 1,
  "strategy_name": "Aggressive Flip",
  "property_id": 12345,
  "match_score": 0.833,
  "criteria_results": {
    "max_purchase_price": {
      "passed": true,
      "actual": 75000,
      "required": 100000
    },
    "min_fix_and_flip_profit": {
      "passed": true,
      "actual": 28.5,
      "required": 25.0
    }
  }
}
```

---

### 10. Renovation Estimator 🟡 Partial
**What it does:** GPT-4o Vision analyzes property photos for rehab costs

**Database:** `renovation_estimates` table
**Service:** `renovation_service.py`

**Endpoints:**
- `POST /api/deal-intelligence/renovation/estimate` - Create from photos
- `GET /api/deal-intelligence/renovation/estimate/{property_id}` - Get estimate
- `PUT /api/deal-intelligence/renovation/estimate/{id}` - Manual override

**AI Analysis (GPT-4o Vision):**
- Upload property photos
- Analyzes condition of:
  - Kitchen (cabinets, appliances, flooring)
  - Bathrooms (fixtures, tile, vanity)
  - Flooring (hardwood, carpet, tile)
  - Roof (age, condition)
  - Windows (single vs double pane)
  - HVAC (age, condition)
  - Electrical/Plumbing (updates needed)

**Cost Estimates:**
- Line-item by room/feature
- Material + labor breakdown
- Low/medium/high estimate ranges
- Confidence score

**AI Quality Thresholds:**
- `renovation_min_photos`: 1 (minimum photos required)
- `renovation_confidence_threshold`: 0.500 (50% confidence minimum)

---

### 11. SMS Notifications 🟡 TODO
**What it does:** Text message alerts via Twilio

**Service:** `sms_service.py` (to be created)

**Twilio Integration:**
```python
# webhook_server/sms_service.py
import os
from twilio.rest import Client

class SMSService:
    def __init__(self):
        self.client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER")

    async def send_alert(self, to_phone: str, message: str):
        self.client.messages.create(
            body=message,
            from_=self.from_number,
            to=to_phone
        )
```

**Environment Variables:**
```bash
TWILIO_ACCOUNT_SID=ACxxxx...
TWILIO_AUTH_TOKEN=xxxx...
TWILIO_PHONE_NUMBER=+15551234567
```

**Cost:**
- Phone number: $15/month
- SMS: $0.0079 per message
- Example: 100 users × 5 alerts = $3.95/month

---

### 12. Push Notifications ✅
**What it does:** iOS/Android push notifications

**Database:** `mobile_push_tokens`, `push_notification_queue`, `push_notification_history` tables
**Service:** `push_notification_service.py`

**Endpoints:**
- `POST /api/deal-intelligence/notifications/register` - Register device token
- `DELETE /api/deal-intelligence/notifications/token/{id}` - Unregister
- `POST /api/deal-intelligence/notifications/create` - Create notification
- `PUT /api/deal-intelligence/notifications/token/{id}/preferences` - Update prefs
- `GET /api/deal-intelligence/notifications/{user_id}/history` - Get history
- `PUT /api/deal-intelligence/notifications/{id}/opened` - Mark opened

**Platforms:**
- **Android:** Firebase Cloud Messaging (FCM)
- **iOS:** Apple Push Notification Service (APNs)

**Notification Types:**
- `hot_deal` - New anomaly detected
- `auction_update` - Sale date/time changed
- `price_drop` - Opening bid reduced
- `status_change` - Property status updated
- `watchlist_alert` - Watchlist trigger
- `comps_available` - New comps analysis

**Background Worker:**
```bash
# Process notification queue
python -m webhook_server.push_notification_worker --interval 30 --batch-size 100
```

---

### 13. County-Level Settings ✅
**What it does:** Per-county feature overrides (3-tier system)

**Database:** `deal_features_county_settings` table
**Service:** `feature_toggle_service.py`

**3-Tier Architecture:**
```
┌─────────────────────────────────────────────────────────────┐
│  Level 1: Admin Settings (Global)                           │
│  • 14 feature toggles                                       │
│  • Lock flags prevent lower-level overrides                │
│  • AI quality thresholds                                    │
└────────────────────────┬────────────────────────────────────┘
                         │ Respects locks
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Level 2: County Settings (Per-County)                      │
│  • Override feature toggles for specific counties           │
│  • County-level lock flags                                  │
│  • Use case: "Enable watchlist in Duval only"              │
└────────────────────────┬────────────────────────────────────┘
                         │ Respects locks
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Level 3: User Preferences (Per-User)                       │
│  • User can enable/disable features for themselves          │
│  • Unless locked at admin or county level                  │
└─────────────────────────────────────────────────────────────┘
```

**Endpoints:**
- `GET /api/deal-intelligence/settings/county/{id}` - Get county settings
- `POST /api/deal-intelligence/settings/county` - Create county settings
- `PUT /api/deal-intelligence/settings/county/{id}` - Update county settings
- `DELETE /api/deal-intelligence/settings/county/{id}` - Delete county settings

**Example Use Case:**
```json
// Duval County: Enable watchlist alerts
{
  "county_id": 1,
  "override_watchlist_alerts": true,
  "feature_lock_watchlist_alerts": false  // Users can still disable
}

// St. Johns County: Disable watchlist alerts
{
  "county_id": 2,
  "override_watchlist_alerts": false
}
```

---

### 14. ML Ranking System ✅
**What it does:** Personalized property scoring with human feedback loop

**Database:** 6 tables
- `deal_intelligence_investor_criteria` - User preferences
- `deal_intelligence_model_weights` - Scoring weights
- `deal_intelligence_property_scores` - Calculated scores
- `deal_intelligence_score_feedback` - Human feedback
- `deal_intelligence_ranking_history` - Historical rankings
- `deal_intelligence_analytics` - Performance metrics

**Service:** `ml_ranking_service.py`

**Endpoints:**
- `GET /api/deal-intelligence/ranking/criteria/{user_id}` - Get investor criteria
- `PUT /api/deal-intelligence/ranking/criteria/{user_id}` - Update criteria
- `GET /api/deal-intelligence/ranking/property/{property_id}/{user_id}` - Get score
- `POST /api/deal-intelligence/ranking/rank` - Batch rank properties
- `GET /api/deal-intelligence/ranking/weights` - Get model weights
- `PUT /api/deal-intelligence/ranking/weights` - Update weights
- `POST /api/deal-intelligence/ranking/feedback` - Submit feedback

**Scoring Dimensions:**
| Dimension | Weight | Description |
|-----------|--------|-------------|
| Price-to-Value | 35% | Upset price vs Zestimate ratio |
| Market Anomaly | 20% | Z-score deviation from area norms |
| Time Urgency | 15% | Days until sale date |
| Property Type | 10% | Matches user preferences |
| Price Range | 10% | Within user budget |
| Location | 10% | Preferred counties |

**Human Feedback Loop:**
```json
{
  "property_id": 12345,
  "user_id": "user-abc",
  "shown_score": 0.82,
  "user_action": "saved",  // saved, hidden, viewed, ignored
  "feedback": "Good deal but too far from my target area"
}
```

Model learns from user actions over time.

---

## V2 Complete Endpoint List (73 Total)

### Feature Settings (11)
```
GET    /api/deal-intelligence/settings/admin
PUT    /api/deal-intelligence/settings/admin
GET    /api/deal-intelligence/settings/county/{id}
POST   /api/deal-intelligence/settings/county
PUT    /api/deal-intelligence/settings/county/{id}
DELETE /api/deal-intelligence/settings/county/{id}
GET    /api/deal-intelligence/settings/user/{user_id}
POST   /api/deal-intelligence/settings/user
PUT    /api/deal-intelligence/settings/user/{user_id}
DELETE /api/deal-intelligence/settings/user/{user_id}
```

### Market Anomalies (4)
```
GET    /api/deal-intelligence/market-anomalies
GET    /api/deal-intelligence/market-anomalies/property/{id}
POST   /api/deal-intelligence/market-anomalies/analyze
PUT    /api/deal-intelligence/market-anomalies/{id}/verify
```

### Comparable Sales (3)
```
GET    /api/deal-intelligence/comparable-sales/{property_id}
POST   /api/deal-intelligence/comparable-sales/analyze
GET    /api/deal-intelligence/comparable-sales/{id}/comps
```

### Saved + Kanban (8)
```
GET    /api/deal-intelligence/saved/{user_id}
POST   /api/deal-intelligence/saved
DELETE /api/deal-intelligence/saved/{id}
PUT    /api/deal-intelligence/saved/stage
GET    /api/deal-intelligence/saved/{user_id}/kanban
PUT    /api/deal-intelligence/saved/{id}/notes
POST   /api/deal-intelligence/saved/bulk-update
GET    /api/deal-intelligence/saved/{user_id}/stats
```

### Renovation Estimator (3)
```
POST   /api/deal-intelligence/renovation/estimate
GET    /api/deal-intelligence/renovation/estimate/{property_id}
PUT    /api/deal-intelligence/renovation/estimate/{id}
```

### Investment Strategies (7)
```
GET    /api/deal-intelligence/strategies/{user_id}
POST   /api/deal-intelligence/strategies
GET    /api/deal-intelligence/strategies/{user_id}/{id}
PUT    /api/deal-intelligence/strategies/{id}
DELETE /api/deal-intelligence/strategies/{id}
PUT    /api/deal-intelligence/strategies/{id}/set-default
POST   /api/deal-intelligence/strategies/{id}/evaluate/{property_id}
```

### Watchlist + Alerts (9)
```
GET    /api/deal-intelligence/watchlist/{user_id}
POST   /api/deal-intelligence/watchlist
DELETE /api/deal-intelligence/watchlist/{id}
PUT    /api/deal-intelligence/watchlist/{id}
GET    /api/deal-intelligence/alerts/{user_id}
PUT    /api/deal-intelligence/alerts/{id}/read
PUT    /api/deal-intelligence/alerts/{user_id}/read-all
DELETE /api/deal-intelligence/alerts/{id}
```

### Portfolio (5)
```
GET    /api/deal-intelligence/portfolio/{user_id}
GET    /api/deal-intelligence/portfolio/{user_id}/summary
POST   /api/deal-intelligence/portfolio
GET    /api/deal-intelligence/portfolio/entry/{id}
PUT    /api/deal-intelligence/portfolio/entry/{id}
DELETE /api/deal-intelligence/portfolio/entry/{id}
```

### Team Collaboration (8)
```
POST   /api/deal-intelligence/collaboration/share
DELETE /api/deal-intelligence/collaboration/share/{id}
GET    /api/deal-intelligence/collaboration/shared-with-me/{user_id}
GET    /api/deal-intelligence/collaboration/shared-by-me/{user_id}
POST   /api/deal-intelligence/collaboration/comments
GET    /api/deal-intelligence/collaboration/comments/{property_id}
PUT    /api/deal-intelligence/collaboration/comments/{id}
DELETE /api/deal-intelligence/collaboration/comments/{id}
```

### Notes + Checklist (7)
```
GET    /api/deal-intelligence/notes/{property_id}
POST   /api/deal-intelligence/notes
PUT    /api/deal-intelligence/notes/{id}
DELETE /api/deal-intelligence/notes/{id}
GET    /api/deal-intelligence/checklist/{property_id}/{user_id}
PUT    /api/deal-intelligence/checklist/{property_id}/{user_id}
POST   /api/deal-intelligence/checklist/{property_id}/{user_id}/reset
```

### Push Notifications (6)
```
POST   /api/deal-intelligence/notifications/register
DELETE /api/deal-intelligence/notifications/token/{id}
POST   /api/deal-intelligence/notifications/create
PUT    /api/deal-intelligence/notifications/token/{id}/preferences
GET    /api/deal-intelligence/notifications/{user_id}/history
PUT    /api/deal-intelligence/notifications/{id}/opened
```

### ML Ranking (7)
```
GET    /api/deal-intelligence/ranking/criteria/{user_id}
PUT    /api/deal-intelligence/ranking/criteria/{user_id}
GET    /api/deal-intelligence/ranking/property/{property_id}/{user_id}
POST   /api/deal-intelligence/ranking/rank
GET    /api/deal-intelligence/ranking/weights
PUT    /api/deal-intelligence/ranking/weights
POST   /api/deal-intelligence/ranking/feedback
```

### CSV Export (1)
```
POST   /api/deal-intelligence/export/csv
```

---

## V2 Database Schema (23 Tables)

### V1 Tables (11)
- `foreclosure_listings`
- `zillow_enrichment`
- `nj_counties`
- `deal_features_admin_settings`
- `market_anomalies`
- `comparable_sales_analysis`
- `saved_properties`
- `user_watchlist`
- `user_alerts`
- `property_notes`
- `due_diligence_checklists`

### V2 Addition Tables (12)
- `deal_features_county_settings` - County overrides
- `deal_features_user_preferences` - User preferences
- `user_portfolio` - Acquired properties
- `shared_properties` - Team sharing
- `property_comments` - Threaded comments
- `investment_strategies` - Strategy templates
- `renovation_estimates` - Photo-based estimates
- `mobile_push_tokens` - Device registry
- `push_notification_queue` - Notification queue
- `push_notification_history` - Sent log
- `deal_intelligence_investor_criteria` - ML user prefs
- `deal_intelligence_model_weights` - ML weights
- `deal_intelligence_property_scores` - ML scores
- `deal_intelligence_score_feedback` - ML feedback
- `deal_intelligence_ranking_history` - ML history
- `deal_intelligence_analytics` - ML metrics

---

## V2 Frontend Additions (Beyond V1)

### New Pages

```
/portfolio
├── List view (acquired properties)
├── Summary stats
├── ROI tracking
└── Stage management

/team
├── Shared with me
├── Shared by me
└── Comments view

/strategies
├── Strategy list
├── Create strategy
├── Edit strategy
└── Evaluate property

/settings (expanded)
├── Feature preferences
├── Alert preferences
├── Notification settings
└── Team management

/analytics (new)
├── ML ranking stats
├── Portfolio performance
└── Feedback impact
```

### New Components

- `PortfolioTracker.tsx` - Portfolio management
- `TeamSharing.tsx` - Share properties
- `CommentThread.tsx` - Threaded comments
- `StrategyBuilder.tsx` - Create strategies
- `RenovationEstimator.tsx` - Photo upload + AI analysis
- `NotificationSettings.tsx` - Push + SMS prefs
- `MLRankingView.tsx` - Ranked property list

---

## V2 vs V1 Comparison

| Aspect | V1 MVP | V2 Full |
|--------|--------|---------|
| **Features** | 6 | 14 |
| **Endpoints** | 34 | 73 |
| **Database Tables** | 11 | 23 |
| **Target Users** | Individual investors | Teams + power users |
| **Settings Tiers** | 2 (Admin → User) | 3 (Admin → County → User) |
| **Notifications** | Email only | Email + SMS + Push |
| **Collaboration** | None | Full team features |
| **Portfolio** | None | Full lifecycle tracking |
| **Strategies** | None | 8 strategy types |
| **Renovation** | None | GPT-4o Vision AI |
| **Analytics** | Basic | ML ranking + feedback |
| **Development Time** | 6 weeks | 12 weeks |
| **Monthly Cost** | ~$0.50 | ~$20 (Twilio + push) |

---

## V2 Cost Summary

| Service | Free Tier | V2 Usage | Monthly Cost |
|---------|-----------|----------|-------------|
| **Supabase** | 500MB DB | ~200MB | $0 |
| **Zillow API** | 250 req/mo | ~200 req/mo | $0 |
| **OpenAI** | $5 credit | ~100k tokens/mo | ~$1 |
| **Mapbox** | 50k loads | ~5k loads | $0 |
| **Google Maps** | $200 credit | ~2k loads | $0 |
| **SendGrid** | 100/day | ~50 emails | $0 |
| **Twilio SMS** | - | ~500 SMS | $4 + $15 phone |
| **FCM/APNs** | Free | Unlimited | $0 |
| **Total** | - | - | **~$20/month** |

---

## When to Launch V2?

**Trigger indicators:**
1. V1 has 100+ active users
2. Teams requesting collaboration features
3. Users asking for portfolio tracking
4. Mobile app development starts
5. Revenue supports additional $20/mo cost

**V2 is "nice to have" for teams and power users. V1 covers 80% of individual investor use cases.**
