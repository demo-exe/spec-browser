# 3GPP Specification browser

This is my opinionated 3GPP spec opener-thingy.

## Usage

1. Run `python main.py` (preferably via a shortcut, in my case its `GUI+o`)
1. Type spec number you want to open ex. `23.501`. Cached specs will be visible in dmenu.
1. Press enter and wait (downloading & unpacking may take a while, progress is tracked via notifications)

## Requirements

```bash
yay -S python dmenu python-dmenu libreoffice-fresh zathura zathura-pdf-mupdf
```

- dmenu is my menu select of choice
- libreoffice - for converting .docx from 3gpp page to pdf
- zathura browses pdfs with vim movements

## Folders

Uses `$XDG_CACHE_HOME/ts-spec-browser` or `$HOME/.cache/ts-spec-browser` for cached documents.

