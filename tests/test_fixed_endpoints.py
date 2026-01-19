#!/usr/bin/env python3
"""
Fixed API endpoint tester with correct field names
"""
import requests
import json
from datetime import datetime

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
                      params: dict = None, description: str = "") -> dict:
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

            if not success:
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
        print("FIXED API ENDPOINT TEST - Correct Field Names")
        print("="*80 + "\n")

        # ========================================
        # PHASE 1: GENERATE TEST DATA
        # ========================================
        print("\n--- PHASE 1: GENERATING TEST DATA ---")

        # Add to watchlist first (creates entry)
        self.test_endpoint("POST", "/api/deal-intelligence/watchlist",
                          data={"property_id": TEST_PROPERTY_ID},
                          description="Add to watchlist (for test data)")

        # Add to saved properties
        self.test_endpoint("POST", "/api/deal-intelligence/saved",
                          data={"property_id": TEST_PROPERTY_ID, "kanban_stage": "analyzing"},
                          description="Save property (for test data)")

        # ========================================
        # PHASE 2: SETTINGS (should all pass now)
        # ========================================
        print("\n--- PHASE 2: SETTINGS ---")

        self.test_endpoint("GET", "/health", description="Health check")
        self.test_endpoint("GET", "/api/deal-intelligence/health", description="DI health")
        self.test_endpoint("GET", "/api/deal-intelligence/settings/admin")
        self.test_endpoint("PUT", "/api/deal-intelligence/settings/admin",
                          data={"feature_market_anomaly_detection": True})
        self.test_endpoint("GET", "/api/deal-intelligence/settings/county/1")
        self.test_endpoint("POST", "/api/deal-intelligence/settings/county",
                          data={"county_id": 1})
        self.test_endpoint("GET", f"/api/deal-intelligence/settings/user/{TEST_USER_ID}")
        self.test_endpoint("POST", "/api/deal-intelligence/settings/user",
                          data={"user_id": TEST_USER_ID, "county_id": 1})

        # ========================================
        # PHASE 3: WATCHLIST (fixed fields)
        # ========================================
        print("\n--- PHASE 3: WATCHLIST ---")

        self.test_endpoint("GET", f"/api/deal-intelligence/watchlist/{TEST_USER_ID}")
        # Now try update with the saved property
        self.test_endpoint("PUT", f"/api/deal-intelligence/watchlist/{TEST_PROPERTY_ID}",
                          data={"priority": "high", "watch_notes": "Hot deal!"})
        self.test_endpoint("GET", f"/api/deal-intelligence/alerts/{TEST_USER_ID}")

        # ========================================
        # PHASE 4: NOTES & CHECKLIST (fixed note_text field)
        # ========================================
        print("\n--- PHASE 4: NOTES & CHECKLIST ---")

        self.test_endpoint("GET", f"/api/deal-intelligence/notes/{TEST_PROPERTY_ID}")
        self.test_endpoint("POST", "/api/deal-intelligence/notes",
                          data={"property_id": TEST_PROPERTY_ID, "note_text": "Test note with correct field"})
        self.test_endpoint("PUT", "/api/deal-intelligence/notes/1",
                          data={"note_text": "Updated note"})
        self.test_endpoint("GET", f"/api/deal-intelligence/checklist/{TEST_PROPERTY_ID}/{TEST_USER_ID}")
        self.test_endpoint("PUT", f"/api/deal-intelligence/checklist/{TEST_PROPERTY_ID}/{TEST_USER_ID}",
                          data={"checklist_items": {"inspection_complete": True}})
        self.test_endpoint("POST", f"/api/deal-intelligence/checklist/{TEST_PROPERTY_ID}/{TEST_USER_ID}/reset")

        # ========================================
        # PHASE 5: STRATEGIES (fixed strategy_type field)
        # ========================================
        print("\n--- PHASE 5: INVESTMENT STRATEGIES ---")

        self.test_endpoint("GET", f"/api/deal-intelligence/strategies/{TEST_USER_ID}")
        self.test_endpoint("POST", "/api/deal-intelligence/strategies",
                          data={
                              "user_id": TEST_USER_ID,
                              "strategy_name": "Fix and Flip",
                              "strategy_type": "fix_and_flip",
                              "max_purchase_price": 100000
                          })
        self.test_endpoint("PUT", "/api/deal-intelligence/strategies/1",
                          params={"user_id": TEST_USER_ID},
                          data={"max_purchase_price": 90000})

        # ========================================
        # PHASE 6: COLLABORATION (fixed field names)
        # ========================================
        print("\n--- PHASE 6: COLLABORATION ---")

        self.test_endpoint("GET", f"/api/deal-intelligence/collaboration/shared-with-me/{TEST_USER_ID}")
        self.test_endpoint("GET", f"/api/deal-intelligence/collaboration/shared-by-me/{TEST_USER_ID}")
        self.test_endpoint("POST", "/api/deal-intelligence/collaboration/share",
                          data={"property_id": TEST_PROPERTY_ID, "shared_with_user_id": "another-user-456", "shared_by_user_id": TEST_USER_ID})
        self.test_endpoint("GET", f"/api/deal-intelligence/collaboration/comments/{TEST_PROPERTY_ID}")
        self.test_endpoint("POST", "/api/deal-intelligence/collaboration/comments",
                          data={"property_id": TEST_PROPERTY_ID, "comment_text": "Great deal!"})

        # ========================================
        # PHASE 7: NOTIFICATIONS (fixed device_token field)
        # ========================================
        print("\n--- PHASE 7: NOTIFICATIONS ---")

        self.test_endpoint("GET", f"/api/deal-intelligence/notifications/{TEST_USER_ID}/history")
        self.test_endpoint("POST", "/api/deal-intelligence/notifications/register",
                          data={"device_token": "test-token-123", "platform": "ios"})

        # ========================================
        # PHASE 8: MARKET ANOMALIES (with address)
        # ========================================
        print("\n--- PHASE 8: MARKET ANOMALIES ---")

        self.test_endpoint("GET", "/api/deal-intelligence/market-anomalies",
                          params={"limit": 5})
        self.test_endpoint("POST", "/api/deal-intelligence/market-anomalies/analyze",
                          data={
                              "property_id": TEST_PROPERTY_ID,
                              "address": "123 Main St, Jacksonville, FL 32205",
                              "list_price": 95000
                          })

        # ========================================
        # PHASE 9: SAVED PROPERTIES & KANBAN
        # ========================================
        print("\n--- PHASE 9: SAVED PROPERTIES & KANBAN ---")

        self.test_endpoint("GET", f"/api/deal-intelligence/saved/{TEST_USER_ID}")
        self.test_endpoint("GET", f"/api/deal-intelligence/saved/{TEST_USER_ID}/kanban")
        self.test_endpoint("GET", f"/api/deal-intelligence/saved/{TEST_USER_ID}/stats")

        # ========================================
        # PHASE 10: PORTFOLIO
        # ========================================
        print("\n--- PHASE 10: PORTFOLIO ---")

        self.test_endpoint("GET", f"/api/deal-intelligence/portfolio/{TEST_USER_ID}")
        self.test_endpoint("GET", f"/api/deal-intelligence/portfolio/{TEST_USER_ID}/summary")

        # Enable portfolio tracking feature first
        self.test_endpoint("PUT", "/api/deal-intelligence/settings/admin",
                          data={"feature_portfolio_tracking": True})

        self.test_endpoint("POST", "/api/deal-intelligence/portfolio",
                          data={"property_id": TEST_PROPERTY_ID, "purchase_price": 95000})

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
        with open(f"/tmp/test_results_fixed_{timestamp}.json", "w") as f:
            json.dump(self.results, f, indent=2)

        # Save Markdown report
        with open(f"/tmp/test_report_fixed_{timestamp}.md", "w") as f:
            f.write(f"# Fixed API Endpoint Test Report\n\n")
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
                    f.write(f"- **{r['method']}** `{r['path']}`\n")

            f.write(f"\n## Failing Endpoints ({failed})\n\n")
            for r in self.results:
                if r.get("status") != "PASS":
                    error = r.get("error", "Unknown error")
                    f.write(f"### {r['method']} `{r['path']}`\n")
                    f.write(f"- **Status:** {r.get('status_code', 'ERROR')}\n")
                    f.write(f"- **Error:** {error[:500]}\n\n")

        print(f"\nResults saved to:")
        print(f"  - /tmp/test_results_fixed_{timestamp}.json")
        print(f"  - /tmp/test_report_fixed_{timestamp}.md")

if __name__ == "__main__":
    tester = EndpointTester()
    tester.run_all_tests()
    tester.save_results()
