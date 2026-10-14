"""Yoga detection and a simple dignity-based planetary strength score."""
from .aspects import aspects_on, combustion, influences
from .constants import ALL_PLANETS, DIG_BALA_HOUSE, EXALTATION_SIGNS, OWN_SIGNS, SIGN_LORDS, SIGNS, ordinal

KENDRAS = [1, 4, 7, 10]


def detect_yogas(chart):
    p = chart["planets"]
    asc = chart["asc_sign_idx"]
    yogas = []

    # Gajakesari: Jupiter in a kendra (1/4/7/10) counted from the Moon.
    rel = (p["Jupiter"]["sign_idx"] - p["Moon"]["sign_idx"]) % 12 + 1
    if rel in KENDRAS:
        yogas.append({
            "Yoga": "Gajakesari Yoga",
            "Category": "Major Auspicious / Wisdom & Fame",
            "Condition Met": f"Jupiter is {ordinal(rel)} from the Moon (House {p['Jupiter']['house']} vs Moon in House {p['Moon']['house']}).",
            "Life Impact": "High intellect, strong reputation, emotional stability and protection against major adversities.",
        })

    # Pancha Mahapurusha: Mars/Mercury/Jupiter/Venus/Saturn in a kendra from Lagna in own or exaltation sign.
    pm = {
        "Mars": ("Ruchaka Yoga", "Courage, executive drive, leadership in engineering, sports or administration."),
        "Mercury": ("Bhadra Yoga", "Exceptional intellect, communication mastery, commercial and analytical depth."),
        "Jupiter": ("Hamsa Yoga", "Wisdom, high ethics, social respect, advisory or academic acclaim."),
        "Venus": ("Malavya Yoga", "Artistic refinement, comfort, charisma and prosperous relationships."),
        "Saturn": ("Sasa Yoga", "Authority over people and systems, discipline, organisational mastery."),
    }
    for planet, (name, impact) in pm.items():
        info = p[planet]
        if info["house"] in KENDRAS and (info["sign"] == EXALTATION_SIGNS[planet] or info["sign"] in OWN_SIGNS[planet]):
            yogas.append({
                "Yoga": name,
                "Category": "Pancha Mahapurusha (Great Person)",
                "Condition Met": f"{planet} is in House {info['house']} ({info['sign']}), where it is {info['dignity'].lower()}.",
                "Life Impact": impact,
            })

    # Budhaditya: Sun and Mercury in the same sign.
    if p["Sun"]["sign_idx"] == p["Mercury"]["sign_idx"]:
        yogas.append({
            "Yoga": "Budhaditya Yoga",
            "Category": "Intellectual & Professional Brilliance",
            "Condition Met": f"Sun and Mercury together in House {p['Sun']['house']} ({p['Sun']['sign']}).",
            "Life Impact": "Sharp business acumen, quick learning and professional standing.",
        })

    # Dhana (simplified): 2nd or 11th lord placed in a wealth/trine house (1, 2, 5, 9, 11).
    h2_lord = SIGN_LORDS[SIGNS[(asc + 1) % 12]]
    h11_lord = SIGN_LORDS[SIGNS[(asc + 10) % 12]]
    wealth_houses = [1, 2, 5, 9, 11]
    if p[h2_lord]["house"] in wealth_houses or p[h11_lord]["house"] in wealth_houses:
        yogas.append({
            "Yoga": "Dhana Yoga (simplified)",
            "Category": "Financial Prosperity",
            "Condition Met": f"2nd lord {h2_lord} (House {p[h2_lord]['house']}) / 11th lord {h11_lord} (House {p[h11_lord]['house']}) in a wealth or trine house.",
            "Life Impact": "Capacity to turn talent and investments into long-term wealth.",
        })
    yogas += more_yogas(chart)
    return yogas


# --------------------------------------------------------------------------------------
# Further classical yogas
# --------------------------------------------------------------------------------------
TRIKONAS = [1, 5, 9]
DUSTHANAS = [6, 8, 12]
BENEFICS = ["Mercury", "Jupiter", "Venus"]
NON_LUMINARY = ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"]  # excludes Sun, Moon and the nodes


def lord_of(chart, house):
    return SIGN_LORDS[SIGNS[(chart["asc_sign_idx"] + house - 1) % 12]]


def connection(chart, a, b):
    """How two planets are linked: same sign, mutual aspect, or sign exchange. None if not linked."""
    p = chart["planets"]
    if p[a]["sign_idx"] == p[b]["sign_idx"]:
        return "together in one sign"
    if SIGN_LORDS[p[a]["sign"]] == b and SIGN_LORDS[p[b]["sign"]] == a:
        return "exchanging signs"
    a_on_b = any(n == a for n, _ in aspects_on(chart, b))
    b_on_a = any(n == b for n, _ in aspects_on(chart, a))
    if a_on_b and b_on_a:
        return "in mutual aspect"
    return None


def _y(name, category, condition, impact):
    return {"Yoga": name, "Category": category, "Condition Met": condition, "Life Impact": impact}


def more_yogas(chart):
    from .insights import neecha_bhanga
    p = chart["planets"]
    out = []

    # Yogakaraka and Raja yogas: kendra lord linked with trikona lord
    kendra_lords = {h: lord_of(chart, h) for h in KENDRAS}
    trikona_lords = {h: lord_of(chart, h) for h in TRIKONAS}
    for pl in set(kendra_lords.values()) & set(trikona_lords.values()):
        kh = [h for h, l in kendra_lords.items() if l == pl and h != 1]
        th = [h for h, l in trikona_lords.items() if l == pl and h != 1]
        if kh and th:
            out.append(_y(f"Yogakaraka {pl}", "Raja Yoga (power and status)",
                          f"{pl} rules both the {ordinal(kh[0])} (kendra) and {ordinal(th[0])} (trikona) houses.",
                          f"{pl} is the single most rewarding planet for your Ascendant; its periods lift status."))
    seen = set()
    for kh, kl in kendra_lords.items():
        for th, tl in trikona_lords.items():
            if kl == tl or kh == th or (kl, tl) in seen or (tl, kl) in seen:
                continue
            link = connection(chart, kl, tl)
            if link:
                seen.add((kl, tl))
                name = "Dharma-Karmadhipati Yoga" if {kh, th} == {9, 10} else "Raja Yoga"
                out.append(_y(name, "Raja Yoga (power and status)",
                              f"{ordinal(kh)} lord {kl} and {ordinal(th)} lord {tl} are {link}.",
                              "Rise in position and recognition, especially in the periods of these planets."))

    # Viparita Raja yogas: lords of difficult houses placed in difficult houses
    for h, name in [(6, "Harsha"), (8, "Sarala"), (12, "Vimala")]:
        l = lord_of(chart, h)
        if p[l]["house"] in DUSTHANAS:
            out.append(_y(f"Viparita Raja Yoga ({name})", "Success through adversity",
                          f"{ordinal(h)} lord {l} sits in the {ordinal(p[l]['house'])} house.",
                          "Setbacks turn into gains; you tend to come out stronger after difficult phases."))

    # Neecha Bhanga Raja Yoga
    for n in ALL_PLANETS:
        if p[n]["dignity"] == "Debilitated" and neecha_bhanga(chart, n):
            out.append(_y("Neecha Bhanga Raja Yoga", "Raja Yoga (rise after struggle)",
                          f"{n} is debilitated in {p[n]['sign']} but the weakness is cancelled.",
                          f"Early struggle around {n}'s themes becomes a source of strength and status later."))

    # Moon-based yogas
    moon = p["Moon"]["sign_idx"]
    second = [n for n in NON_LUMINARY if p[n]["sign_idx"] == (moon + 1) % 12]
    twelfth = [n for n in NON_LUMINARY if p[n]["sign_idx"] == (moon + 11) % 12]
    with_moon = [n for n in NON_LUMINARY if p[n]["sign_idx"] == moon]
    if second and twelfth:
        out.append(_y("Durudhara Yoga", "Wealth and support",
                      f"Planets on both sides of the Moon ({', '.join(twelfth)} before, {', '.join(second)} after).",
                      "Comfort, resources and supportive people around you."))
    elif second:
        out.append(_y("Sunapha Yoga", "Self-made wealth", f"{', '.join(second)} in the 2nd from the Moon.",
                      "Wealth and reputation earned through your own effort."))
    elif twelfth:
        out.append(_y("Anapha Yoga", "Character and health", f"{', '.join(twelfth)} in the 12th from the Moon.",
                      "Good health, dignity and a well-regarded personality."))
    elif not with_moon:
        cancelled = any(p[n]["house"] in KENDRAS for n in NON_LUMINARY + ["Moon"]) or \
            any(n == "Jupiter" for n, _ in aspects_on(chart, "Moon"))
        out.append(_y("Kemadruma Yoga" + (" (cancelled)" if cancelled else ""), "Challenging (emotional support)",
                      "No planets in the 2nd, 12th or with the Moon"
                      + ("; cancelled by planets in kendras or Jupiter's aspect." if cancelled else "."),
                      "Periods of feeling unsupported; build your own steady routines and networks."
                      if not cancelled else "The isolating effect is largely neutralised."))
    if connection(chart, "Moon", "Mars"):
        out.append(_y("Chandra-Mangala Yoga", "Wealth through enterprise",
                      f"Moon and Mars are {connection(chart, 'Moon', 'Mars')}.",
                      "Money through business, property or bold initiative; strong drive."))
    in_678 = [n for n in BENEFICS if (p[n]["sign_idx"] - moon) % 12 + 1 in (6, 7, 8)]
    if len(in_678) >= 2:
        out.append(_y("Adhi Yoga" + ("" if len(in_678) == 3 else " (partial)"), "Leadership and comfort",
                      f"{', '.join(in_678)} in the 6th, 7th or 8th from the Moon.",
                      "Authority, good fortune and a comfortable life; leadership roles come naturally."))

    # Amala: a benefic in the 10th from Lagna or Moon
    for ref, label in [(chart["asc_sign_idx"], "Lagna"), (moon, "Moon")]:
        tenth = [n for n in BENEFICS if p[n]["sign_idx"] == (ref + 9) % 12]
        if tenth:
            out.append(_y("Amala Yoga", "Reputation", f"{', '.join(tenth)} in the 10th from the {label}.",
                          "A clean reputation and lasting good name through your work."))
            break

    # Sun-based yogas
    sun = p["Sun"]["sign_idx"]
    s2 = [n for n in NON_LUMINARY if p[n]["sign_idx"] == (sun + 1) % 12]
    s12 = [n for n in NON_LUMINARY if p[n]["sign_idx"] == (sun + 11) % 12]
    if s2 and s12:
        out.append(_y("Ubhayachari Yoga", "Status and capability",
                      f"{', '.join(s12)} before and {', '.join(s2)} after the Sun.",
                      "Capable, balanced and respected; comfort in life."))
    elif s2:
        out.append(_y("Vesi Yoga", "Character", f"{', '.join(s2)} in the 2nd from the Sun.",
                      "Truthful, balanced and steadily prosperous."))
    elif s12:
        out.append(_y("Vasi Yoga", "Generosity", f"{', '.join(s12)} in the 12th from the Sun.",
                      "Generous, skilful and well-liked."))

    # Parivartana (sign exchange)
    done = set()
    for a in ALL_PLANETS[:7]:
        for b in ALL_PLANETS[:7]:
            if a < b and SIGN_LORDS[p[a]["sign"]] == b and SIGN_LORDS[p[b]["sign"]] == a and (a, b) not in done:
                done.add((a, b))
                houses = {p[a]["house"], p[b]["house"]}
                kind = ("Dainya (difficult)" if houses & set(DUSTHANAS) else
                        "Khala (mixed)" if 3 in houses else "Maha (excellent)")
                out.append(_y(f"Parivartana Yoga: {kind}", "Sign exchange",
                              f"{a} and {b} sit in each other's signs (houses {', '.join(map(str, sorted(houses)))}).",
                              "The two houses involved work as one, strengthening each other."
                              if "Maha" in kind else "The houses involved are tied together for better or worse."))
    return out


# Score adjustments, kept in one place so the UI caption can quote them.
STRENGTH_POINTS = {"Exalted": 35, "Own Sign": 20, "Debilitated": -25, "Dig Bala": 25,
                   "Combust": -15, "Combust (Mercury)": -5, "Jupiter support": 10, "Malefic pressure": -10}


def dignity_strength(chart):
    """Dignity, direction, combustion and aspects on a rough 0-130 scale. A quick indicator, NOT full Shadbala."""
    rows = []
    for name in ALL_PLANETS:
        info = chart["planets"][name]
        score = 50.0
        score += STRENGTH_POINTS.get(info["dignity"], 0)
        dig = DIG_BALA_HOUSE.get(name) == info["house"]
        if dig:
            score += STRENGTH_POINTS["Dig Bala"]
        comb = combustion(chart, name)
        if comb:
            score += STRENGTH_POINTS["Combust (Mercury)" if name == "Mercury" else "Combust"]
        inf = influences(chart, name) if name not in ("Rahu", "Ketu") else {"malefic": [], "jupiter": []}
        if inf["jupiter"]:
            score += STRENGTH_POINTS["Jupiter support"]
        if len(inf["malefic"]) >= 2 and not inf["jupiter"]:
            score += STRENGTH_POINTS["Malefic pressure"]
        status = "Dominant & Strong" if score >= 70 else ("Balanced" if score >= 50 else "Needs Support")
        rows.append({
            "Planet": name, "Sign": info["sign"], "House": info["house"], "Dignity": info["dignity"],
            "Dig Bala": "Yes" if dig else "",
            "Combust": f"{comb['distance']:.1f}° from Sun" if comb else "",
            "Jupiter Support": ", ".join(inf["jupiter"]),
            "Malefic Influence": ", ".join(inf["malefic"]),
            "Strength Score": score, "Status": status,
        })
    return rows
