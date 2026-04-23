from __future__ import annotations

from app.services.note_generation import _classify_analysis_error


def test_classify_analysis_error_maps_http_412() -> None:
    failure = _classify_analysis_error("HTTP Error 412: Precondition Failed")

    assert failure["code"] == "bilibili_request_blocked"
    assert failure["actions"] == ["settings", "retry", "source"]
