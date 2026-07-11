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
