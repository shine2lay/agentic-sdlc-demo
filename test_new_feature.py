"""Acceptance tests for GET /api/footer-config endpoint.

Tests the footer branding configuration endpoint that should return
text, font_size_px, text_color, and opacity fields. Also verifies
no regression on adjacent endpoints and that the response does NOT
include a version field (version is served by /api/version).
"""

import sys

from fastapi.testclient import TestClient

from server.app import app

client = TestClient(app)


def test_footer_config_returns_200_with_expected_fields():
    """GET /api/footer-config returns 200 with text, font_size_px, text_color, opacity."""
    response = client.get("/api/footer-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["text"] == "Powered by Temper AI", f"Unexpected text: {data.get('text')}"
    assert data["font_size_px"] == 12, f"Unexpected font_size_px: {data.get('font_size_px')}"
    assert data["text_color"] == "#94a3b8", f"Unexpected text_color: {data.get('text_color')}"
    assert data["opacity"] == 0.6, f"Unexpected opacity: {data.get('opacity')}"
    # Must NOT contain a version field (version lives at /api/version)
    assert "version" not in data, "footer-config must not include a version field"
    print("PASS: footer-config returns 200 with expected fields")


def test_footer_config_has_exactly_four_fields():
    """Response body must contain exactly {text, font_size_px, text_color, opacity} — no extras."""
    response = client.get("/api/footer-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    expected_keys = {"text", "font_size_px", "text_color", "opacity"}
    assert set(data.keys()) == expected_keys, (
        f"Expected keys {expected_keys}, got {set(data.keys())}"
    )
    print("PASS: footer-config has exactly four fields")


def test_existing_version_endpoint_not_regressed():
    """GET /api/version still returns 200 with version and deployed_by."""
    response = client.get("/api/version")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["version"] == "0.4.0", f"Unexpected version: {data.get('version')}"
    assert data["deployed_by"] == "agentic-sdlc", f"Unexpected deployed_by: {data.get('deployed_by')}"
    print("PASS: /api/version not regressed")


def test_existing_health_endpoint_not_regressed():
    """GET /api/health still returns 200 with status ok."""
    response = client.get("/api/health")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "ok", f"Unexpected status: {data.get('status')}"
    print("PASS: /api/health not regressed")


def test_existing_skeleton_config_not_regressed():
    """GET /api/skeleton-config still returns 200 — no route conflict with adjacent endpoint."""
    response = client.get("/api/skeleton-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "rows" in data, "skeleton-config missing 'rows' field"
    print("PASS: /api/skeleton-config not regressed")


if __name__ == "__main__":
    passed = 0
    failed = 0
    for name, func in [
        ("test_footer_config_returns_200_with_expected_fields", test_footer_config_returns_200_with_expected_fields),
        ("test_footer_config_has_exactly_four_fields", test_footer_config_has_exactly_four_fields),
        ("test_existing_version_endpoint_not_regressed", test_existing_version_endpoint_not_regressed),
        ("test_existing_health_endpoint_not_regressed", test_existing_health_endpoint_not_regressed),
        ("test_existing_skeleton_config_not_regressed", test_existing_skeleton_config_not_regressed),
    ]:
        try:
            func()
            passed += 1
        except Exception as e:
            print(f"FAIL: {name}: {e}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed out of {passed + failed}")
    if failed > 0:
        sys.exit(1)
    else:
        print("ALL TESTS PASSED")
