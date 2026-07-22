from pathlib import Path

from PIL import Image


REF = Path(__file__).parents[1] / "viral-social-remix" / "references"


def test_platform_profiles_contain_exact_output_contracts():
    text = (REF / "platform-profiles.md").read_text(encoding="utf-8")
    for required in ["1152×1536", "1152×1152", "1920×1080", "exactly 9"]:
        assert required in text


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
