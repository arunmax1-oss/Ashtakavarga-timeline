"""Remedies (upaya): which planets need attention, why, and what tradition suggests.

Every remedy is tied to a specific, computed chart fact, so the user can always see *why* it is shown.
No Streamlit here: functions take computed data and return plain lists/dicts/Markdown.

Not covered (the engine does not compute them yet): combustion, planetary aspects, full Shadbala.
"""
import datetime as dt

from .chart import house_from, julian_day, planet_longitude, set_ayanamsha
from .constants import CLASSICAL_PLANETS, ALL_PLANETS, SIGNS, ordinal
from .insights import DUSTHANAS, KENDRAS, TRIKONAS, _domain, neecha_bhanga, ruled_houses
from .narratives import GEM_CAUTION, PLANET_SUPPORT, REMEDIES, dasha_axis

NATURAL_BENEFICS = ["Moon", "Mercury", "Jupiter", "Venus"]
_RANK = {"High": 0, "Medium": 1, "Low": 2}
_SATURN_PHASES = {
    12: ("Sade Sati, first phase", "Medium"), 1: ("Sade Sati, peak phase", "High"),
    2: ("Sade Sati, final phase", "Medium"), 8: ("Ashtama Shani (8th from Moon)", "High"),
    4: ("Ardhashtama Shani (4th from Moon)", "Medium"),
}


# --------------------------------------------------------------------------------------
# Triggers
# --------------------------------------------------------------------------------------
def natal_flags(chart, av, planet):
    """Reasons this planet needs support in the birth chart. Returns (reasons, priority or None)."""
    p = chart["planets"][planet]
    reasons, severe = [], False

    if p["dignity"] == "Debilitated":
        if neecha_bhanga(chart, planet):
            reasons.append(f"Debilitated in {p['sign']}, but the weakness is cancelled (Neecha Bhanga), so it improves with age")
        else:
            reasons.append(f"Debilitated in {p['sign']} (its weakest sign)")
            severe = True

    # 8th and 12th are difficult for every planet. The 6th suits tough planets (Sun, Mars, Saturn, Rahu, Ketu)
    # and is only flagged for the gentle ones.
    if p["house"] in (8, 12) or (p["house"] == 6 and planet in NATURAL_BENEFICS):
        reasons.append(f"Sits in your {ordinal(p['house'])} house ({_domain(p['house'])}), a difficult house")

    if planet in CLASSICAL_PLANETS:
        bav = av["bav"][planet][p["sign_idx"]]
        if bav <= 3:
            reasons.append(f"Only {bav}/8 Ashtakavarga points in the sign it occupies (4 is average)")

    if not reasons:
        return [], None
    only_cancelled = len(reasons) == 1 and "cancelled" in reasons[0]
    priority = "High" if severe or len(reasons) >= 2 else "Low" if only_cancelled else "Medium"
    return reasons, priority


def gem_eligible(chart, planet):
    """Conservative rule: only the Lagna lord, or a lord of a kendra/trikona that rules no difficult house."""
    if not REMEDIES[planet]["gem"]:
        return False
    houses = ruled_houses(chart, planet)
    if 1 in houses:
        return True
    good = any(h in KENDRAS or h in TRIKONAS for h in houses)
    return good and not any(h in DUSTHANAS for h in houses)


def saturn_transit(chart, when, max_days=1500):
    """Saturn's current phase from the natal Moon, and roughly when it leaves the sign. None if no phase is active."""
    set_ayanamsha(chart["ayanamsha"])
    jd = julian_day(when)
    lon, _ = planet_longitude(jd, "Saturn")
    sign = int(lon // 30)
    h_m = house_from(sign, chart["planets"]["Moon"]["sign_idx"])
    if h_m not in _SATURN_PHASES:
        return None
    days = 0
    while days < max_days and int(planet_longitude(jd + days, "Saturn")[0] // 30) == sign:
        days += 1
    name, priority = _SATURN_PHASES[h_m]
    return {"name": name, "priority": priority, "sign": SIGNS[sign], "until": when + dt.timedelta(days=days)}


# --------------------------------------------------------------------------------------
# Assembly
# --------------------------------------------------------------------------------------
def _entry(chart, planet, reasons, priority, until=None):
    r = REMEDIES[planet]
    return {
        "planet": planet, "priority": priority, "reasons": reasons, "until": until,
        "practical": PLANET_SUPPORT[planet][0].upper() + PLANET_SUPPORT[planet][1:] + ".",
        "day": r["day"], "mantra": r["mantra"], "deity": r["deity"], "practice": r["practice"], "charity": r["charity"],
        "gem": r["gem"] if gem_eligible(chart, planet) else None,
        "gem_note": (GEM_CAUTION if gem_eligible(chart, planet) else
                     "No gemstone suggested: this planet has no sign of its own." if not r["gem"] else
                     "No gemstone suggested: this planet rules a difficult house for your Lagna (or no supportive one), "
                     "so strengthening it with a stone is not advised."),
    }


def build_remedies(chart, av, schedule_now, when):
    """schedule_now = (mahadasha, antardasha) dicts or (None, None). Returns {'now': [...], 'lifelong': [...]}."""
    md, ad = schedule_now
    lifelong, natal = [], {}
    for planet in ALL_PLANETS:
        reasons, priority = natal_flags(chart, av, planet)
        natal[planet] = (reasons, priority)
        if reasons:
            lifelong.append(_entry(chart, planet, reasons, priority))

    now = {}

    def add(planet, reason, priority, until):
        if planet in now:
            e = now[planet]
            e["reasons"].insert(0, reason) if reason not in e["reasons"] else None
            e["priority"] = min(e["priority"], priority, key=_RANK.get)
            e["until"] = max(e["until"], until)
        else:
            base, natal_priority = natal[planet]
            if natal_priority in ("High", "Medium"):
                priority = "High"  # a period or transit of a planet that is already weak at birth
            now[planet] = _entry(chart, planet, [reason] + [f"Birth chart: {b[0].lower()}{b[1:]}" for b in base],
                                 priority, until)

    if md and ad:
        add(md["lord"], f"Runs your current main period (Mahadasha) until {md['end']:%b %Y}", "Medium", md["end"])
        add(ad["lord"], f"Runs your current sub-period (Antardasha) until {ad['end']:%b %Y}", "Medium", ad["end"])
        axis, tone, _ = dasha_axis(chart, md["lord"], ad["lord"])
        if tone == "warning" and md["lord"] != ad["lord"]:
            e = now[ad["lord"]]
            e["reasons"].append(f"The two period lords are in a tense relationship ({axis}), so this sub-period needs more care")
            e["priority"] = "High"

    sat = saturn_transit(chart, when)
    if sat:
        add("Saturn", f"{sat['name']}: Saturn is passing through {sat['sign']} until about {sat['until']:%b %Y} "
                      "(it can briefly return when retrograde)", sat["priority"], sat["until"])

    order = lambda e: (_RANK[e["priority"]], ALL_PLANETS.index(e["planet"]))
    return {"now": sorted(now.values(), key=order), "lifelong": sorted(lifelong, key=order)}


# --------------------------------------------------------------------------------------
# Presentation helpers
# --------------------------------------------------------------------------------------
def table_rows(entries):
    return [{
        "Planet": e["planet"], "Priority": e["priority"], "Why it is flagged": "; ".join(e["reasons"]),
        "Simple step": e["practical"], "Day": e["day"],
        "Applies until": f"{e['until']:%d %b %Y}" if e["until"] else "Lifelong",
    } for e in entries]


def entry_markdown(e):
    why = "\n".join(f"- {r}" for r in e["reasons"])
    gem = f"**{e['gem']}.** {e['gem_note']}" if e["gem"] else e["gem_note"]
    return (f"**Why this planet**\n{why}\n\n"
            f"| Tier | What to do |\n|---|---|\n"
            f"| 1. Practical (start here) | {e['practical']} |\n"
            f"| 2. Devotional | On {e['day']}s: {e['practice']}; chant *{e['mantra']}* (traditionally 108 times); "
            f"give {e['charity']}. Deity: {e['deity']}. |\n"
            f"| 3. Gemstone | {gem} |\n")


def remedies_markdown(result):
    """Compact version for the downloadable report."""
    out = []
    for title, key in [("Do now (current period and transits)", "now"), ("Lifelong (birth chart)", "lifelong")]:
        out.append(f"**{title}**\n")
        if not result[key]:
            out.append("- Nothing flagged.\n")
        for e in result[key]:
            out.append(f"- **{e['planet']}** ({e['priority']}): {'; '.join(e['reasons'])}. "
                       f"*Step:* {e['practical']} *{e['day']}:* {e['practice']}, {e['mantra']}.")
        out.append("")
    return "\n".join(out)
