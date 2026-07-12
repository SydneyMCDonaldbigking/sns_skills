from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]
SKILL = ROOT / "viral-social-remix"


def test_skill_has_valid_minimal_structure():
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---\n")
    frontmatter = yaml.safe_load(text.split("---", 2)[1])
    assert frontmatter["name"] == "viral-social-remix"
    assert "Use when" in frontmatter["description"]
    metadata = yaml.safe_load(
        (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
    )
    assert metadata["interface"]["display_name"] == "Viral Social Remix"


def test_skill_routes_every_input_and_platform():
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    required = [
        "post URL",
        "local file",
        "local folder",
        "scan_media.py",
        "Xiaohongshu",
        "Instagram/Facebook",
        "exactly nine",
        "GPT Image 2",
        "manifest.py",
        "validate_output.py",
        "create_run_dir.py",
        "caption-zh.txt",
        "caption-en.txt",
    ]
    for phrase in required:
        assert phrase in text


def test_skill_requires_product_and_brand_only():
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert "Product and brand are mandatory" in text
    assert "Ask only for missing mandatory fields or low-confidence platform" in text


def test_skill_routes_xiaohongshu_real_talk_posts_to_template():
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert "xiaohongshu-real-talk-template.md" in text
    assert "real-talk" in text


def test_skill_uses_editable_brand_profile_before_asking_questions():
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    profile = (SKILL / "brand-profile.md").read_text(encoding="utf-8")
    assert "brand-profile.md" in text
    assert "未填写" in text
    assert "品牌名称：未填写" in profile
    assert "产品名称：未填写" in profile
    assert "不要重复询问" in profile
