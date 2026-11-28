import pytest

from src.run_pipeline import run_with_retries


def test_returns_result_when_first_attempt_works():
    assert run_with_retries(lambda: "done", retries=2, delay=0, sleep=lambda s: None) == "done"


def test_retries_until_it_succeeds():
    calls = {"n": 0}
    waits = []

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionError("database not ready")
        return "ok"

    assert run_with_retries(flaky, retries=2, delay=5, sleep=waits.append) == "ok"
    assert calls["n"] == 3
    assert waits == [5, 5]


def test_gives_up_after_the_allowed_retries():
    calls = {"n": 0}

    def always_fails():
        calls["n"] += 1
        raise ConnectionError("still down")

    with pytest.raises(ConnectionError):
        run_with_retries(always_fails, retries=2, delay=0, sleep=lambda s: None)
    assert calls["n"] == 3