"""Conservative HTML grid recovery with exact source-string offsets."""
from html import unescape
from html.parser import HTMLParser

MAX_HTML_CHARS = 2_000_000
MAX_CELLS = 50_000
MAX_GRID_SLOTS = 500_000


class TableParser(HTMLParser):
    def __init__(self, raw):
        super().__init__(convert_charrefs=False)
        self.raw = raw
        self.line_starts = [0]
        self.line_starts.extend(i + 1 for i, c in enumerate(raw) if c == "\n")
        self.stack = []
        self.cells = []
        self.cell = None
        self.row = -1
        self.in_row = False
        self.tables = 0
        self.issues = []

    def pos(self):
        line, column = self.getpos()
        return self.line_starts[line - 1] + column

    def issue(self, code):
        if code not in self.issues:
            self.issues.append(code)

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.tables += 1
            if self.stack or self.tables != 1:
                self.issue("nested_or_multiple_tables")
        elif tag == "tr":
            if self.in_row or self.cell is not None or not self.stack or self.stack[-1] not in {"table", "tbody", "thead", "tfoot"}:
                self.issue("malformed_rows")
            self.row += 1
            self.in_row = True
        elif tag in {"td", "th"}:
            if not self.in_row or self.cell is not None or not self.stack or self.stack[-1] != "tr":
                self.issue("malformed_cells")
            if len(self.cells) >= MAX_CELLS:
                raise ValueError("HTML cell limit exceeded")
            values = dict(attrs)
            if len(values) != len(attrs):
                self.issue("duplicate_html_attributes")
            spans = []
            for key in ("rowspan", "colspan"):
                value = values.get(key, "1")
                if value is None or not value.isascii() or not value.isdecimal() or not 0 < int(value) <= MAX_CELLS:
                    self.issue("invalid_cell_span")
                    value = "1"  # The invalid grid is withheld, never accepted as repaired.
                spans.append(int(value))
            self.cell = {"row": self.row, "row_span": spans[0], "column_span": spans[1],
                         "start": self.pos(), "end": None, "fragments": [], "unsupported": False}
            self.cells.append(self.cell)
        elif tag not in {"tbody", "thead", "tfoot", "b", "i", "em", "strong", "span", "sup", "sub", "br"}:
            self.issue("unsupported_inline_content" if self.cell is not None else "unsupported_html_content")
            if self.cell is not None:
                self.cell["unsupported"] = True
        if tag not in {"img", "br", "hr", "input", "meta", "link"}:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1] != tag:
            self.issue("unbalanced_html")
        else:
            self.stack.pop()
        if tag in {"td", "th"}:
            if self.cell is not None:
                end = self.raw.find(">", self.pos())
                self.cell["end"] = len(self.raw) if end == -1 else end + 1
            self.cell = None
        elif tag == "tr":
            self.in_row = False

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in {"img", "br", "hr", "input", "meta", "link"}:
            self.handle_endtag(tag)

    def fragment(self, start, end, encoding):
        if self.cell is not None:
            self.cell["fragments"].append({"start": start, "end": end, "encoding": encoding})
        elif self.raw[start:end].strip():
            self.issue("text_outside_cells")

    def handle_data(self, data):
        self.fragment(self.pos(), self.pos() + len(data), "literal")

    def entity(self, name, prefix):
        start = self.pos()
        end = start + len(name) + len(prefix)
        if self.raw[end:end + 1] == ";":
            end += 1
        self.fragment(start, end, "html_entity")

    def handle_entityref(self, name):
        self.entity(name, "&")

    def handle_charref(self, name):
        self.entity(name, "&#")


def parse(raw):
    if len(raw) > MAX_HTML_CHARS:
        raise ValueError("HTML character limit exceeded")
    parser = TableParser(raw)
    parser.feed(raw)
    parser.close()
    if parser.stack or parser.cell is not None or parser.tables != 1 or parser.row < 0:
        parser.issue("incomplete_html")
    structural = [c for c in parser.issues if c not in {"unsupported_inline_content", "unsupported_html_content"}]
    if structural:
        return {"cells": [], "rows": max(0, parser.row + 1), "columns": 0, "state": "unresolved", "issues": parser.issues}
    occupied = set()
    columns = 0
    for cell in parser.cells:
        row, col = cell["row"], 0
        while (row, col) in occupied:
            col += 1
        cell["column"] = col
        if cell["row_span"] * cell["column_span"] + len(occupied) > MAX_GRID_SLOTS:
            raise ValueError("HTML grid resource limit exceeded")
        for r in range(row, row + cell["row_span"]):
            for c in range(col, col + cell["column_span"]):
                if (r, c) in occupied or r > parser.row:
                    parser.issue("overlap_or_span_overflow")
                occupied.add((r, c))
        columns = max(columns, col + cell["column_span"])
        cell["text"] = "".join(unescape(raw[f["start"]:f["end"]]) if f["encoding"] == "html_entity"
                               else raw[f["start"]:f["end"]] for f in cell["fragments"])
    if "overlap_or_span_overflow" in parser.issues:
        return {"cells": [], "rows": parser.row + 1, "columns": columns, "state": "unresolved", "issues": parser.issues}
    if columns * (parser.row + 1) > MAX_GRID_SLOTS:
        raise ValueError("HTML grid resource limit exceeded")
    if len(occupied) != columns * (parser.row + 1):
        parser.issue("grid_holes")
    return {"cells": parser.cells, "rows": parser.row + 1, "columns": columns,
            "state": "partial" if parser.issues else "resolved", "issues": parser.issues}
