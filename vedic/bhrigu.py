"""Bhrigu methods: Bhrigu Bindu, Bhrigu Chakra Paddhati (BCP) and Bhrigu Nandi Nadi (BNN) transit contacts.

- Bhrigu Bindu: the midpoint of Rahu and the Moon, measured forward from Rahu to the Moon. Transits of
  Jupiter, Saturn and the nodes over it are traditionally turning points.
- Bhrigu Chakra Paddhati: each year of life activates one house in sequence: age 0-1 the 1st house,
  1-2 the 2nd ... 11-12 the 12th, then the cycle repeats.
- Bhrigu Nandi Nadi: read the natal planets that transiting Jupiter and Saturn "join" by sign: the same sign,
  the trines (5th/9th), the 7th, and the adjacent signs (2nd/12th), using BNN significations.
"""
import datetime as dt

from .chart import house_from, julian_day, jd_to_datetime, planet_longitude, set_ayanamsha
from .constants import ALL_PLANETS, HOUSE_INFO, SIGN_LORDS, SIGNS, ordinal

# Bhrigu Nandi Nadi significations (karakas), which differ a little from the Parashari ones.
BNN_KARAKA = {
    "Sun": "father, authority, government and status",
    "Moon": "mother, mind, home comforts and the public",
    "Mars": "siblings, property, courage and technical work",
    "Mercury": "education, communication, friends and trade",
    "Jupiter": "the self (jiva), wisdom, children and guidance",
    "Venus": "spouse or partner, wealth, comforts and vehicles",
    "Saturn": "career, profession, labour and long-term karma",
    "Rahu": "foreign links, technology, ambition and the unconventional",
    "Ketu": "spirituality, research, detachment and endings",
}
BNN_RELATIONS = {1: "joins", 5: "trines (5th)", 9: "trines (9th)", 7: "opposes (7th)",
                 2: "moves toward (2nd)", 12: "has just left (12th)"}
TRANSIT_TONE = {
    "Jupiter": "expands and blesses",
    "Saturn": "tests, structures and makes lasting",
}


def _arc(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


def _domain(h):
    return HOUSE_INFO[h][1].lower()


# --------------------------------------------------------------------------------------
# Bhrigu Bindu
# --------------------------------------------------------------------------------------
def bhrigu_bindu(chart):
    p = chart["planets"]
    rahu, moon = p["Rahu"]["lon"], p["Moon"]["lon"]
    lon = (rahu + ((moon - rahu) % 360) / 2) % 360
    sign_idx = int(lon // 30)
    return {"lon": lon, "sign_idx": sign_idx, "sign": SIGNS[sign_idx], "degree": lon % 30,
            "house": house_from(sign_idx, chart["asc_sign_idx"])}


def contact_windows(chart, target_lon, planets, start, end, orb=2.0, step_days=1.0):
    """Periods when each planet is within `orb` degrees of `target_lon` (retrograde loops give several)."""
    set_ayanamsha(chart["ayanamsha"])
    out = []
    for planet in planets:
        jd, jd_end = julian_day(start), julian_day(end)
        inside, w_start, best = False, None, (999, None)
        while jd <= jd_end:
            lon, _ = planet_longitude(jd, planet, chart["true_node"])
            sep = _arc(lon, target_lon)
            if sep <= orb:
                if not inside:
                    inside, w_start, best = True, jd, (sep, jd)
                elif sep < best[0]:
                    best = (sep, jd)
            elif inside:
                out.append({"planet": planet, "start": jd_to_datetime(w_start), "end": jd_to_datetime(jd),
                            "exact": jd_to_datetime(best[1]), "closest": best[0]})
                inside = False
            jd += step_days
        if inside:
            out.append({"planet": planet, "start": jd_to_datetime(w_start), "end": jd_to_datetime(jd_end),
                        "exact": jd_to_datetime(best[1]), "closest": best[0]})
    return sorted(out, key=lambda w: w["start"])


def bhrigu_bindu_reading(chart):
    bb = bhrigu_bindu(chart)
    lord = SIGN_LORDS[bb["sign"]]
    return (f"Your **Bhrigu Bindu** is at **{bb['degree']:.1f}° {bb['sign']}**, in your {ordinal(bb['house'])} house "
            f"({_domain(bb['house'])}). This is where destiny tends to concentrate: events touching "
            f"{_domain(bb['house'])} are the ones that redirect your life. Its sign lord **{lord}** sits in your "
            f"{ordinal(chart['planets'][lord]['house'])} house, so those turning points work through "
            f"{_domain(chart['planets'][lord]['house'])}.")


# --------------------------------------------------------------------------------------
# Bhrigu Chakra Paddhati
# --------------------------------------------------------------------------------------
def bcp_year(chart, when):
    """The house activated by the current year of life, with the planets and lord involved."""
    birth = chart["birth_utc"]
    years = (when - birth).days / 365.25
    completed = int(years)
    house = completed % 12 + 1
    start = birth + dt.timedelta(days=completed * 365.25)
    end = birth + dt.timedelta(days=(completed + 1) * 365.25)
    sign = SIGNS[(chart["asc_sign_idx"] + house - 1) % 12]
    occupants = [n for n in ALL_PLANETS if chart["planets"][n]["house"] == house]
    return {"age": completed, "house": house, "sign": sign, "lord": SIGN_LORDS[sign],
            "occupants": occupants, "start": start, "end": end}


def bcp_reading(chart, when):
    y = bcp_year(chart, when)
    lord_house = chart["planets"][y["lord"]]["house"]
    text = (f"You are in year {y['age'] + 1} of life ({y['start']:%d %b %Y} – {y['end']:%d %b %Y}), which activates "
            f"your **{ordinal(y['house'])} house** of {_domain(y['house'])}. ")
    if y["occupants"]:
        text += (f"{', '.join(y['occupants'])} sit{'s' if len(y['occupants']) == 1 else ''} there in your chart, so "
                 f"{'its' if len(y['occupants']) == 1 else 'their'} themes come forward this year. ")
    text += (f"The house lord **{y['lord']}** is in your {ordinal(lord_house)} house, linking this year's events to "
             f"{_domain(lord_house)}.")
    return text


def bcp_cycle(chart, when, years_ahead=4):
    rows = []
    for k in range(years_ahead + 1):
        y = bcp_year(chart, when + dt.timedelta(days=365.25 * k))
        rows.append({"Age": f"{y['age']}–{y['age'] + 1}", "From": f"{y['start']:%b %Y}", "To": f"{y['end']:%b %Y}",
                     "Active house": HOUSE_INFO[y["house"]][0],
                     "Focus": HOUSE_INFO[y["house"]][1], "Planets there": ", ".join(y["occupants"]) or "—",
                     "House lord": y["lord"]})
    return rows


# --------------------------------------------------------------------------------------
# Bhrigu Nandi Nadi transit contacts
# --------------------------------------------------------------------------------------
def transit_sign(chart, planet, when):
    set_ayanamsha(chart["ayanamsha"])
    lon, _ = planet_longitude(julian_day(when), planet, chart["true_node"])
    return int(lon // 30)


def bnn_contacts(chart, when, transiting=("Jupiter", "Saturn")):
    rows = []
    for t in transiting:
        t_sign = transit_sign(chart, t, when)
        for natal in ALL_PLANETS:
            rel = house_from(chart["planets"][natal]["sign_idx"], t_sign)
            if rel in BNN_RELATIONS and natal != t:
                rows.append({"transit": t, "transit_sign": SIGNS[t_sign], "natal": natal, "relation": rel,
                             "text": f"Transit **{t}** ({SIGNS[t_sign]}) {BNN_RELATIONS[rel]} your natal **{natal}**: "
                                     f"it {TRANSIT_TONE[t]} {BNN_KARAKA[natal]}."})
    # strongest links first: conjunction, then trines, then 7th, then 2nd/12th
    order = {1: 0, 5: 1, 9: 1, 7: 2, 2: 3, 12: 3}
    return sorted(rows, key=lambda r: (r["transit"] != "Jupiter", order[r["relation"]]))
