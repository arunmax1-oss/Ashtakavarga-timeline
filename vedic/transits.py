"""Transit timing: split a planet's real transit path into Kakshya windows scored by Ashtakavarga."""
import datetime as dt

from .ashtakavarga import KAKSHYA_SPAN, kakshya_has_bindu, KAKSHYA_LORDS
from .chart import house_from, jd_to_datetime, julian_day, planet_longitude, set_ayanamsha
from .constants import SIGNS

# Sampling step per planet (hours): small enough that no 3°45' slice can be skipped.
STEP_HOURS = {"Moon": 1, "Mercury": 6, "Venus": 6, "Sun": 12, "Mars": 12, "Jupiter": 24, "Saturn": 24}


def rate(bindu, bav, sav):
    """Same thresholds as the original timing engine: BAV >= 4 and SAV >= 28."""
    if not bindu:
        return "Muted (no Kakshya bindu)"
    if bav >= 4 and sav >= 28:
        return "Strong"
    if bav >= 4 or sav >= 28:
        return "Moderate"
    return "Weak"


def _slice(jd, planet, true_node):
    lon, _ = planet_longitude(jd, planet, true_node)
    return int(lon // KAKSHYA_SPAN) % 96


def transit_segments(chart, av, planet, start, end):
    """Kakshya windows for `planet` between naive-UTC datetimes start and end."""
    set_ayanamsha(chart["ayanamsha"])
    true_node = chart["true_node"]
    step = STEP_HOURS[planet] / 24.0
    jd, jd_end = julian_day(start), julian_day(end)

    boundaries = [jd]
    current = _slice(jd, planet, true_node)
    slices = [current]
    while jd < jd_end:
        nxt = min(jd + step, jd_end)
        s = _slice(nxt, planet, true_node)
        if s != current:
            lo, hi = jd, nxt  # bisect to ~1 minute
            while hi - lo > 1 / 1440:
                mid = (lo + hi) / 2
                if _slice(mid, planet, true_node) == current:
                    lo = mid
                else:
                    hi = mid
            boundaries.append(hi)
            slices.append(s)
            current = s
        jd = nxt
    boundaries.append(jd_end)

    asc = chart["asc_sign_idx"]
    moon_sign = chart["planets"]["Moon"]["sign_idx"]
    out = []
    for i, sl in enumerate(slices):
        sign_idx, k_idx = divmod(sl, 8)
        lord = KAKSHYA_LORDS[k_idx]
        bindu = kakshya_has_bindu(av, planet, sign_idx, lord)
        bav = av["bav"][planet][sign_idx]
        sav = av["sav"][sign_idx]
        out.append({
            "planet": planet,
            "sign_idx": sign_idx,
            "sign": SIGNS[sign_idx],
            "house": house_from(sign_idx, asc),
            "house_from_moon": house_from(sign_idx, moon_sign),
            "kakshya": k_idx + 1,
            "kakshya_lord": lord,
            "bindu": bindu,
            "bav": bav,
            "sav": sav,
            "score": sav * bav if bindu else 0,
            "rating": rate(bindu, bav, sav),
            "start": jd_to_datetime(boundaries[i]),
            "end": jd_to_datetime(boundaries[i + 1]),
        })
    return out


def utc_now():
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)


SATURN_PHASES = {12: "Sade Sati: rising phase", 1: "Sade Sati: peak phase", 2: "Sade Sati: setting phase",
                 4: "Ardhashtama Shani (4th from Moon)", 8: "Ashtama Shani (8th from Moon)"}


def saturn_timeline(chart, start, end):
    """Every Saturn sign period between start and end that is a Sade Sati, Ashtama or Ardhashtama phase,
    plus the overall Sade Sati cycles. Retrograde re-entries appear as separate short periods."""
    from .chart import house_from, jd_to_datetime as to_dt
    set_ayanamsha(chart["ayanamsha"])
    moon = chart["planets"]["Moon"]["sign_idx"]
    jd, jd_end = julian_day(start), julian_day(end)

    def sign(j):
        return int(planet_longitude(j, "Saturn")[0] // 30)

    segments, cur, seg_start = [], sign(jd), jd
    j = jd
    while j < jd_end:
        nxt = min(j + 5, jd_end)
        s = sign(nxt)
        if s != cur:
            lo, hi = j, nxt
            while hi - lo > 1 / 24:
                mid = (lo + hi) / 2
                lo, hi = (mid, hi) if sign(mid) == cur else (lo, mid)
            segments.append((cur, seg_start, hi))
            cur, seg_start = s, hi
        j = nxt
    segments.append((cur, seg_start, jd_end))

    periods = []
    for s, a, b in segments:
        h = house_from(s, moon)
        if h in SATURN_PHASES:
            periods.append({"phase": SATURN_PHASES[h], "house_from_moon": h, "sign": SIGNS[s],
                            "start": to_dt(a), "end": to_dt(b)})

    cycles = []
    for p in periods:
        if p["house_from_moon"] in (12, 1, 2):
            if cycles and (p["start"] - cycles[-1]["end"]).days < 400:
                cycles[-1]["end"] = p["end"]
            else:
                cycles.append({"start": p["start"], "end": p["end"]})
    return periods, cycles


def segments_by(chart, planet, start, end, key, step_days=2.0):
    """Split `planet`'s path between naive-UTC start and end into runs where key(longitude) stays the same.
    Returns [(value, start datetime, end datetime)]; boundaries are found to within an hour."""
    set_ayanamsha(chart["ayanamsha"])
    jd, jd_end = julian_day(start), julian_day(end)

    def val(j):
        return key(planet_longitude(j, planet, chart["true_node"])[0])

    out, cur, seg_start, j = [], val(jd), jd, jd
    while j < jd_end:
        nxt = min(j + step_days, jd_end)
        v = val(nxt)
        if v != cur:
            lo, hi = j, nxt
            while hi - lo > 1 / 24:
                mid = (lo + hi) / 2
                lo, hi = (mid, hi) if val(mid) == cur else (lo, mid)
            out.append((cur, seg_start, hi))
            cur, seg_start = val(hi), hi
        j = nxt
    out.append((cur, seg_start, jd_end))
    return [(v, jd_to_datetime(a), jd_to_datetime(b)) for v, a, b in out]
