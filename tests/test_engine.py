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
        assert len(ins.ashtakavarga_insight(c, av, [av["sav"][(c["asc_sign_idx"] + h) % 12] for h in range(12)])) == 5
        assert len(ins.current_transits(c, av, when)) == 4
        segs = transit_segments(c, av, "Jupiter", when, when + dt.timedelta(days=365))
        ins.upcoming_strong(segs, when)
        assert len(ins.strength_insight(c, dignity_strength(c))) == 9


def test_remedies_are_explained_and_consistent():
    """Every remedy must carry a reason; gemstones never go to Rahu/Ketu or to pure dusthana lords."""
    from vedic import remedies as rem
    from vedic.insights import ruled_houses
    from vedic.narratives import GLOSSARY, eighth_house_reading, health_narrative
    when = dt.datetime(2026, 10, 1)
    for date, time, lat, lon, tz in [
        (dt.date(1985, 6, 15), dt.time(14, 30), 12.97, 77.59, "Asia/Kolkata"),
        (dt.date(1972, 1, 3), dt.time(4, 10), 51.51, -0.13, "Europe/London"),
        (dt.date(1999, 9, 21), dt.time(23, 55), 40.71, -74.01, "America/New_York"),
        (dt.date(2010, 3, 8), dt.time(12, 0), -33.87, 151.21, "Australia/Sydney"),
    ]:
        c = build_chart(date, time, lat, lon, tz)
        av = compute_ashtakavarga(c)
        md, ad, _ = active_periods(vimshottari(c), when)
        res = rem.build_remedies(c, av, (md, ad), when)
        assert {md["lord"], ad["lord"]} <= {e["planet"] for e in res["now"]}
        for e in res["now"] + res["lifelong"]:
            assert e["reasons"] and e["priority"] in ("High", "Medium", "Low")
            assert rem.entry_markdown(e)
            if e["gem"]:
                houses = ruled_houses(c, e["planet"])
                assert e["planet"] not in ("Rahu", "Ketu")
                assert 1 in houses or not any(h in (6, 8, 12) for h in houses)
        assert all(e["until"] for e in res["now"]) and not any(e["until"] for e in res["lifelong"])
        assert rem.table_rows(res["now"]) and rem.remedies_markdown(res)
        sav_house = [av["sav"][(c["asc_sign_idx"] + h) % 12] for h in range(12)]
        assert eighth_house_reading(sav_house[7])[0] in health_narrative(c, sav_house)
    assert len(GLOSSARY) >= 20


def test_aspects_and_combustion():
    from vedic.aspects import aspects_on, combustion, conjunctions, influences
    p = CHART["planets"]
    # 1985 chart: Saturn in Libra aspects the 3rd, 7th and 10th signs from it (Sagittarius, Aries, Cancer)
    assert ("Saturn", 7) in aspects_on(CHART, "Moon")       # Moon in Aries
    assert "Rahu" in conjunctions(CHART, "Moon")
    assert ("Mars", 8) in aspects_on(CHART, "Jupiter")      # Mars in Gemini -> 8th is Capricorn
    # Mars is 9.7 deg from the Sun (limit 17), Mercury 9.4 deg (limit 14); Jupiter is far away
    assert combustion(CHART, "Mars") and combustion(CHART, "Mercury")
    assert combustion(CHART, "Jupiter") is None and combustion(CHART, "Rahu") is None
    # Rahu/Ketu aspects never count as malefic pressure, only their conjunctions
    assert all("Rahu's" not in m for m in influences(CHART, "Venus")["malefic"])
    assert "Rahu in the same sign" in influences(CHART, "Venus")["malefic"]
    assert p["Sun"]["sign"] == "Gemini"
