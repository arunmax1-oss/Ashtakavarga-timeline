"""Remedies (upaya): which planets need attention, why, and what tradition suggests.

Every remedy is tied to a specific, computed chart fact, so the user can always see *why* it is shown.
No Streamlit here: functions take computed data and return plain lists/dicts/Markdown.

Shadbala is optional: pass the result of vedic.shadbala.shadbala() to add its check.
"""
import datetime as dt

from .aspects import combustion, influences
from .chart import house_from, julian_day, planet_longitude, set_ayanamsha
from .constants import CLASSICAL_PLANETS, ALL_PLANETS, SIGNS, ordinal
from .insights import DUSTHANAS, KENDRAS, TRIKONAS, _domain, neecha_bhanga, ruled_houses
from .narratives import GEM_CAUTION, PLANET_SUPPORT, REMEDIES, dasha_axis
from .remedy_eval import APPROACH_TEXT, evaluate, level

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
def natal_flags(chart, av, planet, sb=None):
    """Reasons this planet needs support in the birth chart. Returns (reasons, priority or None).

    Each trigger carries a weight: High (uncancelled debilitation), Medium, or Low. Two Medium triggers make
    the planet High. Mitigating notes (Jupiter's protection) are listed but never count towards priority.
    """
    p = chart["planets"][planet]
    triggers, notes = [], []

    if p["dignity"] == "Debilitated":
        if neecha_bhanga(chart, planet):
            triggers.append((f"Debilitated in {p['sign']}, but the weakness is cancelled (Neecha Bhanga), "
                             "so it improves with age", "Low"))
        else:
            triggers.append((f"Debilitated in {p['sign']} (its weakest sign)", "High"))

    # 8th and 12th are difficult for every planet. The 6th suits tough planets (Sun, Mars, Saturn, Rahu, Ketu)
    # and is only flagged for the gentle ones.
    if p["house"] in (8, 12) or (p["house"] == 6 and planet in NATURAL_BENEFICS):
        triggers.append((f"Sits in your {ordinal(p['house'])} house ({_domain(p['house'])}), a difficult house", "Medium"))

    if planet in CLASSICAL_PLANETS:
        bav = av["bav"][planet][p["sign_idx"]]
        if bav <= 3:
            triggers.append((f"Only {bav}/8 Ashtakavarga points in the sign it occupies (4 is average)", "Medium"))

    if sb and planet in sb and sb[planet]["ratio"] < 1:
        r = sb[planet]
        triggers.append((f"Shadbala {r['rupas']:.2f} rupas, below the {r['required'] / 60:.1f} it needs "
                         f"({r['ratio']:.2f}×)", "Medium"))

    comb = combustion(chart, planet)
    if comb:
        mild = planet == "Mercury"
        triggers.append((f"Combust: {comb['distance']:.1f}° from the Sun (limit {comb['orb']}°), so its themes are "
                         "overshadowed by ego, authority or the father figure"
                         + ("; Mercury is usually close to the Sun, so tradition treats this lightly" if mild else ""),
                         "Low" if mild else "Medium"))

    if planet not in ("Rahu", "Ketu"):
        inf = influences(chart, planet)
        pressure, shield = " and ".join(inf["malefic"]), " and ".join(inf["jupiter"])
        if len(inf["malefic"]) >= 2 and not inf["jupiter"]:
            triggers.append((f"Under combined pressure from {pressure}"
                             + ("" if planet == "Jupiter" else ", with no protective aspect from Jupiter"), "Medium"))
        elif inf["malefic"] and inf["jupiter"]:
            notes.append(f"Mitigation: pressure from {pressure} is eased by {shield}")
        elif inf["malefic"]:
            notes.append(f"Also note: mild pressure from {pressure}")
        elif inf["jupiter"]:
            notes.append(f"Mitigation: protected by {shield}")

    if not triggers:
        return [], None
    weights = [w for _, w in triggers]
    priority = ("High" if "High" in weights or weights.count("Medium") >= 2 else
                "Medium" if "Medium" in weights else "Low")
    return [r for r, _ in triggers] + notes, priority


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
def _entry(chart, planet, reasons, priority, until=None, ev=None):
    r = REMEDIES[planet]
    role = ev["roles"][planet] if ev else {"role": "", "approach": "Strengthen", "tags": [], "why": ""}
    strengthen = role["approach"] == "Strengthen"
    gem_ok = gem_eligible(chart, planet) and strengthen
    return {
        "planet": planet, "priority": priority, "reasons": reasons, "until": until,
        "score": ev["scores"][planet]["score"] if ev else 0,
        "factors": ev["scores"][planet]["factors"] if ev else [],
        "role": role["role"], "approach": role["approach"], "tags": role["tags"], "role_why": role["why"],
        "practical": PLANET_SUPPORT[planet][0].upper() + PLANET_SUPPORT[planet][1:] + ".",
        "day": r["day"], "mantra": r["mantra"], "deity": r["deity"], "practice": r["practice"], "charity": r["charity"],
        "gem": r["gem"] if gem_ok else None,
        "gem_note": (GEM_CAUTION if gem_ok else
                     "No gemstone suggested: this planet has no sign of its own." if not r["gem"] else
                     f"No gemstone: as a {role['role'].lower()} for your Lagna it should be "
                     f"{'pacified' if role['approach'] == 'Pacify' else 'balanced'}, not strengthened."
                     if not strengthen else
                     "No gemstone suggested: this planet rules a difficult house for your Lagna (or no supportive one), "
                     "so strengthening it with a stone is not advised."),
    }


ACTIVATION = {"High": 20, "Medium": 12, "Low": 6}


def _priority(score, floor=None):
    p = level(score)
    p = "Low" if p == "None" else p
    return min(p, floor, key=_RANK.get) if floor else p


def build_remedies(chart, av, schedule_now, when, sb=None):
    """schedule_now = (mahadasha, antardasha) dicts or (None, None).

    Returns {'now', 'lifelong'} remedy entries plus the evaluation behind them: 'roles' (functional nature),
    'doshas' and 'scores' (severity 0-100 with factors). Priority follows the severity score; a planet that is
    active now adds activation points on top of its birth-chart score."""
    md, ad = schedule_now
    ev = evaluate(chart, av, sb)
    lifelong, natal = [], {}
    for planet in ALL_PLANETS:
        flags, _ = natal_flags(chart, av, planet, sb)
        reasons = flags + [f"Part of {d['name']}" + (" (eased by cancellations)" if d["cancelled"] else "")
                           for d in ev["doshas"] if planet in d["planets"]]
        natal[planet] = reasons
        score = ev["scores"][planet]["score"]
        if reasons and score >= 10:
            lifelong.append(_entry(chart, planet, reasons, _priority(score), ev=ev))

    now, active = {}, {}

    def add(planet, reason, priority, until):
        active[planet] = active.get(planet, 0) + ACTIVATION[priority]
        if planet in now:
            e = now[planet]
            e["reasons"].insert(0, reason) if reason not in e["reasons"] else None
            e["until"] = max(e["until"], until)
        else:
            base = natal[planet]
            e = now[planet] = _entry(chart, planet, [reason] + [f"Birth chart: {b[0].lower()}{b[1:]}" for b in base],
                                     "Low", until, ev=ev)
        e["score"] = min(100, ev["scores"][planet]["score"] + active[planet])
        e["priority"] = _priority(e["score"], floor=priority)

    if md and ad:
        add(md["lord"], f"Runs your current main period (Mahadasha) until {md['end']:%b %Y}", "Medium", md["end"])
        add(ad["lord"], f"Runs your current sub-period (Antardasha) until {ad['end']:%b %Y}", "Medium", ad["end"])
        axis, tone, _ = dasha_axis(chart, md["lord"], ad["lord"])
        if tone == "warning" and md["lord"] != ad["lord"]:
            e = now[ad["lord"]]
            e["reasons"].append(f"The two period lords are in a tense relationship ({axis}), so this sub-period needs more care")
            e["score"] = min(100, e["score"] + 15)
            e["priority"] = _priority(e["score"], floor="Medium")

    sat = saturn_transit(chart, when)
    if sat:
        add("Saturn", f"{sat['name']}: Saturn is passing through {sat['sign']} until about {sat['until']:%b %Y} "
                      "(it can briefly return when retrograde)", sat["priority"], sat["until"])

    order = lambda e: (_RANK[e["priority"]], -e["score"], ALL_PLANETS.index(e["planet"]))  # noqa: E731
    return {"now": sorted(now.values(), key=order), "lifelong": sorted(lifelong, key=order), **ev}


# --------------------------------------------------------------------------------------
# Presentation helpers
# --------------------------------------------------------------------------------------
def table_rows(entries):
    return [{
        "Planet": e["planet"], "Priority": e["priority"], "Severity": e["score"], "Approach": e["approach"],
        "Why it is flagged": "; ".join(e["reasons"]),
        "Simple step": e["practical"], "Day": e["day"],
        "Applies until": f"{e['until']:%d %b %Y}" if e["until"] else "Lifelong",
    } for e in entries]


def entry_markdown(e):
    why = "\n".join(f"- {r}" for r in e["reasons"])
    gem = f"**{e['gem']}.** {e['gem_note']}" if e["gem"] else e["gem_note"]
    role = (f"**Role for your Lagna:** {e['role']}" + (f" · {', '.join(e['tags'])}" if e["tags"] else "")
            + f". {e['role_why']}\n\n**Approach: {e['approach']}.** {APPROACH_TEXT[e['approach']]}\n\n"
            if e.get("role") else "")
    pacify = e.get("approach") == "Pacify"
    devotional = (f"On {e['day']}s give **{e['charity']}** in charity and serve those the planet signifies; chant "
                  f"*{e['mantra']}* (traditionally 108 times); {e['practice']}. Deity: {e['deity']}." if pacify else
                  f"On {e['day']}s: {e['practice']}; chant *{e['mantra']}* (traditionally 108 times); "
                  f"give {e['charity']}. Deity: {e['deity']}.")
    factors = ""
    if e.get("factors"):
        factors = ("\n**How the severity score is built** (birth chart"
                   + ("; being active now adds points on top" if e.get("until") else "") + ")\n"
                   + "\n".join(f"- {'+' if x['points'] > 0 else ''}{x['points']}: {x['text']}" for x in e["factors"])
                   + "\n")
    return (f"{role}**Why this planet**\n{why}\n\n"
            f"| Tier | What to do |\n|---|---|\n"
            f"| 1. Practical (start here) | {e['practical']} |\n"
            f"| 2. {'Pacifying' if pacify else 'Devotional'} | {devotional} |\n"
            f"| 3. Gemstone | {gem} |\n{factors}")


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
