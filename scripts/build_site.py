#!/usr/bin/env python3
"""
Paper Radar - Static Site Builder
Reads data JSON files and builds the final index.html for GitHub Pages.
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
SITE_DIR = BASE_DIR / "site"
DIST_DIR = BASE_DIR / "dist"


def build():
    print("🔨 Building static site...")

    # Clean and create dist
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)

    # Copy data files to dist
    data_out = DIST_DIR / "data"
    data_out.mkdir()

    for f in DATA_DIR.glob("*.json"):
        shutil.copy2(f, data_out / f.name)

    # Copy the main HTML
    html_src = SITE_DIR / "index.html"
    if html_src.exists():
        shutil.copy2(html_src, DIST_DIR / "index.html")
    else:
        print("⚠️  site/index.html not found!")
        return

    # Create CNAME if needed
    cname = os.environ.get("CNAME", "")
    if cname:
        (DIST_DIR / "CNAME").write_text(cname)

    # Create .nojekyll for GitHub Pages
    (DIST_DIR / ".nojekyll").touch()

    print(f"✅ Site built → {DIST_DIR}/")
    print(f"   Files: {list(DIST_DIR.rglob('*'))}")


if __name__ == "__main__":
    build()
