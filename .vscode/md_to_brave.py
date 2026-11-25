#!/usr/bin/env python3
"""Render a Markdown file to print-ready HTML and open it in Brave."""

from __future__ import annotations

import html
import subprocess
import sys
from pathlib import Path

import markdown

CSS = """
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  max-width: 900px;
  margin: 28px auto;
  padding: 0 20px 48px;
  color: #0f172a;
  line-height: 1.55;
  font-size: 14px;
}
h1, h2, h3 { color: #0f172a; margin-top: 1.4em; break-after: avoid; }
h1 { border-bottom: 2px solid #cbd5e1; padding-bottom: 6px; }
h2 { border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; }
table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 13px; }
th, td { border: 1px solid #cbd5e1; padding: 6px 9px; text-align: left; vertical-align: top; }
th { background: #f1f5f9; font-weight: 700; }
code { background: #f1f5f9; padding: 1px 5px; border-radius: 4px; font-size: 0.9em; }
pre { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px 12px; overflow-x: auto; }
pre code { background: transparent; padding: 0; }
blockquote { border-left: 4px solid #3b82f6; background: #eff6ff; margin: 12px 0; padding: 8px 14px; border-radius: 0 6px 6px 0; }
img { max-width: 100%; height: auto; border-radius: 6px; margin: 8px 0; }
a { color: #2563eb; }
.print-bar {
  position: sticky; top: 10px; display: flex; justify-content: flex-end; gap: 8px;
  margin-bottom: 8px; z-index: 10;
}
.print-btn {
  cursor: pointer; background: #2563eb; color: #fff; border: none;
  padding: 7px 14px; border-radius: 6px; font-size: 13px; font-weight: 600;
  box-shadow: 0 2px 6px rgba(0,0,0,0.15);
}
.print-btn:hover { background: #1d4ed8; }
@media print {
  .print-bar { display: none !important; }
  body { margin: 0; padding: 0; max-width: none; font-size: 11pt; }
  tr, img, blockquote, pre { break-inside: avoid; }
}
"""


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--no-open"]
    no_open = "--no-open" in sys.argv[1:]
    if not args:
        print("Usage: md_to_brave.py <file.md> [--no-open]", file=sys.stderr)
        return 1

    md_path = Path(args[0]).resolve()
    body_html = markdown.markdown(
        md_path.read_text(encoding="utf-8"),
        extensions=["tables", "fenced_code", "sane_lists"],
    )
    base_href = md_path.parent.as_uri().rstrip("/") + "/"
    title = html.escape(md_path.name)

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <base href="{base_href}" />
  <title>{title}</title>
  <style>{CSS}</style>
</head>
<body>
  <div class="print-bar">
    <button class="print-btn" onclick="window.print()">Print / Save PDF</button>
  </div>
  {body_html}
</body>
</html>
"""
    out_path = Path(f"/tmp/telecine_print_{md_path.stem}.html")
    out_path.write_text(full_html, encoding="utf-8")

    if not no_open:
        subprocess.Popen(
            ["setsid", "-f", "/usr/bin/brave-browser", str(out_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        print(f"Rendered -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
