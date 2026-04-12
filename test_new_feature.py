"""Acceptance tests for pixel-art-config endpoint and existing config endpoints."""
import sys
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)


def test_pixel_art_config_returns_200_with_all_fields():
    response = client.get('/api/pixel-art-config')
    assert response.status_code == 200, f'Expected 200, got {response.status_code}'
    assert response.headers['content-type'] == 'application/json'
    data = response.json()
    assert len(data) == 9, f'Expected 9 fields, got {len(data)}: {list(data.keys())}'
    assert data['title'] == 'Pixel Art Canvas'
    assert data['grid_size'] == 16
    assert data['default_color'] == '#ffffff'
    assert data['pixel_size_px'] == 24
    assert data['grid_line_color'] == '#e5e7eb'
    assert data['grid_line_width_px'] == 1
    assert len(data['palette_colors']) == 16, f'Expected 16 palette colors, got {len(data["palette_colors"])}'
    assert data['show_gridlines'] is True
    assert data['background_color'] == '#ffffff'
    print('PASS: pixel art config returns 200 with all fields')


def test_existing_endpoints_not_regressed():
    for path in ['/api/deploy-checkmark-config', '/api/active-tab-shimmer-config', '/api/typing-test-config', '/api/color-picker-config', '/api/bounce-button-config', '/api/confetti-config', '/api/palette-config', '/api/suggestion-chip-bounce-config', '/api/queue-count', '/api/pixel-art-config']:
        resp = client.get(path)
        assert resp.status_code == 200, f'{path} regressed: {resp.status_code}'
    print('PASS: existing config endpoints not regressed')


if __name__ == '__main__':
    try:
        test_pixel_art_config_returns_200_with_all_fields()
        test_existing_endpoints_not_regressed()
        print('ALL TESTS PASSED')
    except Exception as e:
        print(f'FAIL: {e}')
        sys.exit(1)
