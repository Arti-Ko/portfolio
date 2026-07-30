"""Проверка mermaid-блоков в markdown на зарезервированные идентификаторы.

Mermaid не разрешает использовать ключевые слова как идентификаторы узлов:
`graph`, `end`, `class`, `style` и подобные ломают разбор диаграммы. Ошибка
проявляется только при рендере — на GitHub вместо схемы будет текст ошибки.

Запуск:  python3 tools/lint_mermaid.py
Код возврата 1, если что-то найдено.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Ключевые слова mermaid, недопустимые как идентификаторы узлов и классов.
RESERVED = {
    "graph", "subgraph", "end", "class", "classDef", "click", "style",
    "linkStyle", "direction", "default", "flowchart", "stateDiagram",
    "erDiagram", "sequenceDiagram",
}

# Идентификатор перед открывающей скобкой формы узла: id[...], id(...), id{...}
NODE_DECL = re.compile(r"(?:^|\s)([A-Za-z_][\w-]*)\s*(?:\[\(|\(\(|\[|\(|\{)")
# Источник связи: A --> B, A -- "текст" --> B, A -.-> B
EDGE_SOURCE = re.compile(r"(?:^|\s)([A-Za-z_][\w-]*)\s*(?:-{2,3}>|-\.->|={2,3}>|-{2,3}\s|-\.\s)")
# Цель связи — идентификатор сразу после стрелки
EDGE_TARGET = re.compile(r"(?:-{2,3}>|-\.-?->|={2,3}>)\s*([A-Za-z_][\w-]*)")
CLASS_ASSIGN = re.compile(r"^\s*class\s+([\w,\s-]+)\s+(\w+)\s*$")


def iter_blocks(path: pathlib.Path):
    """Отдаёт (номер первой строки блока, строки блока) для каждого ```mermaid."""
    lines = path.read_text(encoding="utf-8").splitlines()
    current: list[str] | None = None
    start = 0
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if current is None and stripped == "```mermaid":
            current, start = [], idx + 1
        elif current is not None and stripped == "```":
            yield start, current
            current = None
        elif current is not None:
            current.append(line)


def check_block(lines: list[str]) -> list[str]:
    problems = []
    for offset, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("%%"):
            continue

        # subgraph <id>[...] — здесь идентификатор объявляется легально,
        # но сам он тоже не должен быть ключевым словом
        candidates = set()
        if stripped.startswith("subgraph "):
            rest = stripped[len("subgraph "):].strip()
            name = re.match(r"([A-Za-z_][\w-]*)", rest)
            if name:
                candidates.add(name.group(1))
        else:
            candidates.update(NODE_DECL.findall(line))
            candidates.update(EDGE_SOURCE.findall(line))
            candidates.update(EDGE_TARGET.findall(line))

        assign = CLASS_ASSIGN.match(line)
        if assign:
            candidates.update(part.strip() for part in assign.group(1).split(","))
            candidates.add(assign.group(2))

        for name in candidates:
            if name in RESERVED:
                problems.append(
                    f"строка {offset + 1}: «{name}» — зарезервированное слово mermaid"
                )
    return problems


def main() -> int:
    failures = 0
    blocks = 0
    for md in sorted(ROOT.rglob("*.md")):
        if ".git" in md.parts:
            continue
        for start, lines in iter_blocks(md):
            blocks += 1
            for problem in check_block(lines):
                failures += 1
                rel = md.relative_to(ROOT)
                print(f"{rel} (блок со строки {start}) — {problem}")

    if failures:
        print(f"\nНайдено проблем: {failures} в {blocks} блоках")
        return 1
    print(f"Проверено блоков: {blocks} — зарезервированных идентификаторов нет")
    return 0


if __name__ == "__main__":
    sys.exit(main())
