from __future__ import annotations

import ast
import collections
import pprint
import sys

from aspy.refactor_imports.classify import classify_import
from aspy.refactor_imports.classify import ImportType


class Visitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.counts: collections.Counter[str] = collections.Counter()

    def visit_Import(self, node: ast.Import) -> None:
        for name in node.names:
            if classify_import(name.name) == ImportType.BUILTIN:
                self.counts[name.name] += 1
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module and classify_import(node.module) == ImportType.BUILTIN:
            self.counts[node.module] += 1
        self.generic_visit(node)


def main() -> int:
    visitor = Visitor()
    for filename in sys.argv[1:]:
        with open(filename, 'rb') as f:
            try:
                visitor.visit(ast.parse(f.read(), filename=filename))
            except SyntaxError:
                continue

    pprint.pprint(visitor.counts.most_common())
    return 0


if __name__ == '__main__':
    exit(main())
