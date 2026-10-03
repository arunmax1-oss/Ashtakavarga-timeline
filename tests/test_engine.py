"""Run with: pip install pytest && pytest"""
import datetime as dt

from vedic.ashtakavarga import compute_ashtakavarga
from vedic.chart import build_chart
from vedic.dasha import active_periods, vimshottari
from vedic.transits import transit_segments

CHART = build_chart(dt.date(1985, 6, 15), dt.time(14, 30), 12.9716, 77.5946, "Asia/Kolkata")


def test_birth_time_converted_to_utc():
    assert CHART["birth_utc"] == dt.datetime(1985, 6, 15, 9, 0)


def test_known_positions():
    p = CHART["planets"]
    assert p["Jupiter"]["sign"] == "Capricorn" and p["Jupiter"]["retrograde"]
    assert p["Rahu"]["sign"] == "Aries" and p["Ketu"]["sign"] == "Libra"
    assert p["Moon"]["nakshatra"] == "Bharani"


def test_ashtakavarga_classical_totals():
    av = compute_ashtakavarga(CHART)
    totals = {p: sum(v) for p, v in av["bav"].items()}
    assert totals == {"Sun": 48, "Moon": 49, "Mars": 39, "Mercury": 54, "Jupiter": 56, "Venus": 52, "Saturn": 39}
    assert sum(av["sav"]) == 337


def test_dasha_starts_with_moon_nakshatra_lord_and_is_contiguous():
    schedule = vimshottari(CHART)
    assert schedule[0]["lord"] == "Venus"  # Bharani is ruled by Venus
    for a, b in zip(schedule, schedule[1:]):
        assert a["end"] == b["start"]
    md, ad, pd = active_periods(schedule, dt.datetime(2026, 10, 1))
    assert (md["lord"], ad["lord"]) == ("Rahu", "Moon")


def test_transit_segments_are_contiguous():
    av = compute_ashtakavarga(CHART)
    start, end = dt.datetime(2026, 1, 1), dt.datetime(2027, 1, 1)
    segs = transit_segments(CHART, av, "Jupiter", start, end)
    assert segs[0]["start"] == start and segs[-1]["end"] == end
    for a, b in zip(segs, segs[1:]):
        assert a["end"] == b["start"] and (a["sign"], a["kakshya"]) != (b["sign"], b["kakshya"])


def test_insights_generate_for_varied_charts():
    """Every explanation function should run for charts with different ascendants and dashas."""
    from vedic import insights as ins
    from vedic.yogas import dignity_strength
    when = dt.datetime(2026, 10, 1)
    for date, time, lat, lon, tz in [
        (dt.date(1985, 6, 15), dt.time(14, 30), 12.97, 77.59, "Asia/Kolkata"),
        (dt.date(1972, 1, 3), dt.time(4, 10), 51.51, -0.13, "Europe/London"),
        (dt.date(1999, 9, 21), dt.time(23, 55), 40.71, -74.01, "America/New_York"),
        (dt.date(2010, 3, 8), dt.time(12, 0), -33.87, 151.21, "Australia/Sydney"),
    ]:
        c = build_chart(date, time, lat, lon, tz)
        av = compute_ashtakavarga(c)
        sched = vimshottari(c)
        md, ad, _ = active_periods(sched, when)
        assert ins.planets_highlights(c)
        for name in c["planets"]:
            assert ins.planet_story(c, av, name)
        assert ins.dasha_insight(c, av, md, ad)
        ins.upcoming_antardashas(c, av, sched, md, ad)
        assert len(ins.ashtakavarga_insight(c, av, [av["sav"][(c["asc_sign_idx"] + h) % 12] for h in range(12)])) == 4
        assert len(ins.current_transits(c, av, when)) == 4
        segs = transit_segments(c, av, "Jupiter", when, when + dt.timedelta(days=365))
        ins.upcoming_strong(segs, when)
        assert len(ins.strength_insight(c, dignity_strength(c))) == 9
