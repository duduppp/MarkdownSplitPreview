# MarkdownSplitPreview

Side-by-side Markdown preview for Sublime Text 4, with **synchronized scrolling**.

Left pane: source. Right pane: rendered output. Scroll either one and the other follows.

![status](https://img.shields.io/badge/Sublime%20Text-4-ff9800.svg)

## How it renders

The package picks an engine automatically:

| Engine | When it is used | Install |
|---|---|---|
| **python-markdown** | default fallback | installed automatically by Package Control |
| **pandoc** | when found on `PATH` | optional, gives better tables and code blocks |

**It works out of the box** — no external tools required. Installing pandoc is
optional and only improves fidelity in the in-editor preview.

```bash
brew install pandoc        # macOS (optional)
sudo apt install pandoc    # Ubuntu / Debian (optional)
```

## Features

- **Split preview** — source left, rendered right
- **Scroll sync** — the preview follows the source scroll position proportionally
- **Live refresh** — re-renders automatically on save
- **Browser preview** — export a standalone HTML file
- **Quick writing panel** — bold / headings / lists / tables / code blocks

## Usage

Open the command palette (`Cmd+Shift+P` / `Ctrl+Shift+P`):

| Command | What it does |
|---|---|
| `Markdown Split: Preview (side by side)` | Split pane with scroll sync |
| `Markdown Split: Preview in Browser` | Standalone HTML in your browser |
| `Markdown Split: Quick Writing Panel` | Formatting menu |

All commands are also available under the **Markdown Split** menu.

### Recommended key bindings

The package ships no default key bindings to avoid clashes. Add your own in
`Preferences → Key Bindings`:

```json
[
    { "keys": ["super+shift+o"], "command": "mdp_split_preview" },
    { "keys": ["super+shift+m"], "command": "mdp_browser_preview" },
    { "keys": ["super+alt+k"], "command": "mdp_quick_write" }
]
```

## Settings

`Preferences → Package Settings → MarkdownSplitPreview`

```json
{
    "engine": "auto",
    "pandoc_path": "",
    "split_ratio": 0.52,
    "sync_scroll": true,
    "preview_name": "Markdown Preview"
}
```

`engine` accepts `auto`, `pandoc` or `python`.

## Known limitations

Sublime Text renders in-editor HTML with **minihtml**, not a browser engine:

- **Tables** are rendered row by row (`a | b | c`) instead of as a grid
- **Syntax highlighting** inside fenced code blocks is not available

For full fidelity — real tables, highlighted code, embedded images — use
**Preview in Browser**.

## Troubleshooting

- **Nothing happens** — save the file first; unsaved buffers are previewed from a temporary copy.
- **Empty or stale preview** — run the preview command again, or check the log at
  `<cache>/MarkdownSplitPreview.log` (Sublime's cache directory).
- **`python-markdown` missing** — run `Package Control: Satisfy Dependencies`.

## License

MIT

---

# 中文说明

## 渲染引擎

| 引擎 | 使用时机 | 安装方式 |
|---|---|---|
| **python-markdown** | 默认兜底 | Package Control 自动安装 |
| **pandoc** | 检测到就优先使用 | 可选，装了效果更好 |

**开箱即用**，不需要额外安装任何东西。装 pandoc 只是让编辑器内的表格和代码块更接近真实排版。

## 功能

- **左右分屏预览**：左边源码，右边渲染结果
- **滚动联动**：滚动源码，预览按比例跟随
- **保存自动刷新**
- **浏览器预览**：导出独立 HTML 文件
- **快捷写作面板**：加粗、标题、列表、表格、代码块一键插入

## 使用

命令面板（`Cmd+Shift+P`）搜索 `Markdown Split`，或使用菜单栏的 **Markdown Split** 菜单。

本包**不预设快捷键**，避免和其他插件冲突。建议自行在 `Preferences → Key Bindings` 添加：

```json
[
    { "keys": ["super+shift+o"], "command": "mdp_split_preview" },
    { "keys": ["super+shift+m"], "command": "mdp_browser_preview" },
    { "keys": ["super+alt+k"], "command": "mdp_quick_write" }
]
```

## 已知限制

Sublime 内置的 minihtml 不是完整浏览器：**表格**只能逐行显示，**代码块没有语法高亮**。
需要完整排版时请用「Preview in Browser」。
