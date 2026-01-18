#!/usr/bin/env python3
"""Simple Markdown to HTML converter (writes HTML fragments only).
Usage: python3 markdown_to_html.py input.txt output.txt
"""
import re
import sys

BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
ITALIC_RE = re.compile(r"\*(.+?)\*")
LINK_RE = re.compile(r"\[(.*?)\]\((.*?)\)")


def inline_replace(text):
    text = BOLD_RE.sub(r"<strong>\1</strong>", text)
    text = ITALIC_RE.sub(r"<em>\1</em>", text)
    text = LINK_RE.sub(r"<a href=\"\2\">\1</a>", text)
    return text


def convert(lines):
    out = []
    in_code = False
    code_buffer = []
    list_type = None  # 'ul' or 'ol'
    para_buffer = []

    def flush_para():
        nonlocal para_buffer
        if para_buffer:
            out.append("<p>" + inline_replace(" ".join(para_buffer).strip()) + "</p>")
            para_buffer = []

    def close_list():
        nonlocal list_type
        if list_type:
            out.append(f"</{list_type}>")
            list_type = None

    i = 0
    n = len(lines)
    while i < n:
        raw = lines[i]
        line = raw.rstrip('\n')

        if line.strip().startswith("```"):
            if not in_code:
                flush_para()
                close_list()
                in_code = True
                code_buffer = []
            else:
                out.append("<pre><code>")
                out.extend([c for c in code_buffer])
                out.append("</code></pre>")
                in_code = False
                code_buffer = []
            i += 1
            continue

        if in_code:
            code_buffer.append(line)
            i += 1
            continue

        if not line.strip():
            flush_para()
            close_list()
            i += 1
            continue

        # headings
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            flush_para()
            close_list()
            level = len(m.group(1))
            out.append(f"<h{level}>" + inline_replace(m.group(2).strip()) + f"</h{level}>")
            i += 1
            continue

        # horizontal rule
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", line.strip()):
            flush_para()
            close_list()
            out.append("<hr />")
            i += 1
            continue

        # unordered list
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

        # ordered list
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

        # table detection: header line with '|' and next line is a separator like |---|---|
        if '|' in line:
            # Peek next non-empty line
            j = i + 1
            while j < n and not lines[j].strip():
                j += 1
            if j < n:
                sep = lines[j].strip()
                # separator should contain only pipes, colons, dashes, and spaces
                if re.match(r"^\s*[:\-\| \t]+$", sep) and re.search(r"-{3,}", sep):
                    # It's a table
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
                    # consume rows until a blank line or non-table line
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

        # paragraphs (accumulate until blank line)
        para_buffer.append(line.strip())
        i += 1

    # end while
    flush_para()
    close_list()

    # If file ended while still in code block, close it safely
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
