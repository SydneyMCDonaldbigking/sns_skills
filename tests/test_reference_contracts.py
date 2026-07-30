import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).parents[1]
REF = ROOT / "viral-social-remix" / "references"
LOGO_DIR = ROOT / "viral-social-remix" / "umall_logo"
MEMORY = ROOT / "docs" / "memory" / "viral-social-remix"


def test_platform_profiles_contain_exact_output_contracts():
    text = (REF / "platform-profiles.md").read_text(encoding="utf-8")
    for required in ["1152x1536", "1152x1152", "1920x1080", "1080x1920", "exactly 9"]:
        assert required in text
    assert "Xiaohongshu source to English carousel" in text
    assert "a Xiaohongshu URL identifies the source/capture workflow" in text
    assert "`caption-en.txt`" in text


def test_prompt_contract_requires_verbatim_text_and_consistency():
    text = (REF / "prompt-patterns.md").read_text(encoding="utf-8")
    assert "Text (verbatim)" in text
    assert "Consistency lock" in text
    assert "GPT Image 2" in text


def test_output_schema_names_every_delivery_file():
    text = (REF / "output-schema.md").read_text(encoding="utf-8")
    for required in [
        "breakdown.md", "copy.md", "caption-zh.txt", "caption-en.txt",
        "prompts.md", "manifest.json", "validation.json",
        "YYYYMMDD-HHmmss",
    ]:
        assert required in text


def test_output_schema_documents_manifest_generation_state():
    text = (REF / "output-schema.md").read_text(encoding="utf-8")
    for required in [
        "schema_version",
        "source",
        "direct_url",
        "content_type",
        "platform_confidence",
        "provider",
        "prompt_path",
        "request",
        "<redacted data URL>",
        "outputs",
        "last_error",
        "attempts",
        "validated",
        "force",
    ]:
        assert required in text


def test_cooking_workflow_uses_director_first_frame_contract():
    text = (REF / "cooking-video-workflow.md").read_text(encoding="utf-8")
    for required in [
        "Generate the clip 1 `1080x1920` opening frame first",
        "on-demand opening",
        "Give each request only its selected opening reference",
        "official lens-control formula",
        "starting-frame composition + camera movement + direction/amplitude/speed",
        "Do not generate nine storyboard frames by default",
        "generation inputs, not editing assets",
        "Generate a transition opening anchor when the returned last frame is visually",
        "Do not copy the damaged endpoint literally",
        "camera transition, not a generic replacement still",
        "ASIAN GROCER ONLINE",
        "powered by UMALL",
        "Never use the Chinese-region logo",
    ]:
        assert required in text


def test_seedance_reference_distills_prompt_optimizer_rules():
    text = (REF / "seedance-video.md").read_text(encoding="utf-8")
    for required in [
        "Prompt Optimizer Checklist",
        "eight core elements",
        "Classify intent before rewriting",
        "multimodal JSON",
        "content` array",
        "asset-xxx",
        "map them by request order",
        "[Image 1] (product package)",
        "long image, contact sheet, 9-grid, or collage",
        "Detect camera conflicts",
        "only one primary camera movement",
        "Do not silently modify user intent",
        "For editing prompts",
        "complex multi-person front-facing dynamic scenes",
        "`Optimized prompt`, `Optimization`, and `Relevant",
    ]:
        assert required in text


def test_seedance_official_memory_maps_new_base_teaching_to_local_syntax():
    text = (MEMORY / "seedance-official-prompting.md").read_text(encoding="utf-8")
    for required in [
        "workshop prompt optimizer teaching note in `new_base/`",
        "uses `@Image N`",
        "syntax as its example bridge",
        "provider labels like `[Image 1]`",
        "never leave raw `asset-xxx` IDs as action subjects",
        "Prompt Optimizer Lesson",
        "Do not silently modify",
        "`Optimized prompt`,",
        "`Optimization`,",
        "`Relevant principles`",
        "[[seedance-prompt-optimizer]]",
    ]:
        assert required in text


def test_obsidian_has_seedance_prompt_optimizer_distillation_node():
    start = (ROOT / "00-start-here.md").read_text(encoding="utf-8")
    video_map = (MEMORY / "video-production-map.md").read_text(encoding="utf-8")
    index = (MEMORY / "index.md").read_text(encoding="utf-8")
    note = (MEMORY / "seedance-prompt-optimizer.md").read_text(encoding="utf-8")

    assert "[[docs/memory/viral-social-remix/seedance-prompt-optimizer]]" in start
    assert "[[seedance-prompt-optimizer]]" in video_map
    assert "[[seedance-prompt-optimizer]]" in index

    for required in [
        "source_material:",
        "new_base/general-sd2-skills (1).md",
        "not a production video workflow",
        "Classify intent before rewriting",
        "eight core elements",
        "Local Syntax Rule",
        "[Image 1] (product package)",
        "never leave raw `asset-xxx` IDs",
        "Do not silently modify user intent",
        "Editing And Stitching",
        "bad returned last frames need generated transition opening",
    ]:
        assert required in note


def test_obsidian_relationship_maps_connect_current_video_contract():
    start = (ROOT / "00-start-here.md").read_text(encoding="utf-8")
    video_map = (MEMORY / "video-production-map.md").read_text(encoding="utf-8")
    index = (MEMORY / "index.md").read_text(encoding="utf-8")
    original = (MEMORY / "original-cooking-video.md").read_text(encoding="utf-8")
    seedance = (MEMORY / "seedance-video-generation.md").read_text(encoding="utf-8")
    official = (MEMORY / "seedance-official-prompting.md").read_text(encoding="utf-8")
    chatcut = (MEMORY / "chatcut-handoff-workflow.md").read_text(encoding="utf-8")

    for required in [
        "[[docs/memory/viral-social-remix/video-production-map|Video Production Map]]",
        "[[viral-social-remix/references/cooking-video-workflow|Cooking Video Workflow]]",
        "Authority Ladder",
    ]:
        assert required in start

    for required in [
        "Decision Graph",
        "transition opening anchor",
        "Last frame and last motion strip clean?",
        "[[seedance-official-prompting]]",
        "[[chatcut-handoff-workflow]]",
    ]:
        assert required in video_map

    assert "[[video-production-map]]" in index
    assert "transition opening anchor" in original
    assert "transition opening anchor" in seedance
    assert "transition opening anchor" in official
    assert "transition opening anchors or returned last-frame references" in chatcut
    assert "three director-designed opening frames" not in original
    assert "designed into each opening frame" not in chatcut


def test_obsidian_ignores_generated_noise_and_obsolete_notes_are_removed():
    app = json.loads((ROOT / ".obsidian" / "app.json").read_text(encoding="utf-8"))
    graph = json.loads((ROOT / ".obsidian" / "graph.json").read_text(encoding="utf-8"))

    for ignored in [
        ".codex_tmp/",
        ".pytest_cache/",
        ".venv/",
        "new_base/",
        "output/",
        "samples/",
    ]:
        assert ignored in app["userIgnoreFilters"]
        assert ignored.rstrip("/") in graph["search"]

    assert graph["showOrphans"] is False

    for obsolete in [
        "docs/memory/viral-social-remix/distilled-lessons.md",
        "docs/superpowers/specs/2026-07-11-viral-social-content-pipeline-skill-design.md",
        "docs/superpowers/plans/2026-07-11-viral-social-remix-skill-implementation.md",
        "docs/workflows/rednote-subsidy-post-export.md",
        "docs/workflows/instagram-viral-post-export.md",
        "docs/workflows/cross-platform-social-media-export-principles.md",
    ]:
        assert not (ROOT / obsolete).exists()

    start = (ROOT / "00-start-here.md").read_text(encoding="utf-8")
    assert "`new_base/` is raw teaching/source material" in start
    assert "it is not trash" in start


def test_fixed_brand_scene_reference_points_to_readable_asset():
    text = (REF / "fixed-brand-scenes.md").read_text(encoding="utf-8")
    relative_asset = "../assets/umall/umall-warehouse-fixed-reference.png"
    assert relative_asset in text

    asset = (REF / relative_asset).resolve()
    assert asset.is_file()
    with Image.open(asset) as image:
        image.verify()
    with Image.open(asset) as image:
        assert image.format == "PNG"
        assert image.size[0] >= 1000
        assert image.size[1] >= 1000


def test_brand_region_assets_distinguish_english_and_chinese_logos():
    text = (REF / "brand-region-assets.md").read_text(encoding="utf-8")
    for required in [
        "ASIAN GROCER ONLINE",
        "powered by UMALL",
        "asian-grocer-online-powered-by-umall.png",
        "umall_logo.png",
        "Do not use the Chinese-region UMALL logo for English-region deliverables",
    ]:
        assert required in text
    assert (LOGO_DIR / "asian-grocer-online-powered-by-umall.png").is_file()
    assert (LOGO_DIR / "umall_logo.png").is_file()


def test_seedance_reference_documents_controlled_manifest_v2_workflow():
    text = (REF / "seedance-video.md").read_text(encoding="utf-8")
    for required in [
        "Manifest v2",
        "{{ref:hero-food}}",
        "[Image 1]",
        "Never use `@Image1`",
        "visual-preview",
        "--approve-final-spend",
        "request SHA-256",
        "--continue-from-last-frame",
        "visual_qa_passed",
        "prepare-export",
        "export_qa_passed",
    ]:
        assert required in text


def test_brand_rules_require_scene_anchored_exact_logo_compositing():
    cooking = (REF / "cooking-video-workflow.md").read_text(encoding="utf-8")
    brand = (REF / "brand-region-assets.md").read_text(encoding="utf-8")
    for text in [cooking, brand]:
        assert "perspective" in text
        assert "occlusion" in text
        assert "floating" in text


def test_xiaohongshu_real_talk_template_is_reusable_and_source_safe():
    text = (REF / "xiaohongshu-real-talk-template.md").read_text(encoding="utf-8")
    for required in [
        "刚从【对象】回来",
        "攻略没提的大实话",
        "路线或使用过程",
        "最大翻车",
        "费用或购买参考",
        "旅行",
        "探店",
        "产品体验",
        "不得复制原作者原句",
    ]:
        assert required in text
