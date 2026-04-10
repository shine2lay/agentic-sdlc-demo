"""
Acceptance test: display app version in footer via /api/version endpoint.

Verifies:
1. GET /api/version returns {"version": "0.4.0", "deployed_by": "agentic-sdlc"} (backend)
2. frontend/src/api.ts exports a fetchVersion function
3. frontend/src/App.tsx imports fetchVersion + useQuery and renders version in footer
"""
import sys
import re
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)

API_TS = "frontend/src/api.ts"
APP_TSX = "frontend/src/App.tsx"


def read_file(path: str) -> str:
    with open(path, "r") as f:
        return f.read()


def test_api_version_endpoint():
    """GET /api/version returns 200 with version and deployed_by fields."""
    response = client.get("/api/version")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data.get("version") == "0.4.0", f"Expected version '0.4.0', got {data.get('version')}"
    assert data.get("deployed_by") == "agentic-sdlc", (
        f"Expected deployed_by 'agentic-sdlc', got {data.get('deployed_by')}"
    )
    print("PASS: /api/version returns correct response")


def test_fetch_version_function_in_api_ts():
    """frontend/src/api.ts must export an async fetchVersion function."""
    src = read_file(API_TS)

    assert "fetchVersion" in src, "api.ts does not contain 'fetchVersion' function"

    # Should follow the same pattern as fetchHealth: export async function fetchVersion
    pattern = r"export\s+async\s+function\s+fetchVersion\s*\("
    match = re.search(pattern, src)
    assert match is not None, (
        "api.ts does not export an async fetchVersion function matching the expected pattern"
    )

    # Should call /api/version
    assert "/api/version" in src, "fetchVersion does not fetch '/api/version'"
    print("PASS: api.ts exports fetchVersion function")


def test_app_tsx_displays_version_in_footer():
    """App.tsx must import fetchVersion, use useQuery, and render version in footer."""
    src = read_file(APP_TSX)

    # Must import useQuery from @tanstack/react-query
    assert "useQuery" in src, "App.tsx does not import useQuery"
    assert "@tanstack/react-query" in src, "App.tsx does not import from '@tanstack/react-query'"

    # Must import fetchVersion from ./api
    assert "fetchVersion" in src, "App.tsx does not import fetchVersion"

    # Must render version text in footer with conditional rendering
    assert "versionInfo" in src, "App.tsx does not reference 'versionInfo' variable"

    # Footer must still contain the original links (safeguard)
    assert "claude.ai" in src, "Footer is missing Claude link"
    assert "Temper AI" in src, "Footer is missing Temper AI link"
    assert "Source" in src, "Footer is missing Source link"

    # Version display should use text-xs for smaller font than footer text-sm
    version_pattern = r"versionInfo\?\.version"
    match = re.search(version_pattern, src)
    assert match is not None, (
        "App.tsx does not conditionally render versionInfo?.version in the footer"
    )
    print("PASS: App.tsx displays version in footer")


if __name__ == "__main__":
    try:
        test_api_version_endpoint()
        test_fetch_version_function_in_api_ts()
        test_app_tsx_displays_version_in_footer()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)
