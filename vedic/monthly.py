"""Monthly forecast: calendar-month outlook for each area of life, key dates and a day calendar.

Each area (health, finance, career...) is tied to houses and natural significators. For the month:
- Transits: every planet's time in each sign is weighted by its Bhinna Ashtakavarga points there
  (4 is neutral; more bindus = good results, fewer = difficult), applied to the areas whose houses it occupies.
  Significators (e.g. Venus for relationships) add half weight wherever they transit.
- Aspects: Jupiter's aspect on an area house protects (+); Saturn's and Mars's add pressure (-).
- Dasha: the Mahadasha, Antardasha and Pratyantardasha lords activate the houses they rule and occupy, for
  better or worse depending on the house (e.g. the 6th and 8th lords activate health concerns) and on the
  lord's Shadbala.
- Saturn's Sade Sati or Ashtama phase weighs on health, career and family.

These are interpretive rules from classical Jyotish, for reflection and planning, not certainties.
"""
import calendar
import datetime as dt

import swisseph as swe

from .chart import house_from, julian_day, jd_to_datetime, planet_longitude, set_ayanamsha
from .constants import HOUSE_INFO, SIGN_LORDS, SIGNS, ordinal
from .dasha import active_periods, sub_periods
from .weekly import _dasha_changes, _local, _sign_changes, _stations, _utc, day_forecast, tithi_of

AREAS = {
    "Health": {"icon": "🩺", "good": [1], "bad": [6, 8], "karakas": ["Sun", "Moon"],
               "tips": {"up": "Good time to start a fitness or diet routine and keep up check-ups.",
                        "down": "Prioritise rest, sleep and routine check-ups; avoid overwork and risky activity."}},
    "Finance": {"icon": "💰", "good": [2, 11], "bad": [12], "karakas": ["Jupiter", "Venus"],
                "tips": {"up": "Favourable for saving, negotiating pay and planned investments.",
                         "down": "Budget carefully, avoid speculation and big unplanned purchases."}},
    "Career & Job": {"icon": "💼", "good": [10, 6, 11], "bad": [], "karakas": ["Sun", "Saturn", "Mercury"],
                     "tips": {"up": "Push important proposals, ask for responsibility, apply for roles.",
                              "down": "Keep your head down, document your work and avoid office politics."}},
    "Family & Home": {"icon": "🏠", "good": [4, 2], "bad": [], "karakas": ["Moon"],
                      "tips": {"up": "Good for family time, home improvements and property matters.",
                               "down": "Be patient at home; postpone property decisions and avoid arguments."}},
    "Relationships": {"icon": "💞", "good": [7], "bad": [], "karakas": ["Venus"],
                      "tips": {"up": "Warm month for partnerships, social life and commitments.",
                               "down": "Listen more, react less; give relationships space and avoid ultimatums."}},
    "Learning & Children": {"icon": "📚", "good": [5, 4], "bad": [], "karakas": ["Jupiter", "Mercury"],
                            "tips": {"up": "Start courses, creative projects and quality time with children.",
                                     "down": "Revise rather than start new studies; be gentle with children's pressures."}},
    "Travel & Foreign": {"icon": "✈️", "good": [3, 9, 12], "bad": [], "karakas": ["Rahu"],
                         "tips": {"up": "Good for trips, foreign contacts and relocation plans.",
                                  "down": "Plan travel with buffers; double-check documents and bookings."}},
    "Mind & Spirituality": {"icon": "🕉", "good": [9, 12, 5], "bad": [], "karakas": ["Moon", "Jupiter", "Ketu"],
                            "tips": {"up": "Good for meditation, retreats, pilgrimage and reflection.",
                                     "down": "Protect your peace: limit news and noise, keep a calming daily practice."}},
}
TRANSIT_WEIGHT = {"Saturn": 3, "Jupiter": 3, "Rahu": 2, "Ketu": 1.5, "Mars": 1.5, "Sun": 1, "Venus": 1, "Mercury": 1}
ASPECTS = {"Jupiter": ([5, 7, 9], +1.0), "Saturn": ([3, 7, 10], -1.0), "Mars": ([4, 7, 8], -0.5)}
NATURAL_MALEFICS = {"Saturn", "Mars", "Rahu", "Ketu", "Sun"}
RATINGS = [(2.2, "Excellent", "🟢"), (0.8, "Good", "🟢"), (-0.8, "Mixed", "🟡"), (-2.2, "Challenging", "🟠"),
           (-99, "Difficult", "🔴")]
DASHA_WEIGHT = {"MD": 1.0, "AD": 1.5, "PD": 1.0}


def _domain(h):
    return HOUSE_INFO[h][1].lower()


def _lord(chart, h):
    return SIGN_LORDS[SIGNS[(chart["asc_sign_idx"] + h - 1) % 12]]


def month_bounds(year, month, tz_name):
    first = dt.date(year, month, 1)
    last = dt.date(year, month, calendar.monthrange(year, month)[1])
    start = _utc(dt.datetime.combine(first, dt.time()), tz_name)
    end = _utc(dt.datetime.combine(last + dt.timedelta(days=1), dt.time()), tz_name)
    return first, last, start, end


def sign_occupancy(chart, planet, start, end, step_days=1.0):
    """{sign: fraction of the period} for a planet."""
    set_ayanamsha(chart["ayanamsha"])
    jd, jd_end = julian_day(start), julian_day(end)
    counts, n = {}, 0
    while jd < jd_end:
        s = int(planet_longitude(jd + step_days / 2, planet, chart["true_node"])[0] // 30)
        counts[s] = counts.get(s, 0) + 1
        n += 1
        jd += step_days
    return {s: c / n for s, c in counts.items()}


def _bav_effect(av, planet, sign):
    """Transit quality from Ashtakavarga: BAV for the 7 planets, SAV for the nodes (natural malefics)."""
    if planet in ("Rahu", "Ketu"):
        sav = av["sav"][sign]
        return (sav - 28) / 4, f"{sav} SAV"
    bav = av["bav"][planet][sign]
    return (bav - 4) / 2, f"{bav}/8 bindus"


def _lord_quality(chart, sb, lord):
    """+1 for a well-placed functional benefic, -1 for a weak lord of only difficult houses."""
    houses = [h for h in range(1, 13) if _lord(chart, h) == lord]
    good = any(h in (1, 4, 5, 7, 9, 10, 11, 2) for h in houses)
    bad_only = houses and all(h in (6, 8, 12) for h in houses)
    strong = sb.get(lord, {}).get("ratio", 1.0) >= 1 if lord in sb else True
    return (0.5 if good else 0) + (0.5 if strong else -0.5) - (0.5 if bad_only else 0)


def area_scores(chart, av, schedule, sb, start, end):
    """Score each area for the period. Returns {area: {"score", "drivers": [(value, text)]}}."""
    asc = chart["asc_sign_idx"]
    p = chart["planets"]
    occ = {pl: sign_occupancy(chart, pl, start, end, 1.0 if pl in ("Mars", "Sun", "Venus", "Mercury") else 5.0)
           for pl in TRANSIT_WEIGHT}
    mid = start + (end - start) / 2
    result = {a: {"score": 0.0, "drivers": []} for a in AREAS}

    def add(area, value, text):
        result[area]["score"] += value
        if abs(value) >= 0.2:
            result[area]["drivers"].append((value, text))

    # transits through area houses, and significators wherever they are
    for pl, shares in occ.items():
        for sign, share in shares.items():
            h = house_from(sign, asc)
            eff, why = _bav_effect(av, pl, sign)
            for area, spec in AREAS.items():
                if h in spec["good"] + spec["bad"]:
                    v = eff * TRANSIT_WEIGHT[pl] * share * (0.6 if pl in ("Sun", "Venus", "Mercury", "Mars") else 1)
                    if h in spec["bad"] and pl in NATURAL_MALEFICS and eff < 0:
                        v *= 1.3  # malefics weak in the 6th/8th/12th weigh more on that area
                    add(area, v, f"{pl} transits your {ordinal(h)} house with {why}")
                elif pl in spec["karakas"]:
                    add(area, 0.5 * eff * share, f"{pl}, a significator, transits with {why}")

    # aspects from slow planets (mid-month)
    set_ayanamsha(chart["ayanamsha"])
    jd_mid = julian_day(mid)
    for pl, (offsets, sign_val) in ASPECTS.items():
        s = int(planet_longitude(jd_mid, pl)[0] // 30)
        for off in offsets:
            h = house_from((s + off - 1) % 12, asc)
            for area, spec in AREAS.items():
                if h in spec["good"]:
                    add(area, sign_val * (0.8 if pl != "Mars" else 0.6),
                        f"{pl}'s {ordinal(off)} aspect on your {ordinal(h)} house "
                        + ("protects it" if sign_val > 0 else "adds pressure"))

    # dasha lords
    md, ad, _ = active_periods(schedule, mid)
    lords = []
    if md:
        lords += [("MD", md["lord"]), ("AD", ad["lord"])]
        pds = [x for x in sub_periods(ad["lord"], ad["start"], ad["end"]) if x["end"] > start and x["start"] < end]
        for x in pds:
            share = (min(x["end"], end) - max(x["start"], start)) / (end - start)
            lords.append(("PD", x["lord"], share))
    for item in lords:
        level, lord = item[0], item[1]
        share = item[2] if len(item) > 2 else 1.0
        q = _lord_quality(chart, sb, lord)
        ruled = [h for h in range(1, 13) if _lord(chart, h) == lord]
        placed = p[lord]["house"]
        for area, spec in AREAS.items():
            for h in set(ruled + [placed]):
                if h in spec["good"]:
                    add(area, DASHA_WEIGHT[level] * share * 0.8 * q,
                        f"{lord} ({'Mahadasha' if level == 'MD' else 'Antardasha' if level == 'AD' else 'Pratyantardasha'} "
                        f"lord) {'rules' if h in ruled else 'sits in'} your {ordinal(h)} house")
                elif h in spec["bad"]:
                    add(area, -DASHA_WEIGHT[level] * share * 0.6,
                        f"{lord} (running period lord) activates your {ordinal(h)} house")

    # Saturn from the Moon
    sat = int(planet_longitude(jd_mid, "Saturn")[0] // 30)
    hm = house_from(sat, p["Moon"]["sign_idx"])
    if hm in (12, 1, 2, 8):
        label = "Sade Sati" if hm != 8 else "Ashtama Shani"
        for area in ("Health", "Career & Job", "Family & Home"):
            add(area, -0.6 if hm != 1 and hm != 8 else -0.9, f"Saturn's {label} phase calls for patience")

    for area, spec in AREAS.items():
        # areas tied to more houses collect more influences; scale so every area is comparable
        result[area]["score"] /= len(spec["good"] + spec["bad"]) ** 0.5
        result[area]["drivers"].sort(key=lambda d: -abs(d[0]))
    return result


def rate(score):
    return next((name, icon) for limit, name, icon in RATINGS if score >= limit)


def area_text(area, data):
    spec = AREAS[area]
    rating, icon = rate(data["score"])
    pos = [t for v, t in data["drivers"] if v > 0][:2]
    neg = [t for v, t in data["drivers"] if v < 0][:2]
    lead = {"Excellent": "A standout month", "Good": "A supportive month", "Mixed": "A mixed month",
            "Challenging": "A month that needs care", "Difficult": "A demanding month"}[rating]
    text = f"**{lead} for {area.lower()}.** "
    if pos:
        text += "Helping: " + "; ".join(pos) + ". "
    if neg:
        text += "Watch: " + "; ".join(neg) + ". "
    text += spec["tips"]["up" if data["score"] >= 0 else "down"]
    return rating, icon, text


def _lunations_and_eclipses(chart, start, end, tz_name):
    set_ayanamsha(chart["ayanamsha"])
    asc = chart["asc_sign_idx"]
    jd, jd_end = julian_day(start), julian_day(end)
    out = []

    def tithi_at(j):
        m, _ = planet_longitude(j, "Moon")
        s, _ = planet_longitude(j, "Sun")
        return tithi_of(m, s)["number"]

    j = jd
    while j < jd_end:
        nxt = min(j + 0.25, jd_end)
        t0, t1 = tithi_at(j), tithi_at(nxt)
        if t0 != t1 and t1 in (1, 16):
            lo, hi = j, nxt
            while hi - lo > 1 / 1440:
                mid = (lo + hi) / 2
                lo, hi = (mid, hi) if tithi_at(mid) == t0 else (lo, mid)
            moon, _ = planet_longitude(hi, "Moon")
            h = house_from(int(moon // 30), asc)
            kind = "New Moon (Amavasya)" if t1 == 1 else "Full Moon (Purnima)"
            out.append({"when": _local(jd_to_datetime(hi), tz_name), "planet": "Moon",
                        "text": f"**{kind}** in {SIGNS[int(moon // 30)]}, your {ordinal(h)} house: "
                                + ("a fresh start for " if t1 == 1 else "a culmination around ") + _domain(h) + "."})
        j = nxt

    for finder, label in ((lambda t: swe.sol_eclipse_when_glob(t, swe.FLG_MOSEPH, 0, False), "Solar eclipse"),
                          (lambda t: swe.lun_eclipse_when(t, swe.FLG_MOSEPH, 0, False), "Lunar eclipse")):
        flag, tret = finder(jd)
        if jd <= tret[0] < jd_end:
            body = "Sun" if label.startswith("Solar") else "Moon"
            lon, _ = planet_longitude(tret[0], body)
            h = house_from(int(lon // 30), asc)
            kind = ("total" if flag & swe.ECL_TOTAL else "annular" if flag & swe.ECL_ANNULAR else
                    "partial" if flag & swe.ECL_PARTIAL else "penumbral")
            out.append({"when": _local(jd_to_datetime(tret[0]), tz_name), "planet": body,
                        "text": f"**{label}** ({kind}) in {SIGNS[int(lon // 30)]}, your {ordinal(h)} house: "
                                f"traditionally a time to avoid new starts; it can bring turning points in {_domain(h)}."})
    return out


def month_forecast(chart, av, schedule, sb, year, month, tz_name, place=None):
    first, last, start, end = month_bounds(year, month, tz_name)
    scores = area_scores(chart, av, schedule, sb, start, end)
    areas = []
    for area, data in scores.items():
        rating, icon, text = area_text(area, data)
        areas.append({"area": area, "icon": AREAS[area]["icon"], "score": round(data["score"], 2),
                      "rating": rating, "rating_icon": icon, "text": text})

    days = [day_forecast(chart, av, schedule, first + dt.timedelta(days=i), tz_name, place)
            for i in range((last - first).days + 1)]
    events = sorted(_sign_changes(chart, start, end, tz_name) + _stations(chart, start, end, tz_name)
                    + _dasha_changes(schedule, start, end, tz_name)
                    + _lunations_and_eclipses(chart, start, end, tz_name), key=lambda e: e["when"])

    md, ad, pd = active_periods(schedule, start + (end - start) / 2)
    best = sorted(days, key=lambda d: -d["score"])[:4]
    hard = [d for d in days if d["chandrashtama"]]
    ranked = sorted(areas, key=lambda a: -a["score"])
    avg = sum(a["score"] for a in areas) / len(areas)
    tone = ("a strong, forward-moving month" if avg >= 1 else "a steady, constructive month" if avg >= 0 else
            "a month to consolidate rather than push" if avg >= -1 else "a demanding month: pace yourself")
    summary = [
        f"**{calendar.month_name[month]} {year}** looks like **{tone}**.",
        f"**Running periods:** {md['lord']} Mahadasha · {ad['lord']} Antardasha · {pd['lord']} Pratyantardasha."
        if md else "",
        f"**Brightest areas:** {ranked[0]['area']} ({ranked[0]['rating'].lower()}) and {ranked[1]['area']} "
        f"({ranked[1]['rating'].lower()}). **Needs most care:** {ranked[-1]['area']} ({ranked[-1]['rating'].lower()}).",
        "**Best days:** " + ", ".join(f"{d['date']:%a %d}" for d in sorted(best, key=lambda d: d["date"])) + ".",
    ]
    if hard:
        spans = []
        for d in hard:
            if spans and (d["date"] - spans[-1][1]).days == 1:
                spans[-1][1] = d["date"]
            else:
                spans.append([d["date"], d["date"]])
        summary.append("**Go gently (Chandrashtama):** " + ", ".join(
            f"{a:%d}" + (f"–{b:%d %b}" if b != a else f" {a:%b}") for a, b in spans) + ".")
    eclipses = [e for e in events if "eclipse" in e["text"]]
    if eclipses:
        summary.append("**Eclipse this month:** " + "; ".join(f"{e['when']:%d %b}" for e in eclipses)
                       + ". Avoid major new starts within a few days of it.")
    return {"year": year, "month": month, "first": first, "last": last, "areas": areas, "days": days,
            "events": events, "summary": [s for s in summary if s], "periods": (md, ad, pd)}


def year_overview(chart, av, schedule, sb, start_year, start_month, months, tz_name):
    """Area ratings for several months (no day calendar), for the 12-month overview."""
    rows = []
    y, m = start_year, start_month
    for _ in range(months):
        _, _, start, end = month_bounds(y, m, tz_name)
        scores = area_scores(chart, av, schedule, sb, start, end)
        rows.append({"label": f"{calendar.month_abbr[m]} {y}",
                     **{a: round(d["score"], 2) for a, d in scores.items()}})
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return rows
