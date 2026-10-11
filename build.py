"""Build dist/roguelike.pyz: the whole game plus its libraries in one file.

    python build.py

The result runs on any computer with Python 3.11+, no pip install needed:

    python roguelike.pyz

blessed and its dependencies are pure Python, so one file works on Windows,
macOS and Linux alike.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import zipapp
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "app"
DIST = ROOT / "dist"
GAME_FILES = ["main.py", "game.py", "commands.py", "map_gen.py", "combat.py", "entities.py", "ui.py"]
# blessed needs jinxed on Windows only, but bundling it everywhere keeps one file for every OS.
LIBRARIES = ["blessed", "jinxed", "wcwidth"]

LAUNCHER = r"""@echo off
rem Double-click to play. Needs Python 3.11+ installed (python.org).
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (py roguelike.pyz %*) else (python roguelike.pyz %*)
if errorlevel 1 pause
"""


def main() -> None:
    shutil.rmtree(BUILD, ignore_errors=True)
    BUILD.mkdir(parents=True)

    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--quiet", "--no-compile",
         "--target", str(BUILD), *LIBRARIES],
        check=True,
    )
    # Installer metadata and caches aren't needed at runtime.
    for path in BUILD.glob("*.dist-info"):
        shutil.rmtree(path)
    for path in BUILD.rglob("__pycache__"):
        shutil.rmtree(path)
    # Compiled speedups only fit the OS that built them; the libraries fall back to pure Python.
    for pattern in ("*.so", "*.pyd"):
        for path in BUILD.rglob(pattern):
            path.unlink()

    for name in GAME_FILES:
        shutil.copy2(ROOT / name, BUILD / name)
    shutil.copytree(ROOT / "data", BUILD / "data", ignore=shutil.ignore_patterns("__pycache__"))
    # zipapp runs __main__.py; main.py only starts the game under `if __name__ == "__main__"`.
    (BUILD / "__main__.py").write_text(
        "import runpy\nrunpy.run_module('main', run_name='__main__')\n", encoding="utf-8"
    )

    DIST.mkdir(exist_ok=True)
    target = DIST / "roguelike.pyz"
    zipapp.create_archive(BUILD, target, interpreter="/usr/bin/env python3", compressed=True)
    (DIST / "Play Roguelike.bat").write_text(LAUNCHER.replace("\n", "\r\n"), encoding="ascii", newline="")
    print(f"Built {target.relative_to(ROOT)} ({target.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
