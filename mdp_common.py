"""Shared rendering helpers for MarkdownSplitPreview.

Converts Markdown to HTML using pandoc, then adapts the result to the
subset of HTML/CSS that Sublime Text's minihtml engine understands.
"""

import os
import re
import shutil
import subprocess

import sublime

PACKAGE = "MarkdownSplitPreview"


def _log_path():
    return os.path.join(sublime.cache_path(), PACKAGE + ".log")


def log(msg):
    try:
        path = _log_path()
        if os.path.exists(path) and os.path.getsize(path) > 256 * 1024:
            os.remove(path)
        with open(path, "a", encoding="utf-8") as f:
            f.write(str(msg) + "\n")
    except Exception:
        pass


def setting(key, default=None):
    return sublime.load_settings(PACKAGE + ".sublime-settings").get(key, default)


def pandoc_path():
    """Locate pandoc: explicit setting first, then PATH, then common installs."""
    configured = setting("pandoc_path", "") or ""
    if configured and os.path.isfile(configured) and os.access(configured, os.X_OK):
        return configured

    found = shutil.which("pandoc")
    if found:
        return found

    candidates = [
        "/opt/homebrew/bin/pandoc",
        "/usr/local/bin/pandoc",
        "C:\\Program Files\\Pandoc\\pandoc.exe",
    ]
    for path in candidates:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


def cache_dir():
    d = os.path.join(sublime.cache_path(), PACKAGE)
    os.makedirs(d, exist_ok=True)
    return d


def _source_file(view):
    """Return (path_to_render, base_dir) for the given view."""
    path = view.file_name()
    if path:
        return path, os.path.dirname(path)

    tmp = os.path.join(cache_dir(), "untitled.md")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(view.substr(sublime.Region(0, view.size())))
    return tmp, cache_dir()


def run_pandoc(view, to="html"):
    pandoc = pandoc_path()
    if not pandoc:
        raise RuntimeError(
            "pandoc not found. Install it (brew install pandoc) or set "
            "\"pandoc_path\" in MarkdownSplitPreview settings."
        )

    src, base_dir = _source_file(view)
    proc = subprocess.run(
        [
            pandoc, src,
            "--from=gfm+hard_line_breaks+task_lists+pipe_tables",
            "--to=" + to,
            "--no-highlight",
            "--quiet",
        ],
        cwd=base_dir,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or "pandoc failed").strip()[:400])
    return proc.stdout, base_dir


def fix_images(html, base_dir):
    """Rewrite relative image paths so minihtml can load them."""

    def repl(m):
        src = m.group(1)
        if src.startswith(("http://", "https://", "data:", "file://", "/")):
            return m.group(0)
        path = os.path.normpath(os.path.join(base_dir, src))
        return 'src="file://%s"' % path.replace(" ", "%20")

    return re.sub(r'src="([^"]+)"', repl, html)


def table_to_rows(m):
    """minihtml does not lay out tables; render each row as a text line."""
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", m.group(0), flags=re.S)
    out = []
    for index, row in enumerate(rows):
        cells = re.findall(r"<t([hd])[^>]*>(.*?)</t[hd]>", row, flags=re.S)
        parts = []
        for tag, content in cells:
            content = content.strip()
            parts.append("<b>%s</b>" % content if tag == "h" else content)
        if not parts:
            continue
        style = "padding: 3px 0; border-bottom: 1px solid #eaeef2;"
        if index == 0:
            style += " background-color: #f6f8fa;"
        out.append('<div style="%s">%s</div>' % (style, "  |  ".join(parts)))
    return '<div style="margin: 8px 0;">%s</div>' % "".join(out)


def minihtml_fix(html):
    html = re.sub(r"<table[^>]*>.*?</table>", table_to_rows, html, flags=re.S)
    html = re.sub(
        r"<pre[^>]*>\s*<code[^>]*>(.*?)</code>\s*</pre>",
        lambda m: (
            '<div style="font-family: Menlo, Consolas, monospace; font-size: 12px;'
            ' background-color: #f6f8fa; padding: 8px; margin: 8px 0;">%s</div>'
            % m.group(1).replace("\n", "<br>")
        ),
        html,
        flags=re.S,
    )
    html = re.sub(r"<input[^>]*checked[^>]*>", "[x] ", html)
    html = re.sub(r"<input[^>]*>", "[ ] ", html)
    html = re.sub(r'\s+id="[^"]*"', "", html)
    return html


STYLE = """
body { font-family: -apple-system, "PingFang SC", "Segoe UI", "Helvetica Neue", sans-serif;
       font-size: 13px; color: #24292f; background-color: #ffffff; }
h1 { font-size: 21px; font-weight: bold; color: #1f2328; margin: 16px 0 10px 0; }
h2 { font-size: 17px; font-weight: bold; color: #1f2328; margin: 14px 0 8px 0; }
h3 { font-size: 15px; font-weight: bold; margin: 12px 0 6px 0; }
h4 { font-size: 13px; font-weight: bold; margin: 10px 0 5px 0; }
p { margin: 6px 0; }
ul, ol { margin: 6px 0; padding-left: 20px; }
li { margin: 2px 0; }
code { font-family: Menlo, Consolas, monospace; font-size: 12px;
       color: #b31d28; background-color: #f3f5f8; }
blockquote { margin: 8px 0; padding: 2px 10px; color: #57606a;
             border-left: 3px solid #d0d7de; }
a { color: #0969da; }
hr { color: #e5e9ef; }
"""


def render_for_minihtml(view):
    """Markdown -> HTML tailored for minihtml (in-editor preview)."""
    fragment, base_dir = run_pandoc(view, to="html")
    body = fix_images(fragment, base_dir)
    return "<style>%s</style>%s" % (STYLE, minihtml_fix(body))


def render_standalone(view, out_dir=None):
    """Markdown -> self-contained HTML file (browser preview)."""
    pandoc = pandoc_path()
    if not pandoc:
        raise RuntimeError(
            "pandoc not found. Install it (brew install pandoc) or set "
            "\"pandoc_path\" in MarkdownSplitPreview settings."
        )

    src, base_dir = _source_file(view)
    out_dir = out_dir or cache_dir()
    name = os.path.splitext(os.path.basename(src))[0] or "preview"
    out = os.path.join(out_dir, name + ".html")

    proc = subprocess.run(
        [
            pandoc, src,
            "--from=gfm+hard_line_breaks+task_lists+pipe_tables",
            "--to=html5",
            "--standalone",
            "--embed-resources",
            "--highlight-style=tango",
            "--metadata", "title=" + name,
            "--output", out,
        ],
        cwd=base_dir,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    if proc.returncode != 0 or not os.path.exists(out):
        raise RuntimeError((proc.stderr or "pandoc failed").strip()[:400])
    return out
