"""Генератор BPMN 2.0 XML с диаграммной частью (BPMNDI).

Модели описываются декларативно — координаты считаются автоматически по сетке
«дорожка × колонка». Результат открывается в Camunda Modeler, bpmn.io и Visual
Paradigm без ручной доработки раскладки.

Использование:
    from bpmn_gen import Model, Lane, Start, End, Task, Gateway, render
    xml = render(model)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from xml.sax.saxutils import escape

# Геометрия сетки
COL_WIDTH = 190
ROW_HEIGHT = 130
POOL_X = 160
POOL_Y = 80
LANE_LABEL_W = 30
TASK_W, TASK_H = 120, 80
EVENT_SIZE = 36
GATEWAY_SIZE = 50
LANE_PAD = 25

TASK_TAGS = {
    "task": "task",
    "user": "userTask",
    "service": "serviceTask",
    "send": "sendTask",
    "receive": "receiveTask",
    "script": "scriptTask",
    "business": "businessRuleTask",
    "manual": "manualTask",
}

GATEWAY_TAGS = {
    "exclusive": "exclusiveGateway",
    "parallel": "parallelGateway",
    "inclusive": "inclusiveGateway",
    "event": "eventBasedGateway",
}


@dataclass
class Node:
    id: str
    name: str
    lane: str
    col: int
    row: int = 0

    @property
    def size(self) -> tuple[int, int]:
        return TASK_W, TASK_H


@dataclass
class Task(Node):
    kind: str = "task"


@dataclass
class Gateway(Node):
    kind: str = "exclusive"

    @property
    def size(self) -> tuple[int, int]:
        return GATEWAY_SIZE, GATEWAY_SIZE


@dataclass
class Start(Node):
    kind: str = "none"  # none | message | timer

    @property
    def size(self) -> tuple[int, int]:
        return EVENT_SIZE, EVENT_SIZE


@dataclass
class End(Node):
    kind: str = "none"  # none | message | terminate | error

    @property
    def size(self) -> tuple[int, int]:
        return EVENT_SIZE, EVENT_SIZE


@dataclass
class Intermediate(Node):
    kind: str = "timer"  # timer | message

    @property
    def size(self) -> tuple[int, int]:
        return EVENT_SIZE, EVENT_SIZE


@dataclass
class Flow:
    source: str
    target: str
    name: str = ""


@dataclass
class Lane:
    id: str
    name: str
    rows: int = 1


@dataclass
class Model:
    id: str
    name: str
    pool_name: str
    lanes: list[Lane]
    nodes: list[Node]
    flows: list[Flow] = field(default_factory=list)
    documentation: str = ""


class Layout:
    """Считает координаты узлов и точки маршрутов связей."""

    def __init__(self, model: Model):
        self.model = model
        self.by_id = {n.id: n for n in model.nodes}
        self.lane_top: dict[str, int] = {}
        self.lane_height: dict[str, int] = {}

        y = POOL_Y
        for lane in model.lanes:
            height = lane.rows * ROW_HEIGHT + LANE_PAD * 2
            self.lane_top[lane.id] = y
            self.lane_height[lane.id] = height
            y += height
        self.pool_height = y - POOL_Y

        max_col = max((n.col for n in model.nodes), default=0)
        self.pool_width = LANE_LABEL_W + (max_col + 1) * COL_WIDTH + 40

    def bounds(self, node: Node) -> tuple[int, int, int, int]:
        w, h = node.size
        cell_x = POOL_X + LANE_LABEL_W + node.col * COL_WIDTH
        x = cell_x + (COL_WIDTH - w) // 2
        cell_y = self.lane_top[node.lane] + LANE_PAD + node.row * ROW_HEIGHT
        y = cell_y + (ROW_HEIGHT - h) // 2
        return x, y, w, h

    def center(self, node: Node) -> tuple[int, int]:
        x, y, w, h = self.bounds(node)
        return x + w // 2, y + h // 2

    def waypoints(self, flow: Flow) -> list[tuple[int, int]]:
        src, dst = self.by_id[flow.source], self.by_id[flow.target]
        sx, sy, sw, sh = self.bounds(src)
        tx, ty, tw, th = self.bounds(dst)
        scx, scy = sx + sw // 2, sy + sh // 2
        tcx, tcy = tx + tw // 2, ty + th // 2

        if tx > sx + sw:  # цель правее — идём вперёд
            if scy == tcy:
                return [(sx + sw, scy), (tx, tcy)]
            mid = (sx + sw + tx) // 2
            return [(sx + sw, scy), (mid, scy), (mid, tcy), (tx, tcy)]

        if tx + tw < sx:  # цель левее — возвратная петля снизу
            below = max(sy + sh, ty + th) + 45
            return [(scx, sy + sh), (scx, below), (tcx, below), (tcx, ty + th)]

        # одна колонка — вертикальная связь
        if tcy > scy:
            return [(scx, sy + sh), (tcx, ty)]
        return [(scx, sy), (tcx, ty + th)]


def _event_definition(kind: str, indent: str) -> str:
    tags = {
        "message": "messageEventDefinition",
        "timer": "timerEventDefinition",
        "terminate": "terminateEventDefinition",
        "error": "errorEventDefinition",
        "signal": "signalEventDefinition",
    }
    tag = tags.get(kind)
    return f"\n{indent}<bpmn:{tag} />" if tag else ""


def _node_xml(node: Node, incoming: list[str], outgoing: list[str]) -> str:
    ind = "      "
    refs = "".join(f"\n{ind}  <bpmn:incoming>{f}</bpmn:incoming>" for f in incoming)
    refs += "".join(f"\n{ind}  <bpmn:outgoing>{f}</bpmn:outgoing>" for f in outgoing)

    if isinstance(node, Task):
        tag = TASK_TAGS.get(node.kind, "task")
    elif isinstance(node, Gateway):
        tag = GATEWAY_TAGS.get(node.kind, "exclusiveGateway")
    elif isinstance(node, Start):
        tag = "startEvent"
    elif isinstance(node, End):
        tag = "endEvent"
    else:
        tag = "intermediateCatchEvent"

    body = refs
    if isinstance(node, (Start, End, Intermediate)):
        body += _event_definition(node.kind, ind + "  ")

    attrs = f'id="{node.id}" name="{escape(node.name)}"'
    if not body:
        return f"{ind}<bpmn:{tag} {attrs} />"
    return f"{ind}<bpmn:{tag} {attrs}>{body}\n{ind}</bpmn:{tag}>"


def render(model: Model) -> str:
    layout = Layout(model)
    flow_ids = {}
    for idx, flow in enumerate(model.flows, start=1):
        flow_ids[(flow.source, flow.target, flow.name)] = f"Flow_{idx:02d}"

    incoming: dict[str, list[str]] = {n.id: [] for n in model.nodes}
    outgoing: dict[str, list[str]] = {n.id: [] for n in model.nodes}
    for flow in model.flows:
        fid = flow_ids[(flow.source, flow.target, flow.name)]
        outgoing[flow.source].append(fid)
        incoming[flow.target].append(fid)

    lane_nodes: dict[str, list[str]] = {lane.id: [] for lane in model.lanes}
    for node in model.nodes:
        lane_nodes[node.lane].append(node.id)

    proc_id = f"Process_{model.id}"
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"',
        '                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"',
        '                  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"',
        '                  xmlns:di="http://www.omg.org/spec/DD/20100524/DI"',
        '                  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
        f'                  id="Definitions_{model.id}"',
        '                  targetNamespace="http://bpmn.io/schema/bpmn"',
        '                  exporter="sa-portfolio/tools/bpmn_gen.py" exporterVersion="1.0">',
        f'  <bpmn:collaboration id="Collaboration_{model.id}">',
        f'    <bpmn:participant id="Participant_{model.id}" '
        f'name="{escape(model.pool_name)}" processRef="{proc_id}" />',
        '  </bpmn:collaboration>',
        f'  <bpmn:process id="{proc_id}" name="{escape(model.name)}" isExecutable="false">',
    ]

    if model.documentation:
        parts.append(f'    <bpmn:documentation>{escape(model.documentation)}</bpmn:documentation>')

    parts.append(f'    <bpmn:laneSet id="LaneSet_{model.id}">')
    for lane in model.lanes:
        parts.append(f'      <bpmn:lane id="{lane.id}" name="{escape(lane.name)}">')
        for nid in lane_nodes[lane.id]:
            parts.append(f'        <bpmn:flowNodeRef>{nid}</bpmn:flowNodeRef>')
        parts.append('      </bpmn:lane>')
    parts.append('    </bpmn:laneSet>')

    for node in model.nodes:
        parts.append(_node_xml(node, incoming[node.id], outgoing[node.id]))

    for flow in model.flows:
        fid = flow_ids[(flow.source, flow.target, flow.name)]
        name_attr = f' name="{escape(flow.name)}"' if flow.name else ""
        parts.append(
            f'      <bpmn:sequenceFlow id="{fid}"{name_attr} '
            f'sourceRef="{flow.source}" targetRef="{flow.target}" />'
        )
    parts.append('  </bpmn:process>')

    # --- Диаграммная часть ---
    parts.append(f'  <bpmndi:BPMNDiagram id="Diagram_{model.id}">')
    parts.append(
        f'    <bpmndi:BPMNPlane id="Plane_{model.id}" bpmnElement="Collaboration_{model.id}">'
    )
    parts.append(f'      <bpmndi:BPMNShape id="Shape_Participant_{model.id}" '
                 f'bpmnElement="Participant_{model.id}" isHorizontal="true">')
    parts.append(f'        <dc:Bounds x="{POOL_X}" y="{POOL_Y}" '
                 f'width="{layout.pool_width}" height="{layout.pool_height}" />')
    parts.append('      </bpmndi:BPMNShape>')

    for lane in model.lanes:
        parts.append(f'      <bpmndi:BPMNShape id="Shape_{lane.id}" '
                     f'bpmnElement="{lane.id}" isHorizontal="true">')
        parts.append(f'        <dc:Bounds x="{POOL_X + LANE_LABEL_W}" '
                     f'y="{layout.lane_top[lane.id]}" '
                     f'width="{layout.pool_width - LANE_LABEL_W}" '
                     f'height="{layout.lane_height[lane.id]}" />')
        parts.append('      </bpmndi:BPMNShape>')

    for node in model.nodes:
        x, y, w, h = layout.bounds(node)
        parts.append(f'      <bpmndi:BPMNShape id="Shape_{node.id}" bpmnElement="{node.id}">')
        parts.append(f'        <dc:Bounds x="{x}" y="{y}" width="{w}" height="{h}" />')
        if isinstance(node, (Start, End, Intermediate, Gateway)) and node.name:
            parts.append('        <bpmndi:BPMNLabel>')
            parts.append(f'          <dc:Bounds x="{x - 35}" y="{y + h + 6}" '
                         f'width="{w + 70}" height="27" />')
            parts.append('        </bpmndi:BPMNLabel>')
        parts.append('      </bpmndi:BPMNShape>')

    for flow in model.flows:
        fid = flow_ids[(flow.source, flow.target, flow.name)]
        pts = layout.waypoints(flow)
        parts.append(f'      <bpmndi:BPMNEdge id="Edge_{fid}" bpmnElement="{fid}">')
        for px, py in pts:
            parts.append(f'        <di:waypoint x="{px}" y="{py}" />')
        if flow.name:
            lx, ly = pts[len(pts) // 2]
            parts.append('        <bpmndi:BPMNLabel>')
            parts.append(f'          <dc:Bounds x="{lx - 20}" y="{ly - 24}" '
                         f'width="90" height="18" />')
            parts.append('        </bpmndi:BPMNLabel>')
        parts.append('      </bpmndi:BPMNEdge>')

    parts.append('    </bpmndi:BPMNPlane>')
    parts.append('  </bpmndi:BPMNDiagram>')
    parts.append('</bpmn:definitions>')
    return "\n".join(parts) + "\n"
