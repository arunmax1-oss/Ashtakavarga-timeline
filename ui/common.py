"""Shared imports, cached calculations and helpers for every page.

`streamlit_app.py` computes the chart once per run and stores everything the pages need in
st.session_state["ctx"]; pages read it with ctx().
"""
from types import SimpleNamespace

import base64
import calendar
import datetime as dt
import json
import zoneinfo

import pandas as pd
import streamlit as st

from vedic import bhrigu
from vedic import compare as cmp
from vedic import career
from vedic import insights as ins
from vedic import houses as hs
from vedic import journal as jr
from vedic import lifeareas as la
from vedic import monthly
from vedic import muhurta as mh
from vedic import narratives as nar
from vedic import remedies as rem
from vedic import vimshopaka as vim
from vedic.aspects import aspects_on, combustion
from vedic.ashtakavarga import compute_ashtakavarga, sav_by_house, sensitive_nakshatras, shodhana, sign_table
from vedic.chart import build_chart, geocode, jd_to_datetime
from vedic.constants import AYANAMSHAS, CLASSICAL_PLANETS as CLASSICAL, HOUSE_INFO, NAKSHATRA_SPAN, NAKSHATRAS, SIGNS, ordinal
from vedic.chartviz import north_indian_svg, south_indian_svg
from vedic.dasha import active_periods, dasha_balance, periods_in_window, sub_periods, vimshottari
from vedic.dasha_alt import chara_dasha, running, yogini_dasha
from vedic.sensitivity import dasha_shift_per_minute, sensitivity, warning
from vedic.vargas import VARGAS, varga_positions
from vedic.plots import (bav_heatmap, month_calendar_html, sav_figure, shadbala_figure, strength_figure,
                         timeline_figure, to_local, week_figure, year_heatmap)
from vedic.report import build_report
from vedic.shadbala import COMPONENT_LABELS, shadbala
from vedic.transits import saturn_timeline, segments_by, transit_segments, utc_now
from vedic.weekly import day_forecast, fmt_span, week_forecast
from vedic.yogas import detect_yogas, dignity_strength


# --------------------------------------------------------------------------------------
# Cached calculations
# --------------------------------------------------------------------------------------
@st.cache_data(ttl=7 * 86400, show_spinner=False)
def cached_geocode(query):
    return geocode(query)


@st.cache_data(show_spinner=False)
def compute_core(date, time, lat, lon, tz_name, ayanamsha, true_node):
    chart = build_chart(date, time, lat, lon, tz_name, ayanamsha, true_node)
    av = compute_ashtakavarga(chart)
    return chart, av, vimshottari(chart), shadbala(chart)


@st.cache_data(show_spinner=False)
def cached_transits(chart, av, planet, start, end):
    return transit_segments(chart, av, planet, start, end)


@st.cache_data(show_spinner=False)
def cached_week(chart, av, schedule, week_start, tz, sb, place):
    return week_forecast(chart, av, schedule, week_start, tz, sb, place)


@st.cache_data(show_spinner=False)
def cached_month(chart, av, schedule, sb, year, month, tz, place):
    return monthly.month_forecast(chart, av, schedule, sb, year, month, tz, place)


@st.cache_data(show_spinner=False)
def cached_year(chart, av, schedule, sb, year, month, tz):
    return monthly.year_overview(chart, av, schedule, sb, year, month, 12, tz)


@st.cache_data(show_spinner=False)
def cached_sensitivity(chart):
    return sensitivity(chart), dasha_shift_per_minute(chart)


@st.cache_data(show_spinner=False)
def cached_saturn(chart):
    return saturn_timeline(chart, chart["birth_utc"], chart["birth_utc"] + dt.timedelta(days=round(365.25 * 100)))


@st.cache_data(show_spinner=False)
def cached_muhurta(chart, av, schedule, activity, start, days, tz, place):
    return mh.find_days(chart, av, schedule, activity, start, days, tz, place)


@st.cache_data(show_spinner=False)
def cached_day(chart, av, schedule, date, tz):
    return day_forecast(chart, av, schedule, date, tz)


@st.cache_data(show_spinner=False)
def cached_area(chart, av, schedule, sb, key, start):
    """Promise, dasha periods, transits and double-transit windows for one life area (start = today, UTC)."""
    spec = la.AREAS[key]
    return {"promise": la.promise(chart, av, sb, key),
            "periods": la.area_periods(chart, schedule, sb, key, start),
            "transits": la.area_transits(chart, key, start),
            "double": la.double_transit(chart, spec["houses"][0], start),
            "extras": la.EXTRAS[key](chart, av, sb)}


@st.cache_data(show_spinner=False)
def cached_saturn_nakshatras(chart, start, years=12):
    """Saturn's nakshatra periods from `start` (for the Shodhya Pinda sensitive points)."""
    end = start + dt.timedelta(days=round(365.25 * years))
    return segments_by(chart, "Saturn", start, end, lambda lon: int(lon // NAKSHATRA_SPAN), step_days=2)


def today_utc():
    """Midnight UTC today: a stable cache key for once-a-day calculations."""
    return dt.datetime.combine(utc_now().date(), dt.time())


def chart_svg(style, chart, positions, title, degrees=True):
    fn = south_indian_svg if style == "South Indian" else north_indian_svg
    return fn(chart, positions, title, degrees)


@st.cache_data(show_spinner=False)
def cached_bb_windows(chart, start, end):
    return bhrigu.contact_windows(chart, bhrigu.bhrigu_bindu(chart)["lon"], ["Saturn", "Jupiter", "Rahu", "Ketu"],
                                  start, end, orb=2.0)


def fmt_date(d):
    return d.strftime("%d %b %Y")


def ctx():
    """The chart and settings computed by streamlit_app.py for this run."""
    return SimpleNamespace(**st.session_state["ctx"])


# Re-exported for the page modules in app_pages/.
__all__ = [
    "active_periods", "aspects_on", "AYANAMSHAS", "base64", "bav_heatmap", "bhrigu", "build_chart", "build_report",
    "cached_area", "CLASSICAL", "cached_bb_windows", "cached_day", "cached_saturn_nakshatras", "cached_geocode", "cached_month", "cached_muhurta", "cached_saturn",
    "cached_sensitivity", "cached_transits", "cached_week", "cached_year", "calendar", "career", "chara_dasha",
    "chart_svg", "cmp", "combustion", "COMPONENT_LABELS", "compute_ashtakavarga", "compute_core", "ctx",
    "dasha_balance", "dasha_shift_per_minute", "day_forecast", "detect_yogas", "dignity_strength", "dt", "fmt_date",
    "fmt_span", "geocode", "HOUSE_INFO", "hs", "la", "NAKSHATRA_SPAN", "NAKSHATRAS", "segments_by", "sensitive_nakshatras",
    "shodhana", "today_utc", "vim", "ins", "jd_to_datetime", "jr", "json", "mh", "month_calendar_html",
    "monthly", "nar", "north_indian_svg", "ordinal", "pd", "periods_in_window", "rem", "running", "saturn_timeline",
    "sav_by_house", "sav_figure", "sensitivity", "shadbala", "shadbala_figure", "sign_table", "SIGNS",
    "south_indian_svg", "st", "strength_figure", "sub_periods", "timeline_figure", "to_local", "transit_segments",
    "utc_now", "varga_positions", "VARGAS", "vimshottari", "warning", "week_figure", "week_forecast",
    "year_heatmap", "yogini_dasha", "zoneinfo",
]
