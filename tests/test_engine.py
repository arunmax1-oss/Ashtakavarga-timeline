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
