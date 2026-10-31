"""Life-area readings (Health, Wealth, Relationships, Children, Education, Home & Family, Travel & Foreign,
Spirituality) built the Parashari way:

1. Promise in the birth chart: each area's houses (Ashtakavarga points, lord's placement, dignity and Shadbala,
   occupants and aspects), its significators (karakas) and its divisional chart. Every factor scores
   +1, 0 or -1 and is listed with the reason, so the overall rating can be checked.
2. Timing: Vimshottari Antardashas of the planets that rule, occupy or signify the area, and the slow
   transits (Jupiter, Saturn, Rahu) over its houses, including the Jupiter + Saturn "double transit".
3. Area-specific classical checks (e.g. Manglik dosha, Dhana yogas, foreign-travel indicators).

The career area lives in career.py (Job page). Readings are guidance for reflection, not certainties.
"""
import datetime as dt

from .aspects import ASPECT_HOUSES, combustion
from .constants import (CLASSICAL_PLANETS, DEBILITATION_SIGNS, EXALTATION_SIGNS, HOUSE_INFO, OWN_SIGNS, SIGN_LORDS,
                        SIGNS, ordinal)
from .houses import arudha_padas
from .insights import neecha_bhanga
from .transits import segments_by
from .vargas import VARGAS, varga_positions
from .yogas import connection, detect_yogas

KENDRA_TRIKONA = {1, 4, 5, 7, 9, 10}
DUSTHANAS = {6, 8, 12}
UPACHAYAS = {3, 6, 10, 11}
BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}

AREAS = {
    "Health": {
        "icon": "🩺", "houses": [1, 6, 8], "karakas": ["Sun", "Moon"], "special": [], "varga": ("D30", 1),
        "monthly": "Health",
        "intro": "Health is read from the **1st house** (body and vitality), the **6th** (illness and the power to "
                 "overcome it) and the **8th** (longevity and chronic or sudden issues), with the **Sun** (vitality) "
                 "and **Moon** (mind and body fluids) as significators and the **D30** chart for misfortunes.",
        "good": "Good time to start a fitness routine, preventive check-ups and healthy habits.",
        "watch": "Pace yourself: keep up check-ups, sleep and routine, and don't ignore early symptoms.",
    },
    "Wealth": {
        "icon": "💰", "houses": [2, 11, 9], "karakas": ["Jupiter", "Venus"], "special": [], "varga": None,
        "monthly": "Finance",
        "intro": "Wealth is read from the **2nd house** (savings and family assets), the **11th** (income and gains) "
                 "and the **9th** (fortune), with **Jupiter** (wealth) and **Venus** (comforts) as significators, "
                 "**Dhana yogas**, the **D2 (Hora)** chart and the 11th and 12th from the **Arudha Lagna**.",
        "good": "Favourable for saving, investing to a plan and negotiating income.",
        "watch": "Budget carefully; avoid speculation, lending large sums and impulse purchases.",
    },
    "Relationships": {
        "icon": "💞", "houses": [7, 2], "karakas": ["Venus"], "special": ["DK"], "varga": ("D9", 7),
        "monthly": "Relationships",
        "intro": "Marriage and partnership are read from the **7th house** (spouse and partners) and the **2nd** "
                 "(family life), with **Venus** (love; Jupiter is also read for a husband), the **Darakaraka** "
                 "(spouse significator), the **D9 (Navamsa)** chart and the **Upapada**.",
        "good": "Warm period for commitments, meeting people and strengthening bonds.",
        "watch": "Listen more and react less; avoid ultimatums and big relationship decisions in haste.",
    },
    "Children": {
        "icon": "👶", "houses": [5, 9], "karakas": ["Jupiter"], "special": ["PK"], "varga": ("D7", 5),
        "monthly": "Learning & Children",
        "intro": "Children are read from the **5th house** (children and creativity) and the **9th** (the 5th from "
                 "the 5th), with **Jupiter** (Putrakaraka) and the Jaimini **Putrakaraka**, the **D7 (Saptamsa)** "
                 "chart and Jupiter's own Ashtakavarga.",
        "good": "Supportive for family planning, time with children and their milestones.",
        "watch": "Be patient with children's pressures; plan family matters with medical advice.",
    },
    "Education": {
        "icon": "🎓", "houses": [4, 5, 9, 2], "karakas": ["Mercury", "Jupiter"], "special": [], "varga": ("D24", 4),
        "monthly": "Learning & Children",
        "intro": "Learning is read from the **4th house** (formal education), the **5th** (intelligence), the **9th** "
                 "(higher studies) and the **2nd** (early learning and speech), with **Mercury** (intellect) and "
                 "**Jupiter** (wisdom) as significators and the **D24 (Chaturvimshamsa)** chart.",
        "good": "Good time to start courses, exams, certifications and research.",
        "watch": "Revise and consolidate rather than starting new studies; protect your concentration.",
    },
    "Home & Family": {
        "icon": "🏠", "houses": [4, 2, 9, 3], "karakas": ["Moon", "Mars"], "special": [], "varga": ("D4", 4),
        "monthly": "Family & Home",
        "intro": "Home and family are read from the **4th house** (home, mother, property, vehicles), the **2nd** "
                 "(family), the **9th** (father) and the **3rd/11th** (siblings), with the **Moon** (mother, home), "
                 "**Sun** (father), **Mars** (land, siblings) and **Venus** (vehicles), and the D4, D12, D16 and D3 "
                 "charts.",
        "good": "Good for property matters, home improvements and family time.",
        "watch": "Be patient at home; check property papers twice and postpone big purchases if you can.",
    },
    "Travel & Foreign": {
        "icon": "✈️", "houses": [12, 9, 3], "karakas": ["Rahu", "Moon"], "special": [], "varga": None,
        "monthly": "Travel & Foreign",
        "intro": "Travel and foreign links are read from the **12th house** (foreign lands and residence abroad), the "
                 "**9th** (long journeys) and the **3rd** (short trips), with **Rahu** (foreign influences) and the "
                 "**Moon** (movement), and classical indicators for living abroad.",
        "good": "Good for trips, visas, foreign contacts and relocation plans.",
        "watch": "Plan journeys with buffers; double-check documents, bookings and visas.",
    },
    "Spirituality": {
        "icon": "🕉", "houses": [9, 12, 5], "karakas": ["Jupiter", "Ketu"], "special": ["AK"], "varga": ("D20", 9),
        "monthly": "Mind & Spirituality",
        "intro": "Spiritual life is read from the **9th house** (dharma, teachers), the **12th** (liberation, "
                 "retreat) and the **5th** (mantra and devotion), with **Jupiter** (wisdom), **Ketu** (detachment), "
                 "the **Karakamsha** (Atmakaraka in the D9) and the **D20 (Vimshamsa)** chart.",
        "good": "Good for meditation, retreats, pilgrimage and study of scriptures.",
        "watch": "Protect your peace: keep a simple daily practice and limit noise and overcommitment.",
    },
}

SIGN_BODY = ["head and face", "throat, neck and mouth", "shoulders, arms and lungs", "chest and stomach",
             "heart and spine", "intestines and digestion", "kidneys and lower back", "reproductive and excretory organs",
             "hips, thighs and liver", "knees, bones and joints", "calves, ankles and circulation", "feet, lymph and sleep"]
PLANET_BODY = {"Sun": "heart, eyes, bones and vitality", "Moon": "mind, sleep, body fluids and chest",
               "Mars": "blood, muscles, injuries and inflammation", "Mercury": "nerves, skin, speech and breathing",
               "Jupiter": "liver, fat and sugar metabolism", "Venus": "kidneys, hormones and reproductive health",
               "Saturn": "joints, teeth, chronic conditions and stamina",
               "Rahu": "toxins, allergies and hard-to-diagnose issues", "Ketu": "infections and sudden, unclear issues"}
PLANET_SUBJECTS = {"Sun": "administration, political science, medicine", "Moon": "psychology, nursing, literature",
                   "Mars": "engineering, surgery, sports science", "Mercury": "mathematics, commerce, IT, languages",
                   "Jupiter": "law, finance, philosophy, teaching", "Venus": "arts, design, music, media",
                   "Saturn": "history, geology, civil or mechanical engineering",
                   "Rahu": "computing, AI, aviation, foreign languages", "Ketu": "research, coding, mathematics, "
                                                                             "spiritual studies"}
FAMILY_PARTS = [  # (label, houses, karaka, varga, varga house)
    ("Home & property", [4], "Mars", "D4", 4),
    ("Vehicles & comforts", [4], "Venus", "D16", 4),
    ("Mother", [4], "Moon", "D12", 4),
    ("Father", [9], "Sun", "D12", 9),
    ("Siblings", [3, 11], "Mars", "D3", 3),
    ("Family life", [2], "Jupiter", "D9", 2),
]


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------
def lord_of(chart, house):
    return SIGN_LORDS[SIGNS[(chart["asc_sign_idx"] + house - 1) % 12]]


def _sign_of_house(chart, house):
    return (chart["asc_sign_idx"] + house - 1) % 12


def _aspects_sign(planet, from_sign, target_sign):
    return (target_sign - from_sign) % 12 + 1 in ASPECT_HOUSES[planet]


def _special(chart, short):
    return next(k["planet"] for k in chart["karakas"] if k["short"] == short)


def _f(points, text):
    return {"points": points, "text": text}


def planet_state(chart, sb, n):
    """Factors for a planet's own condition: dignity, Shadbala and combustion."""
    p = chart["planets"][n]
    out = []
    if p["dignity"] in ("Exalted", "Own Sign"):
        out.append(_f(1, f"{n} is {'exalted' if p['dignity'] == 'Exalted' else 'in its own sign'} in {p['sign']}"))
    elif p["dignity"] == "Debilitated":
        out.append(_f(0, f"{n} is debilitated in {p['sign']} but its debilitation is cancelled (Neecha Bhanga)")
                   if neecha_bhanga(chart, n) else _f(-1, f"{n} is debilitated in {p['sign']}"))
    if n in sb:
        r = sb[n]["ratio"]
        if r >= 1.15:
            out.append(_f(1, f"{n} is strong in Shadbala ({r:.2f}× its minimum)"))
        elif r < 1:
            out.append(_f(-1, f"{n} is below its Shadbala minimum ({r:.2f}×)"))
    if combustion(chart, n):
        out.append(_f(-1, f"{n} is combust (too close to the Sun)"))
    return out


def house_factors(chart, av, sb, h):
    p = chart["planets"]
    sign = _sign_of_house(chart, h)
    sav = av["sav"][sign]
    out = [_f(1 if sav >= 30 else -1 if sav <= 24 else 0,
              f"{ordinal(h)} house has {sav} Ashtakavarga points "
              + ("(strong)" if sav >= 30 else "(weak)" if sav <= 24 else "(average)"))]
    lord = lord_of(chart, h)
    lh = p[lord]["house"]
    if lh in DUSTHANAS and h in DUSTHANAS:
        out.append(_f(1, f"the {ordinal(h)} lord {lord} sits in the {ordinal(lh)} house: a difficult-house lord in a difficult "
                         "house (Viparita), so troubles tend to cancel out"))
    elif lh in DUSTHANAS:
        out.append(_f(-1, f"the {ordinal(h)} lord {lord} sits in the {ordinal(lh)} house ({HOUSE_INFO[lh][1].lower()})"))
    elif lh in KENDRA_TRIKONA or lh == 11:
        out.append(_f(1, f"the {ordinal(h)} lord {lord} is well placed in the {ordinal(lh)} house"))
    else:
        out.append(_f(0, f"the {ordinal(h)} lord {lord} is in the {ordinal(lh)} house"))
    out += planet_state(chart, sb, lord)
    for n in (x for x in p if x != "Ascendant" and p[x]["sign_idx"] == sign):
        if n in BENEFICS:
            out.append(_f(1, f"{n} (a natural benefic) occupies the {ordinal(h)} house"))
        elif h in UPACHAYAS:
            out.append(_f(1, f"{n} occupies the {ordinal(h)} house, a growth house where malefics do well"))
        else:
            out.append(_f(-1, f"{n} (a natural malefic) occupies the {ordinal(h)} house"))
    for n, pts in (("Jupiter", 1), ("Saturn", -1), ("Mars", -1)):
        if p[n]["sign_idx"] != sign and _aspects_sign(n, p[n]["sign_idx"], sign):
            if pts < 0 and h in UPACHAYAS:
                continue
            out.append(_f(pts, f"{n} aspects the {ordinal(h)} house"
                               + (" (protection)" if pts > 0 else " (pressure and delays)")))
    return out


def karaka_factors(chart, sb, n, role):
    p = chart["planets"][n]
    out = [_f(-1 if p["house"] in DUSTHANAS else 1 if p["house"] in KENDRA_TRIKONA | {11} else 0,
              f"{role} {n} is in your {ordinal(p['house'])} house")]
    out += planet_state(chart, sb, n)
    return out


def varga_factors(chart, varga, house):
    pos = varga_positions(chart, varga)
    asc = pos["Ascendant"]
    sign = (asc + house - 1) % 12
    lord = SIGN_LORDS[SIGNS[sign]]
    lh = (pos[lord] - asc) % 12 + 1
    out = [_f(1 if lh in KENDRA_TRIKONA | {11} else -1 if lh in DUSTHANAS else 0,
              f"in the {varga}, the {ordinal(house)} lord {lord} is in the {ordinal(lh)} house")]
    vs = SIGNS[pos[lord]]
    if vs == EXALTATION_SIGNS.get(lord) or vs in OWN_SIGNS.get(lord, []):
        out.append(_f(1, f"{lord} is in its own or exaltation sign in the {varga}"))
    elif vs == DEBILITATION_SIGNS.get(lord):
        out.append(_f(-1, f"{lord} is debilitated in the {varga}"))
    occ = [n for n in pos if n != "Ascendant" and pos[n] == sign]
    ben, mal = [n for n in occ if n in BENEFICS], [n for n in occ if n in MALEFICS]
    if ben:
        out.append(_f(1, f"{', '.join(ben)} in the {varga} {ordinal(house)} house"))
    if mal:
        out.append(_f(-1, f"{', '.join(mal)} in the {varga} {ordinal(house)} house"))
    return out


def rating(factors):
    total = sum(f["points"] for f in factors)
    ratio = total / max(len(factors), 1)
    index = round(max(0, min(100, 50 + 62.5 * ratio)))
    label = ("Strong" if ratio >= 0.35 else "Good" if ratio >= 0.1 else "Mixed" if ratio >= -0.15 else "Needs care")
    return {"total": total, "index": index, "label": label}


def promise(chart, av, sb, key):
    """All factors for an area grouped by source, plus the overall rating."""
    spec = AREAS[key]
    groups = {}
    for h in spec["houses"]:
        groups[f"{ordinal(h)} house · {HOUSE_INFO[h][1]}"] = house_factors(chart, av, sb, h)
    for n in spec["karakas"]:
        groups[f"Significator {n}"] = karaka_factors(chart, sb, n, "the significator")
    for short in spec["special"]:
        n = _special(chart, short)
        groups[f"Jaimini {short} ({n})"] = karaka_factors(chart, sb, n, f"the {short}")
    if spec["varga"]:
        v, h = spec["varga"]
        groups[f"{v} · {VARGAS[v][0]}"] = varga_factors(chart, v, h)
    every = [f for fs in groups.values() for f in fs]
    return {"groups": groups, **rating(every)}


# --------------------------------------------------------------------------------------
# Timing
# --------------------------------------------------------------------------------------
def roles(chart, key):
    spec = AREAS[key]
    p = chart["planets"]
    out = {}
    for h in spec["houses"]:
        out.setdefault(lord_of(chart, h), []).append(f"{ordinal(h)} lord")
        for n in p:
            if n != "Ascendant" and p[n]["house"] == h:
                out.setdefault(n, []).append(f"in {ordinal(h)}")
    for n in spec["karakas"]:
        out.setdefault(n, []).append("significator")
    for short in spec["special"]:
        out.setdefault(_special(chart, short), []).append(short)
    return out


def _tone(chart, sb, n):
    pts = sum(f["points"] for f in planet_state(chart, sb, n))
    h = chart["planets"][n]["house"]
    pts += 1 if h in KENDRA_TRIKONA | {11} else -1 if h in DUSTHANAS else 0
    return "Supportive" if pts >= 1 else "Testing" if pts <= -1 else "Mixed"


def area_periods(chart, schedule, sb, key, start, years=15):
    """Antardashas from `start` whose lord (or Mahadasha lord) is tied to the area."""
    end = start + dt.timedelta(days=years * 365.25)
    r = roles(chart, key)
    out = []
    for md in schedule:
        if md["end"] <= start or md["start"] >= end:
            continue
        for ad in md["antardashas"]:
            if ad["end"] <= start or ad["start"] >= end:
                continue
            if ad["lord"] not in r and md["lord"] not in r:
                continue
            main = ad["lord"] if ad["lord"] in r else md["lord"]
            out.append({"md": md["lord"], "ad": ad["lord"], "start": max(ad["start"], start), "end": ad["end"],
                        "strength": "Strong" if ad["lord"] in r and md["lord"] in r else
                                    "Main" if ad["lord"] in r else "Background",
                        "roles": "; ".join(f"{n}: {', '.join(r[n])}" for n in dict.fromkeys((md["lord"], ad["lord"]))
                                           if n in r),
                        "tone": _tone(chart, sb, main)})
    return out


TRANSIT_TONE = {"Jupiter": "growth, support and opportunities", "Saturn": "effort, responsibility and slow but "
                "lasting results; possible pressure", "Rahu": "intensity, sudden openings and unusual events; "
                "avoid shortcuts"}


def area_transits(chart, key, start, months=36):
    """Jupiter, Saturn and Rahu sign periods that occupy or aspect one of the area's houses."""
    end = start + dt.timedelta(days=months * 30.44)
    houses = AREAS[key]["houses"]
    rows = []
    for planet in ("Jupiter", "Saturn", "Rahu"):
        for s, a, b in segments_by(chart, planet, start, end, lambda lon: int(lon // 30), step_days=3):
            hits = []
            for h in houses:
                target = _sign_of_house(chart, h)
                if s == target:
                    hits.append(f"transits your {ordinal(h)}")
                elif planet != "Rahu" and _aspects_sign(planet, s, target):
                    hits.append(f"aspects your {ordinal(h)}")
            if hits and (b - a).days >= 1:
                rows.append({"planet": planet, "sign": SIGNS[s], "start": a, "end": b, "what": ", ".join(hits),
                             "tone": TRANSIT_TONE[planet]})
    return sorted(rows, key=lambda r: r["start"])


def double_transit(chart, house, start, months=36):
    """Windows when both Jupiter and Saturn occupy or aspect the house's sign or the sign holding its lord
    (K. N. Rao's double-transit rule for when an event can manifest)."""
    end = start + dt.timedelta(days=months * 30.44)
    targets = {_sign_of_house(chart, house), chart["planets"][lord_of(chart, house)]["sign_idx"]}

    def touches(planet, s):
        return any(s == t or _aspects_sign(planet, s, t) for t in targets)

    sign_key = lambda lon: int(lon // 30)  # noqa: E731
    jup = [x for x in segments_by(chart, "Jupiter", start, end, sign_key, 3) if touches("Jupiter", x[0])]
    sat = [x for x in segments_by(chart, "Saturn", start, end, sign_key, 3) if touches("Saturn", x[0])]
    windows = []
    for _, ja, jb in jup:
        for _, sa, sb_ in sat:
            a, b = max(ja, sa), min(jb, sb_)
            if b > a:
                windows.append((a, b))
    windows.sort()
    merged = []
    for a, b in windows:
        if merged and a <= merged[-1][1] + dt.timedelta(days=1):
            merged[-1] = (merged[-1][0], max(b, merged[-1][1]))
        else:
            merged.append((a, b))
    return merged


# --------------------------------------------------------------------------------------
# Area-specific classical checks: each returns a list of markdown lines
# --------------------------------------------------------------------------------------
def _yogas(chart, words):
    return [y for y in detect_yogas(chart) if any(w.lower() in (y["Yoga"] + " " + y.get("Category", "")).lower()
                                                  for w in words)]


def health_extras(chart, av, sb):
    p = chart["planets"]
    asc = chart["asc_sign_idx"]
    lines = [f"**Body areas to look after:** your Lagna ({SIGNS[asc]}) rules the {SIGN_BODY[asc]}; the 6th sign "
             f"({SIGNS[(asc + 5) % 12]}) the {SIGN_BODY[(asc + 5) % 12]}; the 8th ({SIGNS[(asc + 7) % 12]}) the "
             f"{SIGN_BODY[(asc + 7) % 12]}."]
    weak = []
    for n in CLASSICAL_PLANETS + ["Rahu", "Ketu"]:
        bad = [f["text"] for f in planet_state(chart, sb, n) if f["points"] < 0]
        if n in ("Rahu", "Ketu"):
            bad = ["in the 1st, 6th or 8th house"] if p[n]["house"] in (1, 6, 8) else []
        elif p[n]["house"] in (6, 8):
            bad.append(f"in the {ordinal(p[n]['house'])} house")
        if bad:
            weak.append(f"**{n}** ({PLANET_BODY[n]}): " + "; ".join(bad))
    lines.append("**Planets that need care** and the body systems they govern: " +
                 (" · ".join(weak) if weak else "none stand out; your planets are reasonably well placed."))
    s1, s6, s8 = (av["sav"][(asc + h - 1) % 12] for h in (1, 6, 8))
    lines.append(f"**Ashtakavarga balance:** 1st house {s1} vs 6th {s6} and 8th {s8}. "
                 + ("A stronger 1st house means good recovery power." if s1 >= max(s6, s8) else
                    "The 1st house is lighter than the 6th or 8th, so build stamina deliberately: regular sleep, "
                    "exercise and check-ups pay off more for you than for most."))
    lines.append("This is astrological guidance, not medical advice. See a doctor for any health concern.")
    return lines


def wealth_extras(chart, av, sb):
    p = chart["planets"]
    asc = chart["asc_sign_idx"]
    lines = []
    dhana = []
    for a in (2, 11):
        for b in (1, 5, 9):
            la, lb = lord_of(chart, a), lord_of(chart, b)
            if la == lb:
                dhana.append(f"{la} rules both the {ordinal(a)} and {ordinal(b)} houses")
            else:
                how = connection(chart, la, lb)
                if how:
                    dhana.append(f"{ordinal(a)} lord {la} and {ordinal(b)} lord {lb} are {how}")
    lines.append("**Dhana yogas** (wealth houses 2 and 11 linked with the Lagna or trines 5 and 9): "
                 + ("; ".join(dict.fromkeys(dhana)) + "." if dhana else "none formed by sign, aspect or exchange."))
    l9, l1 = lord_of(chart, 9), lord_of(chart, 1)
    if p[l9]["dignity"] in ("Exalted", "Own Sign") and p[l9]["house"] in KENDRA_TRIKONA and \
            (l1 not in sb or sb[l1]["ratio"] >= 1):
        lines.append(f"**Lakshmi Yoga:** the 9th lord {l9} is {'exalted' if p[l9]['dignity'] == 'Exalted' else 'in its own sign'} in a kendra or trine and the "
                     "Lagna lord is strong: a classic sign of prosperity and good fortune.")
    s11, s12, s2 = (av["sav"][(asc + h - 1) % 12] for h in (11, 12, 2))
    lines.append(f"**Income vs expenses:** 11th house {s11} vs 12th {s12} points: "
                 + ("gains outweigh outgoings, so wealth tends to accumulate." if s11 > s12 else
                    "outgoings match or exceed gains, so saving needs a deliberate system."))
    d2 = varga_positions(chart, "D2")
    sun_h = [n for n in CLASSICAL_PLANETS if d2[n] == 4]
    moon_h = [n for n in CLASSICAL_PLANETS if d2[n] == 3]
    lines.append(f"**D2 (Hora):** Sun's hora (self-made wealth through effort): {', '.join(sun_h) or 'none'}; Moon's "
                 f"hora (wealth through support, family or steady accumulation): {', '.join(moon_h) or 'none'}.")
    al = arudha_padas(chart)[0]["sign_idx"]
    g = [n for n in p if n != "Ascendant" and p[n]["sign_idx"] == (al + 10) % 12]
    lines.append(f"**Arudha Lagna:** planets in the 11th from AL bring visible gains: {', '.join(g) or 'none'}.")
    l11 = lord_of(chart, 11)
    lines.append(f"**Main source of income:** the 11th lord {l11} sits in your {ordinal(p[l11]['house'])} house, "
                 f"pointing to gains through {HOUSE_INFO[p[l11]['house']][1].lower()}.")
    return lines


def relationship_extras(chart, av, sb):
    p = chart["planets"]
    lines = []
    refs = {"Lagna": chart["asc_sign_idx"], "Moon": p["Moon"]["sign_idx"], "Venus": p["Venus"]["sign_idx"]}
    from_ = [r for r, s in refs.items() if (p["Mars"]["sign_idx"] - s) % 12 + 1 in (1, 2, 4, 7, 8, 12)]
    if from_:
        cancel = p["Mars"]["sign"] in ("Aries", "Scorpio", "Capricorn")
        lines.append(f"**Manglik (Kuja) dosha:** Mars is in a sensitive house from your {', '.join(from_)}"
                     + (f", but it is cancelled because Mars is in {p['Mars']['sign']} (own or exaltation sign)."
                        if cancel else ". Traditionally matched with a partner who has the same placement; many "
                                       "astrologers also cancel it after age 28 or by benefic aspects."))
    else:
        lines.append("**Manglik (Kuja) dosha:** not present from the Lagna, Moon or Venus.")
    d9 = varga_positions(chart, "D9")
    l7 = lord_of(chart, 7)
    l7_d9 = (d9[l7] - d9["Ascendant"]) % 12 + 1
    lines.append(f"**7th lord {l7} in the D9** is in {SIGNS[d9[l7]]} (the {ordinal(l7_d9)} from the D9 Lagna); "
                 f"Venus is in {SIGNS[d9['Venus']]}"
                 + (" (vargottama: same sign as in the birth chart, a strong promise)." if d9["Venus"] ==
                    p["Venus"]["sign_idx"] else "."))
    dk = _special(chart, "DK")
    lines.append(f"**Darakaraka {dk}** describes the spouse: in {p[dk]['sign']} in your "
                 f"{ordinal(p[dk]['house'])} house. Its nature colours the partner you attract.")
    ul = arudha_padas(chart)[11]
    nxt = (ul["sign_idx"] + 1) % 12
    occ = [n for n in p if n != "Ascendant" and p[n]["sign_idx"] == nxt]
    lines.append(f"**Upapada (UL)** in {ul['sign']}; 2nd from it holds {', '.join(occ) or 'no planets'}"
                 + (": malefics there ask for patience to keep the marriage strong." if set(occ) & MALEFICS else "."))
    lines.append("For a husband, Jupiter is also read as the significator; for a wife, Venus. Both are shown in the "
                 "Planets page.")
    return lines


def children_extras(chart, av, sb):
    p = chart["planets"]
    asc = chart["asc_sign_idx"]
    lines = []
    s5 = (asc + 4) % 12
    lines.append(f"**5th sign {SIGNS[s5]}:** " + ("a 'fruitful' water sign, classically favourable for children."
                                                  if s5 in (3, 7, 11) else
                                                  "classically called a less fruitful sign; other factors decide."
                                                  if s5 in (2, 4, 5) else "neutral for this question."))
    jup5 = (p["Jupiter"]["sign_idx"] + 4) % 12
    b = av["bav"]["Jupiter"][jup5]
    lines.append(f"**Jupiter's Ashtakavarga:** {b} bindus in the 5th from Jupiter ({SIGNS[jup5]}). "
                 + ("4 or more is supportive for children." if b >= 4 else "Fewer than 4 asks for patience and "
                                                                          "care in this area."))
    pk = _special(chart, "PK")
    lines.append(f"**Putrakaraka {pk}** in your {ordinal(p[pk]['house'])} house: its periods and strength also "
                 "show joys and concerns through children.")
    if p["Jupiter"]["house"] == 5:
        lines.append("Jupiter in the 5th is 'karaka in its own house' (Karako Bhava Nashaya): classically this can "
                     "delay or limit the area while still giving wise, capable children.")
    return lines


def education_extras(chart, av, sb):
    p = chart["planets"]
    infl = {}
    for h in (4, 5):
        sign = _sign_of_house(chart, h)
        for n in p:
            if n == "Ascendant":
                continue
            if p[n]["sign_idx"] == sign or (n not in ("Rahu", "Ketu") and _aspects_sign(n, p[n]["sign_idx"], sign)):
                infl[n] = infl.get(n, 0) + 1
        infl[lord_of(chart, h)] = infl.get(lord_of(chart, h), 0) + 2
    top = sorted(infl, key=lambda n: -infl[n])[:3]
    lines = ["**Subjects that suit you** (from the planets ruling, occupying or aspecting the 4th and 5th): "
             + " · ".join(f"**{n}**: {PLANET_SUBJECTS[n]}" for n in top)]
    yogas = _yogas(chart, ["Saraswati", "Budhaditya", "Gajakesari"])
    if yogas:
        lines.append("**Learning yogas:** " + "; ".join(f"{y['Yoga']}" for y in yogas) + ".")
    mer = chart["planets"]["Mercury"]
    lines.append(f"**Mercury (intellect)** is in {mer['sign']} in your {ordinal(mer['house'])} house"
                 + (f" and {sb['Mercury']['ratio']:.2f}× its Shadbala minimum." if "Mercury" in sb else "."))
    return lines


def family_extras(chart, av, sb):
    """Table rows: one per relation (property, vehicles, mother, father, siblings, family life)."""
    rows = []
    for label, houses, karaka, varga, vh in FAMILY_PARTS:
        fs = [f for h in houses for f in house_factors(chart, av, sb, h)]
        fs += karaka_factors(chart, sb, karaka, "the significator")
        fs += varga_factors(chart, varga, vh)
        r = rating(fs)
        plus = [f["text"] for f in fs if f["points"] > 0][:2]
        minus = [f["text"] for f in fs if f["points"] < 0][:2]
        rows.append({"Area": label, "Rating": r["label"], "Score": r["index"],
                     "Read from": f"{', '.join(ordinal(h) for h in houses)} house, {karaka}, {varga}",
                     "Helps": "; ".join(plus) or "—", "Watch": "; ".join(minus) or "—"})
    return rows


def foreign_extras(chart, av, sb):
    p = chart["planets"]
    checks = [
        ("12th lord in the 1st, 9th or 12th house", p[lord_of(chart, 12)]["house"] in (1, 9, 12)),
        ("Lagna lord in the 12th house", p[lord_of(chart, 1)]["house"] == 12),
        ("9th lord in the 12th house", p[lord_of(chart, 9)]["house"] == 12),
        ("Rahu in the 1st, 4th, 7th, 9th, 10th or 12th house", p["Rahu"]["house"] in (1, 4, 7, 9, 10, 12)),
        ("Moon in the 12th house", p["Moon"]["house"] == 12),
        ("4th house afflicted (leaving the homeland): a malefic in the 4th or its lord in 6, 8 or 12",
         any(p[n]["house"] == 4 for n in ("Saturn", "Mars", "Rahu", "Ketu", "Sun"))
         or p[lord_of(chart, 4)]["house"] in DUSTHANAS),
        ("9th and 12th lords linked", lord_of(chart, 9) == lord_of(chart, 12)
         or bool(connection(chart, lord_of(chart, 9), lord_of(chart, 12)))),
        ("Lagna in a movable sign (Aries, Cancer, Libra, Capricorn)", chart["asc_sign_idx"] % 3 == 0),
    ]
    met = [c for c, ok in checks if ok]
    level = "Strong" if len(met) >= 4 else "Moderate" if len(met) >= 2 else "Low"
    lines = [f"**Foreign living and travel indicators: {len(met)} of {len(checks)} ({level}).**"]
    lines += [f"{'✅' if ok else '▫️'} {c}" for c, ok in checks]
    lines.append("Strong indicators point to long stays or settling abroad; moderate ones to frequent travel or "
                 "foreign links in work; low ones to a life centred near home.")
    return lines


def spiritual_extras(chart, av, sb):
    p = chart["planets"]
    d9 = varga_positions(chart, "D9")
    ak = _special(chart, "AK")
    km = d9[ak]
    twelfth = (km + 11) % 12
    occ = [n for n in d9 if n != "Ascendant" and d9[n] == twelfth]
    lines = [f"**Karakamsha:** your Atmakaraka {ak} is in {SIGNS[km]} in the D9. The 12th from it ({SIGNS[twelfth]}) "
             f"shows the spiritual path: {', '.join(occ) or 'no planets'} there"
             + (", and Ketu there is the classic sign of a deep pull towards liberation." if "Ketu" in occ else
                ", and Jupiter there favours wisdom traditions and a teacher." if "Jupiter" in occ else ".")]
    lines.append(f"**Ketu** (detachment) is in your {ordinal(p['Ketu']['house'])} house: you are naturally detached "
                 f"from {HOUSE_INFO[p['Ketu']['house']][1].lower()}, and spiritual insight comes through that area.")
    moksha = [n for n in p if n != "Ascendant" and p[n]["house"] in (4, 8, 12)]
    lines.append(f"**Moksha houses (4, 8, 12):** {', '.join(moksha) or 'empty'}"
                 + (". Several planets here turn the mind inward with age." if len(moksha) >= 3 else "."))
    signs = {}
    for n in CLASSICAL_PLANETS:
        signs.setdefault(p[n]["sign_idx"], []).append(n)
    group = next((g for g in signs.values() if len(g) >= 4), None)
    if group:
        lines.append(f"**Pravrajya yoga:** {', '.join(group)} together in one sign, a classic indicator of renunciation "
                     "or a strongly spiritual phase of life.")
    return lines


EXTRAS = {"Health": health_extras, "Wealth": wealth_extras, "Relationships": relationship_extras,
          "Children": children_extras, "Education": education_extras, "Home & Family": family_extras,
          "Travel & Foreign": foreign_extras, "Spirituality": spiritual_extras}


def summary_lines(chart, key, prom):
    spec = AREAS[key]
    plus = list(dict.fromkeys(f["text"] for fs in prom["groups"].values() for f in fs if f["points"] > 0))
    minus = list(dict.fromkeys(f["text"] for fs in prom["groups"].values() for f in fs if f["points"] < 0))
    lines = [f"Overall promise: **{prom['label']}** ({prom['index']}/100, from {len(plus)} supportive and "
             f"{len(minus)} challenging factors)."]
    if plus:
        lines.append("**What helps:** " + "; ".join(plus[:4]) + ".")
    if minus:
        lines.append("**What needs care:** " + "; ".join(minus[:4]) + ".")
    lines.append(f"**Supportive periods:** {spec['good']} **Testing periods:** {spec['watch']}")
    return lines
