"""Chart evaluation behind the remedies: functional roles, doshas, a severity score and upcoming triggers.

1. Functional nature (Parashari, by Lagna): lords of trines (1, 5, 9) are benefic, lords of 3, 6 and 11 malefic,
   the 8th lord malefic (unless it also rules the Lagna), kendra lords (4, 7, 10) neutral, a lord of both a kendra
   and a trine is Yogakaraka; 2nd and 12th lords are neutral. Also marked: the Badhaka lord (11th for movable,
   9th for fixed, 7th for dual Lagnas) and the Marakas (2nd and 7th lords). This decides the approach:
   a weak functional benefic is *strengthened*; a functional malefic (or a node) is *pacified*, never given a
   gemstone; neutral or mixed planets are *balanced*.
2. Doshas, each with its classical cancellations: Manglik, Kaal Sarp, Pitru, Grahan, Guru Chandal, Shrapit,
   Angarak, Visha, Kemadruma and Gandanta.
3. Severity 0-100: natal weakness and affliction, confirmed or eased by the D9 and Vimshopaka Bala, with
   protective factors subtracted. Every factor is listed with its points.
4. Upcoming triggers in the next three years: Antardashas of planets that need care, Rahu/Ketu and Saturn
   crossing the natal Moon or Lagna, Saturn's Moon phases and eclipses on natal planets.

Traditions differ on several of these rules; the conventions used are stated in each function.
"""
import datetime as dt

import swisseph as swe

from .aspects import ASPECT_HOUSES, combustion, influences
from .chart import julian_day, jd_to_datetime, planet_longitude, set_ayanamsha
from .constants import (ALL_PLANETS, CLASSICAL_PLANETS, DEBILITATION_SIGNS, EXALTATION_SIGNS, HOUSE_INFO, OWN_SIGNS,
                        SIGN_LORDS, SIGNS, ordinal)
from .insights import neecha_bhanga, ruled_houses
from .transits import saturn_timeline, segments_by
from .vimshopaka import vimshopaka

GENTLE = {"Moon", "Mercury", "Jupiter", "Venus"}
HOUSE_POINTS = {1: 2, 5: 2, 9: 2, 4: 0, 7: 0, 10: 0, 2: 0, 12: 0, 3: -1, 6: -1, 11: -1, 8: -2}
ROLE_APPROACH = {"Yogakaraka": "Strengthen", "Functional benefic": "Strengthen", "Neutral": "Balance",
                 "Mixed": "Balance", "Functional malefic": "Pacify", "Shadow planet": "Pacify"}
APPROACH_TEXT = {
    "Strengthen": "This planet works for you, so remedies aim to **strengthen** it: its mantra, wearing its colour "
                  "on its weekday and (only where marked safe) its gemstone.",
    "Pacify": "This planet's lordship is difficult for your Lagna (or it is a node), so remedies aim to **pacify** "
              "it: charity, service and mantra. Never strengthen it with a gemstone.",
    "Balance": "This planet's role is mixed, so remedies aim to **balance** it with mantra, charity and good habits; "
               "no gemstone.",
}
LEVELS = [(60, "High"), (35, "Medium"), (15, "Low"), (-1, "None")]


def level(score):
    return next(name for limit, name in LEVELS if score >= limit)


def _sign_of_house(chart, h):
    return (chart["asc_sign_idx"] + h - 1) % 12


def _aspects(planet, from_sign, target_sign):
    return (target_sign - from_sign) % 12 + 1 in ASPECT_HOUSES[planet]


def _jupiter_on(chart, sign):
    j = chart["planets"]["Jupiter"]["sign_idx"]
    return j == sign or _aspects("Jupiter", j, sign)


def _together(chart, a, b):
    return chart["planets"][a]["sign_idx"] == chart["planets"][b]["sign_idx"]


# --------------------------------------------------------------------------------------
# 1. Functional nature
# --------------------------------------------------------------------------------------
def badhaka_house(chart):
    return {0: 11, 1: 9, 2: 7}[chart["asc_sign_idx"] % 3]


def functional_roles(chart):
    """{planet: {"role", "approach", "houses", "tags", "why"}} for all nine planets."""
    bad_h = badhaka_house(chart)
    lord = lambda h: SIGN_LORDS[SIGNS[_sign_of_house(chart, h)]]  # noqa: E731
    out = {}
    for n in ALL_PLANETS:
        tags = []
        if n in ("Rahu", "Ketu"):
            disp = SIGN_LORDS[chart["planets"][n]["sign"]]
            out[n] = {"role": "Shadow planet", "approach": "Pacify", "houses": [], "tags": tags,
                      "why": f"A node: it gives the results of its sign lord {disp} and of the "
                             f"{ordinal(chart['planets'][n]['house'])} house it occupies."}
            continue
        houses = ruled_houses(chart, n)
        pts = {h: HOUSE_POINTS[h] for h in houses}
        if 1 in houses and 8 in houses:
            pts[8] = 0  # the Lagna lord is never a malefic for its own chart
        kendra, trine = set(houses) & {4, 7, 10}, set(houses) & {1, 5, 9}
        if kendra and trine and 1 not in houses:
            role = "Yogakaraka"
        elif 1 in houses:
            role = "Functional benefic"
        else:
            total = sum(pts.values())
            role = ("Functional benefic" if total >= 2 else "Functional malefic" if total < 0 and not trine else
                    "Mixed" if any(v > 0 for v in pts.values()) and any(v < 0 for v in pts.values()) else "Neutral")
        if lord(bad_h) == n:
            tags.append("Badhaka (obstruction)")
        if n in (lord(2), lord(7)):
            tags.append("Maraka (drains vitality in its periods)")
        out[n] = {"role": role, "approach": ROLE_APPROACH[role], "houses": houses, "tags": tags,
                  "why": "Rules your " + " and ".join(f"{ordinal(h)} ({HOUSE_INFO[h][1].split(',')[0].lower()})"
                                                      for h in houses) + "."}
    return out


# --------------------------------------------------------------------------------------
# 2. Doshas
# --------------------------------------------------------------------------------------
def _d(name, present, planets, condition, cancellations, remedy, weight=10):
    cancelled = bool(present and cancellations)
    return {"name": name, "present": present, "planets": planets if present else [], "condition": condition,
            "cancellations": cancellations if present else [], "cancelled": cancelled,
            "status": "Not present" if not present else "Present, eased" if cancelled else "Present",
            "remedy": remedy, "weight": weight if present else 0}


def doshas(chart):
    p = chart["planets"]
    asc = chart["asc_sign_idx"]
    out = []

    refs = {"Lagna": asc, "Moon": p["Moon"]["sign_idx"], "Venus": p["Venus"]["sign_idx"]}
    from_ = [r for r, s in refs.items() if (p["Mars"]["sign_idx"] - s) % 12 + 1 in (1, 2, 4, 7, 8, 12)]
    canc = []
    if p["Mars"]["sign"] in ("Aries", "Scorpio", "Capricorn"):
        canc.append(f"Mars is in {p['Mars']['sign']}, its own or exaltation sign")
    if p["Mars"]["sign"] in ("Leo", "Aquarius"):
        canc.append(f"Mars in {p['Mars']['sign']} is a commonly cited exception")
    if _jupiter_on(chart, p["Mars"]["sign_idx"]):
        canc.append("Jupiter aspects or joins Mars")
    out.append(_d("Manglik (Kuja) dosha", bool(from_), ["Mars"],
                  f"Mars in the 1st, 2nd, 4th, 7th, 8th or 12th from the {', '.join(from_) or 'Lagna, Moon or Venus'}",
                  canc, "Hanuman Chalisa on Tuesdays, red lentils in charity; traditionally matched with a partner "
                        "who has a similar placement. Many astrologers consider it eased after age 28.",
                  weight=6 + 3 * len(from_)))

    rahu = p["Rahu"]["lon"]
    side = [(p[n]["lon"] - rahu) % 360 < 180 for n in CLASSICAL_PLANETS]
    hemmed = all(side) or not any(side)
    out.append(_d("Kaal Sarp yoga", hemmed, ["Rahu", "Ketu"],
                  "All seven planets lie on one side of the Rahu-Ketu axis",
                  ["Not described in the classical Parashari texts; treated as a later tradition"] if hemmed else [],
                  "Worship of Shiva (Maha Mrityunjaya mantra) or Nag Panchami observance; Rahu-Ketu mantras.", 8))

    pitru_why = []
    for n in ("Rahu", "Ketu", "Saturn"):
        if _together(chart, "Sun", n):
            pitru_why.append(f"Sun with {n}")
    lord9 = SIGN_LORDS[SIGNS[_sign_of_house(chart, 9)]]
    for n in ("Rahu", "Ketu"):
        if p[n]["house"] == 9:
            pitru_why.append(f"{n} in the 9th house")
        if lord9 not in (n,) and _together(chart, lord9, n):
            pitru_why.append(f"9th lord {lord9} with {n}")
    canc = ["Jupiter aspects or joins the Sun or the 9th house"] if pitru_why and (
        _jupiter_on(chart, p["Sun"]["sign_idx"]) or _jupiter_on(chart, _sign_of_house(chart, 9))) else []
    out.append(_d("Pitru dosha", bool(pitru_why), ["Sun", "Rahu", "Saturn", "Ketu"] if pitru_why else [],
                  "; ".join(pitru_why) or "Sun with Rahu, Ketu or Saturn, or the nodes in or with the 9th lord",
                  canc, "Tarpan or Shraddha for ancestors (especially during Pitru Paksha), feeding crows and the "
                        "needy on Amavasya, respecting and serving elders.", 9))

    gr = [f"{l} with {n}" for l in ("Sun", "Moon") for n in ("Rahu", "Ketu") if _together(chart, l, n)]
    canc = [f"Jupiter protects the {l}" for l in ("Sun", "Moon")
            if any(x.startswith(l) for x in gr) and _jupiter_on(chart, p[l]["sign_idx"])]
    out.append(_d("Grahan dosha", bool(gr), sorted({x.split()[0] for x in gr} | {x.split()[-1] for x in gr}),
                  "; ".join(gr) or "Sun or Moon in the same sign as Rahu or Ketu", canc,
                  "Surya or Chandra mantras on Sundays/Mondays; charity and quiet reflection on eclipse days.", 8))

    gc = _together(chart, "Jupiter", "Rahu")
    out.append(_d("Guru Chandal yoga", gc, ["Jupiter", "Rahu"], "Jupiter in the same sign as Rahu",
                  [f"Jupiter is strong in {p['Jupiter']['sign']}"] if gc and p["Jupiter"]["dignity"] in
                  ("Exalted", "Own Sign") else [],
                  "Respect teachers and elders, Guru mantra on Thursdays, avoid shortcuts in ethics and money.", 8))
    sh = _together(chart, "Saturn", "Rahu")
    out.append(_d("Shrapit dosha", sh, ["Saturn", "Rahu"], "Saturn in the same sign as Rahu",
                  ["Jupiter aspects them"] if sh and _jupiter_on(chart, p["Saturn"]["sign_idx"]) else [],
                  "Shani and Rahu mantras on Saturdays, service to the elderly and labourers, mustard oil in charity.",
                  9))
    an = _together(chart, "Mars", "Rahu")
    out.append(_d("Angarak yoga", an, ["Mars", "Rahu"], "Mars in the same sign as Rahu",
                  ["Jupiter aspects them"] if an and _jupiter_on(chart, p["Mars"]["sign_idx"]) else [],
                  "Hanuman worship on Tuesdays, physical exercise to channel energy, avoid confrontation.", 8))
    vi = _together(chart, "Saturn", "Moon")
    out.append(_d("Visha yoga", vi, ["Saturn", "Moon"], "Saturn in the same sign as the Moon",
                  ["Jupiter aspects the Moon"] if vi and _jupiter_on(chart, p["Moon"]["sign_idx"]) else [],
                  "Shiva worship on Mondays, Om Namah Shivaya, regular sleep and routine; talk worries through.", 8))

    moon = p["Moon"]["sign_idx"]
    flank = [n for n in ("Mars", "Mercury", "Jupiter", "Venus", "Saturn")
             if p[n]["sign_idx"] in ((moon + 1) % 12, (moon - 1) % 12)]
    km = not flank and not any(p[n]["sign_idx"] == moon for n in ("Mars", "Mercury", "Jupiter", "Venus", "Saturn"))
    canc = []
    if km:
        k_moon = [n for n in ("Mars", "Mercury", "Jupiter", "Venus", "Saturn")
                  if (p[n]["sign_idx"] - moon) % 12 in (0, 3, 6, 9)]
        k_lag = [n for n in ("Mars", "Mercury", "Jupiter", "Venus", "Saturn") if p[n]["house"] in (1, 4, 7, 10)]
        if k_moon:
            canc.append(f"{', '.join(k_moon)} in a kendra from the Moon")
        if k_lag:
            canc.append(f"{', '.join(k_lag)} in a kendra from the Lagna")
        if _jupiter_on(chart, moon):
            canc.append("Jupiter aspects the Moon")
    out.append(_d("Kemadruma yoga", km, ["Moon"], "No planet (other than the Sun and nodes) in the 2nd or 12th from, "
                                                  "or with, the Moon", canc,
                  "Monday fasts or Chandra mantra, staying connected with friends and family, Shiva worship.", 7))

    gand = []
    for n in ("Ascendant", "Moon") + tuple(CLASSICAL_PLANETS):
        lon = p[n]["lon"]
        pos = lon % 120  # junctions at 0, 120 and 240 degrees (Pisces-Aries, Cancer-Leo, Scorpio-Sagittarius)
        if pos >= 120 - 10 / 3 or pos < 10 / 3:
            gand.append("Lagna" if n == "Ascendant" else n)
    key_gand = [g for g in gand if g in ("Lagna", "Moon")]
    out.append(_d("Gandanta", bool(key_gand), key_gand if key_gand else [],
                  f"{', '.join(key_gand) or 'Moon or Lagna'} within 3°20' of a water-fire sign junction"
                  + (f" (also: {', '.join(g for g in gand if g not in key_gand)})"
                     if key_gand and len(gand) > len(key_gand) else ""), [],
                  "Ganesha worship and the nakshatra shanti traditionally done for Gandanta births; steady routines.",
                  8))
    return out


# --------------------------------------------------------------------------------------
# 3. Severity
# --------------------------------------------------------------------------------------
def _f(points, text):
    return {"points": points, "text": text}


def severity(chart, av, planet, sb=None, vb=None, dosha_list=None, roles=None):
    """{"score": 0-100, "level", "factors": [{"points", "text"}]} for how much attention the planet needs."""
    p = chart["planets"][planet]
    f = []
    if p["dignity"] == "Debilitated":
        f.append(_f(8, f"Debilitated in {p['sign']}, but cancelled (Neecha Bhanga)") if neecha_bhanga(chart, planet)
                 else _f(25, f"Debilitated in {p['sign']} (its weakest sign)"))
    elif p["dignity"] in ("Exalted", "Own Sign"):
        f.append(_f(-10, f"{'Exalted' if p['dignity'] == 'Exalted' else 'In its own sign'} in {p['sign']}"))
    if p["house"] in (8, 12) or (p["house"] == 6 and planet in GENTLE):
        f.append(_f(12, f"In the {ordinal(p['house'])} house ({HOUSE_INFO[p['house']][1].lower()}), a difficult house"))
    if planet in CLASSICAL_PLANETS:
        b = av["bav"][planet][p["sign_idx"]]
        if b <= 3:
            f.append(_f(16 if b <= 2 else 12, f"Only {b}/8 Ashtakavarga points where it sits (4 is average)"))
        elif b >= 6:
            f.append(_f(-6, f"{b}/8 Ashtakavarga points where it sits (strong)"))
    if sb and planet in sb:
        r = sb[planet]["ratio"]
        if r < 1:
            f.append(_f(round(min(20, 8 + (1 - r) * 40)), f"Shadbala {r:.2f}× its required minimum"))
        elif r >= 1.3:
            f.append(_f(-6, f"Shadbala {r:.2f}× its required minimum (strong)"))
    comb = combustion(chart, planet)
    if comb:
        f.append(_f(4 if planet == "Mercury" else 12, f"Combust, {comb['distance']:.1f}° from the Sun"))
    if planet not in ("Rahu", "Ketu"):
        inf = influences(chart, planet)
        if inf["malefic"]:
            f.append(_f(12 if len(inf["malefic"]) >= 2 else 5, "Malefic pressure: " + " and ".join(inf["malefic"])))
        if inf["jupiter"] and planet != "Jupiter":
            f.append(_f(-8, "Protected by " + " and ".join(inf["jupiter"])))
    else:
        if p["house"] in (1, 5, 7, 8, 9, 12):
            f.append(_f(8, f"Node in the {ordinal(p['house'])} house, a sensitive placement for the nodes"))
    if planet in CLASSICAL_PLANETS:
        d9 = p["d9_sign"]
        if d9 == DEBILITATION_SIGNS[planet]:
            f.append(_f(10, f"Also debilitated in the Navamsa (D9, {d9}): the weakness is confirmed"))
        elif d9 == EXALTATION_SIGNS[planet] or d9 in OWN_SIGNS[planet]:
            f.append(_f(-10, f"Strong in the Navamsa (D9, {d9}): inner strength eases the birth-chart weakness"))
        if p["d9_sign"] == p["sign"]:
            f.append(_f(-8, "Vargottama (same sign in D1 and D9): steady and reliable"))
        if vb:
            v = vb[planet]["scores"]["Shodashavarga (16)"]
            if v < 10:
                f.append(_f(8, f"Vimshopaka Bala {v:.1f}/20: weak across the divisional charts"))
            elif v >= 15:
                f.append(_f(-8, f"Vimshopaka Bala {v:.1f}/20: well supported across the divisional charts"))
    for d in dosha_list or []:
        if planet in d["planets"]:
            f.append(_f(3 if d["cancelled"] else d["weight"], f"Part of {d['name']}"
                        + (" (eased by cancellations)" if d["cancelled"] else "")))
    if roles and roles[planet]["role"] == "Functional malefic" and sum(x["points"] for x in f if x["points"] > 0):
        f.append(_f(5, "A functional malefic for your Lagna, so its afflictions weigh more"))
    score = max(0, min(100, sum(x["points"] for x in f)))
    return {"score": score, "level": level(score), "factors": f}


# --------------------------------------------------------------------------------------
# 4. Upcoming triggers
# --------------------------------------------------------------------------------------
def upcoming(chart, schedule, scores, roles, start, years=3):
    """Time-bound triggers in the next `years`: [{"start", "end", "planet", "what", "why", "begin_by"}]."""
    end = start + dt.timedelta(days=round(365.25 * years))
    rows = []
    for md in schedule:
        for ad in md["antardashas"]:
            if not (start < ad["start"] < end):
                continue
            why = []
            if scores[ad["lord"]]["score"] >= 35:
                why.append(f"{ad['lord']} needs care (severity {scores[ad['lord']]['score']})")
            if roles[ad["lord"]]["role"] == "Functional malefic":
                why.append(f"{ad['lord']} is a functional malefic for your Lagna")
            tags = [t.split(" (")[0] for t in roles[ad["lord"]]["tags"]]
            if tags and why:
                why.append("also " + " and ".join(tags))
            rel = (chart["planets"][ad["lord"]]["sign_idx"] - chart["planets"][md["lord"]]["sign_idx"]) % 12 + 1
            if rel in (6, 8, 12, 2) and md["lord"] != ad["lord"]:
                why.append(f"the two period lords sit {ordinal(rel)} from each other (a tense pairing)")
            if why:
                rows.append({"start": ad["start"], "end": ad["end"], "planet": ad["lord"],
                             "what": f"{md['lord']}–{ad['lord']} sub-period begins", "why": "; ".join(why)})
    set_ayanamsha(chart["ayanamsha"])
    p = chart["planets"]
    lookback = start - dt.timedelta(days=round(365.25 * 3))  # so a phase already running isn't reported as new

    def first_new(items):
        """First occurrence of each label; dropped if it had already started before `start`
        (retrograde re-entries repeat a transit several times)."""
        seen = {}
        for label, a, b in items:
            seen.setdefault(label, (a, b))
        return [(label, a, b) for label, (a, b) in seen.items() if a > start]

    targets = {"Moon": p["Moon"]["sign_idx"], "Lagna": chart["asc_sign_idx"]}
    for body in ("Rahu", "Ketu", "Saturn"):
        hits = [(f"{body} transits your natal {label} sign ({SIGNS[s]})", a, b)
                for s, a, b in segments_by(chart, body, lookback, end, lambda lon: int(lon // 30), step_days=3)
                for label, t in targets.items() if s == t and not (body == "Saturn" and label == "Moon")]
        for what, a, b in first_new(hits):
            rows.append({"start": a, "end": b, "planet": body, "what": what,
                         "why": "a classic period of pressure on the " + ("mind and emotions" if "Moon" in what
                                                                          else "body and direction")})
    phases, _ = saturn_timeline(chart, lookback, end)
    for what, a, b in first_new([(ph["phase"], ph["start"], ph["end"]) for ph in phases]):
        rows.append({"start": a, "end": b, "planet": "Saturn", "what": what + " begins",
                     "why": "Saturn's phases from the Moon test patience, health and routines"})
    natal = {n: p[n]["lon"] for n in ["Ascendant"] + CLASSICAL_PLANETS}
    jd, jd_end = julian_day(start), julian_day(end)
    for finder, label, body in ((lambda t: swe.sol_eclipse_when_glob(t, swe.FLG_MOSEPH, 0, False), "Solar eclipse",
                                 "Sun"), (lambda t: swe.lun_eclipse_when(t, swe.FLG_MOSEPH, 0, False),
                                          "Lunar eclipse", "Moon")):
        t = jd
        while True:
            _, tret = finder(t)
            if tret[0] >= jd_end:
                break
            lon, _ = planet_longitude(tret[0], body)
            hit = [n for n, nl in natal.items() if min(abs(lon - nl) % 360, 360 - abs(lon - nl) % 360) <= 5]
            if hit:
                when = jd_to_datetime(tret[0])
                names = ["Lagna" if n == "Ascendant" else n for n in hit]
                rows.append({"start": when, "end": when + dt.timedelta(days=1), "planet": names[0],
                             "what": f"{label} on your natal {', '.join(names)} ({SIGNS[int(lon // 30)]})",
                             "why": "eclipses on natal points can trigger turning points for that planet's matters"})
            t = tret[0] + 20
    for r in rows:
        lead = 3 if (r["end"] - r["start"]).days <= 2 else 30
        r["begin_by"] = r["start"] - dt.timedelta(days=lead)
    return sorted(rows, key=lambda r: r["start"])


def evaluate(chart, av, sb=None):
    """Everything the remedies need that does not depend on today's date."""
    roles = functional_roles(chart)
    ds = doshas(chart)
    vb = vimshopaka(chart)
    scores = {n: severity(chart, av, n, sb, vb, ds, roles) for n in ALL_PLANETS}
    return {"roles": roles, "doshas": ds, "scores": scores, "vimshopaka": vb}
