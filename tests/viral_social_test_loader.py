from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def load_script(name: str):
    path = Path(__file__).parents[1] / "viral-social-remix" / "scripts" / f"{name}.py"
    spec = spec_from_file_location(name, path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
