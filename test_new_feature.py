"""Acceptance tests for the typing speed test feature."""

import sys
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)


def test_typing_test_config_returns_200_with_all_fields():
    """GET /api/typing-test-config returns 200 with title, sentences, time_limit_seconds, words_per_minute_label."""
    response = client.get("/api/typing-test-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["title"] == "Typing Speed Test"
    assert isinstance(data["sentences"], list)
    assert len(data["sentences"]) == 5, f"Expected 5 sentences, got {len(data['sentences'])}"
    assert data["time_limit_seconds"] == 60
    assert data["words_per_minute_label"] == "WPM"
    expected_fields = {"title", "sentences", "time_limit_seconds", "words_per_minute_label"}
    assert set(data.keys()) == expected_fields, f"Field mismatch: {set(data.keys()) ^ expected_fields}"
    print("PASS: typing test config returns 200 with all fields")


def test_typing_test_calculate_returns_correct_wpm():
    """POST /api/typing-test-calculate with perfect input returns correct WPM and accuracy."""
    response = client.post("/api/typing-test-calculate", json={
        "original": "The quick brown fox",
        "typed": "The quick brown fox",
        "elapsed_seconds": 12.0,
    })
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    # 4 words / 12 seconds * 60 = 20.0 WPM
    assert data["wpm"] == 20.0, f"Expected wpm=20.0, got {data['wpm']}"
    assert data["accuracy"] == 100.0, f"Expected accuracy=100.0, got {data['accuracy']}"
    assert data["correct_chars"] == 19, f"Expected correct_chars=19, got {data['correct_chars']}"
    assert data["total_chars"] == 19, f"Expected total_chars=19, got {data['total_chars']}"
    assert data["elapsed_seconds"] == 12.0
    print("PASS: typing test calculate returns correct WPM")


def test_typing_test_calculate_rejects_zero_elapsed():
    """POST /api/typing-test-calculate with elapsed_seconds=0 returns 400."""
    response = client.post("/api/typing-test-calculate", json={
        "original": "hello",
        "typed": "hello",
        "elapsed_seconds": 0,
    })
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    print("PASS: typing test calculate rejects zero elapsed")


def test_typing_test_calculate_partial_input():
    """POST /api/typing-test-calculate with partial/mistyped input returns correct accuracy."""
    response = client.post("/api/typing-test-calculate", json={
        "original": "hello world",
        "typed": "hallo",
        "elapsed_seconds": 5.0,
    })
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    # zip('hello world', 'hallo') -> h/h=match, e/a=no, l/l=match, l/l=match, o/o=match -> 4 correct
    assert data["correct_chars"] == 4, f"Expected correct_chars=4, got {data['correct_chars']}"
    # accuracy = round((4/11)*100, 1) = 36.4
    assert data["accuracy"] == 36.4, f"Expected accuracy=36.4, got {data['accuracy']}"
    print("PASS: typing test calculate partial input")


def test_community_creations_includes_typing_test():
    """GET /api/community-creations-config includes typing test entry."""
    response = client.get("/api/community-creations-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    paths = [c["path"] for c in data["creations"]]
    assert "/games/typing-test" in paths, f"Typing test not found in creations: {paths}"
    print("PASS: community creations includes typing test")


def test_nearby_endpoints_not_regressed():
    """Emoji rain config and countdown timer config still work."""
    r1 = client.get("/api/emoji-rain-config")
    assert r1.status_code == 200, f"emoji-rain-config returned {r1.status_code}"
    print("PASS: emoji-rain-config not regressed")

    r2 = client.get("/api/countdown-timer-config")
    assert r2.status_code == 200, f"countdown-timer-config returned {r2.status_code}"
    print("PASS: countdown-timer-config not regressed")


if __name__ == "__main__":
    try:
        test_typing_test_config_returns_200_with_all_fields()
        test_typing_test_calculate_returns_correct_wpm()
        test_typing_test_calculate_rejects_zero_elapsed()
        test_typing_test_calculate_partial_input()
        test_community_creations_includes_typing_test()
        test_nearby_endpoints_not_regressed()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)
