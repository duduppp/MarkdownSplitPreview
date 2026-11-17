# MarkdownSplitPreview

Side-by-side Markdown preview for Sublime Text 4, with **synchronized scrolling**.

Left pane: source. Right pane: rendered output. Scroll either one and the other follows.

![status](https://img.shields.io/badge/Sublime%20Text-4-ff9800.svg)

## Requirements

**pandoc** must be installed:

```bash
# macOS
brew install pandoc

# Ubuntu / Debian
sudo apt install pandoc

# Windows
winget install --id JohnMacFarlane.Pandoc
```

If pandoc is somewhere unusual, set `pandoc_path` in the package settings.

## Features

- **Split preview** — source left, rendered right
- **Scroll sync** — the preview follows the source scroll position proportionally
- **Live refresh** — re-renders automatically on save
- **Browser preview** — export a self-contained HTML file (images embedded)
- **Quick writing panel** — bold / headings / lists / tables / code blocks without memorizing syntax

## Usage

Open the command palette (`Cmd+Shift+P` / `Ctrl+Shift+P`):

| Command | What it does |
|---|---|
| `Markdown Split: Preview (side by side)` | Split pane with scroll sync |
| `Markdown Split: Preview in Browser` | Self-contained HTML in your browser |
| `Markdown Split: Quick Writing Panel` | Formatting menu |

All commands are also available under the **Markdown Split** menu.

### Recommended key bindings

The package deliberately ships no default key bindings to avoid clashes.
Add your own in `Preferences → Key Bindings`:

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
    "pandoc_path": "",
    "split_ratio": 0.52,
    "sync_scroll": true,
    "preview_name": "Markdown Preview"
}
```

## Known limitations

Sublime Text renders in-editor HTML with **minihtml**, which is not a full
browser engine. Two consequences:

- **Tables** are rendered row by row (`a | b | c`) instead of as a grid
- **Syntax highlighting** of fenced code blocks is not available

For full fidelity — real tables, highlighted code, embedded images — use
**Preview in Browser**.

## Troubleshooting

- **Nothing happens** — check that pandoc is on your `PATH`: run `pandoc --version` in a terminal.
- **Empty preview** — the file must be saved to disk.
- **Errors** — see the plugin log in Sublime's cache directory
  (`Preferences → Browse Packages` → parent folder → `Cache/MarkdownSplitPreview.log`).

## License

MIT

---

# 中文说明

## 依赖

必须安装 **pandoc**：

```bash
brew install pandoc          # macOS
sudo apt install pandoc      # Ubuntu / Debian
winget install --id JohnMacFarlane.Pandoc   # Windows
```

## 功能

- **左右分屏预览**：左边源码，右边渲染结果
- **滚动联动**：滚动源码，预览按比例跟随
- **保存自动刷新**
- **浏览器预览**：导出单文件 HTML，图片内嵌
- **快捷写作面板**：加粗、标题、列表、表格、代码块一键插入

## 使用

命令面板（`Cmd+Shift+P`）里搜索 `Markdown Split`，或使用菜单栏的 **Markdown Split** 菜单。

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
