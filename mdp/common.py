"""Shared rendering helpers for MarkdownSplitPreview.

Two rendering engines are supported:

* **pandoc** (preferred) -- fast, full-featured, but an external binary.
* **python-markdown** (fallback) -- pure Python, installed automatically as a
  Package Control dependency, so the package works with zero setup.

The engine is chosen with the ``engine`` setting: ``auto`` (default) uses
pandoc when available and falls back to python-markdown, ``pandoc`` forces
pandoc, ``python`` forces the pure Python engine.
"""

import os
import re
import shutil
import subprocess

import sublime

PACKAGE = "MarkdownSplitPreview"
SETTINGS_FILE = PACKAGE + ".sublime-settings"


def _log_path():
    return os.path.join(sublime.cache_path(), PACKAGE + ".log")


def hidden_kwargs():
    """Keep console windows hidden when spawning processes on Windows."""
    if sublime.platform() == "windows":
        info = subprocess.STARTUPINFO()
        info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return {"startupinfo": info, "creationflags": 0x08000000}
    return {}


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
    return sublime.load_settings(SETTINGS_FILE).get(key, default)


def pandoc_path():
    """Locate pandoc: explicit setting first, then PATH, then common installs."""
    configured = setting("pandoc_path", "") or ""
    if configured and os.path.isfile(configured) and os.access(configured, os.X_OK):
        return configured

    found = shutil.which("pandoc")
    if found:
        return found

    for path in (
        "/opt/homebrew/bin/pandoc",
        "/usr/local/bin/pandoc",
        "C:\\Program Files\\Pandoc\\pandoc.exe",
    ):
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


def engine():
    """Resolve which engine to use: 'pandoc' or 'python'."""
    choice = (setting("engine", "auto") or "auto").lower()
    if choice == "pandoc":
        return "pandoc"
    if choice == "python":
        return "python"
    return "pandoc" if pandoc_path() else "python"


def cache_dir():
    d = os.path.join(sublime.cache_path(), PACKAGE)
    os.makedirs(d, exist_ok=True)
    return d


def source_dir(view):
    path = view.file_name()
    if path:
        return os.path.dirname(path)
    return cache_dir()


def _source_file(view):
    """Return (path_to_render, base_dir) for the given view."""
    path = view.file_name()
    if path:
        return path, os.path.dirname(path)

    tmp = os.path.join(cache_dir(), "untitled.md")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(view.substr(sublime.Region(0, view.size())))
    return tmp, cache_dir()


def _run_pandoc(view, to):
    src, base_dir = _source_file(view)
    proc = subprocess.run(
        [
            pandoc_path(), src,
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
        **hidden_kwargs(),
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or "pandoc failed").strip()[:400])
    return proc.stdout, base_dir


MARKDOWN_EXTENSIONS = ["extra", "sane_lists", "nl2br", "toc"]


def _run_python_markdown(view):
    try:
        import markdown
    except ImportError:
        raise RuntimeError(
            "No Markdown engine available.\n\n"
            "Install pandoc (brew install pandoc) or run "
            "\"Package Control: Satisfy Dependencies\" for python-markdown."
        )

    text = view.substr(sublime.Region(0, view.size()))
    try:
        md = markdown.Markdown(extensions=MARKDOWN_EXTENSIONS)
        return md.convert(text)
    except Exception as e:
        raise RuntimeError("python-markdown failed: %s" % e)


def render_fragment(view):
    """Return (html_fragment, base_dir, engine_name)."""
    if engine() == "pandoc":
        html, base_dir = _run_pandoc(view, "html")
        return html, base_dir, "pandoc"
    return _run_python_markdown(view), source_dir(view), "python-markdown"


def fix_images(html, base_dir):
    """Rewrite relative image paths so the output can load them."""

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
    # fenced_code with pandoc may leave bare <pre> blocks
    html = re.sub(
        r"<pre>(.*?)</pre>",
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

WEB_STYLE = """
body { max-width: 860px; margin: 0 auto; padding: 40px 24px 80px;
       font: 16px/1.85 -apple-system, "PingFang SC", "Helvetica Neue", Arial, sans-serif;
       color: #24292f; background: #fff; }
h1, h2, h3, h4 { line-height: 1.4; margin: 1.6em 0 .6em; font-weight: 600; }
h1 { font-size: 2em; border-bottom: 1px solid #e5e9ef; padding-bottom: .3em; }
h2 { font-size: 1.5em; border-bottom: 1px solid #eef1f5; padding-bottom: .25em; }
h3 { font-size: 1.2em; }
a { color: #0969da; text-decoration: none; }
a:hover { text-decoration: underline; }
code { background: #f3f5f8; padding: .15em .4em; border-radius: 4px;
       font-size: .9em; font-family: "SF Mono", Menlo, Consolas, monospace; }
pre { background: #f6f8fa; padding: 14px 16px; border-radius: 8px;
      overflow: auto; border: 1px solid #eaeef2; }
pre code { background: none; padding: 0; font-size: .88em; }
blockquote { margin: 0; padding: .2em 1em; color: #57606a;
             border-left: 4px solid #d0d7de; }
table { border-collapse: collapse; margin: 1em 0; width: 100%; font-size: .95em; }
th, td { border: 1px solid #d0d7de; padding: 8px 12px; }
th { background: #f6f8fa; font-weight: 600; }
tr:nth-child(even) td { background: #fbfcfd; }
img { max-width: 100%; }
hr { border: 0; border-top: 1px solid #e5e9ef; margin: 2em 0; }
ul, ol { padding-left: 1.8em; }
li { margin: .25em 0; }
"""


def render_for_minihtml(view):
    """Markdown -> HTML tailored for minihtml (in-editor preview)."""
    fragment, base_dir, _ = render_fragment(view)
    body = fix_images(fragment, base_dir)
    return "<style>%s</style>%s" % (STYLE, minihtml_fix(body))


def _write_standalone(view, html, title):
    out_dir = cache_dir()
    name = os.path.splitext(os.path.basename(view.file_name() or "preview"))[0]
    out = os.path.join(out_dir, name + ".html")
    doc = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>%s</title><style>%s</style></head><body>%s</body></html>"
        % (title, WEB_STYLE, html)
    )
    with open(out, "w", encoding="utf-8") as f:
        f.write(doc)
    return out


def render_standalone(view):
    """Markdown -> standalone HTML file (browser preview)."""
    if engine() == "pandoc":
        pandoc = pandoc_path()
        src, base_dir = _source_file(view)
        out_dir = cache_dir()
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
            **hidden_kwargs(),
        )
        if proc.returncode != 0 or not os.path.exists(out):
            raise RuntimeError((proc.stderr or "pandoc failed").strip()[:400])
        return out

    fragment = _run_python_markdown(view)
    fragment = fix_images(fragment, source_dir(view))
    return _write_standalone(view, fragment, "Markdown Preview")
