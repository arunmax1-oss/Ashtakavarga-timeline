"""Birth-time sensitivity: how far the birth time can move before key chart factors change."""
from .chart import ascendant_longitude, navamsha_sign, planet_longitude, set_ayanamsha
from .constants import DASHA_LORDS, DASHA_YEARS, NAKSHATRA_SPAN, NAKSHATRAS, SIGNS

FACTORS = {
    "Lagna (Ascendant) sign": "Houses, house lords, yogas, remedies and Bhrigu years all shift.",
    "Navamsa (D9) Lagna": "The D9 chart (marriage, inner strength) and Saptavarga strength change.",
    "Moon sign": "Moon-based readings, Sade Sati phases and weekly Chandra Bala change.",
    "Moon nakshatra": "The Dasha sequence and weekly Tara Bala change.",
}


def _values(chart, jd):
    asc = ascendant_longitude(jd, chart["lat"], chart["lon"])
    moon, _ = planet_longitude(jd, "Moon")
    return {
        "Lagna (Ascendant) sign": SIGNS[int(asc // 30)],
        "Navamsa (D9) Lagna": SIGNS[navamsha_sign(asc)],
        "Moon sign": SIGNS[int(moon // 30)],
        "Moon nakshatra": NAKSHATRAS[int(moon // NAKSHATRA_SPAN)],
    }


def _first_change(chart, factor, direction, limit_minutes):
    """Minutes until `factor` changes when the birth time moves in `direction` (+1 later, -1 earlier)."""
    base = _values(chart, chart["jd"])[factor]
    for m in range(1, limit_minutes + 1):
        v = _values(chart, chart["jd"] + direction * m / 1440)[factor]
        if v != base:
            return m, v
    return None, None


def sensitivity(chart, limit_minutes=240):
    set_ayanamsha(chart["ayanamsha"])
    now = _values(chart, chart["jd"])
    rows = []
    for factor, impact in FACTORS.items():
        early_m, early_v = _first_change(chart, factor, -1, limit_minutes)
        late_m, late_v = _first_change(chart, factor, +1, limit_minutes)
        nearest = min(m for m in (early_m, late_m, 10 ** 6) if m is not None)
        rows.append({"factor": factor, "value": now[factor], "impact": impact,
                     "earlier": (early_m, early_v), "later": (late_m, late_v), "nearest": nearest})
    return rows


def dasha_shift_per_minute(chart):
    """Days by which the first Mahadasha's end date moves per minute of birth-time change."""
    set_ayanamsha(chart["ayanamsha"])
    m0, _ = planet_longitude(chart["jd"], "Moon")
    m1, _ = planet_longitude(chart["jd"] + 1 / 1440, "Moon")
    lord = DASHA_LORDS[int(m0 // NAKSHATRA_SPAN) % 9]
    moved = (m1 - m0) % 360  # degrees per minute
    return moved / NAKSHATRA_SPAN * DASHA_YEARS[lord] * 365.25


def warning(rows, threshold=15):
    """Plain-English warning if any factor changes within `threshold` minutes, else None."""
    close = [r for r in rows if r["nearest"] <= threshold]
    if not close:
        return None
    parts = []
    for r in close:
        side, (m, v) = ("earlier", r["earlier"]) if r["earlier"][0] == r["nearest"] else ("later", r["later"])
        parts.append(f"**{r['factor']}** becomes **{v}** if you were born {m} min {side}")
    return ("⏱ Your chart is sensitive to the exact birth time: " + "; ".join(parts)
            + ". If your recorded time could be off by that much, treat the affected readings with care.")
