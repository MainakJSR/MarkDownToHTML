from markdown_to_html import convert


def test_simple():
    md = [
        "# Hi",
        "",
        "This is **bold** and *italic*.",
        "",
        "- a",
        "- b",
    ]
    out = convert(md)
    assert "<h1>Hi</h1>" in out
    assert "<strong>bold</strong>" in out
    assert "<em>italic</em>" in out
    assert "<ul>" in out and "</ul>" in out


def test_table():
    md = [
        "| Name | Age |",
        "| ---- | --- |",
        "| Alice | 30 |",
        "| Bob | 25 |",
    ]
    out = convert(md)
    assert "<table>" in out
    assert "<th>Name</th>" in out and "<td>Alice</td>" in out
