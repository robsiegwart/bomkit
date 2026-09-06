import os
import subprocess
import sys

# Force UTF-8 stdout in subprocesses (needed on Windows with non-UTF-8 code pages)
_UTF8_ENV = {**os.environ, "PYTHONUTF8": "1"}


def test_cli_summary_action(simple_xlsx):
    proc = subprocess.run(
        [sys.executable, "-m", "bomkit", str(simple_xlsx), "summary"],
        capture_output=True, text=True, env=_UTF8_ENV,
    )
    assert proc.returncode == 0
    assert "P1" in proc.stdout


def test_cli_tree_action(simple_xlsx):
    proc = subprocess.run(
        [sys.executable, "-m", "bomkit", str(simple_xlsx), "tree"],
        capture_output=True, text=True, env=_UTF8_ENV,
    )
    assert proc.returncode == 0
    assert "P1" in proc.stdout


def test_cli_dir_path(bom_folder):
    proc = subprocess.run(
        [sys.executable, "-m", "bomkit", str(bom_folder), "tree"],
        capture_output=True, text=True, env=_UTF8_ENV,
    )
    assert proc.returncode == 0


def test_cli_dir_with_lone_single_file_xlsx(simple_xlsx):
    # A directory with no 'Parts list.xlsx' but exactly one .xlsx should be
    # treated as a single-file BOM, not a broken multi-file layout.
    proc = subprocess.run(
        [sys.executable, "-m", "bomkit", str(simple_xlsx.parent), "tree"],
        capture_output=True, text=True, env=_UTF8_ENV,
    )
    assert proc.returncode == 0
    assert "P1" in proc.stdout
