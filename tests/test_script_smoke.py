import subprocess
import sys
from pathlib import Path


SCRIPTS = Path(__file__).parents[1] / "viral-social-remix" / "scripts"


def test_rednote_ocr_scripts_show_help_without_optional_ocr_dependencies():
    for script_name in [
        "ocr_rednote_images.py",
        "map_rednote_profile_ocr.py",
        "export_rednote_subsidy_posts.py",
    ]:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / script_name), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "usage:" in result.stdout


def test_core_workflow_scripts_expose_command_line_help():
    for script_name in [
        "scan_media.py",
        "extract_keyframes.py",
        "make_contact_sheet.py",
        "validate_output.py",
    ]:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / script_name), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "usage:" in result.stdout
