"""Weekly forecast: daily Panchang, Moon-based day ratings and the week's key planetary events.

Each day is rated from classical, chart-specific rules:
- Tara Bala: the transit Moon's nakshatra counted from your birth nakshatra (9-fold cycle).
  (The Moon is read at local midday; the tithi at 06:00, the Panchang's sunrise convention.)
- Chandra Bala: the transit Moon's house counted from your natal Moon (8th = Chandrashtama, the hardest).
- The Moon's own Ashtakavarga points in the sign it is transiting.
- The tithi (lunar day) and whether the weekday lord is one of your running Dasha lords.
The week adds slow-planet events: sign changes, retrograde stations, Dasha changes, strong Kakshya windows,
Bhrigu Bindu contacts and the Gochara (transit from Moon) climate of the faster planets.

These are interpretive rules for reflection, not certainties.
"""
import datetime as dt
import zoneinfo

from .bhrigu import bcp_year, bhrigu_bindu, contact_windows
from .chart import house_from, julian_day, jd_to_datetime, planet_longitude, set_ayanamsha
from .constants import HOUSE_INFO, NAKSHATRA_SPAN, NAKSHATRAS, SIGNS, ordinal
from .dasha import active_periods, sub_periods
from .narratives import GOCHARA_GOOD_FROM_MOON
from .transits import transit_segments

TITHI_NAMES = ["Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi", "Saptami", "Ashtami",
               "Navami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi"]
TITHI_GROUPS = {1: ("Nanda", "joy and celebration"), 2: ("Bhadra", "steady work and health"),
                3: ("Jaya", "competition and winning"), 4: ("Rikta", "finishing and clearing, not starting"),
                0: ("Purna", "completion and fulfilment")}
TARAS = [("Janma", "mixed: personal focus, go gently", -1), ("Sampat", "wealth and gains", 2),
         ("Vipat", "obstacles; avoid big launches", -2), ("Kshema", "well-being and safety", 2),
         ("Pratyari", "opposition; expect resistance", -2), ("Sadhana", "achievement through effort", 2),
         ("Naidhana", "the hardest star; rest and postpone", -2), ("Mitra", "friendly support", 2),
         ("Parama Mitra", "best support from others", 2)]
CHANDRA_GOOD = [1, 3, 6, 7, 10, 11]
WEEKDAY_LORDS = ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun"]  # Monday first
WEEKDAY_THEMES = {
    "Sun": "authority, government work, health routines", "Moon": "home, family, public dealings",
    "Mars": "physical work, property, decisive action", "Mercury": "study, writing, trade, paperwork",
    "Jupiter": "learning, advice, finance, ceremonies", "Venus": "relationships, art, purchases, comfort",
    "Saturn": "routine work, service, discipline, clearing backlogs",
}
EVENT_PLANETS = ["Sun", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu"]
RATINGS = [(3, "Excellent", "🟢"), (1, "Good", "🟢"), (0, "Mixed", "🟡"), (-2, "Careful", "🟠"), (-99, "Difficult", "🔴")]


def _domain(h):
    return HOUSE_INFO[h][1].lower()


def _bisect(jd0, jd1, same, minutes=1):
    """Earliest moment in (jd0, jd1] where same(jd) turns False."""
    lo, hi = jd0, jd1
    while hi - lo > minutes / 1440:
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if same(mid) else (lo, mid)
    return hi


def _local(utc_naive, tz_name):
    return utc_naive.replace(tzinfo=dt.timezone.utc).astimezone(zoneinfo.ZoneInfo(tz_name)).replace(tzinfo=None)


def _utc(local_naive, tz_name):
    return local_naive.replace(tzinfo=zoneinfo.ZoneInfo(tz_name)).astimezone(dt.timezone.utc).replace(tzinfo=None)


# --------------------------------------------------------------------------------------
# Panchang pieces
# --------------------------------------------------------------------------------------
def moon_sun(chart, jd):
    moon, _ = planet_longitude(jd, "Moon")
    sun, _ = planet_longitude(jd, "Sun")
    return moon, sun


def tithi_of(moon, sun):
    n = int(((moon - sun) % 360) // 12) + 1  # 1..30
    paksha = "Shukla" if n <= 15 else "Krishna"
    k = (n - 1) % 15
    name = "Purnima" if n == 15 else "Amavasya" if n == 30 else TITHI_NAMES[k]
    group = TITHI_GROUPS[(k + 1) % 5] if n != 30 else ("Amavasya", "rest, reflection and ancestral rites; not for starting")
    return {"number": n, "paksha": paksha, "name": f"{paksha} {name}", "group": group[0], "group_use": group[1]}


def tara_of(chart, moon_lon):
    birth_nak = int(chart["planets"]["Moon"]["lon"] // NAKSHATRA_SPAN)
    count = (int(moon_lon // NAKSHATRA_SPAN) - birth_nak) % 27
    name, meaning, score = TARAS[count % 9]
    return {"name": name, "meaning": meaning, "score": score}


# --------------------------------------------------------------------------------------
# One day
# --------------------------------------------------------------------------------------
def _changes(jd0, jd1, value, label, tz_name):
    """Every moment value(jd) changes between jd0 and jd1 (handles more than one change)."""
    out, j = [], jd0
    while value(jd1) != value(j):
        v = value(j)
        t = _bisect(j, jd1, lambda x: value(x) == v)
        out.append(f"{label(value(t))} at {_local(jd_to_datetime(t), tz_name):%H:%M}")
        j = t
    return out


def day_forecast(chart, av, schedule, date, tz_name):
    """Rate one civil day.

    The tithi is the one prevailing at 06:00 local time (the Panchang convention of sunrise). The Moon's sign
    and nakshatra are read at midday, which covers most of the waking day; every change during the day is listed.
    """
    set_ayanamsha(chart["ayanamsha"])
    day_start = julian_day(_utc(dt.datetime.combine(date, dt.time(0, 0)), tz_name))
    t0 = _utc(dt.datetime.combine(date, dt.time(12, 0)), tz_name)
    jd0 = julian_day(t0)
    moon, sun = moon_sun(chart, jd0)
    sign = int(moon // 30)
    nak = int(moon // NAKSHATRA_SPAN)
    natal_moon = chart["planets"]["Moon"]["sign_idx"]

    tithi = tithi_of(*moon_sun(chart, day_start + 0.25))
    tara = tara_of(chart, moon)
    from_moon = house_from(sign, natal_moon)
    from_lagna = house_from(sign, chart["asc_sign_idx"])
    bav = av["bav"]["Moon"][sign]
    lord = WEEKDAY_LORDS[date.weekday()]
    md, ad, pd = active_periods(schedule, t0)
    period_lords = [x["lord"] for x in (md, ad, pd) if x]

    score, reasons = tara["score"], [f"Tara: {tara['name']} ({tara['meaning']})"]
    if from_moon == 8:
        score -= 3
        reasons.append("Chandrashtama: the Moon is 8th from your natal Moon; keep the day light")
    elif from_moon in CHANDRA_GOOD:
        score += 1
        reasons.append(f"Chandra Bala: Moon {ordinal(from_moon)} from your natal Moon (supportive)")
    else:
        reasons.append(f"Chandra Bala: Moon {ordinal(from_moon)} from your natal Moon (neutral)")
    if bav >= 5:
        score += 1
        reasons.append(f"The Moon has {bav}/8 of its Ashtakavarga points in {SIGNS[sign]} (strong)")
    elif bav <= 3:
        score -= 1
        reasons.append(f"The Moon has only {bav}/8 Ashtakavarga points in {SIGNS[sign]} (weak)")
    if tithi["group"] == "Rikta" or tithi["number"] == 30:
        score -= 1
        reasons.append(f"{tithi['name']} is a {'new-moon' if tithi['number'] == 30 else 'Rikta'} tithi: "
                       "better for finishing than starting")
    if lord in period_lords:
        score += 1
        reasons.append(f"{date:%A} is ruled by {lord}, one of your running Dasha lords")

    rating, icon = next((name, ic) for limit, name, ic in RATINGS if score >= limit)

    day_end = day_start + 1
    changes = (_changes(day_start, day_end, lambda j: int(planet_longitude(j, "Moon")[0] // 30),
                        lambda v: f"Moon enters {SIGNS[v]}", tz_name)
               + _changes(day_start, day_end, lambda j: int(planet_longitude(j, "Moon")[0] // NAKSHATRA_SPAN),
                          lambda v: f"Nakshatra {NAKSHATRAS[v]} begins", tz_name))

    use = f"{_domain(from_lagna)} ({ordinal(from_lagna)} house); {WEEKDAY_THEMES[lord]}"
    return {"date": date, "weekday": f"{date:%A}", "weekday_lord": lord, "tithi": tithi, "nakshatra": NAKSHATRAS[nak],
            "moon_sign": SIGNS[sign], "from_moon": from_moon, "from_lagna": from_lagna, "moon_bav": bav,
            "tara": tara, "score": score, "rating": rating, "icon": icon, "reasons": reasons,
            "changes": changes, "best_use": use, "chandrashtama": from_moon == 8}


# --------------------------------------------------------------------------------------
# Week events
# --------------------------------------------------------------------------------------
def _sign_changes(chart, start, end, tz_name):
    set_ayanamsha(chart["ayanamsha"])
    out, jd, jd_end = [], julian_day(start), julian_day(end)
    for planet in EVENT_PLANETS:
        j = jd
        while j < jd_end:
            nxt = min(j + 0.5, jd_end)
            s0 = int(planet_longitude(j, planet, chart["true_node"])[0] // 30)
            s1 = int(planet_longitude(nxt, planet, chart["true_node"])[0] // 30)
            if s0 != s1:
                t = _bisect(j, nxt, lambda x: int(planet_longitude(x, planet, chart["true_node"])[0] // 30) == s0)
                h = house_from(s1, chart["asc_sign_idx"])
                out.append({"when": _local(jd_to_datetime(t), tz_name), "planet": planet,
                            "text": f"**{planet}** moves into **{SIGNS[s1]}**, your {ordinal(h)} house "
                                    f"({_domain(h)}), bringing its focus there for the coming "
                                    + {"Sun": "month", "Mars": "6–7 weeks", "Mercury": "3–4 weeks", "Venus": "month",
                                       "Jupiter": "year", "Saturn": "2½ years", "Rahu": "18 months"}[planet] + "."})
            j = nxt
    return out


def _stations(chart, start, end, tz_name):
    set_ayanamsha(chart["ayanamsha"])
    out, jd, jd_end = [], julian_day(start), julian_day(end)
    for planet in ["Mercury", "Venus", "Mars", "Jupiter", "Saturn"]:
        j = jd
        while j < jd_end:
            nxt = min(j + 0.5, jd_end)
            r0 = planet_longitude(j, planet)[1] < 0
            r1 = planet_longitude(nxt, planet)[1] < 0
            if r0 != r1:
                t = _bisect(j, nxt, lambda x: (planet_longitude(x, planet)[1] < 0) == r0)
                out.append({"when": _local(jd_to_datetime(t), tz_name), "planet": planet,
                            "text": f"**{planet}** turns **{'retrograde' if r1 else 'direct'}**: "
                                    + ("review, revise and avoid rushing its matters." if r1 else
                                       "delayed matters start moving again.")})
            j = nxt
    return out


def _dasha_changes(schedule, start, end, tz_name):
    out = []
    md, ad, _ = active_periods(schedule, start)
    if not md:
        return out
    for a in md["antardashas"]:
        if start < a["start"] <= end:
            out.append({"when": _local(a["start"], tz_name), "planet": a["lord"],
                        "text": f"Your **{a['lord']} Antardasha** begins: a new sub-chapter for months to come."})
        for p in sub_periods(a["lord"], a["start"], a["end"]):
            if start < p["start"] <= end:
                out.append({"when": _local(p["start"], tz_name), "planet": p["lord"],
                            "text": f"**{p['lord']} Pratyantardasha** begins (within {md['lord']}–{a['lord']}): "
                                    f"{p['lord']}'s themes colour the next few weeks."})
    return out


def _gochara_climate(chart, when):
    set_ayanamsha(chart["ayanamsha"])
    jd = julian_day(when)
    natal_moon = chart["planets"]["Moon"]["sign_idx"]
    out = []
    for planet in ["Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]:
        s = int(planet_longitude(jd, planet)[0] // 30)
        h_m, h_l = house_from(s, natal_moon), house_from(s, chart["asc_sign_idx"])
        good = h_m in GOCHARA_GOOD_FROM_MOON[planet]
        out.append({"planet": planet, "sign": SIGNS[s], "from_moon": h_m, "from_lagna": h_l, "good": good})
    return out


def week_forecast(chart, av, schedule, week_start, tz_name, sb=None):
    """Forecast for the 7 days starting on week_start (a date). Returns days, events and a summary."""
    days = [day_forecast(chart, av, schedule, week_start + dt.timedelta(days=i), tz_name) for i in range(7)]
    start = _utc(dt.datetime.combine(week_start, dt.time()), tz_name)
    end = start + dt.timedelta(days=7)
    mid = start + dt.timedelta(days=3.5)

    events = sorted(_sign_changes(chart, start, end, tz_name) + _stations(chart, start, end, tz_name)
                    + _dasha_changes(schedule, start, end, tz_name), key=lambda e: e["when"])

    md, ad, pd = active_periods(schedule, mid)
    climate = _gochara_climate(chart, mid)

    strong = []
    for planet in ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury"]:
        for t in transit_segments(chart, av, planet, start, end):
            if t["rating"] == "Strong":
                strong.append({**t, "start_local": _local(t["start"], tz_name), "end_local": _local(t["end"], tz_name)})

    bb = bhrigu_bindu(chart)
    bb_hits = contact_windows(chart, bb["lon"], ["Saturn", "Jupiter", "Rahu", "Mars", "Sun"], start, end, orb=2.0,
                              step_days=0.25)
    bcp = bcp_year(chart, mid)

    avg = sum(d["score"] for d in days) / 7
    good_climate = sum(c["good"] for c in climate)
    best = [d for d in sorted(days, key=lambda d: -d["score"]) if d["score"] >= 1][:3]
    hard = [d for d in sorted(days, key=lambda d: d["score"]) if d["score"] <= -2][:2]
    tone = ("a supportive week: momentum is on your side" if avg >= 1 else
            "a balanced week: steady effort pays" if avg >= -0.3 else
            "a week to pace yourself: protect energy and avoid forcing outcomes")

    focus_houses = {}
    for d in days:
        focus_houses[d["from_lagna"]] = focus_houses.get(d["from_lagna"], 0) + 1
    for t in strong:
        focus_houses[t["house"]] = focus_houses.get(t["house"], 0) + 2
    top_focus = sorted(focus_houses, key=lambda h: -focus_houses[h])[:3]

    summary = [
        f"Overall this is **{tone}** (average day score {avg:+.1f}; {good_climate} of 6 transiting planets are "
        "classically favourable from your Moon).",
        f"**Running periods:** {md['lord']} Mahadasha · {ad['lord']} Antardasha · {pd['lord']} Pratyantardasha. "
        f"{pd['lord']}'s themes are most immediate this week." if md else "",
        "**Where life is busiest:** " + "; ".join(f"{_domain(h)} ({ordinal(h)} house)" for h in top_focus) + ".",
    ]
    if best:
        summary.append("**Best days:** " + ", ".join(f"{d['weekday']} ({d['rating'].lower()})" for d in best)
                       + ". Use them for important meetings, starts and requests.")
    if hard:
        summary.append("**Go gently on:** " + ", ".join(
            f"{d['weekday']}" + (" (Chandrashtama)" if d["chandrashtama"] else f" ({d['tara']['name']} tara)")
            for d in hard) + ". Keep plans flexible and avoid big commitments.")
    if bb_hits:
        summary.append("**Bhrigu Bindu activated** by " + ", ".join(sorted({w['planet'] for w in bb_hits}))
                       + f": events this week touch {_domain(bb['house'])} and can have lasting impact.")
    summary.append(f"**Year theme (Bhrigu Chakra):** your {ordinal(bcp['house'])} house, {_domain(bcp['house'])}.")
    if sb:
        weak = [x["lord"] for x in (md, ad, pd) if x and x["lord"] in sb and sb[x["lord"]]["ratio"] < 1]
        if weak:
            summary.append(f"**Note:** {', '.join(weak)} (running period lord) is below its required Shadbala, so its "
                           "results this week need extra effort; see the Remedies tab.")

    return {"days": days, "events": events, "climate": climate, "strong": strong, "bb_hits": bb_hits,
            "bcp": bcp, "summary": [s for s in summary if s], "periods": (md, ad, pd), "average": avg}
