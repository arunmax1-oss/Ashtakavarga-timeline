"""SVG drawings of a chart in South Indian (fixed signs) or North Indian (fixed houses) style."""
import html

from .constants import PLANET_COLORS, SIGNS

ABBR = {"Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me", "Jupiter": "Ju", "Venus": "Ve",
        "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke"}
STROKE, TEXT, MUTED, BG, ASC = "#8892a6", "#e6e6e6", "#8a93a3", "#161b22", "#F5C242"

# South Indian grid: (row, col) of each sign, Pisces at top-left, running clockwise.
SOUTH_CELLS = {11: (0, 0), 0: (0, 1), 1: (0, 2), 2: (0, 3), 3: (1, 3), 4: (2, 3),
               5: (3, 3), 6: (3, 2), 7: (3, 1), 8: (3, 0), 9: (2, 0), 10: (1, 0)}


def _labels(chart, positions, show_degrees):
    """{sign index: [(text, colour)]} for every planet in `positions` (a {body: sign} map)."""
    out = {}
    for name, sign in positions.items():
        if name == "Ascendant":
            continue
        p = chart["planets"][name]
        text = ABBR[name] + ("℞" if p.get("retrograde") else "")
        if show_degrees:
            text += f" {int(p['degree'])}°"
        out.setdefault(sign, []).append((text, PLANET_COLORS[name]))
    return out


def _text(x, y, s, size=13, color=TEXT, weight="normal", anchor="middle"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{color}" font-weight="{weight}" '
            f'text-anchor="{anchor}" font-family="sans-serif">{html.escape(s)}</text>')


def _stack(x, y, items, size=13, line=16):
    """Planet labels stacked around (x, y), two per line when crowded."""
    rows = [items[i:i + 2] for i in range(0, len(items), 2)] if len(items) > 3 else [[it] for it in items]
    top = y - (len(rows) - 1) * line / 2
    out = []
    for r, row in enumerate(rows):
        if len(row) == 1:
            out.append(_text(x, top + r * line, row[0][0], size, row[0][1], "bold"))
        else:
            out.append(_text(x - 22, top + r * line, row[0][0], size, row[0][1], "bold"))
            out.append(_text(x + 22, top + r * line, row[1][0], size, row[1][1], "bold"))
    return "".join(out)


def south_indian_svg(chart, positions, title="", show_degrees=True, size=420):
    asc_sign = positions["Ascendant"]
    labels = _labels(chart, positions, show_degrees)
    c = size / 4
    parts = [f'<svg viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg" '
             f'style="width:100%;max-width:{size}px;aspect-ratio:1;height:auto;background:{BG};border-radius:8px">']
    for sign, (r, col) in SOUTH_CELLS.items():
        x, y = col * c, r * c
        parts.append(f'<rect x="{x}" y="{y}" width="{c}" height="{c}" fill="none" stroke="{STROKE}"/>')
        parts.append(_text(x + 6, y + 15, SIGNS[sign][:3], 11, MUTED, anchor="start"))
        if sign == asc_sign:
            parts.append(f'<rect x="{x + 2}" y="{y + 2}" width="{c - 4}" height="{c - 4}" fill="none" '
                         f'stroke="{ASC}" stroke-width="2" rx="3"/>')
            parts.append(_text(x + c - 6, y + 15, "Asc", 11, ASC, "bold", "end"))
        if sign in labels:
            parts.append(_stack(x + c / 2, y + c / 2 + 8, labels[sign]))
    parts.append(f'<rect x="{c}" y="{c}" width="{2 * c}" height="{2 * c}" fill="none" stroke="{STROKE}"/>')
    parts.append(_text(size / 2, size / 2 - 4, title, 15, TEXT, "bold"))
    parts.append(_text(size / 2, size / 2 + 16, f"Lagna {SIGNS[asc_sign]}", 12, MUTED))
    parts.append("</svg>")
    return "".join(parts)


def north_indian_svg(chart, positions, title="", show_degrees=True, size=420):
    s = size
    asc_sign = positions["Ascendant"]
    labels = _labels(chart, positions, show_degrees)
    q = s / 4
    T, R, B, L, C = (s / 2, 0), (s, s / 2), (s / 2, s), (0, s / 2), (s / 2, s / 2)
    TL, TR, BR, BL = (0, 0), (s, 0), (s, s), (0, s)
    a, b, c, d = (q, q), (3 * q, q), (3 * q, 3 * q), (q, 3 * q)  # inner diamond corners
    houses = {1: [T, b, C, a], 2: [TL, T, a], 3: [TL, a, L], 4: [L, a, C, d], 5: [L, d, BL], 6: [BL, d, B],
              7: [B, d, C, c], 8: [B, c, BR], 9: [BR, c, R], 10: [R, c, C, b], 11: [R, b, TR], 12: [TR, b, T]}
    parts = [f'<svg viewBox="0 0 {s} {s}" xmlns="http://www.w3.org/2000/svg" '
             f'style="width:100%;max-width:{s}px;aspect-ratio:1;height:auto;background:{BG};border-radius:8px">',
             f'<rect x="0" y="0" width="{s}" height="{s}" fill="none" stroke="{STROKE}"/>',
             f'<line x1="0" y1="0" x2="{s}" y2="{s}" stroke="{STROKE}"/>',
             f'<line x1="{s}" y1="0" x2="0" y2="{s}" stroke="{STROKE}"/>',
             f'<polygon points="{T[0]},{T[1]} {R[0]},{R[1]} {B[0]},{B[1]} {L[0]},{L[1]}" fill="none" stroke="{STROKE}"/>']
    inner = [a, b, c, d]

    def lerp(p, q, t):
        return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)

    for h, poly in houses.items():
        sign = (asc_sign + h - 1) % 12
        centroid = (sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly))
        if len(poly) == 4:  # kite: number toward the centre, planets toward the outer edge
            num = lerp(centroid, C, 0.62)
            body = lerp(centroid, poly[0], 0.12)
        else:  # triangle: number near the inner-diamond corner, planets at the centre of the triangle
            corner = next(p for p in poly if p in inner)
            num = lerp(corner, centroid, 0.35)
            side = h in (3, 5, 9, 11)  # tall narrow triangles on the left and right edges
            body = centroid if side else lerp(centroid, (centroid[0], 0 if centroid[1] < s / 2 else s), 0.25)
        parts.append(_text(num[0], num[1] + 4, str(sign + 1), 11, ASC if h == 1 else MUTED,
                           "bold" if h == 1 else "normal"))
        if sign in labels:
            parts.append(_stack(body[0], body[1] + 4, labels[sign], 12 if len(poly) == 3 else 13, 14))
    parts.append("</svg>")
    return "".join(parts)
