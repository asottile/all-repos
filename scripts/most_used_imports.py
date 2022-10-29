from __future__ import annotations

import ast
import sys


class Visitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.n = 0

    def visit_Import(self, node: ast.Import | ast.ImportFrom) -> None:
        if node.col_offset == 0:
            self.n = node.lineno

    visit_ImportFrom = visit_Import


def import_count(filename: str) -> int:
    visitor = Visitor()
    with open(filename, 'rb') as f:
        try:
            visitor.visit(ast.parse(f.read(), filename))
        except SyntaxError:
            return 0
    return visitor.n


def main() -> int:
    for filename in sys.argv[1:]:
        print(f'{import_count(filename)} {filename}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
