#!/usr/bin/env python3
"""Simple Markdown to HTML converter (writes HTML fragments only).

Design notes:
- Produces HTML fragments only (no <html>/<head>/<body> wrapper).
- Lightweight, dependency-free: uses regular expressions and line-based parsing.
- Supports headings, paragraphs, bold/italic/link inline formatting,
  unordered/ordered lists, fenced code blocks (```), horizontal rules,
  and a basic GitHub-style table detection.

Usage: python3 markdown_to_html.py input.txt output.txt
"""
import re
import sys

# Regular expressions for simple inline markdown features.
# These are intentionally simple and cover common cases (not full CommonMark).
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
ITALIC_RE = re.compile(r"\*(.+?)\*")
LINK_RE = re.compile(r"\[(.*?)\]\((.*?)\)")


def inline_replace(text):
    """Replace inline markdown (bold, italic, links) in a text line.

    Note: order matters (bold before italic) to avoid clobbering markers.
    This function does not escape HTML — assume trusted/simple inputs.
    """
    # Bold first (strong)
    text = BOLD_RE.sub(r"<strong>\1</strong>", text)
    # Then italic (em)
    text = ITALIC_RE.sub(r"<em>\1</em>", text)
    # Then links [text](url)
    text = LINK_RE.sub(r"<a href=\"\2\">\1</a>", text)
    return text


def convert(lines):
    """Convert a list of input lines (strings) from markdown to HTML fragment.

    High-level approach:
    - Iterate lines with an index so we can peek ahead for tables.
    - Maintain small parser state: in_code, current list type, paragraph buffer.
    - Emit tags for headings, lists, tables, and code blocks as encountered.
    """
    out = []
    in_code = False
    code_buffer = []
    list_type = None  # 'ul' or 'ol'
    para_buffer = []

    def flush_para():
        """Flush an accumulated paragraph buffer into a single <p> element.

        Paragraph lines are joined with spaces (preserve words across wrapped
        lines in the source). After flushing, the buffer is cleared.
        """
        nonlocal para_buffer
        if para_buffer:
            out.append("<p>" + inline_replace(" ".join(para_buffer).strip()) + "</p>")
            para_buffer = []

    def close_list():
        """Close any open list (</ul> or </ol>) and reset state."""
        nonlocal list_type
        if list_type:
            out.append(f"</{list_type}>")
            list_type = None

    i = 0
    n = len(lines)
    while i < n:
        raw = lines[i]
        line = raw.rstrip('\n')

        # Fenced code block start/end
        if line.strip().startswith("```"):
            if not in_code:
                # Starting a code block: close running paragraphs/lists first
                flush_para()
                close_list()
                in_code = True
                code_buffer = []
            else:
                # Ending a code block: emit the collected lines unchanged
                out.append("<pre><code>")
                out.extend([c for c in code_buffer])
                out.append("</code></pre>")
                in_code = False
                code_buffer = []
            i += 1
            continue

        # Inside a fenced code block: collect raw lines until closing ```
        if in_code:
            code_buffer.append(line)
            i += 1
            continue

        # Blank line => end current paragraph or list
        if not line.strip():
            flush_para()
            close_list()
            i += 1
            continue

        # Headings: lines starting with 1-6 '#' characters
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            flush_para()
            close_list()
            level = len(m.group(1))
            out.append(f"<h{level}>" + inline_replace(m.group(2).strip()) + f"</h{level}>")
            i += 1
            continue

        # Horizontal rule (e.g. '---' or '***') on a line by itself
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", line.strip()):
            flush_para()
            close_list()
            out.append("<hr />")
            i += 1
            continue

        # Unordered list item (lines starting with '-' or '*')
        m = re.match(r"^\s*[-\*]\s+(.*)$", line)
        if m:
            flush_para()
            if list_type != 'ul':
                close_list()
                out.append("<ul>")
                list_type = 'ul'
            out.append("<li>" + inline_replace(m.group(1).strip()) + "</li>")
            i += 1
            continue

        # Ordered list item (e.g. '1. item')
        m = re.match(r"^\s*\d+\.\s+(.*)$", line)
        if m:
            flush_para()
            if list_type != 'ol':
                close_list()
                out.append("<ol>")
                list_type = 'ol'
            out.append("<li>" + inline_replace(m.group(1).strip()) + "</li>")
            i += 1
            continue

        # Basic table detection: a line containing '|' followed by a separator
        # line such as '| --- | --- |'. This implements a simple GitHub-style
        # table parser: header row -> separator row -> body rows.
        if '|' in line:
            # Peek next non-empty line to see if it looks like a table separator
            j = i + 1
            while j < n and not lines[j].strip():
                j += 1
            if j < n:
                sep = lines[j].strip()
                # separator should contain only pipes, colons, dashes, and spaces
                if re.match(r"^\s*[:\-\| \t]+$", sep) and re.search(r"-{3,}", sep):
                    # It's a table: emit <table>, <thead>, and <tbody>
                    flush_para()
                    close_list()
                    header_line = line.strip().strip('|')
                    headers = [h.strip() for h in re.split(r"\s*\|\s*", header_line)]
                    out.append("<table>")
                    out.append("<thead>")
                    out.append("<tr>" + ''.join([f"<th>{inline_replace(h)}</th>" for h in headers]) + "</tr>")
                    out.append("</thead>")
                    out.append("<tbody>")
                    i = j + 1
                    # consume rows until a blank line or a line without '|' character
                    while i < n and lines[i].strip():
                        row = lines[i].strip()
                        if '|' not in row:
                            break
                        row_cells = [c.strip() for c in re.split(r"\s*\|\s*", row.strip().strip('|'))]
                        out.append("<tr>" + ''.join([f"<td>{inline_replace(c)}</td>" for c in row_cells]) + "</tr>")
                        i += 1
                    out.append("</tbody>")
                    out.append("</table>")
                    continue

    # Fallback: accumulate paragraph lines until a blank line
    para_buffer.append(line.strip())
    i += 1

    # end while
    flush_para()
    close_list()

    # If file ended while still in code block, close it safely so output is
    # well-formed. This mirrors the behavior of closing a fenced block above.
    if in_code:
        out.append("<pre><code>")
        out.extend([c for c in code_buffer])
        out.append("</code></pre>")

    return "\n".join(out)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: markdown_to_html.py input.txt output.txt")
        sys.exit(2)
    inp, outp = sys.argv[1], sys.argv[2]
    with open(inp, 'r', encoding='utf-8') as f:
        src = f.readlines()
    html = convert(src)
    with open(outp, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Wrote {outp}")
