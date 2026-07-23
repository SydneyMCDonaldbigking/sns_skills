from pathlib import Path


REF = Path(__file__).parents[1] / "viral-social-remix" / "references"


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


def test_cooking_workflow_uses_fixed_no_text_brand_prop_storyboard():
    text = (REF / "cooking-video-workflow.md").read_text(encoding="utf-8")
    for required in [
        "ingredients/product close-ups -> cooking process -> plated finished dish",
        "01 Ingredient, seasoning, and product close-up",
        "09 Finished dish hero shot with company table sign",
        "real physical prop",
        "no subtitles, captions, title cards, lower-thirds, labels",
    ]:
        assert required in text
    assert "natural platform text only if needed" not in text


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
