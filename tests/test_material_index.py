import json

from viral_social_test_loader import load_script


material_index = load_script("material_index")


def test_material_index_appends_utf8_jsonl_and_summarizes(tmp_path):
    path = tmp_path / "material-index.jsonl"

    first = material_index.append(
        path,
        {
            "record_type": "post",
            "platform": "rednote",
            "title": "百万补贴",
        },
    )
    second = material_index.append(
        path,
        {
            "record_type": "asset",
            "platform": "brand_site",
            "title": "Umall 官网商品图",
        },
    )

    assert first["indexed_at"]
    assert second["indexed_at"]
    rows = material_index.load(path)
    assert [row["title"] for row in rows] == ["百万补贴", "Umall 官网商品图"]
    assert material_index.summarize(path) == {
        "index": str(path),
        "total": 2,
        "by_platform": {"rednote": 1, "brand_site": 1},
        "by_type": {"post": 1, "asset": 1},
    }

    raw_lines = path.read_text(encoding="utf-8").splitlines()
    assert json.loads(raw_lines[0])["title"] == "百万补贴"


def test_material_index_append_many_skips_existing_record_ids(tmp_path):
    path = tmp_path / "material-index.jsonl"
    records = [
        {"record_id": "same", "record_type": "asset", "platform": "brand_site"},
        {"record_id": "same", "record_type": "asset", "platform": "brand_site"},
    ]

    first_write = material_index.append_many(path, records)
    second_write = material_index.append_many(path, records)

    assert len(first_write) == 1
    assert second_write == []
    assert material_index.summarize(path)["total"] == 1
