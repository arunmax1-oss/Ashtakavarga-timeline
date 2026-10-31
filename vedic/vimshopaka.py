"""Vimshopaka Bala (BPHS): a planet's strength out of 20 from its dignity across the divisional charts.

In every varga the planet scores by the sign it occupies: own sign, exaltation or Moolatrikona 20, great
friend 18, friend 15, neutral 10, enemy 7, great enemy 5 (friendship is compound: natural plus temporary,
from the birth chart). Each varga's score is weighted, and the weights of a scheme add up to 20.

Convention: exaltation is scored like an own sign (BPHS lists only the friendship grades; most software
treats exaltation as 20). Rahu and Ketu are not scored.
"""
from .constants import CLASSICAL_PLANETS, EXALTATION_SIGNS, OWN_SIGNS, SIGN_LORDS, SIGNS
from .shadbala import MOOLATRIKONA, compound_relation
from .vargas import VARGAS

SCHEMES = {
    "Shadvarga (6)": {"D1": 6, "D2": 2, "D3": 4, "D9": 5, "D12": 2, "D30": 1},
    "Saptavarga (7)": {"D1": 5, "D2": 2, "D3": 3, "D7": 2.5, "D9": 4.5, "D12": 2, "D30": 1},
    "Dashavarga (10)": {"D1": 3, "D2": 1.5, "D3": 1.5, "D7": 1.5, "D9": 1.5, "D10": 1.5, "D12": 1.5, "D16": 1.5,
                        "D30": 1.5, "D60": 5},
    "Shodashavarga (16)": {"D1": 3.5, "D2": 1, "D3": 1, "D4": 0.5, "D7": 0.5, "D9": 3, "D10": 0.5, "D12": 0.5,
                           "D16": 2, "D20": 0.5, "D24": 0.5, "D27": 0.5, "D30": 1, "D40": 0.5, "D45": 0.5, "D60": 4},
}
POINTS = {"Own": 20, "Exalted": 20, "Moolatrikona": 20, "Great friend": 18, "Friend": 15, "Neutral": 10,
          "Enemy": 7, "Great enemy": 5}
# Number of Dashavarga charts in own sign, exaltation or Moolatrikona -> classical title (BPHS).
AMSHA_TITLES = {2: "Parijatamsha", 3: "Uttamamsha", 4: "Gopuramsha", 5: "Simhasanamsha", 6: "Paravatamsha",
                7: "Devalokamsha", 8: "Brahmalokamsha", 9: "Airavatamsha", 10: "Sridhamamsha"}


def varga_dignity(chart, planet, varga):
    """(sign name, dignity grade) of `planet` in `varga`."""
    lon = chart["planets"][planet]["lon"]
    sign = VARGAS[varga][1](lon)
    name = SIGNS[sign]
    if varga == "D1":
        mt_sign, lo, hi = MOOLATRIKONA[planet]
        if sign == mt_sign and lo <= lon % 30 < hi:
            return name, "Moolatrikona"
    if name == EXALTATION_SIGNS[planet]:
        return name, "Exalted"
    if name in OWN_SIGNS[planet]:
        return name, "Own"
    return name, compound_relation(chart, planet, SIGN_LORDS[name])


def label(score):
    return ("Excellent" if score >= 15 else "Good" if score >= 10 else "Ordinary" if score >= 5 else "Weak")


def vimshopaka(chart):
    """{planet: {"scores": {scheme: 0-20}, "dignities": {varga: (sign, grade)}, "own_count", "title"}}."""
    out = {}
    for planet in CLASSICAL_PLANETS:
        dign = {v: varga_dignity(chart, planet, v) for v in VARGAS}
        scores = {name: round(sum(w * POINTS[dign[v][1]] / 20 for v, w in weights.items()), 2)
                  for name, weights in SCHEMES.items()}
        own = sum(dign[v][1] in ("Own", "Exalted", "Moolatrikona") for v in SCHEMES["Dashavarga (10)"])
        out[planet] = {"scores": scores, "dignities": dign, "own_count": own, "title": AMSHA_TITLES.get(own, "")}
    return out


def insight(vb):
    scheme = "Shodashavarga (16)"
    ranked = sorted(vb, key=lambda p: -vb[p]["scores"][scheme])
    best, worst = ranked[0], ranked[-1]
    lines = [f"Across all 16 divisional charts, **{best}** is your most consistently dignified planet "
             f"({vb[best]['scores'][scheme]:.1f}/20, {label(vb[best]['scores'][scheme]).lower()}): its themes hold "
             f"up in every area of life it touches.",
             f"**{worst}** scores lowest ({vb[worst]['scores'][scheme]:.1f}/20): its promise in the birth chart "
             "is less well supported by the divisional charts, so its results need more effort."]
    titled = [f"{p} ({vb[p]['title']}, {vb[p]['own_count']} of 10 charts)" for p in ranked if vb[p]["title"]]
    if titled:
        lines.append("Planets in their own or exaltation sign in several Dashavarga charts earn a classical title "
                     "and give distinguished results: " + ", ".join(titled) + ".")
    return lines
