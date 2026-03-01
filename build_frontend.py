#!/usr/bin/env python3
"""Simple build script to export static frontend for GitHub Pages.

Usage:
    python build_frontend.py

This copies the Jinja template `templates/index.html` and the `static/`
folder into a `docs/` directory which GitHub Pages can serve. The template
is already purely static (no server-side variables), so we just copy it.

After running, commit the `docs/` directory and push to GitHub. In the
repository settings, set GitHub Pages source to "main branch /docs folder".

The API endpoint used by the frontend is configured via `static/js/config.js`.
Uncomment and set `API_BASE_URL` to the Render URL (e.g. https://your-app.onrender.com).
"""

import os
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(ROOT, "docs")

# Ensure docs/ directory exists and is empty
if os.path.exists(DOCS):
    shutil.rmtree(DOCS)
os.makedirs(DOCS)

# Copy index.html from templates
shutil.copyfile(os.path.join(ROOT, "templates", "index.html"),
                os.path.join(DOCS, "index.html"))

# Copy static assets
shutil.copytree(os.path.join(ROOT, "static"), os.path.join(DOCS, "static"))

print("Built static frontend into docs/ folder.")
print("Commit and push docs/ to GitHub. Set Pages source to main/docs.")
