"""A very small template language for block markup.

Blocks keep their markup next to their stylesheet so a whole block is one
self-contained folder that a designer can edit without touching Python. The
language is deliberately tiny — there is no expression evaluation, no includes
and no arbitrary lookups, so a template can only ever render the data it is
handed.

    {{name}}            escaped text
    {{{name}}}          raw markup, only for values the project itself owns
    {{#name}}...{{/}}   repeat once per item in a list, with the item in scope
    {{?name}}...{{/}}   render only when the value is present
    {{^name}}...{{/}}   render only when the value is absent
    {{@n}} {{@nn}}      1-based index inside a repeat, plain and zero-padded

Inside a repeat, a bare name resolves against the current item first and then
against the surrounding scope, so shared values stay reachable.
"""
from __future__ import annotations

import html
import re
from typing import Any, Mapping, Sequence

TOKEN = re.compile(r"\{\{(\{)?\s*([#?^@/])?\s*([a-zA-Z0-9_.]*)\s*\}?\}\}")


class TemplateError(ValueError):
    """Raised when a template is malformed or asks for data it was not given."""


class _Scope:
    """A stack of mappings plus the current repeat index."""

    __slots__ = ("frames", "index", "length")

    def __init__(self, frames: list[Mapping[str, Any]], index: int = 0, length: int = 0) -> None:
        self.frames = frames
        self.index = index
        self.length = length

    def push(self, frame: Mapping[str, Any], index: int, length: int) -> "_Scope":
        return _Scope([frame, *self.frames], index, length)

    def lookup(self, path: str) -> Any:
        head, _, rest = path.partition(".")
        for frame in self.frames:
            if isinstance(frame, Mapping) and head in frame:
                value = frame[head]
                for part in rest.split(".") if rest else ():
                    if not isinstance(value, Mapping) or part not in value:
                        return None
                    value = value[part]
                return value
        return None


def _present(value: Any) -> bool:
    return value not in (None, "", [], {}, False)


def _parse(template: str) -> list[Any]:
    """Turn a template into a tree of literals, slots and sections."""
    root: list[Any] = []
    stack: list[tuple[str, str, list[Any]]] = []
    current = root
    position = 0

    for match in TOKEN.finditer(template):
        literal = template[position:match.start()]
        if literal:
            current.append(literal)
        position = match.end()

        raw, kind, name = bool(match.group(1)), match.group(2), match.group(3)

        if kind == "/":
            if not stack:
                raise TemplateError("Unbalanced closing tag in template")
            _, _, parent = stack.pop()
            current = parent
        elif kind in {"#", "?", "^"}:
            body: list[Any] = []
            current.append((kind, name, body))
            stack.append((kind, name, current))
            current = body
        elif kind == "@":
            current.append(("@", name, None))
        else:
            if not name:
                raise TemplateError("Empty slot name in template")
            current.append(("raw" if raw else "text", name, None))

    if stack:
        raise TemplateError(f"Unclosed section '{stack[-1][1]}' in template")
    tail = template[position:]
    if tail:
        current.append(tail)
    return root


def _render(nodes: Sequence[Any], scope: _Scope, out: list[str]) -> None:
    for node in nodes:
        if isinstance(node, str):
            out.append(node)
            continue
        kind, name, body = node
        if kind == "text":
            value = scope.lookup(name)
            out.append(html.escape(str(value), quote=True) if _present(value) else "")
        elif kind == "raw":
            value = scope.lookup(name)
            out.append(str(value) if _present(value) else "")
        elif kind == "@":
            number = scope.index + 1
            out.append(f"{number:02d}" if name == "nn" else str(number))
        elif kind == "#":
            items = scope.lookup(name)
            if not _present(items):
                continue
            if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
                raise TemplateError(f"Section '{name}' expects a list")
            for index, item in enumerate(items):
                frame = item if isinstance(item, Mapping) else {"value": item}
                _render(body, scope.push(frame, index, len(items)), out)
        elif kind == "?":
            if _present(scope.lookup(name)):
                _render(body, scope, out)
        elif kind == "^":
            if not _present(scope.lookup(name)):
                _render(body, scope, out)


def render_template(template: str, data: Mapping[str, Any]) -> str:
    out: list[str] = []
    _render(_parse(template), _Scope([data]), out)
    return "".join(out)
