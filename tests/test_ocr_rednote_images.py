import builtins

from viral_social_test_loader import load_script


ocr_rednote_images = load_script("ocr_rednote_images")


def test_ocr_script_imports_without_optional_dependency():
    assert ocr_rednote_images.DEFAULT_PATTERNS


def test_ocr_engine_reports_missing_optional_dependency(monkeypatch):
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "rapidocr_onnxruntime":
            raise ImportError(name)
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    try:
        ocr_rednote_images.load_ocr_engine()
    except SystemExit as exc:
        assert "pip install -e .[ocr]" in str(exc)
    else:
        raise AssertionError("Expected SystemExit")
