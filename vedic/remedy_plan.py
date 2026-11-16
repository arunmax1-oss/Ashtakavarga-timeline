"""Putting remedies into practice: when to start, which life areas each planet touches, and a gemstone plan.

- Calendar: the planet's own weekday over the coming weeks, rated with the personal day rating (Tara Bala,
  Chandra Bala, tithi...), with the planet's daytime horas (planetary hours) and Rahu Kalam to avoid.
  Strengthening remedies prefer the waxing Moon. Rahu uses Saturn's hora and Ketu Mars's.
- Life areas: the houses a planet rules and occupies, mapped to the app's life-area pages.
- Gemstone plan: at most two stones, only for planets to strengthen that actually need it (severity 15+),
  never two whose planets are natural enemies (e.g. Sun and Saturn).
"""
import datetime as dt

from .constants import HOUSE_INFO, SIGN_LORDS, ordinal
from .insights import ruled_houses
from .lifeareas import AREAS
from .narratives import HORA_STAND_IN, REMEDIES, REMEDY_DETAILS
from .shadbala import HORA_ORDER, NATURAL_FRIENDS, WEEKDAY_LORDS
from .weekly import day_forecast

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
GEM_MIN_SEVERITY = 15
MAX_GEMS = 2


# --------------------------------------------------------------------------------------
# Calendar
# --------------------------------------------------------------------------------------
def day_horas(date, sunrise, sunset):
    """[(lord, start, end)] for the 12 daytime planetary hours of a civil date."""
    lord = WEEKDAY_LORDS[(date.weekday() + 1) % 7]  # date.weekday(): Monday = 0; WEEKDAY_LORDS starts on Sunday
    first = HORA_ORDER.index(lord)
    step = (sunset - sunrise) / 12
    return [(HORA_ORDER[(first + i) % 7], sunrise + i * step, sunrise + (i + 1) * step) for i in range(12)]


def start_days(chart, av, schedule, planet, approach, start, tz_name, place, weeks=6):
    """The planet's weekdays in the next `weeks`, best first: [{"date", "score", "rating", "notes", "horas",
    "rahu_kalam", "nakshatra", "tithi"}]."""
    weekday = WEEKDAYS.index(REMEDIES[planet]["day"])
    hora_lord = HORA_STAND_IN.get(planet, planet)
    out = []
    for i in range(weeks * 7):
        d = start + dt.timedelta(days=i)
        if d.weekday() != weekday:
            continue
        f = day_forecast(chart, av, schedule, d, tz_name, place)
        score, notes = f["score"], []
        if approach == "Strengthen" and f["tithi"]["paksha"] != "Shukla":
            score -= 1
            notes.append("waning Moon: better for pacifying than strengthening")
        elif approach == "Strengthen":
            notes.append("waxing Moon supports strengthening")
        if f["chandrashtama"]:
            score -= 2
            notes.append("Chandrashtama (Moon 8th from yours): avoid starting")
        if f["tithi"]["group"] in ("Rikta", "Amavasya"):  # already lowers the day score
            notes.append(f"{f['tithi']['group']} tithi: traditionally avoided for new beginnings")
        t = f["timings"]
        horas = [(a, b) for lord, a, b in day_horas(d, t["sunrise"], t["sunset"]) if lord == hora_lord] if t else []
        out.append({"date": d, "score": score, "rating": f["rating"], "notes": notes, "horas": horas,
                    "rahu_kalam": t["rahu_kalam"] if t else None, "nakshatra": f["nakshatra"],
                    "tithi": f["tithi"]["name"]})
    return sorted(out, key=lambda r: (-r["score"], r["date"]))


# --------------------------------------------------------------------------------------
# Life areas
# --------------------------------------------------------------------------------------
def life_links(chart, planet):
    """{"houses": [...], "text": ..., "areas": [area names, main area first]}."""
    ruled = ruled_houses(chart, planet)
    sits = chart["planets"][planet]["house"]
    houses = list(dict.fromkeys(ruled + [sits]))
    areas = []
    for h in houses:
        if h in (10, 6) and "Job" not in areas:
            areas.append("Job")
        for key, spec in AREAS.items():
            if h in spec["houses"] and key not in areas:
                areas.append(key)
    for key, spec in AREAS.items():
        if planet in spec["karakas"] and key not in areas:
            areas.append(key)
    parts = []
    if ruled:
        parts.append("rules your " + " and ".join(f"{ordinal(h)} ({HOUSE_INFO[h][1].split(',')[0].lower()})"
                                                  for h in ruled))
    parts.append(f"sits in your {ordinal(sits)} ({HOUSE_INFO[sits][1].split(',')[0].lower()})")
    return {"houses": houses, "areas": areas, "text": f"{planet} " + " and ".join(parts) + "."}


def area_focus(chart, remedies, key):
    """Planets needing care (severity 15+) that rule, occupy or signify a life area's houses."""
    spec = AREAS[key]
    out = []
    for planet, sc in remedies["scores"].items():
        if sc["score"] < GEM_MIN_SEVERITY:
            continue
        houses = set(ruled_houses(chart, planet)) | {chart["planets"][planet]["house"]}
        hit = sorted(houses & set(spec["houses"]))
        if hit or planet in spec["karakas"]:
            why = (f"{'rules or occupies' if hit else ''} your {', '.join(ordinal(h) for h in hit)}" if hit else
                   "is a significator of this area")
            out.append({"planet": planet, "score": sc["score"], "approach": remedies["roles"][planet]["approach"],
                        "why": why.strip()})
    return sorted(out, key=lambda r: -r["score"])


# --------------------------------------------------------------------------------------
# Gemstones
# --------------------------------------------------------------------------------------
def enemies(a, b):
    def hates(x, y):
        return x in NATURAL_FRIENDS and y in NATURAL_FRIENDS[x][2]
    return hates(a, b) or hates(b, a)


def gem_plan(chart, remedies):
    """{"wear": [...], "skip": [...]} where each item is {"planet", "stone", "reason", "details"}."""
    entries = {e["planet"]: e for e in remedies["lifelong"] + remedies["now"] if e["gem"]}
    lagna_lord = SIGN_LORDS[chart["planets"]["Ascendant"]["sign"]]
    ranked = sorted(entries, key=lambda p: (p != lagna_lord, -remedies["scores"][p]["score"]))
    wear, skip = [], []
    for p in ranked:
        e = entries[p]
        details = REMEDY_DETAILS[p]["gem"]
        sev = remedies["scores"][p]["score"]
        if sev < GEM_MIN_SEVERITY:
            skip.append({"planet": p, "stone": e["gem"], "details": details,
                         "reason": f"not needed: severity {sev} means {p} is already reasonably strong"})
        elif any(enemies(p, w["planet"]) for w in wear):
            other = next(w for w in wear if enemies(p, w["planet"]))
            skip.append({"planet": p, "stone": e["gem"], "details": details,
                         "reason": f"conflicts with {other['stone']} ({p} and {other['planet']} are natural enemies)"})
        elif len(wear) >= MAX_GEMS:
            skip.append({"planet": p, "stone": e["gem"], "details": details,
                         "reason": f"limit of {MAX_GEMS} stones; the ones above need it more"})
        else:
            why = ("your Lagna lord, the safest planet to strengthen" if p == lagna_lord else
                   f"a {remedies['roles'][p]['role'].lower()} with severity {sev}")
            wear.append({"planet": p, "stone": e["gem"], "details": details, "reason": why})
    return {"wear": wear, "skip": skip}


def guidance_rows(planet, approach, gem=None):
    """[(label, text)] of the fuller traditional guidance for one planet."""
    d = REMEDY_DETAILS[planet]
    rows = [("Beej mantra", f"*{d['beej']}*: 108 times a day; a full course is traditionally {d['japa']:,} "
                            "repetitions (sources differ)"),
            ("Hymn (stotra)", d["stotra"]),
            ("Donate", f"{d['donate']}, on {REMEDIES[planet]['day']}s"),
            ("Conduct", d["conduct"][0].upper() + d["conduct"][1:]),
            ("Fasting", d["fast"]),
            ("Rudraksha", f"{d['rudraksha']} (worn after it is energised, as tradition advises)")]
    if approach == "Strengthen":
        rows.insert(4, ("Colours", f"wear {d['colours']}, especially on {REMEDIES[planet]['day']}s"))
    elif approach == "Balance":
        rows.insert(4, ("Colours", f"{d['colours']}: optional, a gentle way to stay mindful of the planet"))
    else:
        rows.insert(4, ("Colours", f"{d['colours']} are this planet's colours; no need to wear them while "
                                   "pacifying it"))
    if gem and d["gem"]:
        g = d["gem"]
        rows.append(("Gemstone details", f"{gem}: commonly {g['carats']} carats, set in {g['metal']}, worn on the "
                                         f"{g['finger']} of the working hand, first worn on {g['start']}. "
                                         f"Gentler substitutes: {g['substitutes']}. Try it for a few weeks and "
                                         "remove it if things clearly worsen."))
    return rows
