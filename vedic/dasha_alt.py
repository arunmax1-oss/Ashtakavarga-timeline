"""Alternative dasha systems for cross-checking Vimshottari: Yogini Dasha and Jaimini Chara Dasha.

Yogini: 8 yoginis totalling 36 years. The first yogini is (birth nakshatra number + 3) mod 8, and its balance
at birth is the unelapsed part of the Moon's nakshatra, as in Vimshottari.

Chara (K. N. Rao's method): sign-based periods starting from the Lagna sign. They run in zodiacal order
when the 9th sign from Lagna is a savya (odd-footed) sign, otherwise in reverse. A sign's years are the count
from the sign to its lord (forward for savya signs, backward otherwise) minus one; a lord in its own sign
gives 12 years. Scorpio and Aquarius use the stronger of their two lords. The second cycle gives each sign
12 minus its first-cycle years. Other Jaimini schools differ in details.
"""
import datetime as dt

from .constants import DAYS_PER_YEAR, NAKSHATRA_SPAN, SIGN_LORDS, SIGNS

YOGINIS = [("Mangala", "Moon", 1), ("Pingala", "Sun", 2), ("Dhanya", "Jupiter", 3), ("Bhramari", "Mars", 4),
           ("Bhadrika", "Mercury", 5), ("Ulka", "Saturn", 6), ("Siddha", "Venus", 7), ("Sankata", "Rahu", 8)]
YOGINI_MEANING = {
    "Mangala": "auspicious beginnings and good fortune", "Pingala": "stress, heat and conflicts to manage",
    "Dhanya": "prosperity, learning and blessings", "Bhramari": "travel, restlessness and change",
    "Bhadrika": "success, friendships and good deeds", "Ulka": "hard work, losses and lessons",
    "Siddha": "accomplishment, comfort and fulfilment", "Sankata": "crises and testing situations",
}
SAVYA = {0, 1, 2, 6, 7, 8}  # Aries, Taurus, Gemini, Libra, Scorpio, Sagittarius
CO_LORDS = {7: ("Mars", "Ketu"), 10: ("Saturn", "Rahu")}


def yogini_dasha(chart, years_after_birth=100):
    moon = chart["planets"]["Moon"]["lon"]
    nak = int(moon // NAKSHATRA_SPAN)
    elapsed = (moon % NAKSHATRA_SPAN) / NAKSHATRA_SPAN
    first = ((nak + 1) + 3) % 8 - 1  # 0-based index; remainder 0 means the 8th yogini
    birth = chart["birth_utc"]
    cursor = birth - dt.timedelta(days=elapsed * YOGINIS[first][2] * DAYS_PER_YEAR)
    horizon = birth + dt.timedelta(days=years_after_birth * DAYS_PER_YEAR)
    out, k = [], 0
    while cursor < horizon:
        name, lord, years = YOGINIS[(first + k) % 8]
        end = cursor + dt.timedelta(days=years * DAYS_PER_YEAR)
        out.append({"name": name, "lord": lord, "years": years, "start": max(cursor, birth), "end": end,
                    "meaning": YOGINI_MEANING[name]})
        cursor, k = end, k + 1
    return out


def _sign_of(chart, planet):
    return chart["planets"][planet]["sign_idx"]


def chara_lord(chart, sign):
    if sign not in CO_LORDS:
        return SIGN_LORDS[SIGNS[sign]]
    a, b = CO_LORDS[sign]
    if _sign_of(chart, a) == sign and _sign_of(chart, b) != sign:
        return b
    if _sign_of(chart, b) == sign and _sign_of(chart, a) != sign:
        return a
    count = {pl: sum(1 for n, p in chart["planets"].items()
                     if n not in ("Ascendant", pl) and p["sign_idx"] == _sign_of(chart, pl)) for pl in (a, b)}
    if count[a] != count[b]:
        return a if count[a] > count[b] else b
    return a if chart["planets"][a]["degree"] >= chart["planets"][b]["degree"] else b


def chara_years(chart, sign):
    lord = chara_lord(chart, sign)
    target = _sign_of(chart, lord)
    count = ((target - sign) % 12 if sign in SAVYA else (sign - target) % 12)
    return (count if count else 12), lord


def chara_dasha(chart, cycles=2):
    asc = chart["asc_sign_idx"]
    forward = (asc + 8) % 12 in SAVYA
    order = [(asc + i) % 12 if forward else (asc - i) % 12 for i in range(12)]
    first = {s: chara_years(chart, s) for s in order}
    out, cursor = [], chart["birth_utc"]
    for c in range(cycles):
        for s in order:
            years, lord = first[s]
            if c == 1:
                years = 12 - years or 12
            end = cursor + dt.timedelta(days=years * DAYS_PER_YEAR)
            out.append({"sign": SIGNS[s], "lord": lord, "years": years, "start": cursor, "end": end, "cycle": c + 1})
            cursor = end
    return out, ("zodiacal" if forward else "reverse")


def running(periods, when):
    return next((p for p in periods if p["start"] <= when < p["end"]), None)
