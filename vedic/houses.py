"""House-level Parashari techniques: Arudha Padas, Argala and Bhava Chalit (Sripati) houses.

Arudha Pada: count from a house to its lord, then the same number again from the lord. If the result is
the house itself or the 7th from it, the 10th from that result is used instead (BPHS). Scorpio and Aquarius
use the stronger of their two lords (same rule as Chara Dasha).

Argala (intervention): planets in the 2nd, 4th and 11th from a house (and 5th, secondary) influence it;
planets in the 12th, 10th and 3rd (and 9th) obstruct those influences. An argala holds when it has more
planets than its obstruction. Malefics in the 3rd give Vipareeta Argala, which cannot be obstructed.

Bhava Chalit (Sripati): the Ascendant and Midheaven are house middles and each quadrant between them is
split into three equal parts (Porphyry cusps as house middles); house borders (sandhis) lie halfway
between middles. A planet near a sign edge can fall in a different Bhava than its whole-sign house.
"""
import swisseph as swe

from .chart import set_ayanamsha
from .constants import ALL_PLANETS, HOUSE_INFO, SIGNS, ordinal
from .dasha_alt import chara_lord

PADA_NAMES = {
    1: ("AL", "Arudha Lagna", "how the world sees you: image, status and reputation"),
    2: ("A2", "Dhana Pada", "visible wealth and family standing"),
    3: ("A3", "Vikrama Pada", "image of courage, siblings and your own initiatives"),
    4: ("A4", "Sukha Pada", "home, property and vehicles as others see them"),
    5: ("A5", "Mantra Pada", "reputation for intelligence, advice and children"),
    6: ("A6", "Shatru Pada", "visible enemies, disputes and health issues"),
    7: ("A7", "Dara Pada", "partners and business associates, how relationships appear"),
    8: ("A8", "Mrityu Pada", "visible crises, inheritances and hidden matters coming to light"),
    9: ("A9", "Bhagya Pada", "fortune, father and teachers as seen by others"),
    10: ("A10", "Rajya Pada", "career image: your position and achievements"),
    11: ("A11", "Labha Pada", "visible gains, income and network"),
    12: ("UL", "Upapada", "marriage and the spouse; the 2nd from it shows how lasting the marriage is"),
}
MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
ARGALA_PAIRS = [(2, 12, "wealth, family and resources"), (4, 10, "comforts, home and support"),
                (11, 3, "gains, friends and fulfilment"), (5, 9, "intelligence, advice and children (secondary)")]


def _occupants(chart, sign):
    return [n for n in ALL_PLANETS if chart["planets"][n]["sign_idx"] == sign]


# --------------------------------------------------------------------------------------
# Arudha Padas
# --------------------------------------------------------------------------------------
def arudha_padas(chart):
    asc = chart["asc_sign_idx"]
    p = chart["planets"]
    out = []
    for h in range(1, 13):
        sign = (asc + h - 1) % 12
        lord = chara_lord(chart, sign)
        lord_sign = p[lord]["sign_idx"]
        count = (lord_sign - sign) % 12
        pada = (lord_sign + count) % 12
        if pada in (sign, (sign + 6) % 12):
            pada = (pada + 9) % 12
        short, name, meaning = PADA_NAMES[h]
        out.append({"house": h, "short": short, "name": name, "meaning": meaning, "lord": lord,
                    "sign_idx": pada, "sign": SIGNS[pada], "pada_house": (pada - asc) % 12 + 1,
                    "occupants": _occupants(chart, pada)})
    return out


def arudha_insight(chart, padas):
    by = {d["short"]: d for d in padas}
    al, ul, a7 = by["AL"], by["UL"], by["A7"]
    lines = []
    from_al = lambda n: (al["sign_idx"] + n - 1) % 12  # noqa: E731
    lines.append(f"Your **Arudha Lagna (AL)** is **{al['sign']}**, in your {ordinal(al['pada_house'])} house: "
                 f"people tend to see you through the lens of {HOUSE_INFO[al['pada_house']][1].lower()}."
                 + (f" {', '.join(al['occupants'])} in the AL colour{'s' if len(al['occupants']) == 1 else ''} "
                    "your public image." if al["occupants"] else ""))
    gains, spend = _occupants(chart, from_al(11)), _occupants(chart, from_al(12))
    lines.append("**Wealth from the AL:** planets in the 11th from AL bring visible gains, planets in the 12th from "
                 f"AL drain them. 11th from AL: {', '.join(gains) or 'empty'}; 12th from AL: "
                 f"{', '.join(spend) or 'empty'}."
                 + (" Gains outweigh outgoings." if len(gains) > len(spend) else
                    " Watch spending that is driven by image." if len(spend) > len(gains) else ""))
    second_ul = (ul["sign_idx"] + 1) % 12
    occ2 = _occupants(chart, second_ul)
    mal2 = [n for n in occ2 if n in MALEFICS]
    lines.append(f"**Upapada (UL)** is **{ul['sign']}** ({ordinal(ul['pada_house'])} house), describing marriage and "
                 f"the spouse. The 2nd from UL ({SIGNS[second_ul]}) shows how lasting it is: "
                 + (f"benefics there ({', '.join(occ2)}) support a lasting bond." if occ2 and not mal2 else
                    f"malefics there ({', '.join(mal2)}) ask for patience and care in marriage." if mal2 else
                    "it is empty, so its lord and aspects decide; no special stress is shown."))
    rel = (a7["sign_idx"] - al["sign_idx"]) % 12 + 1
    lines.append(f"**Dara Pada (A7)** is in {a7['sign']}, the {ordinal(rel)} from your AL: "
                 + ("in a kendra or trine from the AL, partnerships and business dealings work well with your image."
                    if rel in (1, 4, 5, 7, 9, 10) else
                    "in a 6th, 8th or 12th from the AL, partners and associates may pull in a different direction; "
                    "choose them carefully." if rel in (6, 8, 12) else
                    "a neutral placement from the AL for partnerships."))
    return lines


# --------------------------------------------------------------------------------------
# Argala
# --------------------------------------------------------------------------------------
def argala(chart, house):
    """Interventions on `house` (1-12): list of {"from", "theme", "planets", "obstructed_by", "status"}."""
    sign = (chart["asc_sign_idx"] + house - 1) % 12
    rows = []
    for nth, block, theme in ARGALA_PAIRS:
        planets = _occupants(chart, (sign + nth - 1) % 12)
        if not planets:
            continue
        blockers = _occupants(chart, (sign + block - 1) % 12)
        status = "Effective" if len(planets) > len(blockers) else "Obstructed"
        nature = ("benefic" if all(n in BENEFICS for n in planets) else
                  "malefic" if all(n in MALEFICS for n in planets) else "mixed")
        rows.append({"from": nth, "theme": theme, "planets": planets, "obstructed_by": blockers,
                     "status": status, "nature": nature, "obstructs": block})
    third = [n for n in _occupants(chart, (sign + 2) % 12) if n in MALEFICS]
    if third:
        rows.append({"from": 3, "theme": "Vipareeta Argala: malefics in the 3rd remove obstacles", "planets": third,
                     "obstructed_by": [], "status": "Effective", "nature": "malefic", "obstructs": None})
    return rows


def argala_summary(chart):
    """{house: (effective count, obstructed count, benefic effective count)} for all 12 houses."""
    out = {}
    for h in range(1, 13):
        rows = argala(chart, h)
        eff = [r for r in rows if r["status"] == "Effective"]
        out[h] = (len(eff), len(rows) - len(eff), sum(r["nature"] == "benefic" for r in eff))
    return out


# --------------------------------------------------------------------------------------
# Bhava Chalit (Sripati)
# --------------------------------------------------------------------------------------
def _between(x, a, b):
    """True if longitude x lies on the arc from a forward to b."""
    return (x - a) % 360 < (b - a) % 360


def bhava_chalit(chart):
    """{"madhya": [12 longitudes], "sandhi": [12 starts], "planets": {name: bhava}}."""
    set_ayanamsha(chart["ayanamsha"])
    cusps, _ = swe.houses_ex(chart["jd"], chart["lat"], chart["lon"], b"O", swe.FLG_SIDEREAL)
    madhya = [c % 360 for c in cusps[:12]]
    # starts[i] begins bhava i+1: halfway between the middles of bhava i and bhava i+1
    starts = [(madhya[i - 1] + ((madhya[i] - madhya[i - 1]) % 360) / 2) % 360 for i in range(12)]
    planets = {}
    for name, p in chart["planets"].items():
        if name == "Ascendant":
            continue
        planets[name] = next(h + 1 for h in range(12) if _between(p["lon"], starts[h], starts[(h + 1) % 12]))
    return {"madhya": madhya, "sandhi": starts, "planets": planets}


def chalit_insight(chart, bc):
    moved = [(n, chart["planets"][n]["house"], h) for n, h in bc["planets"].items() if h != chart["planets"][n]["house"]]
    if not moved:
        return ["Every planet falls in the same Bhava as its whole-sign house, so house readings are unambiguous."]
    return ["These planets sit near a house border, so they also give results of the neighbouring house "
            "(many astrologers read the sign for strength and the Bhava for which house's matters it delivers):"] + \
        [f"**{n}**: {ordinal(a)} house by sign, **{ordinal(b)} house by Bhava** "
         f"({HOUSE_INFO[b][1].lower()})." for n, a, b in moved]
