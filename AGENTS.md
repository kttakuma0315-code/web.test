# Verification requirements

The user explicitly requires real interaction testing before reporting completion. Do not substitute a build or syntax check for browser behavior.

- For UI or navigation changes, use a real browser and exercise actual links in both the regular HTML site and generated preview.html.
- Regenerate preview.html with `python3 scripts/build_preview.py` whenever source HTML, CSS or JavaScript changes.
- For transition changes, inspect intermediate frames and assert visibility during navigation, not only the final destination.
- Check desktop and mobile layouts, rapid repeated navigation, back/forward history, page anchors, reduced-motion settings and unsupported-feature fallback when relevant.
- Run `tests/motion_regression.py` with the local HTTP server running. Reproduce and fix relevant failures before publishing.
- Verify the intended commit reached GitHub after pushing. State testing limits accurately; do not claim Safari or iPhone hardware testing unless it occurred.
- Preserve native scrolling, external links, telephone links, modified clicks and browser history.
