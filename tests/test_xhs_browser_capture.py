from pathlib import Path


ROOT = Path(__file__).parents[1]
HELPER = ROOT / "viral-social-remix" / "scripts" / "xhs_browser_capture.mjs"


def test_xhs_browser_capture_helper_keeps_fast_paths():
    text = HELPER.read_text(encoding="utf-8")
    for required in [
        "searchXhs",
        "openAndCaptureXhsPost",
        "isXhsPostHref",
        "evaluatePostCards",
        "scoreRemixCandidate",
        "DEFAULT_REMIX_HINTS",
        "scanLimit",
        "minScore",
        "collectSlidesFromDom",
        "dom-warmed",
        "click-fallback",
        "search_result",
        "observedImageUrls",
    ]:
        assert required in text
