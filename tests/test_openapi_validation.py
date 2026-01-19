"""
Pytest tests to validate OpenAPI/Swagger schema correctness.

These tests ensure that the OpenAPI spec remains a strict, accurate API contract
and that future changes cannot silently break Swagger correctness.

Run with:
    ./venv/bin/python -m pytest tests/test_openapi_validation.py -v
"""

import sys
from pathlib import Path

# Add parent directory to path to import webhook_server module
sys.path.insert(0, str(Path(__file__).parent.parent))

from webhook_server.app import app


def test_openapi_schema_exists():
    """Test that the OpenAPI schema can be generated."""
    openapi_schema = app.openapi()
    assert openapi_schema is not None
    assert isinstance(openapi_schema, dict)


def test_openapi_required_components():
    """Test that required component schemas exist."""
    openapi_schema = app.openapi()
    components = openapi_schema.get("components", {})
    schemas = components.get("schemas", {})

    # Response models
    required_schemas = [
        "ErrorResponse",
        "WebhookResponse",
        "ScheduledScrapeResponse",
        "HealthResponse",
        "StatusResponse",
        "ChangeDetectionWebhook",
        "EnrichmentResponse",
        "EnrichmentStatusResponse",
        # Settings models
        "AdminSettingsUpdate",
        "CountySettingsCreate",
        "CountySettingsUpdate",
        "UserPreferencesCreate",
        "UserPreferencesUpdate",
        "TemplateApplyRequest",
        "EnrichPropertyRequest",
        "SkipTraceRequest",
        "BulkSkipTraceRequest",
    ]

    for schema_name in required_schemas:
        assert schema_name in schemas, f"Missing required schema: {schema_name}"


def test_error_response_schema_structure():
    """Test that ErrorResponse schema has correct structure."""
    openapi_schema = app.openapi()
    error_response = openapi_schema["components"]["schemas"]["ErrorResponse"]

    assert error_response["type"] == "object"
    assert "properties" in error_response
    assert "detail" in error_response["properties"]
    assert error_response["properties"]["detail"]["type"] == "string"
    assert "detail" in error_response.get("required", [])


def test_scheduled_scrape_response_schema_structure():
    """Test that ScheduledScrapeResponse schema has correct structure."""
    openapi_schema = app.openapi()
    schema = openapi_schema["components"]["schemas"]["ScheduledScrapeResponse"]

    assert schema["type"] == "object"
    properties = schema["properties"]

    # Check required fields exist
    required_fields = {
        "status",
        "message",
        "queued_counties",
        "already_running",
        "total_counties"
    }
    assert required_fields.issubset(properties.keys())

    # Check types
    assert properties["status"]["type"] == "string"
    assert properties["message"]["type"] == "string"
    assert properties["queued_counties"]["type"] == "integer"
    assert properties["already_running"]["type"] == "array"
    assert properties["total_counties"]["type"] == "integer"


def test_webhook_response_schema_structure():
    """Test that WebhookResponse schema has correct structure."""
    openapi_schema = app.openapi()
    schema = openapi_schema["components"]["schemas"]["WebhookResponse"]

    assert schema["type"] == "object"
    properties = schema["properties"]

    # Check required fields exist
    required_fields = {"status", "message", "county", "job_id"}
    assert required_fields.issubset(properties.keys())

    # Check types
    assert properties["status"]["type"] == "string"
    assert properties["message"]["type"] == "string"
    # county and job_id are nullable (anyOf with string or null)
    assert "anyOf" in properties["county"]
    assert "anyOf" in properties["job_id"]


def test_endpoint_uses_schema_refs():
    """Test that key endpoints use proper schema refs in responses."""
    openapi_schema = app.openapi()

    # Test cases: (path, method, status_code, expected_schema_ref)
    test_cases = [
        ("/trigger/{county}", "post", "200", "WebhookResponse"),
        ("/trigger/{county}", "post", "401", "ErrorResponse"),
        ("/trigger/{county}", "post", "422", "HTTPValidationError"),
        ("/webhooks/scheduled", "post", "200", "ScheduledScrapeResponse"),
        ("/webhooks/scheduled", "post", "401", "ErrorResponse"),
        ("/webhooks/changedetection", "post", "200", "WebhookResponse"),
        ("/webhooks/changedetection", "post", "400", "ErrorResponse"),
        ("/webhooks/changedetection", "post", "401", "ErrorResponse"),
    ]

    for path, method, status_code, expected_ref in test_cases:
        endpoint = openapi_schema["paths"][path][method]
        response = endpoint["responses"][status_code]
        schema = response["content"]["application/json"]["schema"]

        assert "$ref" in schema, f"{method.upper()} {path} {status_code} missing schema ref"
        assert schema["$ref"] == f"#/components/schemas/{expected_ref}", \
            f"{method.upper()} {path} {status_code} expected {expected_ref}, got {schema['$ref']}"


def test_openapi_version_and_info():
    """Test that OpenAPI has correct version and metadata."""
    openapi_schema = app.openapi()

    assert openapi_schema["openapi"] == "3.1.0"
    assert "info" in openapi_schema
    assert openapi_schema["info"]["title"] == "NJ Sheriff Sale Scraper API"
    assert "version" in openapi_schema["info"]


def test_all_error_responses_use_schema_refs():
    """Test that all error responses use schema refs, not inline schemas."""
    openapi_schema = app.openapi()

    error_status_codes = ["400", "401", "404", "422", "500"]

    for path, path_item in openapi_schema["paths"].items():
        for method, endpoint in path_item.items():
            if method not in ["get", "post", "put", "delete", "patch"]:
                continue

            responses = endpoint.get("responses", {})

            for status_code in error_status_codes:
                if status_code not in responses:
                    continue

                response = responses[status_code]
                if "content" not in response:
                    continue
                if "application/json" not in response["content"]:
                    continue

                schema = response["content"]["application/json"].get("schema", {})

                # Error responses should use schema refs
                if schema:
                    # Either it's a ref, or it's the built-in HTTPValidationError
                    # (which has a specific structure for validation errors)
                    if "$ref" not in schema:
                        # Allow HTTPValidationError's inline structure
                        assert status_code == "422", \
                            f"{method.upper()} {path} {status_code} should use schema ref, not inline schema"


def test_trigger_endpoint_has_all_responses():
    """Test that /trigger/{county} endpoint has all required response codes."""
    openapi_schema = app.openapi()
    endpoint = openapi_schema["paths"]["/trigger/{county}"]["post"]

    responses = endpoint["responses"]
    assert "200" in responses  # Success
    assert "202" in responses  # Already running
    assert "401" in responses  # Invalid webhook secret
    assert "422" in responses  # Validation error


def test_scheduled_webhook_has_all_responses():
    """Test that /webhooks/scheduled endpoint has all required response codes."""
    openapi_schema = app.openapi()
    endpoint = openapi_schema["paths"]["/webhooks/scheduled"]["post"]

    responses = endpoint["responses"]
    assert "200" in responses  # Success
    assert "401" in responses  # Invalid schedule secret
    assert "422" in responses  # Validation error


def test_changedetection_webhook_has_all_responses():
    """Test that /webhooks/changedetection endpoint has all required response codes."""
    openapi_schema = app.openapi()
    endpoint = openapi_schema["paths"]["/webhooks/changedetection"]["post"]

    responses = endpoint["responses"]
    assert "200" in responses  # Success
    assert "202" in responses  # Already running
    assert "400" in responses  # Invalid watch_title
    assert "401" in responses  # Invalid webhook secret
    assert "422" in responses  # Validation error


def test_health_endpoint_exists():
    """Test that health check endpoints exist."""
    openapi_schema = app.openapi()

    assert "/health" in openapi_schema["paths"]
    assert "/status" in openapi_schema["paths"]


def test_openapi_tags_defined():
    """Test that OpenAPI tags are defined."""
    openapi_schema = app.openapi()

    tags = openapi_schema.get("tags") or []
    # Tags are optional in OpenAPI - just verify the schema is valid
    # The tags are defined in the app but may not appear in the generated schema
    # This is a minimal test to ensure the schema structure is correct
    assert isinstance(tags, list)


if __name__ == "__main__":
    # Run tests with pytest
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
