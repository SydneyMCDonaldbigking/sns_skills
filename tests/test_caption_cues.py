import argparse

import pytest

from viral_social_test_loader import load_script


caption_cues = load_script("caption_cues")


@pytest.mark.parametrize(
    "value, expected",
    [
        (5, 5.0),
        (2.5, 2.5),
        ("5", 5.0),
        ("1:30", 90.0),
        ("1:00:30", 3630.0),
        ("00:01:02,500", 62.5),
    ],
)
def test_parse_time_accepts_numbers_and_timecodes(value, expected):
    assert caption_cues.parse_time(value) == expected


def test_parse_time_rejects_negative_values():
    with pytest.raises(ValueError):
        caption_cues.parse_time(-1)


def test_parse_time_rejects_empty_string():
    with pytest.raises(ValueError):
        caption_cues.parse_time("")


def test_format_srt_time_renders_hours_minutes_seconds_millis():
    assert caption_cues.format_srt_time(3722.5) == "01:02:02,500"
    assert caption_cues.format_srt_time(62.5) == "00:01:02,500"


def test_parse_trim_accepts_colon_dot_dot_and_comma_forms():
    assert caption_cues.parse_trim("clip-01=0.25:5.70") == ("clip-01", (0.25, 5.7))
    assert caption_cues.parse_trim("clip-01=0.25..5.70") == ("clip-01", (0.25, 5.7))
    assert caption_cues.parse_trim("clip-01=0.25,5.70") == ("clip-01", (0.25, 5.7))


def test_parse_trim_rejects_end_before_start():
    with pytest.raises(argparse.ArgumentTypeError):
        caption_cues.parse_trim("clip-01=5.0:1.0")


def test_parse_duration_rejects_zero_or_negative():
    with pytest.raises(argparse.ArgumentTypeError):
        caption_cues.parse_duration("clip-01=0")


def test_sorted_clip_names_orders_single_clip_before_numbered_clips():
    names = ["clip-02", "single-10s", "clip-01", "outro"]
    assert caption_cues.sorted_clip_names(names) == [
        "single-10s",
        "clip-01",
        "clip-02",
        "outro",
    ]
