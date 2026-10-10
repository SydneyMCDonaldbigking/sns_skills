from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_local_only_directories_are_ignored():
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    required = {
        "output/",
        "samples/",
        "new_base/",
        "claude_only/",
        ".codex_tmp/",
        ".tmp/",
        ".cleanup-archive/",
        ".venv/",
        "__pycache__/",
    }
    assert required.issubset(set(gitignore))


def test_repository_hygiene_doc_names_boundaries():
    text = (ROOT / "docs" / "workflows" / "repository-hygiene.md").read_text(
        encoding="utf-8"
    )
    assert "Tracked Structure" in text
    assert "Local-Only Structure" in text
    assert "viral-social-remix/" in text
    assert "claude_only/" in text
