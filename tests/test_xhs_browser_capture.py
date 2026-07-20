from pathlib import Path
import json
import subprocess


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
        "dom-observed-recovered",
        "click-fallback",
        "click-fallback-observed-recovered",
        "recoverSlidesFromObserved",
        "search_result",
        "observedImageUrls",
    ]:
        assert required in text


def test_recover_slides_from_observed_completes_partial_xhs_carousel():
    helper_uri = HELPER.as_uri()
    code = f"""
      const mod = await import({json.dumps(helper_uri)});
      const makeUrl = (suffix, quality = "nd_dft") =>
        `https://sns-webpic-qc.xhscdn.com/202607191929/hash/oss-sg/notes_pre_post/1040g3mo322i0vis57q${{suffix}}nv455egbub3x!${{quality}}_wlteh_webp_3`;
      const suffixes = ["005", "0g5", "105", "1g5", "205", "2g5", "305", "3g5"];
      const slides = suffixes.slice(0, 6).map((suffix, index) => ({{
        indicator: `${{index + 1}}/8`,
        url: makeUrl(suffix, "nc_n_webp_mw_1"),
      }}));
      const observed = [
        "https://sns-webpic-qc.xhscdn.com/t/hash/oss-sg/notes_pre_post/unrelated001nv455egbub3x!nd_dft_wlteh_webp_3",
        makeUrl("3g5"),
        makeUrl("005"),
        makeUrl("0g5"),
        makeUrl("105"),
        makeUrl("1g5"),
        makeUrl("205"),
        makeUrl("2g5"),
        makeUrl("305"),
      ];
      const recovered = mod.recoverSlidesFromObserved(slides, 8, observed);
      process.stdout.write(JSON.stringify(recovered));
    """

    completed = subprocess.run(
        ["node", "--input-type=module", "-e", code],
        check=True,
        capture_output=True,
        text=True,
    )
    recovered = json.loads(completed.stdout)

    assert len(recovered) == 8
    assert [item["indicator"] for item in recovered] == [f"{index}/8" for index in range(1, 9)]
    assert [item["source"] for item in recovered] == ["observed-recovered"] * 8
    assert [item["url"].split("57q", 1)[1].split("nv", 1)[0] for item in recovered] == [
        "005",
        "0g5",
        "105",
        "1g5",
        "205",
        "2g5",
        "305",
        "3g5",
    ]
