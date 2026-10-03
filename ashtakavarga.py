"""Classical Parashari Ashtakavarga (BPHS).

For each of the 7 planets, 8 contributors (the 7 planets + Lagna) give a bindu (benefic point)
to the signs at fixed house-distances from where the contributor sits in the natal chart.
That planet's Bhinna Ashtakavarga (BAV) is the bindu count per sign (0-8); the
Sarvashtakavarga (SAV) is the sum of the 7 BAVs per sign (always 337 in total).

Kakshya: each sign is split into 8 slices of 3°45', ruled in order by
Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon, Lagna. A transiting planet "delivers"
while it moves through a slice whose lord contributed a bindu to that planet's BAV in that sign.
"""
from .constants import CLASSICAL_PLANETS, SIGNS

CONTRIBUTORS = CLASSICAL_PLANETS + ["Lagna"]

# BENEFIC_PLACES[planet][contributor] = houses counted from the contributor that receive a bindu.
BENEFIC_PLACES = {
    "Sun": {
        "Sun": [1, 2, 4, 7, 8, 9, 10, 11], "Moon": [3, 6, 10, 11],
        "Mars": [1, 2, 4, 7, 8, 9, 10, 11], "Mercury": [3, 5, 6, 9, 10, 11, 12],
        "Jupiter": [5, 6, 9, 11], "Venus": [6, 7, 12],
        "Saturn": [1, 2, 4, 7, 8, 9, 10, 11], "Lagna": [3, 4, 6, 10, 11, 12],
    },
    "Moon": {
        "Sun": [3, 6, 7, 8, 10, 11], "Moon": [1, 3, 6, 7, 10, 11],
        "Mars": [2, 3, 5, 6, 9, 10, 11], "Mercury": [1, 3, 4, 5, 7, 8, 10, 11],
        "Jupiter": [1, 4, 7, 8, 10, 11, 12], "Venus": [3, 4, 5, 7, 9, 10, 11],
        "Saturn": [3, 5, 6, 11], "Lagna": [3, 6, 10, 11],
    },
    "Mars": {
        "Sun": [3, 5, 6, 10, 11], "Moon": [3, 6, 11],
        "Mars": [1, 2, 4, 7, 8, 10, 11], "Mercury": [3, 5, 6, 11],
        "Jupiter": [6, 10, 11, 12], "Venus": [6, 8, 11, 12],
        "Saturn": [1, 4, 7, 8, 9, 10, 11], "Lagna": [1, 3, 6, 10, 11],
    },
    "Mercury": {
        "Sun": [5, 6, 9, 11, 12], "Moon": [2, 4, 6, 8, 10, 11],
        "Mars": [1, 2, 4, 7, 8, 9, 10, 11], "Mercury": [1, 3, 5, 6, 9, 10, 11, 12],
        "Jupiter": [6, 8, 11, 12], "Venus": [1, 2, 3, 4, 5, 8, 9, 11],
        "Saturn": [1, 2, 4, 7, 8, 9, 10, 11], "Lagna": [1, 2, 4, 6, 8, 10, 11],
    },
    "Jupiter": {
        "Sun": [1, 2, 3, 4, 7, 8, 9, 10, 11], "Moon": [2, 5, 7, 9, 11],
        "Mars": [1, 2, 4, 7, 8, 10, 11], "Mercury": [1, 2, 4, 5, 6, 9, 10, 11],
        "Jupiter": [1, 2, 3, 4, 7, 8, 10, 11], "Venus": [2, 5, 6, 9, 10, 11],
        "Saturn": [3, 5, 6, 12], "Lagna": [1, 2, 4, 5, 6, 7, 9, 10, 11],
    },
    "Venus": {
        "Sun": [8, 11, 12], "Moon": [1, 2, 3, 4, 5, 8, 9, 11, 12],
        "Mars": [3, 5, 6, 9, 11, 12], "Mercury": [3, 5, 6, 9, 11],
        "Jupiter": [5, 8, 9, 10, 11], "Venus": [1, 2, 3, 4, 5, 8, 9, 10, 11],
        "Saturn": [3, 4, 5, 8, 9, 10, 11], "Lagna": [1, 2, 3, 4, 5, 8, 9, 11],
    },
    "Saturn": {
        "Sun": [1, 2, 4, 7, 8, 10, 11], "Moon": [3, 6, 11],
        "Mars": [3, 5, 6, 10, 11, 12], "Mercury": [6, 8, 9, 10, 11, 12],
        "Jupiter": [5, 6, 11, 12], "Venus": [6, 11, 12],
        "Saturn": [3, 5, 6, 11], "Lagna": [1, 3, 4, 6, 10, 11],
    },
}

KAKSHYA_LORDS = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon", "Lagna"]
KAKSHYA_SPAN = 30.0 / 8  # 3°45'


def _contributor_signs(chart):
    p = chart["planets"]
    signs = {name: p[name]["sign_idx"] for name in CLASSICAL_PLANETS}
    signs["Lagna"] = chart["asc_sign_idx"]
    return signs


def compute_ashtakavarga(chart):
    """Return {"bav": {planet: [12 ints]}, "sav": [12 ints], "prastara": {planet: {contrib: [12 0/1]}}}.

    Lists are indexed by sign (0 = Aries), not by house.
    """
    contrib_sign = _contributor_signs(chart)
    prastara, bav = {}, {}
    for planet, table in BENEFIC_PLACES.items():
        prastara[planet] = {}
        for contributor in CONTRIBUTORS:
            row = [0] * 12
            for house in table[contributor]:
                row[(contrib_sign[contributor] + house - 1) % 12] = 1
            prastara[planet][contributor] = row
        bav[planet] = [sum(prastara[planet][c][s] for c in CONTRIBUTORS) for s in range(12)]
    sav = [sum(bav[p][s] for p in CLASSICAL_PLANETS) for s in range(12)]
    return {"bav": bav, "sav": sav, "prastara": prastara}


def sav_by_house(chart, av):
    """SAV re-indexed so position 0 is the 1st house (Ascendant sign)."""
    asc = chart["asc_sign_idx"]
    return [av["sav"][(asc + h) % 12] for h in range(12)]


def kakshya_of(lon):
    """(kakshya index 0-7, lord) for a sidereal longitude."""
    idx = int((lon % 30) // KAKSHYA_SPAN)
    return idx, KAKSHYA_LORDS[idx]


def kakshya_has_bindu(av, planet, sign_idx, kakshya_lord):
    return av["prastara"][planet][kakshya_lord][sign_idx] == 1


def sign_table(av):
    """Rows for a BAV/SAV table: one row per sign."""
    rows = []
    for s in range(12):
        row = {"Sign": SIGNS[s]}
        for p in CLASSICAL_PLANETS:
            row[p] = av["bav"][p][s]
        row["SAV"] = av["sav"][s]
        rows.append(row)
    return rows
