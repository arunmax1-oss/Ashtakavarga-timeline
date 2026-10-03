"""Vimshottari Dasha: Mahadasha -> Antardasha -> Pratyantardasha.

The first Mahadasha is the lord of the Moon's natal nakshatra. Its *full* period starts
before birth (by the fraction of the nakshatra the Moon has already crossed), so sub-periods
are generated from that true start and simply clipped at birth.
Years are 365.25 days.
"""
import datetime as dt

from .constants import DASHA_LORDS, DASHA_TOTAL_YEARS, DASHA_YEARS, DAYS_PER_YEAR, NAKSHATRA_SPAN


def _sequence_from(lord):
    i = DASHA_LORDS.index(lord)
    return [DASHA_LORDS[(i + k) % 9] for k in range(9)]


def sub_periods(parent_lord, start, end):
    """Split [start, end) into the 9 sub-periods of parent_lord, proportional to dasha years."""
    total = end - start
    out, cursor = [], start
    for lord in _sequence_from(parent_lord):
        length = total * (DASHA_YEARS[lord] / DASHA_TOTAL_YEARS)
        out.append({"lord": lord, "start": cursor, "end": cursor + length})
        cursor += length
    out[-1]["end"] = end  # absorb float rounding
    return out


def vimshottari(chart, years_after_birth=120):
    """List of Mahadashas, each with its Antardashas, covering birth -> birth + years_after_birth."""
    birth = chart["birth_utc"]
    moon_lon = chart["planets"]["Moon"]["lon"]
    nak_idx = int(moon_lon // NAKSHATRA_SPAN)
    elapsed = (moon_lon % NAKSHATRA_SPAN) / NAKSHATRA_SPAN
    first_lord = DASHA_LORDS[nak_idx % 9]

    cursor = birth - dt.timedelta(days=elapsed * DASHA_YEARS[first_lord] * DAYS_PER_YEAR)
    horizon = birth + dt.timedelta(days=years_after_birth * DAYS_PER_YEAR)
    schedule, k = [], 0
    while cursor < horizon:
        lord = _sequence_from(first_lord)[k % 9]
        end = cursor + dt.timedelta(days=DASHA_YEARS[lord] * DAYS_PER_YEAR)
        schedule.append({
            "lord": lord,
            "start": cursor,
            "end": end,
            "antardashas": sub_periods(lord, cursor, end),
            "balance_at_birth": k == 0,
        })
        cursor, k = end, k + 1
    return schedule


def dasha_balance(chart, schedule):
    """Remaining years of the first Mahadasha at birth."""
    first = schedule[0]
    return (first["end"] - chart["birth_utc"]).days / DAYS_PER_YEAR


def active_periods(schedule, when):
    """(mahadasha, antardasha, pratyantardasha) dicts running at `when`, or Nones."""
    for md in schedule:
        if md["start"] <= when < md["end"]:
            for ad in md["antardashas"]:
                if ad["start"] <= when < ad["end"]:
                    for pd in sub_periods(ad["lord"], ad["start"], ad["end"]):
                        if pd["start"] <= when < pd["end"]:
                            return md, ad, pd
    return None, None, None


def periods_in_window(schedule, start, end):
    """Flat rows of MD / AD / PD periods overlapping [start, end) for the timeline chart."""
    rows = []
    for md in schedule:
        if md["end"] <= start or md["start"] >= end:
            continue
        rows.append({"level": "Mahadasha", "label": f"{md['lord']} Mahadasha",
                     "lords": md["lord"], "lord": md["lord"], "start": md["start"], "end": md["end"]})
        for ad in md["antardashas"]:
            if ad["end"] <= start or ad["start"] >= end:
                continue
            rows.append({"level": "Antardasha", "label": f"{md['lord']}–{ad['lord']}",
                         "lords": f"{md['lord']} / {ad['lord']}", "lord": ad["lord"],
                         "start": ad["start"], "end": ad["end"]})
            for pd in sub_periods(ad["lord"], ad["start"], ad["end"]):
                if pd["end"] <= start or pd["start"] >= end:
                    continue
                rows.append({"level": "Pratyantardasha", "label": f"{md['lord']}–{ad['lord']}–{pd['lord']}",
                             "lords": f"{md['lord']} / {ad['lord']} / {pd['lord']}", "lord": pd["lord"],
                             "start": pd["start"], "end": pd["end"]})
    return rows
