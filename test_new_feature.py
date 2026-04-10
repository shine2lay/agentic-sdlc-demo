import sys
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)


def test_gradient_banner_config_returns_all_fields_with_correct_values():
    """Verify GET /api/gradient-banner-config returns 200 with all 8 expected fields and exact values."""
    response = client.get("/api/gradient-banner-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    expected = {
        "text": "Powered by AI",
        "font_size_px": 14,
        "font_weight": "600",
        "text_color": "#ffffff",
        "height_px": 40,
        "gradient_start": "#6366f1",
        "gradient_end": "#8b5cf6",
        "gradient_angle_deg": 90,
    }
    for key, value in expected.items():
        assert key in data, f"Missing field: {key}"
        assert data[key] == value, f"Field {key}: expected {value!r}, got {data[key]!r}"
    print("PASS: gradient-banner-config returns all fields with correct values")


def test_existing_endpoints_still_work():
    """Verify /api/health and /api/footer-config are unaffected by the new endpoint."""
    # Health check
    health = client.get("/api/health")
    assert health.status_code == 200, f"Health expected 200, got {health.status_code}"
    assert health.json() == {"status": "ok"}, f"Unexpected health body: {health.json()}"

    # Footer config regression
    footer = client.get("/api/footer-config")
    assert footer.status_code == 200, f"Footer expected 200, got {footer.status_code}"
    footer_data = footer.json()
    assert footer_data["text"] == "Powered by Temper AI"
    assert footer_data["font_size_px"] == 12
    print("PASS: existing endpoints still work")


if __name__ == "__main__":
    try:
        test_gradient_banner_config_returns_all_fields_with_correct_values()
        test_existing_endpoints_still_work()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)
