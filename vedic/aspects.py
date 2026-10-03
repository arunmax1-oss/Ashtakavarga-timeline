"""Combustion and planetary aspects (graha drishti) in the birth chart.

Aspects are whole-sign: a planet aspects whole signs counted from its own sign. Every planet aspects
the 7th; Mars also the 4th and 8th, Jupiter the 5th and 9th, Saturn the 3rd and 10th. Rahu and Ketu
are given the 5th/7th/9th aspects, a common (but not universal) convention.
"""
from .constants import ordinal

ASPECT_HOUSES = {
    "Sun": [7], "Moon": [7], "Mercury": [7], "Venus": [7],
    "Mars": [4, 7, 8], "Jupiter": [5, 7, 9], "Saturn": [3, 7, 10],
    "Rahu": [5, 7, 9], "Ketu": [5, 7, 9],
}
MALEFICS = ["Saturn", "Mars", "Rahu", "Ketu"]
# Rahu/Ketu aspects are disputed between traditions, so only their conjunctions count as malefic pressure.
ASPECTING_MALEFICS = ["Saturn", "Mars"]

# Classical combustion limits in degrees from the Sun; (direct, retrograde) where they differ.
COMBUST_ORBS = {"Moon": 12, "Mars": 17, "Mercury": (14, 12), "Jupiter": 11, "Venus": (10, 8), "Saturn": 15}


def _separation(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


def combustion(chart, planet):
    """{'distance', 'orb'} if the planet is combust, else None. Rahu/Ketu and the Sun are never combust."""
    if planet not in COMBUST_ORBS:
        return None
    p = chart["planets"][planet]
    orb = COMBUST_ORBS[planet]
    if isinstance(orb, tuple):
        orb = orb[1] if p["retrograde"] else orb[0]
    distance = _separation(p["lon"], chart["planets"]["Sun"]["lon"])
    return {"distance": distance, "orb": orb} if distance <= orb else None


def aspects_on(chart, target):
    """Planets aspecting `target`'s sign: [(planet, nth-house aspect)]."""
    p = chart["planets"]
    out = []
    for name, houses in ASPECT_HOUSES.items():
        if name == target:
            continue
        nth = (p[target]["sign_idx"] - p[name]["sign_idx"]) % 12 + 1
        if nth in houses:
            out.append((name, nth))
    return out


def aspected_houses(chart, planet):
    """Houses (from Lagna) that `planet` aspects."""
    p = chart["planets"]
    return [(p[planet]["house"] + h - 2) % 12 + 1 for h in ASPECT_HOUSES[planet]]


def conjunctions(chart, target):
    p = chart["planets"]
    return [n for n in ASPECT_HOUSES if n != target and p[n]["sign_idx"] == p[target]["sign_idx"]]


def influences(chart, target):
    """Summary used by remedies and insights: malefic pressure and Jupiter protection on a planet."""
    asp = aspects_on(chart, target)
    conj = conjunctions(chart, target)
    malefic = ([f"{n}'s {ordinal(h)} aspect" for n, h in asp if n in ASPECTING_MALEFICS]
               + [f"{n} in the same sign" for n in conj if n in MALEFICS])
    jupiter = [f"Jupiter's {ordinal(h)} aspect" for n, h in asp if n == "Jupiter"] + \
              (["Jupiter in the same sign"] if "Jupiter" in conj else [])
    return {"aspects": asp, "conjunctions": conj, "malefic": malefic, "jupiter": jupiter}
