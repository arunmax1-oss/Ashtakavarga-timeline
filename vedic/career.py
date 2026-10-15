"""Career analysis for the Job tab: 10th house, D10, Amatyakaraka, suitable fields, job vs business,
career-period timeline and slow-planet transits over the career houses."""
import datetime as dt

from .aspects import aspects_on, combustion
from .chart import house_from, julian_day, jd_to_datetime, planet_longitude, set_ayanamsha
from .constants import ALL_PLANETS, HOUSE_INFO, SIGN_LORDS, SIGNS, ordinal
from .dasha import sub_periods
from .vargas import varga_positions

PLANET_CAREERS = {
    "Sun": ["Government and public administration", "Leadership and senior management", "Politics",
            "Medicine (physician)", "Energy and power sector"],
    "Moon": ["Healthcare and nursing", "Hospitality and food", "Public relations and customer service",
             "Human resources", "Shipping, water and dairy"],
    "Mars": ["Engineering", "Defence, police and security", "Surgery", "Real estate and construction",
             "Sports and fitness", "Manufacturing"],
    "Mercury": ["Business and trade", "Accounting and analytics", "Software and IT", "Writing, media and publishing",
                "Consulting and sales", "Teaching languages and communication"],
    "Jupiter": ["Teaching and academia", "Law and judiciary", "Banking and finance", "Advisory and mentoring",
                "Religious or charitable work", "Management consulting"],
    "Venus": ["Arts, design and fashion", "Entertainment and media", "Luxury goods and beauty",
              "Hospitality and travel", "Automobiles", "Interior and creative industries"],
    "Saturn": ["Operations and process management", "Civil service and governance", "Logistics and supply chain",
               "Mining, oil and heavy industry", "Agriculture and land", "Labour-intensive enterprises"],
    "Rahu": ["Technology and innovation", "Foreign companies and global roles", "Aviation", "Films and mass media",
             "Research in unconventional fields", "Politics and large organisations"],
    "Ketu": ["Research and investigation", "Specialised technical work and coding", "Healing and alternative medicine",
             "Spiritual or philosophical work", "Mathematics and analysis"],
}

PERIOD_THEMES = [  # (role key, label, description) in priority order
    ("10th lord", "Career peak", "recognition, promotion or a significant new responsibility"),
    ("in 10th", "Career peak", "visibility and important developments at work"),
    ("AmK", "Career direction", "clarity about your vocation and decisive career moves"),
    ("6th lord", "Job change", "new roles, interviews, competition and a heavier workload"),
    ("11th lord", "Income growth", "raises, gains and support from your professional network"),
    ("2nd lord", "Income growth", "savings, salary and financial stability"),
    ("12th lord", "Transition", "relocation, foreign work, a break or a change of environment"),
    ("8th lord", "Restructuring", "sudden changes, reorganisations or a shift in career direction"),
]


def _lord(chart, house):
    return SIGN_LORDS[SIGNS[(chart["asc_sign_idx"] + house - 1) % 12]]


def _domain(h):
    return HOUSE_INFO[h][1].lower()


def roles(chart):
    """Which planets hold which career roles in this chart."""
    p = chart["planets"]
    amk = next(k["planet"] for k in chart["karakas"] if k["short"] == "AmK")
    out = {n: [] for n in ALL_PLANETS}
    for h in (10, 6, 11, 2, 12, 8):
        out[_lord(chart, h)].append(f"{ordinal(h)} lord")
    out[amk].append("AmK")
    for n in ALL_PLANETS:
        if p[n]["house"] == 10:
            out[n].append("in 10th")
    return {n: r for n, r in out.items() if r}


def profile(chart, av, sb):
    p = chart["planets"]
    asc = chart["asc_sign_idx"]
    h10_sign = (asc + 9) % 12
    lord10 = _lord(chart, 10)
    amk = next(k["planet"] for k in chart["karakas"] if k["short"] == "AmK")
    in10 = [n for n in ALL_PLANETS if p[n]["house"] == 10]
    aspecting10 = [n for n in ALL_PLANETS
                   if (h10_sign - p[n]["sign_idx"]) % 12 + 1 in {"Mars": [4, 7, 8], "Jupiter": [5, 7, 9],
                                                                 "Saturn": [3, 7, 10]}.get(n, [7])
                   and n not in ("Rahu", "Ketu")]
    d10 = varga_positions(chart, "D10")
    d10_asc = d10["Ascendant"]
    d10_lord10 = SIGN_LORDS[SIGNS[(d10_asc + 9) % 12]]
    d10_kendra = [n for n in ALL_PLANETS if (d10[n] - d10_asc) % 12 + 1 in (1, 4, 7, 10)]

    weights = {}
    for n, w in [(lord10, 3), (amk, 3), (SIGN_LORDS[SIGNS[d10_asc]], 1), (d10_lord10, 1)] + \
            [(n, 2) for n in in10] + [(n, 1) for n in aspecting10]:
        weights[n] = weights.get(n, 0) + w
    ranked = sorted(weights, key=lambda n: -weights[n])
    fields = []
    for n in ranked[:3]:
        fields.append({"planet": n, "weight": weights[n], "fields": PLANET_CAREERS[n]})

    def strength(n):
        return sb[n]["ratio"] if n in sb else None

    lord6, lord7 = _lord(chart, 6), _lord(chart, 7)
    sav = lambda h: av["sav"][(asc + h - 1) % 12]  # noqa: E731
    service = sav(6) + 3 * (p[lord10]["house"] in (6, 10)) + 2 * (p["Saturn"]["house"] in (6, 10)) + \
        2 * ((strength(lord6) or 1) >= 1)
    business = sav(7) + 3 * (p[lord10]["house"] in (7, 11, 3)) + 2 * (p["Mercury"]["house"] in (1, 7, 10, 11)) + \
        2 * ((strength(lord7) or 1) >= 1) + 1 * ((strength("Mercury") or 1) >= 1)
    if abs(service - business) <= 2:
        leaning = ("Balanced: both employment and an independent practice can work; a senior employed role with "
                   "entrepreneurial freedom suits you best.")
    elif service > business:
        leaning = ("Leans towards **employment**: structured organisations, service roles and steady progression "
                   "suit you more than running your own business.")
    else:
        leaning = ("Leans towards **business or independent work**: trade, partnerships, consulting or your own "
                   "venture suit you more than a long-term salaried role.")

    return {
        "h10_sign": SIGNS[h10_sign], "lord10": lord10, "lord10_house": p[lord10]["house"],
        "lord10_sign": p[lord10]["sign"], "lord10_dignity": p[lord10]["dignity"],
        "lord10_strength": strength(lord10), "lord10_combust": bool(combustion(chart, lord10)),
        "in10": in10, "aspecting10": aspecting10, "sav10": sav(10), "sav11": sav(11), "sav2": sav(2),
        "amk": amk, "amk_house": p[amk]["house"], "amk_sign": p[amk]["sign"], "amk_d10": SIGNS[d10[amk]],
        "amk_strength": strength(amk),
        "d10_asc": SIGNS[d10_asc], "d10_lord10": d10_lord10, "d10_lord10_sign": SIGNS[d10[d10_lord10]],
        "d10_kendra": d10_kendra, "fields": fields, "service": service, "business": business, "leaning": leaning,
        "lord10_aspects": aspects_on(chart, lord10),
    }


def profile_text(chart, prof):
    s10 = prof["sav10"]
    strength = prof["lord10_strength"]
    lines = [
        f"Your **10th house (career)** is **{prof['h10_sign']}**, ruled by **{prof['lord10']}**, which sits in your "
        f"{ordinal(prof['lord10_house'])} house ({_domain(prof['lord10_house'])}) in {prof['lord10_sign']}"
        + (f", {prof['lord10_dignity'].lower()}" if prof["lord10_dignity"] not in ("Neutral", "") else "")
        + ". Career growth runs through that area of life.",
        f"The 10th house holds **{s10} SAV** "
        + ("(strong: work tends to reward your effort readily)." if s10 >= 30 else
           "(average: steady, effort-proportional progress)." if s10 >= 28 else
           "(below average: progress comes through persistence and strategy rather than luck).")
        + (f" Its lord {prof['lord10']} has **{strength:.2f}×** its required Shadbala"
           + (", so it can deliver well." if strength >= 1 else ", so career results need extra effort.")
           if strength else ""),
    ]
    if prof["lord10_combust"]:
        lines.append(f"{prof['lord10']} is combust, so your work can be overshadowed by bosses or authority figures "
                     "until you claim visible ownership of your results.")
    if prof["in10"]:
        lines.append(f"**{', '.join(prof['in10'])}** in the 10th house colour{'s' if len(prof['in10']) == 1 else ''} "
                     "how you work and how you are seen professionally.")
    lines.append(f"**Amatyakaraka {prof['amk']}** (the career planet) is in your {ordinal(prof['amk_house'])} house "
                 f"and in {prof['amk_d10']} in the D10, pointing to work involving "
                 f"{PLANET_CAREERS[prof['amk']][0].lower()} and {PLANET_CAREERS[prof['amk']][1].lower()}.")
    lines.append(f"**D10 (career chart):** Lagna {prof['d10_asc']}; its 10th lord {prof['d10_lord10']} is in "
                 f"{prof['d10_lord10_sign']}. Planets in D10 kendras (strong at work): "
                 f"{', '.join(prof['d10_kendra']) or 'none'}.")
    lines.append(f"**Income:** 11th house (gains) {prof['sav11']} SAV, 2nd house (savings) {prof['sav2']} SAV: "
                 + ("earnings potential is strong." if prof["sav11"] >= 30 else
                    "earnings grow steadily with experience." if prof["sav11"] >= 28 else
                    "build income deliberately through skills and multiple streams."))
    return lines


def career_periods(chart, schedule, sb, start, years=12):
    """Antardashas from `start` for `years`, tagged with their career theme."""
    end = start + dt.timedelta(days=years * 365.25)
    r = roles(chart)
    out = []
    for md in schedule:
        if md["end"] <= start or md["start"] >= end:
            continue
        for ad in md["antardashas"]:
            if ad["end"] <= start or ad["start"] >= end:
                continue
            lord_roles = r.get(ad["lord"], []) + [f"MD {x}" for x in r.get(md["lord"], [])]
            theme = next(((label, desc) for key, label, desc in PERIOD_THEMES if key in r.get(ad["lord"], [])),
                         None)
            if not theme:
                theme = next(((label, desc) for key, label, desc in PERIOD_THEMES if key in r.get(md["lord"], [])),
                             ("Steady", "routine progress; build skills and relationships"))
            strength = sb[ad["lord"]]["ratio"] if ad["lord"] in sb else None
            quality = ("Strong" if strength and strength >= 1.15 else "Moderate" if strength is None or strength >= 1
                       else "Needs effort")
            pratyantars = [pd for pd in sub_periods(ad["lord"], ad["start"], ad["end"])
                           if "10th lord" in r.get(pd["lord"], []) or "AmK" in r.get(pd["lord"], [])]
            out.append({"md": md["lord"], "ad": ad["lord"], "start": max(ad["start"], start), "end": ad["end"],
                        "theme": theme[0], "meaning": theme[1], "roles": ", ".join(lord_roles) or "—",
                        "quality": quality, "peaks": pratyantars})
    return out


def _sign_segments(chart, planet, start, end):
    set_ayanamsha(chart["ayanamsha"])
    jd, jd_end = julian_day(start), julian_day(end)

    def sign(j):
        return int(planet_longitude(j, planet, chart["true_node"])[0] // 30)

    segs, cur, seg_start, j = [], sign(jd), jd, jd
    while j < jd_end:
        nxt = min(j + 3, jd_end)
        s = sign(nxt)
        if s != cur:
            lo, hi = j, nxt
            while hi - lo > 1 / 24:
                mid = (lo + hi) / 2
                lo, hi = (mid, hi) if sign(mid) == cur else (lo, mid)
            segs.append((cur, seg_start, hi))
            cur, seg_start = s, hi
        j = nxt
    segs.append((cur, seg_start, jd_end))
    return [(s, jd_to_datetime(a), jd_to_datetime(b)) for s, a, b in segs]


def career_transits(chart, start, months=36):
    """Jupiter, Saturn and Rahu periods that touch the 10th house (by occupation or aspect) or the 11th."""
    end = start + dt.timedelta(days=months * 30.44)
    asc = chart["asc_sign_idx"]
    moon = chart["planets"]["Moon"]["sign_idx"]
    asp = {"Jupiter": [5, 7, 9], "Saturn": [3, 7, 10], "Rahu": [5, 7, 9]}
    rows = []
    for planet in ("Jupiter", "Saturn", "Rahu"):
        for s, a, b in _sign_segments(chart, planet, start, end):
            h = house_from(s, asc)
            hm = house_from(s, moon)
            aspects_10 = (asc + 9 - s) % 12 + 1 in asp[planet]
            notes = []
            if h == 10:
                notes.append("transits your 10th house")
            elif aspects_10:
                notes.append("aspects your 10th house")
            if h == 11:
                notes.append("transits your 11th house (gains)")
            if hm == 10:
                notes.append("10th from your Moon")
            if not notes:
                continue
            tone = {"Jupiter": "opportunities, growth and support from seniors",
                    "Saturn": "hard work, responsibility and lasting (if slow) progress; possible pressure",
                    "Rahu": "ambition, sudden opportunities, foreign or technology links; avoid shortcuts"}[planet]
            rows.append({"planet": planet, "sign": SIGNS[s], "house": h, "start": a, "end": b,
                         "what": "; ".join(notes), "tone": tone})
    return sorted(rows, key=lambda r: r["start"])
