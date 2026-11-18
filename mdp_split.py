"""Side-by-side Markdown preview with synchronized scrolling.

The preview is a scratch view holding a single LAYOUT_BLOCK phantom.
Using a real view (instead of an HtmlSheet) is what makes scroll
synchronization possible: the plugin can read viewport_position() from
the source view and push a proportional position into the preview.
"""

import traceback

import sublime
import sublime_plugin

from .mdp.common import log, render_for_minihtml, setting

PREVIEW_NAME = setting("preview_name", "Markdown Preview")
PHANTOM_KEY = "mdp_preview_block"
SYNC_INTERVAL_MS = 120
IDLE_INTERVAL_MS = 600

# preview_view_id -> source_view_id
_PAIRS = {}
# source_view_id -> last seen viewport position
_LAST = {}


def _find_preview(window):
    for view in window.views():
        if view.name() == PREVIEW_NAME and view.is_scratch():
            return view
    return None


def _create_preview(window):
    view = window.new_file()
    view.set_scratch(True)
    view.set_read_only(True)
    view.set_name(PREVIEW_NAME)

    s = view.settings()
    s.set("gutter", False)
    s.set("line_numbers", False)
    s.set("fold_buttons", False)
    s.set("highlight_line", False)
    s.set("word_wrap", True)
    s.set("draw_centered", False)
    s.set("scroll_past_end", False)
    s.set("draw_white_space", "none")
    s.set("caret_style", "invisible")
    return view


class MdpRenderPreviewCommand(sublime_plugin.TextCommand):
    """Replace the preview view contents with rendered HTML."""

    def run(self, edit, html=""):
        view = self.view
        view.set_read_only(False)
        view.erase_phantoms(PHANTOM_KEY)
        if view.size() == 0:
            view.insert(edit, 0, "\n")
        view.add_phantom(
            PHANTOM_KEY, sublime.Region(0, 1), html, sublime.LAYOUT_BLOCK, None
        )
        view.set_read_only(True)


class MdpSplitPreviewCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        try:
            window = self.view.window()
            if not window:
                return

            html = render_for_minihtml(self.view)

            ratio = float(setting("split_ratio", 0.52))
            ratio = max(0.2, min(0.8, ratio))
            window.set_layout({
                "cols": [0.0, ratio, 1.0],
                "rows": [0.0, 1.0],
                "cells": [[0, 0, 1, 1], [1, 0, 2, 1]],
            })
            window.set_view_index(self.view, 0, 0)

            preview = _find_preview(window)
            if preview is None:
                preview = _create_preview(window)
                window.set_view_index(preview, 1, 0)

            preview.run_command("mdp_render_preview", {"html": html})

            _PAIRS[preview.id()] = self.view.id()
            _LAST[self.view.id()] = self.view.viewport_position()

            window.focus_group(0)
        except Exception:
            log("split preview failed:\n" + traceback.format_exc())
            sublime.error_message(
                "Markdown split preview failed.\n\nSee %s"
                % ("the plugin log in the Sublime cache directory")
            )


class MdpSplitPreviewListener(sublime_plugin.EventListener):
    def on_post_save(self, view):
        for preview_id, source_id in list(_PAIRS.items()):
            if source_id != view.id():
                continue
            try:
                preview = sublime.View(preview_id)
                if preview.is_valid():
                    preview.run_command(
                        "mdp_render_preview", {"html": render_for_minihtml(view)}
                    )
            except Exception:
                log("refresh failed:\n" + traceback.format_exc())

    def on_close(self, view):
        _PAIRS.pop(view.id(), None)
        _LAST.pop(view.id(), None)
        for preview_id, source_id in list(_PAIRS.items()):
            if source_id == view.id():
                _PAIRS.pop(preview_id, None)


def _tick():
    try:
        if _PAIRS and setting("sync_scroll", True):
            for preview_id, source_id in list(_PAIRS.items()):
                preview = sublime.View(preview_id)
                source = sublime.View(source_id)
                if not preview.is_valid() or not source.is_valid():
                    _PAIRS.pop(preview_id, None)
                    continue

                position = source.viewport_position()
                if _LAST.get(source_id) == position:
                    continue
                _LAST[source_id] = position

                source_scrollable = source.layout_extent()[1] - source.viewport_extent()[1]
                preview_scrollable = preview.layout_extent()[1] - preview.viewport_extent()[1]
                if source_scrollable <= 0 or preview_scrollable <= 0:
                    continue

                ratio = max(0.0, min(1.0, position[1] / source_scrollable))
                preview.set_viewport_position((0, ratio * preview_scrollable), False)
    except Exception:
        log("scroll sync failed:\n" + traceback.format_exc())

    sublime.set_timeout(_tick, SYNC_INTERVAL_MS if _PAIRS else IDLE_INTERVAL_MS)


def plugin_loaded():
    sublime.set_timeout(_tick, SYNC_INTERVAL_MS)
