#!/usr/bin/env python3
"""
Comprehensive API endpoint tester for Deal Intelligence API
Tests all endpoints with proper authentication and parameters
"""
import requests
import json
from datetime import datetime
from typing import Dict, List, Tuple

BASE_URL = "http://localhost:8080"
TEST_USER_ID = "test-user-123"
TEST_PROPERTY_ID = 1436

class EndpointTester:
    def __init__(self):
        self.results = []
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "X-User-ID": TEST_USER_ID
        })

    def test_endpoint(self, method: str, path: str, data: dict = None,
                      params: dict = None, description: str = "",
                      expect_success: bool = True) -> dict:
        """Test a single endpoint"""
        url = f"{BASE_URL}{path}"
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, params=params)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, params=params)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, params=params)
            else:
                return {"status": "SKIP", "error": f"Unknown method: {method}"}

            success = response.status_code < 400

            result = {
                "method": method,
                "path": path,
                "status_code": response.status_code,
                "status": "PASS" if success else "FAIL",
                "description": description,
                "sample_data": str(response.json()) if response.content else ""
            }

            if not success and expect_success:
                result["error"] = response.text

            self.results.append(result)
            print(f"{'✅' if success else '❌'} {method} {path} - {response.status_code}")
            return result

        except Exception as e:
            result = {
                "method": method,
                "path": path,
                "status": "ERROR",
                "error": str(e),
                "description": description
            }
            self.results.append(result)
            print(f"⚠️ {method} {path} - ERROR: {e}")
            return result

    def run_all_tests(self):
        """Run all endpoint tests"""
        print("\n" + "="*80)
        print("COMPREHENSIVE API ENDPOINT TEST")
        print("="*80 + "\n")

        # ========================================
        # HEALTH & SETTINGS
        # ========================================
        print("\n--- HEALTH & SETTINGS ---")

        self.test_endpoint("GET", "/health", description="Health check")
        self.test_endpoint("GET", "/api/deal-intelligence/health", description="Deal Intelligence health")
        self.test_endpoint("GET", "/api/deal-intelligence/settings/admin",
                          description="Get admin settings")
        self.test_endpoint("PUT", "/api/deal-intelligence/settings/admin",
                          data={"feature_market_anomaly_detection": True},
                          description="Update admin settings")
        self.test_endpoint("GET", "/api/deal-intelligence/settings/county/1",
                          description="Get county settings")
        self.test_endpoint("POST", "/api/deal-intelligence/settings/county",
                          data={"county_id": 1, "feature_market_anomaly_detection": True},
                          description="Create county settings")
        self.test_endpoint("GET", "/api/deal-intelligence/settings/user/test-user-123",
                          description="Get user settings")
        self.test_endpoint("POST", "/api/deal-intelligence/settings/user",
                          data={"user_id": "test-user-123", "county_id": 1},
                          description="Create user settings")

        # ========================================
        # WATCHLIST
        # ========================================
        print("\n--- WATCHLIST ---")

        self.test_endpoint("GET", f"/api/deal-intelligence/watchlist/{TEST_USER_ID}",
                          description="Get user watchlist")
        self.test_endpoint("POST", "/api/deal-intelligence/watchlist",
                          data={"property_id": TEST_PROPERTY_ID, "alert_price": 100000},
                          description="Add to watchlist")
        self.test_endpoint("PUT", f"/api/deal-intelligence/watchlist/{TEST_PROPERTY_ID}",
                          data={"alert_price": 90000, "alert_days_on_market": 30},
                          description="Update watchlist item")
        self.test_endpoint("GET", f"/api/deal-intelligence/alerts/{TEST_USER_ID}",
                          description="Get user alerts")

        # ========================================
        # PORTFOLIO
        # ========================================
        print("\n--- PORTFOLIO ---")

        self.test_endpoint("GET", f"/api/deal-intelligence/portfolio/{TEST_USER_ID}",
                          description="Get user portfolio")
        self.test_endpoint("GET", f"/api/deal-intelligence/portfolio/{TEST_USER_ID}/summary",
                          description="Get portfolio summary")
        self.test_endpoint("POST", "/api/deal-intelligence/portfolio",
                          data={"property_id": TEST_PROPERTY_ID, "purchase_price": 95000},
                          description="Add to portfolio")
        self.test_endpoint("PUT", f"/api/deal-intelligence/portfolio/{TEST_PROPERTY_ID}",
                          data={"arv": 150000, "renovation_cost": 20000},
                          description="Update portfolio entry")

        # ========================================
        # SAVED PROPERTIES & KANBAN
        # ========================================
        print("\n--- SAVED PROPERTIES & KANBAN ---")

        self.test_endpoint("GET", f"/api/deal-intelligence/saved/{TEST_USER_ID}",
                          description="Get saved properties")
        self.test_endpoint("GET", f"/api/deal-intelligence/saved/{TEST_USER_ID}/kanban",
                          description="Get kanban board")
        self.test_endpoint("GET", f"/api/deal-intelligence/saved/{TEST_USER_ID}/stats",
                          description="Get saved properties stats")
        self.test_endpoint("POST", "/api/deal-intelligence/saved",
                          data={"property_id": TEST_PROPERTY_ID, "kanban_stage": "analyzing"},
                          description="Save property")
        self.test_endpoint("PUT", f"/api/deal-intelligence/saved/{TEST_PROPERTY_ID}/stage",
                          data={"kanban_stage": "due_diligence"},
                          description="Move property to new stage")

        # ========================================
        # NOTES & CHECKLIST
        # ========================================
        print("\n--- NOTES & CHECKLIST ---")

        self.test_endpoint("GET", f"/api/deal-intelligence/notes/{TEST_PROPERTY_ID}",
                          description="Get property notes")
        self.test_endpoint("POST", "/api/deal-intelligence/notes",
                          data={"property_id": TEST_PROPERTY_ID, "content": "Test note"},
                          description="Add note")
        self.test_endpoint("PUT", f"/api/deal-intelligence/notes/1",
                          data={"content": "Updated note"},
                          description="Update note")
        self.test_endpoint("GET", f"/api/deal-intelligence/checklist/{TEST_PROPERTY_ID}/{TEST_USER_ID}",
                          description="Get checklist")
        self.test_endpoint("PUT", f"/api/deal-intelligence/checklist/{TEST_PROPERTY_ID}/{TEST_USER_ID}",
                          data={"checklist_items": {"inspection_complete": True}},
                          description="Update checklist")
        self.test_endpoint("POST", f"/api/deal-intelligence/checklist/{TEST_PROPERTY_ID}/{TEST_USER_ID}/reset",
                          description="Reset checklist")

        # ========================================
        # MARKET ANOMALIES
        # ========================================
        print("\n--- MARKET ANOMALIES ---")

        self.test_endpoint("GET", "/api/deal-intelligence/market-anomalies",
                          params={"limit": 5},
                          description="Get market anomalies")
        self.test_endpoint("GET", f"/api/deal-intelligence/market-anomalies/property/{TEST_PROPERTY_ID}",
                          description="Get property anomaly")
        self.test_endpoint("POST", "/api/deal-intelligence/market-anomalies/analyze",
                          data={"property_id": TEST_PROPERTY_ID},
                          description="Trigger anomaly analysis")

        # ========================================
        # COMPARABLE SALES
        # ========================================
        print("\n--- COMPARABLE SALES ---")

        self.test_endpoint("GET", f"/api/deal-intelligence/comparable-sales/{TEST_PROPERTY_ID}",
                          description="Get comparable sales")
        self.test_endpoint("POST", f"/api/deal-intelligence/comparable-sales/{TEST_PROPERTY_ID}",
                          data={"max_distance_miles": 1.0, "max_age_days": 365},
                          description="Create comps analysis")
        self.test_endpoint("POST", "/api/deal-intelligence/comparable-sales/ai-analyze",
                          data={"property_id": TEST_PROPERTY_ID},
                          description="AI-powered comps analysis")

        # ========================================
        # RENOVATION ESTIMATES
        # ========================================
        print("\n--- RENOVATION ESTIMATES ---")

        self.test_endpoint("GET", f"/api/deal-intelligence/renovation/estimate/{TEST_PROPERTY_ID}",
                          description="Get renovation estimate")
        self.test_endpoint("POST", "/api/deal-intelligence/renovation/analyze",
                          data={"property_id": TEST_PROPERTY_ID},
                          description="Create renovation estimate")

        # ========================================
        # INVESTMENT STRATEGIES
        # ========================================
        print("\n--- INVESTMENT STRATEGIES ---")

        self.test_endpoint("GET", f"/api/deal-intelligence/strategies/{TEST_USER_ID}",
                          description="Get user strategies")
        self.test_endpoint("POST", "/api/deal-intelligence/strategies",
                          data={
                              "user_id": TEST_USER_ID,
                              "strategy_name": "Fix and Flip",
                              "min_arv": 150000,
                              "max_purchase_price": 100000
                          },
                          description="Create strategy")
        self.test_endpoint("PUT", "/api/deal-intelligence/strategies/1",
                          data={"min_arv": 160000},
                          description="Update strategy")

        # ========================================
        # COLLABORATION
        # ========================================
        print("\n--- COLLABORATION ---")

        self.test_endpoint("GET", f"/api/deal-intelligence/collaboration/shared-with-me/{TEST_USER_ID}",
                          description="Get shared with me")
        self.test_endpoint("GET", f"/api/deal-intelligence/collaboration/shared-by-me/{TEST_USER_ID}",
                          description="Get shared by me")
        self.test_endpoint("POST", "/api/deal-intelligence/collaboration/share",
                          data={"property_id": TEST_PROPERTY_ID, "shared_with": "another-user"},
                          description="Share property")
        self.test_endpoint("GET", f"/api/deal-intelligence/collaboration/comments/{TEST_PROPERTY_ID}",
                          description="Get property comments")
        self.test_endpoint("POST", "/api/deal-intelligence/collaboration/comments",
                          data={"property_id": TEST_PROPERTY_ID, "content": "Great deal!"},
                          description="Add comment")

        # ========================================
        # NOTIFICATIONS
        # ========================================
        print("\n--- NOTIFICATIONS ---")

        self.test_endpoint("GET", f"/api/deal-intelligence/notifications/{TEST_USER_ID}/history",
                          description="Get notification history")
        self.test_endpoint("POST", "/api/deal-intelligence/notifications/register",
                          data={"token": "test-device-token", "platform": "ios"},
                          description="Register push token")

        # ========================================
        # EXPORT
        # ========================================
        print("\n--- EXPORT ---")

        self.test_endpoint("POST", "/api/deal-intelligence/export/csv",
                          data={"property_ids": [TEST_PROPERTY_ID]},
                          description="Export to CSV")

        # ========================================
        # PROPERTIES API
        # ========================================
        print("\n--- PROPERTIES API ---")

        self.test_endpoint("GET", "/api/properties",
                          params={"page": 1, "page_size": 10},
                          description="List properties")
        self.test_endpoint("GET", f"/api/properties/{TEST_PROPERTY_ID}",
                          description="Get property details")
        self.test_endpoint("GET", "/api/properties/search",
                          params={"query": "Jacksonville"},
                          description="Search properties")

        # ========================================
        # ENRICHMENT API
        # ========================================
        print("\n--- ENRICHMENT API ---")

        self.test_endpoint("GET", "/api/enrichment/settings",
                          description="Get enrichment settings")
        self.test_endpoint("PUT", "/api/enrichment/settings",
                          data={"auto_enrich_new": True},
                          description="Update enrichment settings")
        self.test_endpoint("POST", f"/api/enrichment/{TEST_PROPERTY_ID}",
                          description="Enrich property")
        self.test_endpoint("GET", f"/api/enrichment/status/{TEST_PROPERTY_ID}",
                          description="Get enrichment status")

        # ========================================
        # WEBHOOKS
        # ========================================
        print("\n--- WEBHOOKS ---")

        self.test_endpoint("GET", "/api/webhooks", description="List webhooks")
        self.test_endpoint("POST", "/api/webhooks",
                          data={"url": "https://example.com/webhook", "events": ["property.created"]},
                          description="Create webhook")

        # ========================================
        # PRINT SUMMARY
        # ========================================
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.get("status") == "PASS")
        failed = total - passed

        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Total: {total}")
        print(f"Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"Failed: {failed} ({failed/total*100:.1f}%)")
        print("="*80 + "\n")

        # Print failures
        if failed > 0:
            print("FAILING ENDPOINTS:")
            print("-" * 80)
            for result in self.results:
                if result.get("status") != "PASS":
                    error = result.get("error", "Unknown error")
                    print(f"  {result['method']} {result['path']}")
                    print(f"    Status: {result.get('status_code', 'N/A')}")
                    print(f"    Error: {error[:200]}")
                    print()

    def save_results(self):
        """Save test results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save JSON
        with open(f"/tmp/test_results_{timestamp}.json", "w") as f:
            json.dump(self.results, f, indent=2)

        # Save Markdown report
        with open(f"/tmp/test_report_{timestamp}.md", "w") as f:
            f.write(f"# API Endpoint Test Report\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            total = len(self.results)
            passed = sum(1 for r in self.results if r.get("status") == "PASS")
            failed = total - passed

            f.write(f"## Summary\n\n")
            f.write(f"| Metric | Count |\n")
            f.write(f"|--------|-------|\n")
            f.write(f"| Total | {total} |\n")
            f.write(f"| Passed | {passed} ({passed/total*100:.1f}%) |\n")
            f.write(f"| Failed | {failed} ({failed/total*100:.1f}%) |\n\n")

            f.write(f"## Passing Endpoints ({passed})\n\n")
            for r in self.results:
                if r.get("status") == "PASS":
                    f.write(f"- **{r['method']}** `{r['path']}` - {r['description']}\n")

            f.write(f"\n## Failing Endpoints ({failed})\n\n")
            for r in self.results:
                if r.get("status") != "PASS":
                    error = r.get("error", "Unknown error")
                    f.write(f"### {r['method']} `{r['path']}`\n")
                    f.write(f"- **Status:** {r.get('status_code', 'ERROR')}\n")
                    f.write(f"- **Error:** {error[:500]}\n\n")

        print(f"\nResults saved to:")
        print(f"  - /tmp/test_results_{timestamp}.json")
        print(f"  - /tmp/test_report_{timestamp}.md")

if __name__ == "__main__":
    tester = EndpointTester()
    tester.run_all_tests()
    tester.save_results()
