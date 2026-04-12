"""Acceptance tests for queue-count endpoint and existing config endpoints."""
import sys
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)


def test_suggestion_chip_bounce_config_returns_200_with_all_fields():
    response = client.get('/api/suggestion-chip-bounce-config')
    assert response.status_code == 200, f'Expected 200, got {response.status_code}'
    assert response.headers['content-type'] == 'application/json'
    data = response.json()
    assert len(data) == 9, f'Expected 9 fields, got {len(data)}: {list(data.keys())}'
    assert data['enabled'] is True
    assert data['translate_y_px'] == 4.0
    assert data['duration_ms'] == 500
    assert data['easing'] == 'cubic-bezier(0.34, 1.56, 0.64, 1)'
    assert data['stagger_ms'] == 80
    assert data['initial_delay_ms'] == 300
    assert data['iteration_count'] == 1
    assert data['respect_reduced_motion'] is True
    assert data['target'] == 'suggestion-chip'
    print('PASS: suggestion chip bounce config returns 200 with all fields')


def test_queue_count_returns_valid_response():
    resp = client.get('/api/queue-count')
    assert resp.status_code == 200, f'Expected 200, got {resp.status_code}'
    data = resp.json()
    assert 'queued_runs' in data, f'Missing queued_runs field: {list(data.keys())}'
    assert 'poll_interval_ms' in data, f'Missing poll_interval_ms field: {list(data.keys())}'
    assert isinstance(data['queued_runs'], int), f'queued_runs should be int, got {type(data["queued_runs"])}'
    assert data['queued_runs'] >= 0, f'queued_runs should be non-negative, got {data["queued_runs"]}'
    assert data['poll_interval_ms'] == 5000, f'Expected poll_interval_ms=5000, got {data["poll_interval_ms"]}'
    print('PASS: queue count returns valid response')


def test_existing_endpoints_not_regressed():
    for path in ['/api/deploy-checkmark-config', '/api/active-tab-shimmer-config', '/api/typing-test-config', '/api/color-picker-config', '/api/bounce-button-config', '/api/confetti-config', '/api/palette-config', '/api/suggestion-chip-bounce-config', '/api/queue-count']:
        resp = client.get(path)
        assert resp.status_code == 200, f'{path} regressed: {resp.status_code}'
    print('PASS: existing config endpoints not regressed')


if __name__ == '__main__':
    try:
        test_suggestion_chip_bounce_config_returns_200_with_all_fields()
        test_queue_count_returns_valid_response()
        test_existing_endpoints_not_regressed()
        print('ALL TESTS PASSED')
    except Exception as e:
        print(f'FAIL: {e}')
        sys.exit(1)
