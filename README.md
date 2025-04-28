# href-hound

This project was created using Vibe Coding (OpenAI Codex).

href-hound is a Python-based tool for crawling static HTML pages starting from a seed URL and checking for broken links. It offers both a Command Line Interface (CLI) and a Graphical User Interface (GUI) built with PyQt5, using a shared core logic.

## Features

- Crawl HTML pages and extract `<a>` links
- Optional resource link checking: `<img>`, `<link>`, `<script>`
- Configurable options:
  - Same-origin only or include subdomains
  - Maximum crawl depth (`-1` for unlimited)
  - Exclude/include URL patterns (substring match)
  - Custom User-Agent, timeout, concurrency, delay, and error status codes
- Generate a single-file HTML report listing broken links grouped by source page
- CLI and GUI share the same core processing logic

## Requirements

- Python 3.7 or newer
- PyQt5
- Other dependencies listed in `requirements.txt`

Install dependencies:
```bash
pip install -r requirements.txt
```

## Installation

```bash
git clone <repo_url>
cd <repo_dir>
pip install -r requirements.txt
```

## CLI Usage

Run the CLI checker:
```bash
python -m href_hound.cli <start_url> [options]
```

Common options:
- `-o, --output`: output HTML report path (default: `report.html`)
- `--same-origin`: crawl same origin only (default)
- `--include-subdomains`: include subdomains
- `--max-depth N`: maximum crawl depth (default `3`, use `-1` for unlimited)
- `--exclude PATTERN`: exclude URLs containing `PATTERN` (substring match, repeatable)
- `--include PATTERN`: include only URLs containing `PATTERN` (repeatable)
- `--check-resources`: also check resource links (`img`, `link`, `script`)
  - `--user-agent STRING`: custom User-Agent (default: `href-hound/1.0`)
- `--timeout SECONDS`: request timeout (default: `10.0`)
- `--concurrency N`: max concurrent requests (default: `5`)
- `--delay SECONDS`: delay between requests (default: `0.0`)
- `--error-codes CODE1,CODE2,...`: additional HTTP status codes to treat as broken

Example:
```bash
python -m href_hound.cli https://example.com -o report.html \
  --max-depth -1 --check-resources \
  --exclude "/blocks/docs/en/" \
  --user-agent "MyBot/1.0" --timeout 5
```

## GUI Usage

Run the GUI application:
```bash
python -m href_hound.gui
```

In the GUI:
1. Enter **Start URL** and **Output HTML Report** path
2. Configure options:
   - Same-origin / Include subdomains
   - Max depth (`-1` for unlimited)
   - Exclude/include URL patterns (one per line)
   - Check resource links (`img`, `link`, `script`)
   - User-Agent, Timeout, Concurrency, Delay, Error codes
3. Click **Start** to begin; progress and logs appear in real time
4. Click **Stop** to cancel mid-run
5. Click **Open Report** after completion to view the HTML report

## Report Format

The generated HTML report groups broken links by their source page and lists the target URL, HTTP status (or error message), making it easy to locate and fix broken references.

## Troubleshooting

- If GUI labels or title bar display garbled text on Ubuntu/WSL2, install a Japanese font package:
  ```bash
  sudo apt update && sudo apt install fonts-noto-cjk
  ```

---
Enjoy efficient link checking with href-hound!