from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_env_files_are_not_unignored():
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".env" in gitignore
    assert ".env.*" in gitignore
    assert "!.env.example" not in gitignore
