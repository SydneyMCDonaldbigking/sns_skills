from pathlib import Path

import pytest

from viral_social_test_loader import load_script


video_job = load_script("video_job")


def _structured_manifest() -> dict:
    return {
        "schema_version": 2,
        "platform": "vertical-video",
        "video": {
            "mode": "compact-reference",
            "profile": "visual-preview",
            "references": [
                {
                    "id": "motion",
                    "type": "video",
                    "order": 1,
                    "url": "https://cdn.example/motion.mp4",
                },
                {
                    "id": "product",
                    "type": "image",
                    "order": 2,
                    "url": "https://cdn.example/product.png",
                },
                {
                    "id": "food",
                    "type": "image",
                    "order": 1,
                    "url": "https://cdn.example/food.png",
                },
                {
                    "id": "ambience",
                    "type": "audio",
                    "order": 1,
                    "url": "https://cdn.example/ambience.mp3",
                },
            ],
        },
        "assets": {},
    }


def test_collect_and_compile_structured_references_by_media_order():
    references = video_job.collect_manifest_references(_structured_manifest())

    assert [(item["id"], item["prompt_label"]) for item in references] == [
        ("food", "[Image 1]"),
        ("product", "[Image 2]"),
        ("motion", "[Video 1]"),
        ("ambience", "[Audio 1]"),
    ]

    compiled, warnings = video_job.compile_prompt(
        "Use {{ref:food}} for the opening, {{ref:product}} for the package, "
        "{{ref:motion}} for camera rhythm, and {{ref:ambience}} for sound.",
        references,
    )

    assert "[Image 1]" in compiled
    assert "[Image 2]" in compiled
    assert "[Video 1]" in compiled
    assert "[Audio 1]" in compiled
    assert warnings == []


def test_compile_prompt_rejects_editor_style_at_reference():
    references = video_job.collect_manifest_references(_structured_manifest())

    with pytest.raises(video_job.VideoJobError, match=r"\[Image 1\]"):
        video_job.compile_prompt("Use @Image1 as the product.", references)


def test_compile_prompt_rejects_unknown_or_out_of_range_reference():
    references = video_job.collect_manifest_references(_structured_manifest())

    with pytest.raises(video_job.VideoJobError, match="unknown semantic asset"):
        video_job.compile_prompt("Use {{ref:missing}}.", references)

    with pytest.raises(video_job.VideoJobError, match="contains 2 image"):
        video_job.compile_prompt("Use [Image 3].", references)


def test_visual_preview_profile_is_silent_and_returns_last_frame():
    defaults = video_job.generation_defaults(
        _structured_manifest(),
        "vertical-video",
    )

    assert defaults == {
        "duration": 5,
        "resolution": "1080p",
        "generate_audio": False,
        "watermark": False,
        "return_last_frame": True,
        "ratio": "9:16",
        "profile": "visual-preview",
    }


def test_submission_budget_requires_final_approval_and_limits_retries():
    data = _structured_manifest()
    data["video"]["budget"] = {
        "retry_limit": 1,
        "stop_before_final": True,
    }

    with pytest.raises(video_job.VideoJobError, match="approve-final-spend"):
        video_job.authorize_submission(
            data,
            profile="final-clip",
            approve_final_spend=False,
        )

    approved = video_job.authorize_submission(
        data,
        profile="final-clip",
        approve_final_spend=True,
    )
    assert approved["attempt"] == 1
    assert approved["max_attempts"] == 2

    data["video_generation"] = {"attempts": 2}
    with pytest.raises(video_job.VideoJobError, match="budget is exhausted"):
        video_job.authorize_submission(
            data,
            profile="visual-preview",
            approve_final_spend=False,
        )


def test_submission_budget_blocks_accidental_duplicate_paid_attempt():
    data = _structured_manifest()
    data["video_generation"] = {
        "status": "submitted",
        "attempts": 1,
    }

    with pytest.raises(video_job.VideoJobError, match="duplicate paid"):
        video_job.authorize_submission(
            data,
            profile="visual-preview",
            approve_final_spend=False,
        )

    forced = video_job.authorize_submission(
        data,
        profile="visual-preview",
        approve_final_spend=False,
        force=True,
    )
    assert forced["attempt"] == 2
    assert forced["forced"] is True


def test_validate_generation_enforces_official_seedance_bounds():
    references = video_job.collect_manifest_references(_structured_manifest())
    valid = {
        "ratio": "9:16",
        "duration": 5,
        "resolution": "1080p",
        "generate_audio": False,
        "watermark": False,
    }

    video_job.validate_generation(
        model="dreamina-seedance-2-0-260128",
        options=valid,
        references=references,
    )

    with pytest.raises(video_job.VideoJobError, match="between 4 and 15"):
        video_job.validate_generation(
            model="dreamina-seedance-2-0-260128",
            options={**valid, "duration": 3},
            references=references,
        )

    with pytest.raises(video_job.VideoJobError, match="at most 720p"):
        video_job.validate_generation(
            model="dreamina-seedance-2-0-fast-260128",
            options=valid,
            references=references,
        )


def test_validate_generation_rejects_audio_only_or_too_many_images():
    audio_only = video_job.merge_reference_overrides(
        [],
        video_job.cli_references(
            audio_refs=["https://cdn.example/ambience.mp3"]
        ),
    )
    options = {
        "ratio": "9:16",
        "duration": 5,
        "resolution": "720p",
        "generate_audio": False,
        "watermark": False,
    }

    with pytest.raises(video_job.VideoJobError, match="audio-only"):
        video_job.validate_generation(
            model="dreamina-seedance-2-0-260128",
            options=options,
            references=audio_only,
        )

    too_many = video_job.merge_reference_overrides(
        [],
        video_job.cli_references(
            image_refs=[
                f"https://cdn.example/{index}.png"
                for index in range(10)
            ]
        ),
    )
    with pytest.raises(video_job.VideoJobError, match="at most 9 image"):
        video_job.validate_generation(
            model="dreamina-seedance-2-0-260128",
            options=options,
            references=too_many,
        )


def test_materialize_local_image_requires_explicit_data_url_permission(tmp_path: Path):
    image = tmp_path / "reference.png"
    image.write_bytes(b"fake image")
    references = video_job.merge_reference_overrides(
        [],
        video_job.cli_references(image_refs=[str(image)]),
    )

    with pytest.raises(video_job.VideoJobError, match="reference image URL"):
        video_job.materialize_references(
            tmp_path,
            references,
            allow_data_url=False,
        )

    materialized = video_job.materialize_references(
        tmp_path,
        references,
        allow_data_url=True,
    )
    assert materialized[0]["url"].startswith("data:image/png;base64,")


def test_materialize_local_video_requires_public_url(tmp_path: Path):
    video = tmp_path / "motion.mp4"
    video.write_bytes(b"fake video")
    references = video_job.merge_reference_overrides(
        [],
        video_job.cli_references(video_refs=[str(video)]),
    )

    with pytest.raises(video_job.VideoJobError, match="needs a public URL"):
        video_job.materialize_references(
            tmp_path,
            references,
            allow_data_url=True,
        )
