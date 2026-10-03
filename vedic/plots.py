"""Plotly figure builders shared by the Streamlit UI and the HTML report."""
import datetime as dt
import zoneinfo

import pandas as pd
import plotly.express as px

from .constants import CLASSICAL_PLANETS, HOUSE_INFO, PLANET_COLORS, SIGNS
from .narratives import house_strength_label

STRENGTH_COLORS = {"Strong (≥30)": "#2E9E5B", "Average (28–29)": "#2D8BD0", "Weak (<28)": "#D8483E"}


def to_local(utc_naive, tz_name):
    return utc_naive.replace(tzinfo=dt.timezone.utc).astimezone(zoneinfo.ZoneInfo(tz_name)).replace(tzinfo=None)


def _rgba(hex_color, alpha):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def timeline_figure(dasha_rows, transit_rows, tz_name, window, title="Ashtakavarga Timing Cascade"):
    """Gantt chart: Dasha levels on top, then one row per transiting planet's Kakshya windows.

    window = (start, end) naive UTC; dasha bars are clipped to it (hover still shows the real dates).
    """
    fmt = "%d %b %Y, %H:%M"
    w_start, w_end = (to_local(w, tz_name) for w in window)
    records = []
    for r in dasha_rows:
        s, e = to_local(r["start"], tz_name), to_local(r["end"], tz_name)
        records.append({
            "Tier": r["level"], "Start": max(s, w_start), "End": min(e, w_end), "Legend": r["level"],
            "Hover": (f"<b>{r['label']}</b><br>{s:{fmt}} ➔ {e:{fmt}}<br>"
                      f"Lords: {r['lords']}"),
        })
    for t in transit_rows:
        s, e = to_local(t["start"], tz_name), to_local(t["end"], tz_name)
        muted = not t["bindu"]
        records.append({
            "Tier": f"{t['planet']} transit", "Start": s, "End": e,
            "Legend": f"{t['planet']} ({'muted' if muted else 'bindu'})",
            "Hover": (f"<b>{t['planet']} in {t['sign']} — {t['kakshya_lord']} kakshya ({t['kakshya']}/8)</b><br>"
                      f"{s:{fmt}} ➔ {e:{fmt}}<br>"
                      f"House from Lagna: {t['house']} · from Moon: {t['house_from_moon']}<br>"
                      f"SAV of sign: {t['sav']} · {t['planet']} BAV: {t['bav']}/8<br>"
                      f"Kakshya lord bindu: <b>{'Yes' if t['bindu'] else 'No'}</b> · Score: {t['score']}<br>"
                      f"<i>{t['rating']}</i>"),
        })
    df = pd.DataFrame(records)

    color_map = {"Mahadasha": PLANET_COLORS["Dasha"], "Antardasha": _rgba(PLANET_COLORS["Dasha"], 0.75),
                 "Pratyantardasha": _rgba(PLANET_COLORS["Dasha"], 0.5)}
    for p in CLASSICAL_PLANETS:
        color_map[f"{p} (bindu)"] = PLANET_COLORS[p]
        color_map[f"{p} (muted)"] = _rgba(PLANET_COLORS[p], 0.22)

    tiers = ["Mahadasha", "Antardasha", "Pratyantardasha"] + [f"{p} transit" for p in
                                                              ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]]
    tiers = [t for t in tiers if t in set(df["Tier"])]
    fig = px.timeline(df, x_start="Start", x_end="End", y="Tier", color="Legend",
                      color_discrete_map=color_map, custom_data=["Hover"],
                      category_orders={"Tier": tiers}, title=f"<b>{title}</b>")
    fig.update_traces(hovertemplate="%{customdata[0]}<extra></extra>", marker_line_width=0)
    fig.update_yaxes(title_text="")
    fig.update_xaxes(title_text=f"Time ({tz_name})", rangeslider_visible=True, range=[w_start, w_end])
    fig.update_layout(height=140 + 55 * len(tiers), margin=dict(l=10, r=10, t=60, b=10),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title_text=""))
    return fig


def sav_figure(sav_house):
    df = pd.DataFrame({
        "House": [HOUSE_INFO[h][0] for h in range(1, 13)],
        "SAV": sav_house,
        "Domain": [HOUSE_INFO[h][1] for h in range(1, 13)],
    })
    df["Strength"] = df["SAV"].apply(house_strength_label)
    fig = px.bar(df, x="House", y="SAV", color="Strength", text="SAV", color_discrete_map=STRENGTH_COLORS,
                 hover_data={"Domain": True}, category_orders={"Strength": list(STRENGTH_COLORS), "House": list(df["House"])},
                 title="<b>Sarvashtakavarga by House</b>")
    fig.add_hline(y=28, line_dash="dash", line_color="orange", annotation_text="Average baseline (28)",
                  annotation_position="top left")
    fig.update_traces(textposition="outside")
    fig.update_layout(xaxis_tickangle=-30, yaxis=dict(range=[0, max(sav_house) + 8]), height=430,
                      margin=dict(l=10, r=10, t=60, b=10), legend_title_text="")
    return fig


def bav_heatmap(av, asc_sign_idx):
    """Bindus per planet per house (house 1 = Ascendant sign)."""
    houses = [f"H{h + 1} {SIGNS[(asc_sign_idx + h) % 12][:3]}" for h in range(12)]
    z = [[av["bav"][p][(asc_sign_idx + h) % 12] for h in range(12)] for p in CLASSICAL_PLANETS]
    fig = px.imshow(z, x=houses, y=CLASSICAL_PLANETS, text_auto=True, zmin=0, zmax=8,
                    color_continuous_scale="Viridis", aspect="auto",
                    title="<b>Bhinna Ashtakavarga (bindus 0–8)</b>")
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=60, b=10), coloraxis_colorbar_title="Bindus")
    return fig


def strength_figure(rows):
    df = pd.DataFrame(rows)
    fig = px.bar(df, x="Planet", y="Strength Score", text="Strength Score", color="Status",
                 color_discrete_map={"Dominant & Strong": "#2E9E5B", "Balanced": "#2D8BD0", "Needs Support": "#D8483E"},
                 category_orders={"Planet": list(df["Planet"])}, title="<b>Dignity & Directional Strength</b>")
    fig.add_hline(y=50, line_dash="dash", line_color="gray", annotation_text="Baseline (50)")
    fig.update_layout(height=400, margin=dict(l=10, r=10, t=60, b=10), legend_title_text="")
    return fig
