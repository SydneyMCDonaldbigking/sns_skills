import importlib.util
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "viral-social-remix" / "scripts" / "image_provider.py"


def load_module():
    spec = importlib.util.spec_from_file_location("image_provider", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_image_provider_defaults_are_redacted(monkeypatch):
    for key in [
        "OPENROUTER_API_KEY",
        "VSR_IMAGE_PROVIDER",
        "VSR_IMAGE_MODEL",
        "VSR_IMAGE_QUALITY",
        "VSR_IMAGE_ENDPOINT",
    ]:
        monkeypatch.delenv(key, raising=False)
    module = load_module()
    monkeypatch.setattr(module, "LOCAL_ENV", ROOT / "missing.env.local")
    config = module.resolve()
    assert config == {
        "provider": "openrouter",
        "model": "openai/gpt-image-2",
        "quality": "medium",
        "endpoint": "",
        "api_key_set": False,
    }


def test_image_provider_detects_key_without_returning_it(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "secret-value")
    module = load_module()
    config = module.resolve()
    assert config["api_key_set"] is True
    assert "secret-value" not in str(config)
