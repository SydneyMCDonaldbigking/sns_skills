from pathlib import Path


REF = Path(__file__).parents[1] / "viral-social-remix" / "references"


def test_platform_profiles_contain_exact_output_contracts():
    text = (REF / "platform-profiles.md").read_text(encoding="utf-8")
    for required in ["2048×1152", "1152×1152", "1920×1080", "exactly 9"]:
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
