"""Browser preview and quick formatting tools."""

import datetime
import traceback
import webbrowser

import sublime
import sublime_plugin

from .mdp.common import log, render_standalone

TABLE_SNIPPET = (
    "| Column 1 | Column 2 | Column 3 |\n"
    "| --- | --- | --- |\n"
    "| Value | Value | Value |\n"
)


class MdpBrowserPreviewCommand(sublime_plugin.TextCommand):
    """Render with pandoc and open a self-contained HTML file in the browser."""

    def run(self, edit):
        try:
            out = render_standalone(self.view)
            webbrowser.open("file://" + out)
            sublime.status_message("Preview written: " + out)
        except Exception:
            log("browser preview failed:\n" + traceback.format_exc())
            sublime.error_message(
                "Markdown browser preview failed.\n\n"
                "Make sure pandoc is installed (brew install pandoc)."
            )


class MdpPrefixLinesCommand(sublime_plugin.TextCommand):
    def run(self, edit, prefix="", strip_existing=False):
        view = self.view
        starts = set()
        for region in view.sel():
            for line in view.lines(region):
                starts.add(line.begin())

        for pos in sorted(starts, reverse=True):
            if strip_existing:
                line = view.line(pos)
                text = view.substr(line)
                stripped = text.lstrip("#> -")
                removed = len(text) - len(stripped)
                if removed:
                    view.erase(edit, sublime.Region(line.begin(), line.begin() + removed))
            view.insert(edit, pos, prefix)


class MdpFormatCommand(sublime_plugin.TextCommand):
    WRAPPERS = {
        "bold": ("**", "**"),
        "italic": ("*", "*"),
        "strike": ("~~", "~~"),
        "code": ("`", "`"),
        "link": ("[", "](https://)"),
        "image": ("![", "](path/to/image.png)"),
    }
    PREFIXES = {
        "h1": "# ",
        "h2": "## ",
        "h3": "### ",
        "ul": "- ",
        "ol": "1. ",
        "task": "- [ ] ",
        "quote": "> ",
    }

    def run(self, edit, action):
        view = self.view

        if action in self.WRAPPERS:
            left, right = self.WRAPPERS[action]
            view.run_command("insert_snippet",
                             {"contents": left + "$SELECTION" + right})
        elif action in self.PREFIXES:
            view.run_command("mdp_prefix_lines",
                             {"prefix": self.PREFIXES[action],
                              "strip_existing": True})
        elif action == "codeblock":
            view.run_command("insert_snippet", {"contents": "```\n$SELECTION\n```\n"})
        elif action == "table":
            view.run_command("insert_snippet", {"contents": TABLE_SNIPPET})
        elif action == "hr":
            view.run_command("insert_snippet", {"contents": "\n---\n"})
        elif action == "date":
            view.run_command("insert_snippet",
                             {"contents": datetime.date.today().isoformat()})
        elif action == "preview":
            view.run_command("mdp_split_preview")


class MdpQuickWriteCommand(sublime_plugin.TextCommand):
    ITEMS = [
        ("Bold  **text**", "bold"),
        ("Italic  *text*", "italic"),
        ("Strikethrough  ~~text~~", "strike"),
        ("Inline code  `code`", "code"),
        ("", ""),
        ("Heading 1  #", "h1"),
        ("Heading 2  ##", "h2"),
        ("Heading 3  ###", "h3"),
        ("", ""),
        ("Bullet list  -", "ul"),
        ("Numbered list  1.", "ol"),
        ("Task list  - [ ]", "task"),
        ("Blockquote  >", "quote"),
        ("", ""),
        ("Code block  ```", "codeblock"),
        ("Table", "table"),
        ("Horizontal rule  ---", "hr"),
        ("", ""),
        ("Insert today's date", "date"),
        ("Preview in split pane", "preview"),
    ]

    def run(self, edit):
        window = self.view.window()
        if not window:
            return
        labels = [item[0] for item in self.ITEMS]
        actions = [item[1] for item in self.ITEMS]

        def on_done(index):
            if index < 0:
                return
            action = actions[index]
            if action:
                self.view.run_command("mdp_format", {"action": action})

        window.show_quick_panel(labels, on_done)
