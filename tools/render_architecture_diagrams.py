#!/usr/bin/env python3
"""Render architecture diagram PNGs used by the brief."""

from __future__ import annotations

from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "assets" / "architecture-diagrams"
FONT_PATH = Path("/System/Library/Fonts/STHeiti Medium.ttc")

INK = "#0f172a"
MUTED = "#64748b"
BLUE = "#165dff"
TEAL = "#0f766e"
GREEN = "#16a34a"
ORANGE = "#d97706"
RED = "#dc2626"
BORDER = "#bfd0e6"
BOX = "#f8fbff"
TEAL_BOX = "#eefcf8"
GREEN_BOX = "#f0fdf4"
ORANGE_BOX = "#fff7ed"
RED_BOX = "#fef2f2"


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size=size)


def text_lines(text: str, max_chars: int) -> list[str]:
    lines: list[str] = []
    for part in text.split("\n"):
        if not part:
            lines.append("")
            continue
        lines.extend(wrap(part, width=max_chars, break_long_words=False, replace_whitespace=False))
    return lines


def rounded(draw: ImageDraw.ImageDraw, box, fill, outline=BORDER, width=2, radius=18) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def pixel_wrap(text: str, max_width: int, font_obj: ImageFont.FreeTypeFont) -> list[str]:
    lines: list[str] = []
    for part in text.split("\n"):
        current = ""
        for ch in part:
            candidate = current + ch
            if current and draw_probe.textlength(candidate, font=font_obj) > max_width:
                lines.append(current)
                current = ch
            else:
                current = candidate
        if current:
            lines.append(current)
        if not part:
            lines.append("")
    return lines


draw_probe_image = Image.new("RGB", (1, 1), "white")
draw_probe = ImageDraw.Draw(draw_probe_image)


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    max_chars_or_px: int,
    font_obj: ImageFont.FreeTypeFont,
    fill=INK,
    line_gap=7,
) -> int:
    x, y = xy
    if max_chars_or_px > 80:
        lines = pixel_wrap(text, max_chars_or_px, font_obj)
    else:
        lines = text_lines(text, max_chars_or_px)
    for line in lines:
        draw.text((x, y), line, font=font_obj, fill=fill)
        y += font_obj.size + line_gap
    return y


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color=TEAL, width=4) -> None:
    draw.line([start, end], fill=color, width=width)
    x1, y1 = start
    x2, y2 = end
    if x2 >= x1:
        points = [(x2, y2), (x2 - 15, y2 - 9), (x2 - 15, y2 + 9)]
    else:
        points = [(x2, y2), (x2 + 15, y2 - 9), (x2 + 15, y2 + 9)]
    draw.polygon(points, fill=color)


def flow_box(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    body: str,
    accent=TEAL,
    fill=BOX,
) -> None:
    rounded(draw, box, fill=fill)
    x1, y1, _, _ = box
    draw.rectangle((x1, y1 + 2, x1 + 8, box[3] - 2), fill=accent)
    draw.text((x1 + 24, y1 + 20), title, font=font(28), fill=INK)
    draw_wrapped(draw, (x1 + 24, y1 + 62), body, box[2] - box[0] - 52, font(20), fill=MUTED, line_gap=8)


def render_agent_value() -> None:
    img = Image.new("RGB", (1900, 1200), "white")
    draw = ImageDraw.Draw(img)
    draw.text((42, 30), "Agent 价值闭环与可信网络位置", font=font(42), fill=INK)
    draw.text((42, 88), "Agent 不理解源表，而是发现产品、申请授权、编排调用、适配接口变化并验证执行凭证。", font=font(24), fill=MUTED)

    boxes = [
        ("发现", "读取产品目录\nOSDK / MCP 描述", TEAL, TEAL_BOX),
        ("授权", "申请 entitlement\n不绕过 Policy", TEAL, BOX),
        ("编排", "调用产品动作\n不接触 SQL", TEAL, BOX),
        ("适配", "读取新 OSDK\n避开收缩接口", TEAL, BOX),
        ("验证", "校验 receipt\n确认 hash 和版本", TEAL, BOX),
    ]
    x = 42
    y = 150
    w = 330
    h = 170
    gap = 30
    coords = []
    for title, body, accent, fill in boxes:
        box = (x, y, x + w, y + h)
        flow_box(draw, box, title, body, accent, fill)
        coords.append(box)
        x += w + gap
    for left, right in zip(coords, coords[1:]):
        arrow(draw, (left[2] + 8, y + h // 2), (right[0] - 10, y + h // 2))

    draw.text((42, 375), "Agent 在可信网络里的位置", font=font(32), fill=INK)
    node_y = 470
    node_h = 120
    nodes = [
        ((42, node_y, 330, node_y + node_h), "业务用户", "自然语言目标 / 业务对象", BLUE),
        ((410, node_y - 28, 780, node_y + node_h + 28), "Agent Workload", "计划、选择产品、申请授权、编排调用", TEAL),
        ((870, node_y - 28, 1240, node_y + node_h + 28), "Product OSDK", "命名 Query/Action，不暴露底层表", GREEN),
        ((1330, node_y - 28, 1858, node_y + node_h + 28), "可信数据空间网关", "身份、签名、合约、路由、审计", ORANGE),
    ]
    for box, title, body, accent in nodes:
        flow_box(draw, box, title, body, accent, BOX)
    for left, right in zip(nodes, nodes[1:]):
        arrow(draw, (left[0][2] + 12, (left[0][1] + left[0][3]) // 2), (right[0][0] - 12, (right[0][1] + right[0][3]) // 2), color=TEAL)

    runtime = (1330, 725, 1858, 845)
    policy = (870, 725, 1240, 845)
    flow_box(draw, runtime, "Provider Runtime", "本地映射、本地计算、原始数据不出域", TEAL, BOX)
    flow_box(draw, policy, "Policy / Entitlement", "用途、期限、粒度、撤销状态", RED, BOX)
    arrow(draw, (1585, 590), (1585, 712), color=ORANGE)
    arrow(draw, (1320, 785), (1252, 785), color=RED)

    callout = (42, 930, 1858, 1125)
    rounded(draw, callout, fill=TEAL_BOX, outline="#99d8cf", radius=18)
    draw.text((78, 960), "这带来的改进", font=font(28), fill=TEAL)
    bullets = [
        "Agent 不再被迫理解源表，而是面向可信数据产品编排。",
        "每次调用都有授权和凭证，便于审计、撤销和复核。",
        "本体变化会反映为 OSDK 接口变化，Agent 可以自动适配新的安全边界。",
    ]
    by = 1010
    for item in bullets:
        draw.text((82, by), "•", font=font(26), fill=TEAL)
        draw.text((118, by), item, font=font(23), fill=INK)
        by += 42

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    img.save(OUT_DIR / "agent-value-framework.png")


def render_framework_structure() -> None:
    img = Image.new("RGB", (1680, 1740), "white")
    draw = ImageDraw.Draw(img)
    draw.text((42, 30), "动态本体 OSDK 可信数据产品框架结构", font=font(42), fill=INK)
    draw.text((42, 88), "从数据域资产到动态本体，再编译为受控 OSDK/MCP，并经可信网络进入 Runtime 执行。", font=font(24), fill=MUTED)

    layers = [
        ("1. 数据域资产", "结构化表、非结构化文档、GIS、监测摘要、历史隐患", BOX),
        ("2. DOIR / 动态本体 Registry", "SourceDataset、ObjectType、PropertyType、LinkType、ActionType", BOX),
        ("3. Product Compiler", "产品投影、分类分级、质量门槛、Runtime 能力声明", TEAL_BOX),
        ("4. Generated Interfaces", "Python/TypeScript OSDK、MCP Tool、OpenAPI、产品 Schema", GREEN_BOX),
        ("5. Trusted Execution Plane", "可信数据空间网关、Policy、Entitlement、Application Host、Provider Runtime", ORANGE_BOX),
        ("6. Verification / Audit", "ExecutionReceipt、hash chain、签名、Receipt Verifier", RED_BOX),
    ]
    x1, x2 = 42, 1638
    y = 155
    h = 112
    gap = 30
    prev_center = None
    for title, body, fill in layers:
        box = (x1, y, x2, y + h)
        rounded(draw, box, fill=fill, radius=18)
        draw.text((x1 + 32, y + 32), title, font=font(30), fill=INK)
        draw_wrapped(draw, (x1 + 500, y + 36), body, 55, font(23), fill=MUTED)
        center = ((x1 + x2) // 2, y + h // 2)
        if prev_center:
            arrow(draw, (prev_center[0], prev_center[1] + h // 2 - 6), (center[0], y - 8), color=TEAL)
        prev_center = center
        y += h + gap

    draw.text((42, y + 10), "两种 OSDK 部署形态", font=font(32), fill=INK)
    y += 70
    cards = [
        ((42, y, 792, y + 295), "客户侧 OSDK Workload", ["客户 App / Agent", "Product OSDK", "可信数据空间网关", "Provider Runtime"]),
        ((888, y, 1638, y + 295), "我方独立 OSDK 沙箱", ["客户代码包", "per-customer sandbox", "可信数据空间网关", "Provider Runtime"]),
    ]
    for card, title, steps in cards:
        rounded(draw, card, fill="white", radius=18)
        draw.text((card[0] + 30, card[1] + 28), title, font=font(30), fill=TEAL)
        sx = card[0] + 35
        sy = card[1] + 112
        step_w = 150
        step_h = 86
        step_boxes = []
        for step in steps:
            sbox = (sx, sy, sx + step_w, sy + step_h)
            rounded(draw, sbox, fill=BOX, radius=14)
            draw_wrapped(draw, (sx + 16, sy + 20), step, 12, font(20), fill=INK, line_gap=5)
            step_boxes.append(sbox)
            sx += step_w + 48
        for left, right in zip(step_boxes, step_boxes[1:]):
            arrow(draw, (left[2] + 8, sy + step_h // 2), (right[0] - 8, sy + step_h // 2), color=TEAL)
        draw_wrapped(
            draw,
            (card[0] + 35, card[1] + 225),
            "共同约束：OSDK workload 不直连数据库或 Runtime 内网，所有调用都带签名、授权和审计 envelope。",
            42,
            font(21),
            fill=MUTED,
        )

    callout = (42, 1432, 1638, 1660)
    rounded(draw, callout, fill=TEAL_BOX, outline="#99d8cf", radius=18)
    draw.text((78, 1464), "工程落地真正难点", font=font(30), fill=TEAL)
    bullets = [
        "动态本体编译正确性：不能把 COMPUTE_ONLY、HIDDEN 字段漏生成到外部接口。",
        "Runtime Binding 一致性：不同 Provider 的异构数据要返回同一产品语义和质量口径。",
        "可信网络强约束：网关、Policy、沙箱、Receipt 必须形成闭环，而不是只做 SDK 包装。",
    ]
    by = 1516
    for item in bullets:
        draw.text((82, by), "•", font=font(25), fill=TEAL)
        draw.text((118, by), item, font=font(22), fill=INK)
        by += 38

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    img.save(OUT_DIR / "framework-structure.png")


def render_upstream_skill_boundary() -> None:
    img = Image.new("RGB", (1900, 1260), "white")
    draw = ImageDraw.Draw(img)
    draw.text((42, 30), "上游动态本体平台、Agent Skill 与 OSDK 产品层分工", font=font(40), fill=INK)
    draw.text(
        (42, 86),
        "OntoFlow 或其他动态本体平台负责内部生产，我们把可对外服务的能力编译成受控 Product OSDK，并由 awiki.ai Agent 网络协作运营。",
        font=font(23),
        fill=MUTED,
    )
    legend_y = 124
    legend_items = [("内部生产流", TEAL), ("Agent skill 调用", BLUE), ("产品编译输入", ORANGE)]
    legend_x = 42
    for label, color in legend_items:
        draw.line((legend_x, legend_y + 10, legend_x + 44, legend_y + 10), fill=color, width=5)
        draw.polygon([(legend_x + 44, legend_y + 10), (legend_x + 34, legend_y + 4), (legend_x + 34, legend_y + 16)], fill=color)
        draw.text((legend_x + 58, legend_y), label, font=font(18), fill=MUTED)
        legend_x += 210

    col_y = 172
    col_h = 840
    col_w = 540
    gap = 65
    columns = [
        ((42, col_y, 42 + col_w, col_y + col_h), "数据提供方内部生产域", TEAL, TEAL_BOX),
        ((42 + col_w + gap, col_y, 42 + col_w * 2 + gap, col_y + col_h), "awiki.ai Agent 网络", BLUE, BOX),
        ((42 + col_w * 2 + gap * 2, col_y, 42 + col_w * 3 + gap * 2, col_y + col_h), "可信数据产品层", ORANGE, ORANGE_BOX),
    ]
    for box, title, accent, fill in columns:
        rounded(draw, box, fill=fill, outline=BORDER, radius=22)
        draw.text((box[0] + 28, box[1] + 24), title, font=font(30), fill=accent)

    def inner_card(box, offset_y, title, body, accent=TEAL, fill="white"):
        x1, y1, x2, _ = box
        card = (x1 + 30, y1 + offset_y, x2 - 30, y1 + offset_y + 145)
        rounded(draw, card, fill=fill, outline=BORDER, radius=16)
        draw.text((card[0] + 22, card[1] + 18), title, font=font(24), fill=accent)
        draw_wrapped(draw, (card[0] + 22, card[1] + 58), body, card[2] - card[0] - 44, font(19), fill=MUTED, line_gap=7)
        return card

    provider = columns[0][0]
    awiki = columns[1][0]
    product = columns[2][0]

    catalog = inner_card(provider, 92, "数据目录 / 湖仓 / GIS / 图数据库", "源表、文档、空间数据、图关系、规则和监测摘要。")
    ontology = inner_card(provider, 270, "OntoFlow / 动态本体平台", "建模、映射、实例化、关系编排和内部 action。")
    quality = inner_card(provider, 448, "质量 / 分类分级 / 血缘", "检查覆盖率、敏感级别、数据窗口和可发布条件。")
    doir = inner_card(provider, 626, "DOIR / Product Projection", "输出中间表示和产品投影，作为 OSDK 编译输入。", accent=GREEN)

    ops = inner_card(awiki, 92, "数据运营 Agent", "有受控全栈工具箱：目录、建模、质检、编译、审计。", accent=BLUE)
    skills = inner_card(awiki, 270, "Skill Registry", "把 OntoFlow、质量检查、编译、发布、审计注册成可调用 skill。", accent=BLUE)
    human = inner_card(awiki, 448, "人工审批 / 复核", "发布、授权、外发、生产绑定变更必须人审。", accent=RED, fill=RED_BOX)
    notices = inner_card(awiki, 626, "异步协作通知", "审批、质检、执行、Receipt 验证通过 Agent 网络回传。", accent=BLUE)

    compiler = inner_card(product, 92, "Product Compiler", "按用途、授权、分类分级和质量门槛裁剪产品接口。", accent=ORANGE)
    osdk = inner_card(product, 270, "OSDK / MCP / OpenAPI", "只暴露命名动作，不暴露底层表、SQL、文件和连接串。", accent=GREEN, fill=GREEN_BOX)
    gateway = inner_card(product, 448, "Gateway / Policy / Runtime", "身份、签名、路由、授权校验和数据域内执行。", accent=ORANGE)
    receipt = inner_card(product, 626, "Receipt / Audit", "记录授权、应用、本体、产品、Runtime、输入输出 hash 和签名。", accent=RED, fill=RED_BOX)

    for left, right in [
        (catalog, ontology),
        (ontology, quality),
        (quality, doir),
        (ops, skills),
        (skills, human),
        (human, notices),
        (compiler, osdk),
        (osdk, gateway),
        (gateway, receipt),
    ]:
        arrow(draw, ((left[0] + left[2]) // 2, left[3] + 8), ((right[0] + right[2]) // 2, right[1] - 8), color=TEAL, width=3)

    arrow(draw, (doir[2] + 16, (doir[1] + doir[3]) // 2), (compiler[0] - 16, (compiler[1] + compiler[3]) // 2), color=ORANGE, width=4)
    arrow(draw, (skills[0] - 16, (skills[1] + skills[3]) // 2), (ontology[2] + 16, (ontology[1] + ontology[3]) // 2), color=BLUE, width=4)
    arrow(draw, (skills[2] + 16, (skills[1] + skills[3]) // 2), (compiler[0] - 16, (compiler[1] + compiler[3]) // 2), color=BLUE, width=4)
    arrow(draw, (notices[2] + 16, (notices[1] + notices[3]) // 2), (receipt[0] - 16, (receipt[1] + receipt[3]) // 2), color=BLUE, width=4)

    callout = (42, 1060, 1858, 1204)
    rounded(draw, callout, fill=TEAL_BOX, outline="#99d8cf", radius=18)
    draw.text((78, 1090), "核心判断", font=font(28), fill=TEAL)
    draw_wrapped(
        draw,
        (78, 1134),
        "我们不重做所有上游平台。我们的价值在于把上游动态本体和数据平台能力，编译成可授权、可调用、可审计、可验证的数据产品，并让 Agent 网络围绕这些产品完成交易和运营。",
        callout[2] - callout[0] - 120,
        font(22),
        fill=INK,
        line_gap=8,
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    img.save(OUT_DIR / "upstream-ontology-skill-boundary.png")


def main() -> None:
    render_agent_value()
    render_framework_structure()
    render_upstream_skill_boundary()
    print(OUT_DIR / "agent-value-framework.png")
    print(OUT_DIR / "framework-structure.png")
    print(OUT_DIR / "upstream-ontology-skill-boundary.png")


if __name__ == "__main__":
    main()
