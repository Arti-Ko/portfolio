"""Экспорт BPMN-моделей в Mermaid — для превью прямо в markdown на GitHub.

Источник истины — те же модели, что и для .bpmn, поэтому схема в документе
не может разойтись с файлом для BPMN-моделлера.
"""
from __future__ import annotations

from bpmn_gen import End, Gateway, Model, Start, Task

# Имена классов не должны совпадать с ключевыми словами mermaid (start, end).
STYLE = {
    "evStart": "fill:#1f7a3f,stroke:#0f4523,color:#ffffff",
    "evEnd": "fill:#8a1f1f,stroke:#4a0f0f,color:#ffffff",
    "gw": "fill:#e0a800,stroke:#8a6800,color:#1a1a1a",
    "userTask": "fill:#2b5d8a,stroke:#143349,color:#ffffff",
    "svcTask": "fill:#3a3f4b,stroke:#1b1e24,color:#ffffff",
    "msgTask": "fill:#5a3a7a,stroke:#2e1c40,color:#ffffff",
}


def _label(text: str) -> str:
    return text.replace("\n", "<br/>").replace('"', "'")


def _shape(node) -> str:
    label = _label(node.name)
    if isinstance(node, (Start, End)):
        return f'{node.id}(("{label}"))'
    if isinstance(node, Gateway):
        return f'{node.id}{{"{label}"}}'
    return f'{node.id}["{label}"]'


def _class_of(node) -> str:
    if isinstance(node, Start):
        return "evStart"
    if isinstance(node, End):
        return "evEnd"
    if isinstance(node, Gateway):
        return "gw"
    if isinstance(node, Task):
        if node.kind in ("user", "manual"):
            return "userTask"
        if node.kind in ("send", "receive"):
            return "msgTask"
    return "svcTask"


def to_mermaid(model: Model) -> str:
    lines = ["flowchart LR"]
    by_lane: dict[str, list] = {lane.id: [] for lane in model.lanes}
    for node in model.nodes:
        by_lane[node.lane].append(node)

    for lane in model.lanes:
        lines.append(f'    subgraph {lane.id}["{lane.name}"]')
        lines.append("        direction LR")
        for node in sorted(by_lane[lane.id], key=lambda n: (n.col, n.row)):
            lines.append(f"        {_shape(node)}")
        lines.append("    end")

    for flow in model.flows:
        if flow.name:
            lines.append(f'    {flow.source} -- "{_label(flow.name)}" --> {flow.target}')
        else:
            lines.append(f"    {flow.source} --> {flow.target}")

    groups: dict[str, list[str]] = {}
    for node in model.nodes:
        groups.setdefault(_class_of(node), []).append(node.id)
    for cls, style in STYLE.items():
        if cls in groups:
            lines.append(f"    classDef {cls} {style}")
    for cls, ids in groups.items():
        lines.append(f"    class {','.join(ids)} {cls}")

    return "\n".join(lines)
