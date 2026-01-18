# MarkdownToHTML

Simple converter that reads markdown from `input.txt` and writes HTML fragments to `output.txt` (no <html>/<head>/<body> wrappers).

Usage:

```bash
python3 markdown_to_html.py input.txt output.txt
```

Files:

- `markdown_to_html.py` - converter script
- `input.txt` - sample input
- `output.txt` - generated output (created when you run the script)

Tests:

```bash
pip install pytest
pytest -q
```
