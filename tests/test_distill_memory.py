import json

from viral_social_test_loader import load_script


distill_memory = load_script("distill_memory")


def test_distill_memory_summarizes_only_safe_run_notes(tmp_path):
    run_dir = tmp_path / "output" / "run-a"
    (run_dir / "analysis").mkdir(parents=True)
    (run_dir / "qa").mkdir()
    (run_dir / "analysis" / "manifest.json").write_text(
        json.dumps(
            {
                "platform": "xiaohongshu",
                "assets": {"01": {"status": "validated"}},
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "qa" / "validation.json").write_text(
        json.dumps({"valid": True}),
        encoding="utf-8",
    )
    (run_dir / "qa" / "openrouter-cost.json").write_text(
        json.dumps({"total_cost": 0.1234}),
        encoding="utf-8",
    )
    (run_dir / "qa" / "run-notes.md").write_text(
        """# Run Notes

## What Worked

- Captured open XHS tab first.
- OPENROUTER_API_KEY should not survive sanitizing.
- GROK_OPENROUTER_API_KEY should not survive sanitizing.

## Problems

- Phone screenshot drifted into cover prompt.
- data:image/png;base64,abc

## Memory Candidates

- Phone screenshot can be final CTA only when user says so.
""",
        encoding="utf-8",
    )

    summary = distill_memory.build_summary(tmp_path)

    assert "Captured open XHS tab first." in summary
    assert "Phone screenshot can be final CTA only" in summary
    assert "OPENROUTER_API_KEY" not in summary
    assert "GROK_OPENROUTER_API_KEY" not in summary
    assert "data:image" not in summary
    assert "Platform: xiaohongshu" in summary
    assert "Cost: $0.1234" in summary


def test_distill_memory_summarizes_retrospectives(tmp_path):
    retrospective = tmp_path / "docs" / "retrospectives" / "2026-07-23-example.md"
    retrospective.parent.mkdir(parents=True)
    retrospective.write_text(
        """# Example Retrospective

## Correct Behavior

- Use the original source page count.

## API Lesson

- Prefer the dedicated Images API.
""",
        encoding="utf-8",
    )

    summary = distill_memory.build_summary(tmp_path)

    assert "Example Retrospective" in summary
    assert "Use the original source page count." in summary
    assert "Prefer the dedicated Images API." in summary
