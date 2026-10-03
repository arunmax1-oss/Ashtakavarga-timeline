"""Yoga detection and a simple dignity-based planetary strength score."""
from .aspects import combustion, influences
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
                "Condition Met": f"{planet} is in House {info['house']} ({info['sign']}), its {info['dignity'].lower()}.",
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
    return yogas


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
