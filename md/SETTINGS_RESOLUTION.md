# Settings Resolution Logic

**Version:** 1.0
**Date:** December 27, 2025

---

## Overview

The enrichment settings system uses a three-tier hierarchy with lock-based override controls. This document explains exactly how settings are resolved for any enrichment request.

---

## Table of Contents

- [Hierarchy Overview](#hierarchy-overview)
- [Lock Mechanism](#lock-mechanism)
- [Resolution Algorithm](#resolution-algorithm)
- [Examples](#examples)
- [Edge Cases](#edge-cases)

---

## Hierarchy Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        ADMIN SETTINGS                            │
│  (enrichment_admin_settings - singleton, id=1)                   │
│  - Global defaults for all users/counties                        │
│  - Lock flags to prevent overrides                              │
│  - Permission flags (allow_user_overrides, etc.)                 │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Can override (if not locked)
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                       COUNTY SETTINGS                            │
│  (county_enrichment_settings - one row per county)               │
│  - Per-county overrides                                         │
│  - NULL values use admin defaults                               │
│  - County-level locks prevent user overrides                    │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Can override (if not locked + admin allows)
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                       USER PREFERENCES                            │
│  (user_enrichment_preferences - one row per user+county)          │
│  - Per-user preferences                                         │
│  - NULL values use county/admin defaults                        │
│  - Only active if admin.allow_user_overrides = true             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Lock Mechanism

### Lock Flags

Each endpoint has a corresponding lock flag:

| Setting Lock | What It Does |
|--------------|--------------|
| `endpoint_lock_pro_byaddress` | Locks `endpoint_pro_byaddress` at this level |
| `endpoint_lock_custom_ad_byzpid` | Locks `endpoint_custom_ad_byzpid` at this level |
| `endpoint_lock_similar` | Locks `endpoint_similar` at this level |
| `endpoint_lock_nearby` | Locks `endpoint_lock_nearby` at this level |
| ... | ... (one lock per endpoint) |
| `skip_trace_external_lock` | Locks external skip tracing setting |

### Lock Behavior

| Lock Level | Effect |
|------------|--------|
| **Admin lock = true** | County and User CANNOT override. Only admin value used. |
| **County lock = true** | User CANNOT override. County value used (or admin if county is NULL). |
| **No locks** | User > County > Admin priority applies. |

---

## Resolution Algorithm

### Pseudo-Code

```python
def resolve_enrichment_settings(
    county_id: int,
    state: str,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Resolve settings for an enrichment request.

    Returns: Dictionary with all settings and their source.
    """

    # ========================================================================
    # STEP 1: Fetch all three levels
    # ========================================================================

    admin = fetch_admin_settings()  # Singleton, always exists
    county = fetch_county_settings(county_id)  # May be None
    user = None

    if user_id and admin.allow_user_overrides:
        user = fetch_user_preferences(user_id, county_id, state)  # May be None


    # ========================================================================
    # STEP 2: Resolve each setting with lock logic
    # ========================================================================

    resolved = {}
    sources = {}  # Track where each value came from (for debugging)

    # List of all boolean endpoint settings
    endpoint_settings = [
        "endpoint_pro_byaddress",
        "endpoint_custom_ad_byzpid",
        "endpoint_similar",
        "endpoint_nearby",
        "endpoint_pricehistory",
        "endpoint_graph_listing_price",
        "endpoint_taxinfo",
        "endpoint_climate",
        "endpoint_walk_transit_bike",
        "endpoint_housing_market",
        "endpoint_rental_market",
        "endpoint_ownerinfo",
        "endpoint_custom_ae_search",
        "skip_trace_external_enabled"
    ]

    for setting in endpoint_settings:
        # Get the lock flag for this setting
        lock_setting = f"{setting}_lock" if setting.startswith("endpoint_") else "skip_trace_external_lock"

        # Get values at each level
        admin_value = admin[setting]
        admin_lock = admin[lock_setting]

        county_value = county[setting] if county else None
        county_lock = county[lock_setting] if county else False

        user_value = user[setting] if user else None

        # Apply lock logic
        final_value, source = resolve_single_setting(
            admin_value, admin_lock,
            county_value, county_lock,
            user_value
        )

        resolved[setting] = final_value
        sources[setting] = source


    # ========================================================================
    # STEP 3: Resolve investment parameters (no locks on these)
    # ========================================================================

    investment_settings = [
        "inv_annual_appreciation",
        "inv_mortgage_rate",
        "inv_down_payment_rate",
        "inv_insurance_rate",
        "inv_loan_term_months",
        "inv_maintenance_rate",
        "inv_property_mgmt_rate",
        "inv_property_tax_rate",
        "inv_vacancy_rate",
        "inv_renovation_cost",
        "template_preset"
    ]

    for setting in investment_settings:
        admin_value = admin[setting]
        county_value = county[setting] if county else None
        user_value = user[setting] if user else None

        # Investment params use simple priority (no locks)
        final_value = coalesce(user_value, county_value, admin_value)

        resolved[setting] = final_value

        # Track source
        if user_value is not None and admin.allow_user_overrides and admin.allow_custom_investment_params:
            sources[setting] = "user"
        elif county_value is not None:
            sources[setting] = "county"
        else:
            sources[setting] = "admin"


    # ========================================================================
    # STEP 4: Add metadata
    # ========================================================================

    return {
        "settings": resolved,
        "sources": sources,
        "allow_user_overrides": admin.allow_user_overrides,
        "allow_custom_investment_params": admin.allow_custom_investment_params
    }


def resolve_single_setting(
    admin_value: Any,
    admin_lock: bool,
    county_value: Any,
    county_lock: bool,
    user_value: Any
) -> Tuple[Any, str]:
    """
    Resolve a single setting with lock logic.

    Returns: (final_value, source)
    """

    # Case 1: Admin locked - admin value wins, no exceptions
    if admin_lock:
        return admin_value, "admin (locked)"

    # Case 2: County locked - county or admin wins, user cannot override
    if county_lock:
        if county_value is not None:
            return county_value, "county (locked)"
        else:
            return admin_value, "admin (county locked but NULL)"

    # Case 3: No locks - use highest priority non-null value
    if user_value is not None:
        return user_value, "user"

    if county_value is not None:
        return county_value, "county"

    return admin_value, "admin"


def coalesce(*values) -> Any:
    """Return first non-None value."""
    for v in values:
        if v is not None:
            return v
    return None
```

---

## Examples

### Example 1: Simple Case (No Locks)

**Admin Settings:**
```json
{
  "endpoint_similar": true,
  "endpoint_climate": false,
  "endpoint_lock_similar": false,
  "endpoint_lock_climate": false,
  "allow_user_overrides": true
}
```

**County Settings (Duval, FL):**
```json
{
  "endpoint_similar": true,
  "endpoint_climate": true
}
```

**User Preferences:**
```json
{
  "endpoint_similar": false,
  "endpoint_climate": null
}
```

**Resolution:**

| Setting | Admin | County | User | Locks | Final Value | Source |
|---------|-------|--------|------|-------|-------------|--------|
| `endpoint_similar` | true | true | false | None | **false** | user |
| `endpoint_climate` | false | true | null | None | **true** | county |

---

### Example 2: Admin Lock

**Admin Settings:**
```json
{
  "endpoint_similar": true,
  "endpoint_lock_similar": true  // LOCKED by admin
}
```

**County Settings:**
```json
{
  "endpoint_similar": false  // Trying to override
}
```

**User Preferences:**
```json
{
  "endpoint_similar": false  // Also trying to override
}
```

**Resolution:**

| Setting | Admin | County | User | Locks | Final Value | Source |
|---------|-------|--------|------|-------|-------------|--------|
| `endpoint_similar` | true | false | false | admin_lock | **true** | admin (locked) |

**Result:** Admin lock prevents ANY override. Value stays `true`.

---

### Example 3: County Lock

**Admin Settings:**
```json
{
  "endpoint_similar": true,
  "endpoint_lock_similar": false  // Not locked at admin
}
```

**County Settings:**
```json
{
  "endpoint_similar": false,
  "endpoint_lock_similar": true  // LOCKED at county
}
```

**User Preferences:**
```json
{
  "endpoint_similar": true  // Trying to override
}
```

**Resolution:**

| Setting | Admin | County | User | Locks | Final Value | Source |
|---------|-------|--------|------|-------|-------------|--------|
| `endpoint_similar` | true | false | true | county_lock | **false** | county (locked) |

**Result:** County lock prevents user override. Value uses county setting.

---

### Example 4: User Overrides Disabled

**Admin Settings:**
```json
{
  "endpoint_similar": true,
  "allow_user_overrides": false  // Users cannot override anything
}
```

**County Settings:**
```json
{
  "endpoint_similar": false
}
```

**User Preferences:**
```json
{
  "endpoint_similar": true  // Ignored!
}
```

**Resolution:**

| Setting | Admin | County | User | Locks | Final Value | Source |
|---------|-------|--------|------|-------|-------------|--------|
| `endpoint_similar` | true | false | true | None | **false** | county |

**Result:** User preference is ignored because `allow_user_overrides = false`. County value wins.

---

### Example 5: Investment Parameters

**Admin Settings:**
```json
{
  "inv_annual_appreciation": 0.03,
  "inv_mortgage_rate": 0.045,
  "allow_custom_investment_params": true
}
```

**County Settings:**
```json
{
  "inv_annual_appreciation": 0.04,  // Higher appreciation expected
  "inv_mortgage_rate": null         // Use admin default
}
```

**User Preferences:**
```json
{
  "inv_annual_appreciation": 0.035,  // Conservative estimate
  "inv_mortgage_rate": 0.05          // Higher rate assumption
}
```

**Resolution:**

| Setting | Admin | County | User | Final Value | Source |
|---------|-------|--------|------|-------------|--------|
| `inv_annual_appreciation` | 0.03 | 0.04 | 0.035 | **0.035** | user |
| `inv_mortgage_rate` | 0.045 | null | 0.05 | **0.05** | user |

---

### Example 6: Custom Investment Params Disabled

**Admin Settings:**
```json
{
  "inv_annual_appreciation": 0.03,
  "allow_custom_investment_params": false  // Users must use admin/county params
}
```

**County Settings:**
```json
{
  "inv_annual_appreciation": 0.04
}
```

**User Preferences:**
```json
{
  "inv_annual_appreciation": 0.02  // Ignored!
}
```

**Resolution:**

| Setting | Admin | County | User | Custom Allowed | Final Value | Source |
|---------|-------|--------|------|----------------|-------------|--------|
| `inv_annual_appreciation` | 0.03 | 0.04 | 0.02 | false | **0.04** | county |

---

## Edge Cases

### Edge Case 1: No County Settings

When a county has no settings row:

```
Admin: endpoint_similar = true
County: NULL
User: endpoint_similar = false
```

**Result:** `false` (user value used, county treated as NULL)

---

### Edge Case 2: No User Preferences

When a user has no preferences row:

```
Admin: endpoint_similar = true
County: endpoint_similar = false
User: NULL
```

**Result:** `false` (county value used)

---

### Edge Case 3: All NULL Except Admin

```
Admin: endpoint_similar = true
County: NULL
User: NULL
```

**Result:** `true` (admin default used)

---

### Edge Case 4: Template Preset

When a template preset is applied, it sets multiple values at once:

**Template: "flipper"**

Applies these endpoint settings:
- `endpoint_pro_byaddress` = true
- `endpoint_custom_ad_byzpid` = true
- `endpoint_similar` = true
- `endpoint_nearby` = true
- `endpoint_pricehistory` = true
- `endpoint_taxinfo` = true
- `endpoint_ownerinfo` = true
- All others = false

After applying template, individual settings can still be overridden (unless locked).

---

### Edge Case 5: External Skip Tracing

External skip tracing has its own lock:

```
Admin:
  enable_skip_trace_external = true
  skip_trace_external_enabled = false
  skip_trace_external_lock = false

County:
  skip_trace_external_enabled = true

User:
  skip_trace_external_enabled = false
```

**Result:** `true` (county enables it for this county)

If admin had `skip_trace_external_lock = true`, county/user couldn't change it.

---

## Permission Matrix

| Admin Setting | Effect When TRUE |
|---------------|------------------|
| `allow_user_overrides` | Users can set their own preferences |
| `allow_user_templates` | Users can select template presets |
| `allow_custom_investment_params` | Users can customize ROI formula inputs |

### Permission Combinations

| allow_user_overrides | allow_custom_investment_params | User Can Override Endpoints | User Can Override Investment Params |
|---------------------|-------------------------------|----------------------------|-----------------------------------|
| false | false | No | No |
| false | true | No | Yes (only ROI formulas) |
| true | false | Yes (if not locked) | No |
| true | true | Yes (if not locked) | Yes |

---

## Debugging Resolution

To debug settings resolution, the API returns the `sources` field:

```json
{
  "settings": {
    "endpoint_similar": true,
    "endpoint_climate": false
  },
  "sources": {
    "endpoint_similar": "user",
    "endpoint_climate": "admin"
  }
}
```

This shows exactly where each value came from.

---

## Implementation Notes

1. **Always fetch all three levels** even if you think some won't be used
2. **Check `allow_user_overrides` BEFORE fetching user preferences**
3. **Investment params have no locks** - only `allow_custom_investment_params` gate
4. **NULL at any level means "use next level up"**
5. **Locks propagate down** - admin lock > county lock > no lock
6. **Template presets are just bulk updates** - they don't bypass locks
