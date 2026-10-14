"""Vedic Astrology & Ashtakavarga Timing Engine — Streamlit UI.

All calculations live in the `vedic/` package; this file only gathers input and lays out results.
"""
import base64
import datetime as dt
import json
import zoneinfo

import pandas as pd
import streamlit as st

from vedic import bhrigu
from vedic import compare as cmp
from vedic import compatibility as compat
from vedic import insights as ins
from vedic import journal as jr
from vedic import muhurta as mh
from vedic import narratives as nar
from vedic import remedies as rem
from vedic.aspects import aspects_on, combustion
from vedic.ashtakavarga import compute_ashtakavarga, sav_by_house, sign_table
from vedic.chart import build_chart, geocode, jd_to_datetime
from vedic.constants import AYANAMSHAS, HOUSE_INFO, SIGNS, ordinal
from vedic.chartviz import north_indian_svg, south_indian_svg
from vedic.dasha import active_periods, dasha_balance, periods_in_window, sub_periods, vimshottari
from vedic.dasha_alt import chara_dasha, running, yogini_dasha
from vedic.sensitivity import dasha_shift_per_minute, sensitivity, warning
from vedic.vargas import VARGAS, varga_positions
from vedic.plots import (bav_heatmap, sav_figure, shadbala_figure, strength_figure, timeline_figure, to_local,
                         week_figure)
from vedic.report import build_report
from vedic.shadbala import COMPONENT_LABELS, shadbala
from vedic.transits import saturn_timeline, transit_segments, utc_now
from vedic.weekly import day_forecast, fmt_span, week_forecast
from vedic.yogas import detect_yogas, dignity_strength

st.set_page_config(page_title="Vedic Astrology & Ashtakavarga Engine", page_icon="🔮", layout="wide")


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


def chart_svg(style, chart, positions, title, degrees=True):
    fn = south_indian_svg if style == "South Indian" else north_indian_svg
    return fn(chart, positions, title, degrees)


# --------------------------------------------------------------------------------------
# Saved profiles: kept in the page link (?p=...) so a bookmark reopens them
# --------------------------------------------------------------------------------------
PROFILE_KEYS = {"name": "k_name", "dob": "k_dob", "tob": "k_tob", "place": "k_place", "manual": "k_manual",
                "lat": "k_lat", "lon": "k_lon", "tz": "k_tz"}
DEFAULT_PROFILE = {"name": "", "dob": dt.date(1985, 6, 15), "tob": dt.time(14, 30), "place": "Bengaluru, India",
                   "manual": False, "lat": 12.9716, "lon": 77.5946, "tz": "Asia/Kolkata"}


def encode_profiles(profiles):
    raw = [{**p, "dob": p["dob"].isoformat(), "tob": p["tob"].strftime("%H:%M")} for p in profiles]
    return base64.urlsafe_b64encode(json.dumps(raw, separators=(",", ":")).encode()).decode()


def decode_profiles(text):
    try:
        raw = json.loads(base64.urlsafe_b64decode(text.encode()).decode())
        return [{**DEFAULT_PROFILE, **p, "dob": dt.date.fromisoformat(p["dob"]),
                 "tob": dt.datetime.strptime(p["tob"], "%H:%M").time()} for p in raw]
    except Exception:
        return []


def load_profile(profile):
    """Show `profile` in the sidebar. Bumping the version gives every field a fresh key, so each one is
    redrawn with the profile's value (Streamlit ignores a new default for a widget it already knows)."""
    st.session_state["_prof"] = dict(profile)
    st.session_state["_ver"] = st.session_state.get("_ver", 0) + 1


def field(name):
    """(key, starting value) for a sidebar field. Values live in our own copy (_prof) because Streamlit
    forgets a widget's value while it is hidden, e.g. the manual coordinates."""
    return {"key": f"{PROFILE_KEYS[name]}_{st.session_state['_ver']}", "value": st.session_state["_prof"][name]}


def remember(name, value):
    st.session_state["_prof"][name] = value
    return value


def on_pick_profile():
    choice = st.session_state["profile_pick"]
    if choice == "➕ New person":
        load_profile(DEFAULT_PROFILE)
    else:
        load_profile(next(p for p in st.session_state["profiles"] if p["name"] == choice))


def current_profile():
    return dict(st.session_state["_prof"])


if "profiles" not in st.session_state:
    st.session_state["profiles"] = decode_profiles(st.query_params.get("p", ""))
    first = st.session_state["profiles"][0] if st.session_state["profiles"] else DEFAULT_PROFILE
    load_profile(first)
    if st.session_state["profiles"]:
        st.session_state["profile_pick"] = first["name"]


@st.cache_data(show_spinner=False)
def cached_bb_windows(chart, start, end):
    return bhrigu.contact_windows(chart, bhrigu.bhrigu_bindu(chart)["lon"], ["Saturn", "Jupiter", "Rahu", "Ketu"],
                                  start, end, orb=2.0)


def fmt_date(d):
    return d.strftime("%d %b %Y")


# --------------------------------------------------------------------------------------
# Sidebar: birth details
# --------------------------------------------------------------------------------------
st.sidebar.header("👤 Birth Details")
names = [p["name"] for p in st.session_state["profiles"]]
if "pending_pick" in st.session_state:  # set by Save/Remove on the previous run
    pick = st.session_state.pop("pending_pick")
    st.session_state["profile_pick"] = pick if pick in names else "➕ New person"
if names:
    st.sidebar.selectbox("Saved people", names + ["➕ New person"], key="profile_pick", on_change=on_pick_profile)
user_name = remember("name", st.sidebar.text_input("Name", placeholder="Needed to save a profile", **field("name")))
dob = remember("dob", st.sidebar.date_input("Date of Birth", min_value=dt.date(1900, 1, 1), max_value=dt.date.today(),
                                            format="DD/MM/YYYY", **field("dob")))
tob = remember("tob", st.sidebar.time_input("Time of Birth (24h, local)", step=60, **field("tob")))
place = remember("place", st.sidebar.text_input("Place of Birth", **field("place"),
                                                help="City and country, e.g. 'Chennai, India' or 'London, UK'."))
manual = remember("manual", st.sidebar.checkbox("Enter coordinates manually", **field("manual"),
                                                help="Use if the place lookup fails."))

if manual:
    c1, c2 = st.sidebar.columns(2)
    lat = remember("lat", c1.number_input("Latitude", min_value=-90.0, max_value=90.0, format="%.4f",
                                          **field("lat")))
    lon = remember("lon", c2.number_input("Longitude", min_value=-180.0, max_value=180.0, format="%.4f",
                                          **field("lon")))
    zones = sorted(zoneinfo.available_timezones())
    tz_field = field("tz")
    tz_name = remember("tz", st.sidebar.selectbox("Time zone", zones, key=tz_field["key"],
                                                  index=zones.index(tz_field["value"])))
    address = f"{lat:.4f}, {lon:.4f}"
else:
    loc = cached_geocode(place.strip()) if place.strip() else None
    if not loc:
        st.sidebar.error("Couldn't find that place. Try 'City, Country', or tick *Enter coordinates manually*.")
        st.stop()
    lat, lon, tz_name, address = loc["lat"], loc["lon"], loc["tz_name"], loc["address"]
    st.session_state["_prof"].update(lat=lat, lon=lon, tz=tz_name)  # pre-fills the manual fields if ticked later

with st.sidebar.expander("⚙ Calculation settings"):
    ayanamsha = st.selectbox("Ayanamsha", AYANAMSHAS, index=0)
    true_node = st.radio("Rahu/Ketu", ["Mean node", "True node"], horizontal=True) == "True node"
    st.caption("Houses: whole sign (Rasi = Bhava). Ephemeris: Swiss Ephemeris (Moshier).")

chart, av, schedule, sb = compute_core(dob, tob, lat, lon, tz_name, ayanamsha, true_node)
P = chart["planets"]
sav_house = sav_by_house(chart, av)
now = utc_now()
md_now, ad_now, pd_now = active_periods(schedule, now)

st.sidebar.caption(f"📍 {address}")
st.sidebar.caption(f"🌐 {lat:.2f}°, {lon:.2f}° · {tz_name} (UTC{chart['utc_offset']:+.2f} at birth)")

with st.sidebar.expander("💾 Save or remove this person"):
    st.caption("Profiles are stored in the page link. After saving, **bookmark the page** to keep them.")
    s1, s2 = st.columns(2)
    if s1.button("Save", width="stretch", disabled=not user_name.strip()):
        prof = current_profile()
        if not manual:
            prof.update(lat=lat, lon=lon, tz=tz_name)
        others = [p for p in st.session_state["profiles"] if p["name"] != prof["name"]]
        st.session_state["profiles"] = others + [prof]
        st.query_params["p"] = encode_profiles(st.session_state["profiles"])
        st.session_state["pending_pick"] = prof["name"]
        st.rerun()
    if s2.button("Remove", width="stretch", disabled=user_name not in names):
        st.session_state["profiles"] = [p for p in st.session_state["profiles"] if p["name"] != user_name]
        if st.session_state["profiles"]:
            st.query_params["p"] = encode_profiles(st.session_state["profiles"])
        else:
            st.query_params.pop("p", None)
        st.session_state["pending_pick"] = "➕ New person"
        st.rerun()

# --------------------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------------------
st.title("🔮 Vedic Astrology & Ashtakavarga Engine")
who = f"**{user_name}** · " if user_name else ""
st.caption(f"{who}Born {fmt_date(dob)} at {tob.strftime('%H:%M')} · {address} · "
           f"{ayanamsha} ayanamsha {chart['ayanamsha_deg']:.4f}°")

m = st.columns(5)
m[0].metric("Lagna", P["Ascendant"]["sign"], f"{P['Ascendant']['degree']:.1f}° {P['Ascendant']['nakshatra']}",
            delta_color="off", help="Your rising sign: the starting point of the chart. Describes body and temperament.")
m[1].metric("Moon Sign", P["Moon"]["sign"], P["Moon"]["nakshatra"], delta_color="off",
            help="Your Rashi: mind and emotions. The second line is your birth star (nakshatra).")
m[2].metric("Atmakaraka", nar.karaka(chart, "AK")["planet"],
            help="Your 'soul planet': the planet with the highest degree. Its themes are your main life lesson.")
m[3].metric("Amatyakaraka", nar.karaka(chart, "AmK")["planet"],
            help="Your 'career planet': the second-highest degree. It shapes the kind of work that suits you.")
m[4].metric("Mahadasha", md_now["lord"] if md_now else "—",
            f"{ad_now['lord']} AD until {fmt_date(ad_now['end'])}" if ad_now else None, delta_color="off",
            help="The planet running your current multi-year life chapter. AD = Antardasha, the current sub-chapter.")

with st.expander("📖 New to this? Plain-English glossary of the terms used on every tab"):
    st.markdown("\n".join(f"- **{k}:** {v}" for k, v in nar.GLOSSARY.items()))

sens_rows, dasha_days_per_min = cached_sensitivity(chart)
sens_warning = warning(sens_rows)
if sens_warning:
    st.warning(sens_warning + " Details are on the Planets tab.")

remedies = rem.build_remedies(chart, av, (md_now, ad_now), now, sb)

(tab_summary, tab_week, tab_planner, tab_planets, tab_dasha, tab_av, tab_timing, tab_bhrigu, tab_strength,
 tab_remedies, tab_match, tab_journal) = st.tabs(
    ["📜 Summary", "🗓 This Week", "📅 Planner", "🪐 Planets", "⏳ Dasha", "📊 Ashtakavarga", "🎯 Timing",
     "🔱 Bhrigu", "⚡ Strength", "🪔 Remedies", "💞 Match", "📓 Journal"])

# --------------------------------------------------------------------------------------
# Summary
# --------------------------------------------------------------------------------------
with tab_summary:
    style = st.radio("Chart style", ["South Indian", "North Indian"], horizontal=True, key="chart_style")
    cA, cB = st.columns(2)
    cA.markdown(chart_svg(style, chart, varga_positions(chart, "D1"), "Rasi (D1)"), unsafe_allow_html=True)
    cB.markdown(chart_svg(style, chart, varga_positions(chart, "D9"), "Navamsa (D9)", False), unsafe_allow_html=True)
    st.caption("℞ = retrograde. Numbers in the North Indian chart are sign numbers (1 = Aries); the top diamond is "
               "the 1st house. More divisional charts are on the Planets tab.")
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🌟 Core Identity & Mindset")
        ak = nar.karaka(chart, "AK")["planet"]
        st.markdown(
            f"- **Rising sign:** {P['Ascendant']['sign']} ({P['Ascendant']['nakshatra']}, pada {P['Ascendant']['pada']})\n"
            f"- **Moon sign (mind & mood):** {P['Moon']['sign']} ({P['Moon']['nakshatra']}, lord {P['Moon']['nakshatra_lord']})\n"
            f"- **Soul purpose (Atmakaraka):** {ak} — the life journey develops the higher qualities of {ak}."
        )
        st.subheader("💼 Career & Wealth")
        st.markdown(nar.career_narrative(chart, sav_house))
    with col2:
        st.subheader("🩺 Health & Vitality")
        st.markdown(nar.health_narrative(chart, sav_house))
        st.caption("For reflection only — not medical advice.")

    st.divider()
    st.subheader("✨ Yogas (Special Planetary Alignments)")
    yogas = detect_yogas(chart)
    if yogas:
        st.dataframe(pd.DataFrame(yogas), width="stretch", hide_index=True)
    else:
        st.info("None of the tracked yogas are present: a well-balanced distribution without extreme concentrations.")

# --------------------------------------------------------------------------------------
# Weekly forecast
# --------------------------------------------------------------------------------------
with tab_week:
    st.markdown("> 💡 A **weekly forecast** built from your chart. Each day is rated from the Moon's transit: its "
                "**Tara Bala** (the Moon's nakshatra counted from your birth star), **Chandra Bala** (its house from "
                "your natal Moon; the 8th, *Chandrashtama*, is the hardest), the Moon's own Ashtakavarga points, the "
                "**tithi** (lunar day) and whether the weekday is ruled by one of your Dasha lords. The week adds "
                "sign changes, retrograde stations, Dasha changes, strong Kakshya windows and Bhrigu Bindu contacts.")
    c1, c2 = st.columns([1, 2])
    week_start = c1.date_input("7 days starting", value=dt.date.today(), format="DD/MM/YYYY", key="week_pick")
    here = c2.text_input("Where you are now (for sunrise, Rahu Kalam etc.)", value="", key="here_place",
                         placeholder=f"Leave blank to use the birth place ({address.split(',')[0]})")
    here_loc = cached_geocode(here.strip()) if here.strip() else None
    if here.strip() and not here_loc:
        st.warning("Couldn't find that place; using the birth place for daily timings.")
    week_tz = here_loc["tz_name"] if here_loc else tz_name
    week_place = (here_loc["lat"], here_loc["lon"]) if here_loc else (lat, lon)
    st.session_state["week_ctx"] = (week_tz, week_place)
    wk = cached_week(chart, av, schedule, week_start, week_tz, sb, week_place)
    st.caption(f"Times shown in {week_tz}.")
    st.subheader(f"🧭 {week_start:%a %d %b} – {week_start + dt.timedelta(days=6):%a %d %b %Y}")
    for line in wk["summary"]:
        st.markdown(f"- {line}")

    st.plotly_chart(week_figure(wk["days"]), width="stretch")
    st.dataframe(pd.DataFrame([{
        "Day": f"{d['icon']} {d['date']:%a %d %b}", "Rating": d["rating"], "Tithi": d["tithi"]["name"],
        "Nakshatra": d["nakshatra"], "Moon": f"{d['moon_sign']} ({ordinal(d['from_lagna'])} house)",
        "Tara": d["tara"]["name"],
        "Rahu Kalam": fmt_span(d["timings"]["rahu_kalam"]) if d["timings"] else "—",
        "Abhijit": fmt_span(d["timings"]["abhijit"]) if d["timings"] else "—",
        "Best for": d["best_use"],
    } for d in wk["days"]]), width="stretch", hide_index=True)
    st.caption("**Rahu Kalam** is the daily slot traditionally avoided for new starts; **Abhijit Muhurta** is the "
               "auspicious window around local noon.")

    st.subheader("Day by day")
    for d in wk["days"]:
        with st.expander(f"{d['icon']} {d['date']:%A %d %b} · {d['rating']} · {d['nakshatra']} · {d['tithi']['name']}"):
            st.markdown(f"**Best for:** {d['best_use']}.  \n**Tithi:** {d['tithi']['name']} "
                        f"({d['tithi']['group']}: {d['tithi']['group_use']}). **Weekday lord:** {d['weekday_lord']}.")
            st.markdown("**Why this rating**\n" + "\n".join(f"- {r}" for r in d["reasons"]))
            t = d["timings"]
            if t:
                st.markdown(f"**Timings:** sunrise {t['sunrise']:%H:%M}, sunset {t['sunset']:%H:%M} · "
                            f"Rahu Kalam {fmt_span(t['rahu_kalam'])} · Yamaganda {fmt_span(t['yamaganda'])} · "
                            f"Gulika {fmt_span(t['gulika'])} · Abhijit {fmt_span(t['abhijit'])}"
                            + (f" ({t['abhijit_note']})" if t["abhijit_note"] else ""))
            if d["changes"]:
                st.caption("During the day: " + "; ".join(d["changes"]) + ".")

    st.subheader("📌 Key events this week")
    if wk["events"]:
        for e in wk["events"]:
            st.markdown(f"- **{e['when']:%a %d %b, %H:%M}:** {e['text']}")
    else:
        st.caption("No sign changes, retrograde stations or Dasha changes this week.")
    if wk["strong"]:
        st.markdown("**Strong transit windows overlapping this week:**")
        for t in wk["strong"]:
            st.markdown(f"- {t['planet']} in {t['sign']} (your {ordinal(t['house'])} house), {t['kakshya_lord']} kakshya: "
                        f"{t['start_local']:%d %b} → {t['end_local']:%d %b}")
    if wk["bb_hits"]:
        st.markdown("**Bhrigu Bindu contacts:** " + "; ".join(
            f"{w['planet']} within {w['closest']:.1f}°" for w in wk["bb_hits"]))

    with st.expander("Planetary climate from your Moon (Gochara)"):
        st.dataframe(pd.DataFrame([{
            "Planet": c["planet"], "Sign": c["sign"], "House from Moon": c["from_moon"],
            "House from Lagna": c["from_lagna"], "Classical result": "Favourable" if c["good"] else "Testing",
        } for c in wk["climate"]]), width="stretch", hide_index=True)
    st.caption("Ratings are interpretive rules from classical Jyotish, for reflection and planning, not certainties.")
    week_report = build_report(
        title=f"Weekly Forecast{' — ' + user_name if user_name else ''}",
        subtitle=f"7 days from {week_start:%d %b %Y} · Born {fmt_date(dob)} {tob.strftime('%H:%M')} · {address}",
        metrics=[("Running Dasha", " / ".join(p["lord"] for p in wk["periods"] if p)),
                 ("Average day", f"{wk['average']:+.1f}"),
                 ("Best day", max(wk["days"], key=lambda d: d["score"])["weekday"])],
        sections=[("This week", "\n".join(f"- {x}" for x in wk["summary"])),
                  ("Day by day", "\n".join(f"- **{d['date']:%a %d %b}: {d['rating']}.** {d['nakshatra']}, "
                                            f"{d['tithi']['name']}. Best for {d['best_use']}." for d in wk["days"])),
                  ("Key events", "\n".join(f"- {e['when']:%a %d %b %H:%M}: {e['text']}" for e in wk["events"])
                   or "- None")],
        figures=[week_figure(wk["days"])],
    )
    st.download_button("📥 Download this week (HTML)", week_report,
                       file_name=f"weekly_forecast_{week_start:%Y_%m_%d}.html", mime="text/html")

# --------------------------------------------------------------------------------------
# Planner (muhurta)
# --------------------------------------------------------------------------------------
with tab_planner:
    st.markdown("> 💡 **Muhurta** is choosing a good time to begin something. Pick an activity and the planner ranks "
                "the coming days by your personal day rating plus the classical rules for that activity: suitable "
                "nakshatras, favourable weekdays and good tithis. Days with Chandrashtama, a difficult Tara or a "
                "Rikta/new-moon tithi are ruled out. Start within Abhijit Muhurta if you can, and avoid Rahu Kalam.")
    p1, p2, p3 = st.columns([2, 1, 1])
    activity = p1.selectbox("Activity", list(mh.ACTIVITIES), key="mh_activity")
    mh_start = p2.date_input("From", value=dt.date.today(), format="DD/MM/YYYY", key="mh_start")
    mh_days = p3.slider("Days to search", 14, 90, 45, key="mh_days")
    ctx_tz, ctx_place = st.session_state.get("week_ctx", (tz_name, (lat, lon)))
    best, ruled_out = cached_muhurta(chart, av, schedule, activity, mh_start, mh_days, ctx_tz, ctx_place)
    st.caption(f"{mh.ACTIVITIES[activity]['why']} {ruled_out} of {mh_days} days were ruled out. Timings use the "
               "place set on the This Week tab (or your birth place).")
    if best:
        st.dataframe(pd.DataFrame([{
            "Date": f"{d['date']:%a %d %b %Y}", "Score": d["muhurta_score"], "Nakshatra": d["nakshatra"],
            "Tithi": d["tithi"]["name"], "Tara": d["tara"]["name"],
            "Abhijit (best slot)": fmt_span(d["timings"]["abhijit"]) if d["timings"] else "—",
            "Avoid (Rahu Kalam)": fmt_span(d["timings"]["rahu_kalam"]) if d["timings"] else "—",
            "Why": "; ".join(d["muhurta_reasons"]) or "Personal day rating only",
        } for d in best]), width="stretch", hide_index=True)
        top = max(best, key=lambda d: d["muhurta_score"])
        st.success(f"**Top pick: {top['date']:%A %d %b %Y}**, {top['nakshatra']} nakshatra, {top['tithi']['name']}"
                   + (f"; begin around {fmt_span(top['timings']['abhijit'])}" if top["timings"] else "") + ".")
    else:
        st.info("No suitable days in this range. Try a longer search window.")
    st.caption("A traditional muhurta also checks the Lagna at the start time; for major events, confirm with an "
               "astrologer.")

# --------------------------------------------------------------------------------------
# Planets & Nakshatras
# --------------------------------------------------------------------------------------
with tab_planets:
    st.markdown("> 💡 Each sign is divided into **Nakshatras** (lunar mansions) of 13°20'. They reveal instincts, "
                "sub-talents and planetary motivations. **D9** (Navamsha) shows inner strength and partnerships; "
                "**D10** (Dashamsha) shows career.")
    st.subheader("🧭 What this means for you")
    for line in ins.planets_highlights(chart):
        st.markdown(f"- {line}")

    st.subheader("Planet by planet")
    st.caption("Open a planet to see what its sign, house, nakshatra and lordship mean in your chart.")
    for n, p in P.items():
        label = f"{n}{' ℞' if p['retrograde'] else ''} · {p['sign']} · {ordinal(p['house'])} house · {p['nakshatra']}"
        with st.expander(label):
            st.markdown(ins.planet_story(chart, av, n))

    st.subheader("Reference table")
    rows = [{
        "Planet": n + (" ℞" if p["retrograde"] else ""), "Sign": p["sign"], "Degree": f"{p['degree']:.2f}°",
        "House": p["house"], "Nakshatra": p["nakshatra"], "Pada": p["pada"], "Nak. Lord": p["nakshatra_lord"],
        "Dignity": p["dignity"], "D9": p["d9_sign"], "D10": p["d10_sign"],
        "Combust": (f"{combustion(chart, n)['distance']:.1f}°" if n != "Ascendant" and combustion(chart, n) else ""),
        "Aspected by": ", ".join(f"{a} ({ordinal(h)})" for a, h in aspects_on(chart, n)) if n != "Ascendant" else "",
    } for n, p in P.items()]
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    st.caption("Combust = degrees from the Sun when inside the classical limit. Aspected by = whole-sign aspects "
               "received (Rahu/Ketu aspects are informational and not scored).")

    st.subheader("Jaimini Chara Karakas")
    st.dataframe(pd.DataFrame([{"Role": k["role"], "Planet": k["planet"], "Sign": k["sign"],
                                "Degree": f"{k['degree']:.2f}°", "Meaning": k["meaning"]} for k in chart["karakas"]]),
                 width="stretch", hide_index=True)
    st.markdown(ins.karaka_insight(chart))

    st.subheader("🗺 Divisional charts")
    v1, v2 = st.columns([1, 1])
    varga = v1.selectbox("Chart", list(VARGAS), format_func=lambda k: f"{k} · {VARGAS[k][0]}", index=5,
                         key="varga_pick")
    vstyle = v2.radio("Style", ["South Indian", "North Indian"], horizontal=True, key="varga_style")
    g1, g2 = st.columns(2)
    g1.markdown(chart_svg(vstyle, chart, varga_positions(chart, "D1"), "Rasi (D1)"), unsafe_allow_html=True)
    g2.markdown(chart_svg(vstyle, chart, varga_positions(chart, varga), varga, False), unsafe_allow_html=True)
    vpos = varga_positions(chart, varga)
    same = [n for n in P if n != "Ascendant" and vpos[n] == P[n]["sign_idx"]]
    st.caption(f"{VARGAS[varga][0]}. Planets in the same sign as in D1 (vargottama in this chart): "
               f"{', '.join(same) or 'none'}.")

    st.subheader("⏱ Birth-time sensitivity")
    st.markdown("How many minutes the birth time can move before each factor changes. Small numbers mean those "
                "readings depend on a precise birth time.")
    st.dataframe(pd.DataFrame([{
        "Factor": r["factor"], "Now": r["value"],
        "If born earlier": f"{r['earlier'][1]} after {r['earlier'][0]} min" if r["earlier"][0] else "no change within 4 h",
        "If born later": f"{r['later'][1]} after {r['later'][0]} min" if r["later"][0] else "no change within 4 h",
        "What it affects": r["impact"],
    } for r in sens_rows]), width="stretch", hide_index=True)
    st.caption(f"Each minute of birth-time error shifts all Vimshottari Dasha dates by about "
               f"{dasha_days_per_min:.1f} days.")

    with st.expander("🔍 Compare with other software (e.g. Jagannatha Hora)"):
        st.markdown("Paste planet positions from another program, one per line, e.g. `Sun 0°33' Gemini`, "
                    "`Moon Ar 25:29:24`, `Lagna 2 Li 06` or an absolute longitude like `Mars 70.30`.")
        pasted = st.text_area("Positions", height=180, key="cmp_text",
                              placeholder="Lagna 2 Li 06\nSun 0 Ge 33\nMoon 25 Ar 29\n...")
        if pasted.strip():
            theirs, unread = cmp.parse_positions(pasted)
            if theirs:
                crow = cmp.compare(chart, theirs)
                st.dataframe(pd.DataFrame(crow), width="stretch", hide_index=True)
                st.info(cmp.diagnose(crow))
            if unread:
                st.caption("Could not read: " + "; ".join(unread))

# --------------------------------------------------------------------------------------
# Dasha
# --------------------------------------------------------------------------------------
with tab_dasha:
    if md_now:
        st.success(f"📌 **Running now:** {md_now['lord']} Mahadasha · {ad_now['lord']} Antardasha "
                   f"(until {fmt_date(ad_now['end'])}) · {pd_now['lord']} Pratyantardasha (until {fmt_date(pd_now['end'])})")
    st.caption(f"Dasha balance at birth: {schedule[0]['lord']} {dasha_balance(chart, schedule):.2f} years "
               f"(Moon in {P['Moon']['nakshatra']}).")
    st.markdown("> 💡 **Vimshottari Dasha** divides life into planetary chapters. The **Mahadasha** lord sets the "
                "overall theme for years; the **Antardasha** lord decides which part of that theme is active now. "
                "Each lord gives results through the house it sits in and the houses it rules in your chart, and how "
                "much it can deliver depends on the SAV of its sign.")
    if md_now:
        st.subheader("🧭 Your current period")
        st.markdown(ins.dasha_insight(chart, av, md_now, ad_now))
        st.markdown("**Coming up**")
        st.markdown(ins.upcoming_antardashas(chart, av, schedule, md_now, ad_now))

    st.subheader("Explore any period")
    md_labels = [f"{md['lord']} ({md['start'].year}–{md['end'].year})" for md in schedule]
    md_default = schedule.index(md_now) if md_now else 0
    c1, c2 = st.columns(2)
    md_sel = schedule[c1.selectbox("Mahadasha", range(len(schedule)), index=md_default,
                                   format_func=lambda i: md_labels[i])]
    ads = md_sel["antardashas"]
    ad_default = ads.index(ad_now) if ad_now in ads else 0
    ad_sel = ads[c2.selectbox("Antardasha", range(len(ads)), index=ad_default,
                              format_func=lambda i: f"{ads[i]['lord']} ({fmt_date(ads[i]['start'])} – {fmt_date(ads[i]['end'])})")]

    axis, tone, axis_text = nar.dasha_axis(chart, md_sel["lord"], ad_sel["lord"])
    {"success": st.success, "warning": st.warning, "info": st.info}[tone](
        f"**{md_sel['lord']} / {ad_sel['lord']}: {axis}.** {axis_text}")
    st.markdown(ins.dasha_insight(chart, av, md_sel, ad_sel))

    with st.expander("Pratyantardashas in this Antardasha"):
        st.dataframe(pd.DataFrame([{"Pratyantardasha": p["lord"], "Starts": fmt_date(p["start"]),
                                    "Ends": fmt_date(p["end"])} for p in sub_periods(ad_sel["lord"], ad_sel["start"], ad_sel["end"])]),
                     width="stretch", hide_index=True)

    st.subheader("📜 Mahadasha Timeline")
    st.dataframe(pd.DataFrame([{
        "Mahadasha": md["lord"], "Starts": fmt_date(max(md["start"], chart["birth_utc"])), "Ends": fmt_date(md["end"]),
        "Years": round((md["end"] - max(md["start"], chart["birth_utc"])).days / 365.25, 2),
        "Status": "▶ Running" if md is md_now else ("Past" if md["end"] < now else ""),
    } for md in schedule]), width="stretch", hide_index=True)

    st.subheader("🔁 Cross-check with other Dasha systems")
    st.caption("When Vimshottari, Yogini and Chara Dasha point to similar themes at the same time, the prediction "
               "is considered more reliable.")
    yog = yogini_dasha(chart)
    y_now = running(yog, now)
    ch, ch_dir = chara_dasha(chart)
    c_now = running(ch, now)
    d1, d2 = st.columns(2)
    with d1:
        st.markdown("**Yogini Dasha** (36-year cycle of 8 yoginis)")
        if y_now:
            st.success(f"Running: **{y_now['name']}** (lord {y_now['lord']}) until {fmt_date(y_now['end'])}: "
                       f"{y_now['meaning']}.")
        st.dataframe(pd.DataFrame([{"Yogini": p["name"], "Lord": p["lord"], "Starts": fmt_date(p["start"]),
                                    "Ends": fmt_date(p["end"]), "Theme": p["meaning"]} for p in yog]),
                     width="stretch", hide_index=True, height=280)
    with d2:
        st.markdown(f"**Jaimini Chara Dasha** (sign periods, {ch_dir} order, K. N. Rao's method)")
        if c_now:
            h = (SIGNS.index(c_now["sign"]) - chart["asc_sign_idx"]) % 12 + 1
            st.success(f"Running: **{c_now['sign']}** (your {ordinal(h)} house: {HOUSE_INFO[h][1].lower()}) until "
                       f"{fmt_date(c_now['end'])}.")
        st.dataframe(pd.DataFrame([{"Sign": p["sign"], "Lord used": p["lord"], "Years": p["years"],
                                    "Starts": fmt_date(p["start"]), "Ends": fmt_date(p["end"]), "Cycle": p["cycle"]}
                                   for p in ch]), width="stretch", hide_index=True, height=280)

# --------------------------------------------------------------------------------------
# Ashtakavarga
# --------------------------------------------------------------------------------------
with tab_av:
    st.markdown("> 💡 **Sarvashtakavarga (SAV)** totals the benefic points every planet gives each sign "
                "(337 in all; 28 is average). Higher points mean that life area — and planets transiting it — "
                "deliver more easily.")
    st.subheader("🧭 What this means for you")
    for line in ins.ashtakavarga_insight(chart, av, sav_house):
        st.markdown(f"- {line}")
    st.plotly_chart(sav_figure(sav_house), width="stretch")

    house_df = pd.DataFrame([{
        "House": HOUSE_INFO[h + 1][0], "Sign": SIGNS[(chart["asc_sign_idx"] + h) % 12], "SAV": sav_house[h],
        "Strength": nar.house_strength_label(sav_house[h]), "Life Domain": HOUSE_INFO[h + 1][1],
    } for h in range(12)])
    st.dataframe(house_df, width="stretch", hide_index=True, column_config={
        "SAV": st.column_config.ProgressColumn("SAV (baseline 28)", format="%d", min_value=0, max_value=56)})

    st.subheader("Domain Diagnostics")
    s = sav_house
    d = st.columns(4)
    d[0].metric("10th House (career)", f"{s[9]} pts", "Strong" if s[9] >= 28 else "Challenging",
                delta_color="normal" if s[9] >= 28 else "inverse")
    d[1].metric("Gains vs Losses (11 vs 12)", f"{s[10]} vs {s[11]}",
                "Optimal flow" if s[10] > s[11] else "Leaking value", delta_color="normal" if s[10] > s[11] else "inverse")
    d[2].metric("Vitality vs Stress (1 vs 6)", f"{s[0]} vs {s[5]}",
                "Resilient" if s[0] >= s[5] else "Vulnerable", delta_color="normal" if s[0] >= s[5] else "inverse")
    d[3].metric("8th House (sudden change)", f"{s[7]} pts", nar.eighth_house_reading(s[7])[0], delta_color="off",
                help=nar.eighth_house_reading(s[7])[1])

    st.plotly_chart(bav_heatmap(av, chart["asc_sign_idx"]), width="stretch")
    st.caption("How to read: each row is one planet's own scorecard (Bhinna Ashtakavarga). A bright cell (5–8) means "
               "that planet gives good results when it transits that house; a dark cell (0–3) means its transit there "
               "is weak. The Timing Engine tab uses these numbers.")
    with st.expander("BAV / SAV table by sign"):
        st.dataframe(pd.DataFrame(sign_table(av)), width="stretch", hide_index=True)

# --------------------------------------------------------------------------------------
# Timing engine
# --------------------------------------------------------------------------------------
with tab_timing:
    st.markdown("> 💡 Each sign is split into 8 **Kakshyas** of 3°45'. A transiting planet delivers results while it "
                "crosses a Kakshya whose lord gave it a bindu in your chart. Windows are rated **Strong** when the "
                "Kakshya has a bindu, the planet's BAV in that sign is ≥ 4, and the sign's SAV is ≥ 28.")
    c1, c2, c3, c4 = st.columns([1, 1, 2, 1])
    start_date = c1.date_input("From", value=dt.date.today(), format="DD/MM/YYYY")
    months = c2.slider("Months", 1, 36, 12)
    planets = c3.multiselect("Slow planets", ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury"],
                             default=["Saturn", "Jupiter", "Mars"])
    moon_days = c4.slider("Moon days", 0, 60, 14, help="Moon Kakshyas last ~6¾ hours, so they're shown for a shorter span.")
    zones = sorted(zoneinfo.available_timezones())
    show_tz = st.selectbox("Show times in", zones, index=zones.index(tz_name))

    st.subheader("🧭 Right now")
    for line in ins.current_transits(chart, av, now):
        st.markdown(f"- {line}")

    win_start = dt.datetime.combine(start_date, dt.time()).replace(tzinfo=zoneinfo.ZoneInfo(show_tz)) \
        .astimezone(dt.timezone.utc).replace(tzinfo=None)
    win_end = win_start + dt.timedelta(days=round(months * 30.44))

    segments = []
    for p in planets:
        segments += cached_transits(chart, av, p, win_start, win_end)
    if moon_days:
        segments += cached_transits(chart, av, "Moon", win_start, win_start + dt.timedelta(days=moon_days))
    dasha_rows = periods_in_window(schedule, win_start, win_end)

    fig = timeline_figure(dasha_rows, segments, show_tz, (win_start, win_end))
    st.plotly_chart(fig, width="stretch")
    st.caption("How to read: the top three rows show which Dasha periods are running. Below, each bar is a "
               "planet crossing one kakshya. Solid bars carry a bindu (the planet can deliver); faded bars are muted. "
               "Hover any bar for the house, scores and rating. The best moments are when a strong transit window "
               "falls in a house the current Dasha lords are connected to.")

    upcoming = ins.upcoming_strong(segments, now)
    st.subheader("⭐ Next strong windows")
    st.markdown(upcoming or "No strong windows in this range. Try a longer span or more planets.")

    st.subheader("Windows")
    only_strong = st.toggle("Strong windows only", value=True)
    rows = [{
        "Planet": t["planet"], "Sign": t["sign"], "House": t["house"], "Kakshya Lord": t["kakshya_lord"],
        "Bindu": "✓" if t["bindu"] else "", "BAV": t["bav"], "SAV": t["sav"], "Score": t["score"],
        "Rating": t["rating"], "Starts": to_local(t["start"], show_tz), "Ends": to_local(t["end"], show_tz),
    } for t in sorted(segments, key=lambda t: t["start"]) if not only_strong or t["rating"] == "Strong"]
    if rows:
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True, column_config={
            "Starts": st.column_config.DatetimeColumn(format="DD MMM YYYY, HH:mm"),
            "Ends": st.column_config.DatetimeColumn(format="DD MMM YYYY, HH:mm")})
    else:
        st.info("No windows match in this range.")

    report = build_report(
        title=f"Vedic Astrology Report{' — ' + user_name if user_name else ''}",
        subtitle=f"Born {fmt_date(dob)} {tob.strftime('%H:%M')} · {address} · {ayanamsha}",
        metrics=[("Lagna", P["Ascendant"]["sign"]), ("Moon", f"{P['Moon']['sign']} · {P['Moon']['nakshatra']}"),
                 ("Atmakaraka", nar.karaka(chart, "AK")["planet"]), ("Amatyakaraka", nar.karaka(chart, "AmK")["planet"]),
                 ("Current Dasha", f"{md_now['lord']} / {ad_now['lord']}" if md_now else "—"),
                 ("10th House SAV", sav_house[9])],
        sections=[("💼 Career & Wealth", nar.career_narrative(chart, sav_house)),
                  ("🩺 Health & Vitality", nar.health_narrative(chart, sav_house)),
                  ("🪔 Remedies", rem.remedies_markdown(remedies) + "\n\n*" + nar.REMEDY_DISCLAIMER + "*")],
        figures=[fig, sav_figure(sav_house)],
    )
    st.download_button("📥 Download HTML report", report, file_name="vedic_astrology_report.html", mime="text/html")

    st.subheader("🪐 Lifetime Saturn timeline (Sade Sati, Ashtama, Ardhashtama)")
    periods, cycles = cached_saturn(chart)
    if cycles:
        st.markdown("**Sade Sati cycles:** " + "; ".join(
            f"{c['start']:%b %Y} – {c['end']:%b %Y}" + (" ▶ now" if c["start"] <= now < c["end"] else "")
            for c in cycles))
    st.dataframe(pd.DataFrame([{
        "Phase": p["phase"], "Saturn in": p["sign"], "From": fmt_date(p["start"]), "To": fmt_date(p["end"]),
        "Status": "▶ Now" if p["start"] <= now < p["end"] else ("Past" if p["end"] < now else ""),
    } for p in periods]), width="stretch", hide_index=True, height=320)
    st.caption("Short repeated periods are Saturn's retrograde loops back into the previous sign. Sade Sati brings "
               "responsibility and restructuring; its effect depends on Saturn's strength in your chart (see the "
               "Strength and Ashtakavarga tabs).")

# --------------------------------------------------------------------------------------
# Bhrigu
# --------------------------------------------------------------------------------------
with tab_bhrigu:
    st.markdown("> 💡 Three techniques from the **Bhrigu** tradition. The **Bhrigu Bindu** is a sensitive point "
                "midway between Rahu and the Moon. **Bhrigu Chakra Paddhati** activates one house for each year of "
                "life. **Bhrigu Nandi Nadi** reads the natal planets that Jupiter and Saturn are touching by sign.")
    st.subheader("🎯 Bhrigu Bindu")
    st.markdown(bhrigu.bhrigu_bindu_reading(chart))
    bb_windows = cached_bb_windows(chart, now, now + dt.timedelta(days=round(365.25 * 6)))
    if bb_windows:
        st.markdown("**Coming activations** (Saturn, Jupiter, Rahu or Ketu within 2° of your Bhrigu Bindu, next 6 years):")
        st.dataframe(pd.DataFrame([{
            "Planet": w["planet"], "From": to_local(w["start"], tz_name).date(), "To": to_local(w["end"], tz_name).date(),
            "Exact around": to_local(w["exact"], tz_name).date(),
            "Meaning": {"Saturn": "a karmic turning point: responsibilities and lasting change",
                        "Jupiter": "an opening: growth, opportunity and protection",
                        "Rahu": "a sudden push: ambition, change and the unexpected",
                        "Ketu": "a release: endings, letting go and inner turns"}[w["planet"]],
        } for w in bb_windows]), width="stretch", hide_index=True)
    else:
        st.caption("No slow-planet contacts with your Bhrigu Bindu in the next 6 years.")

    st.subheader("🔄 Bhrigu Chakra Paddhati (yearly house)")
    st.markdown(bhrigu.bcp_reading(chart, now))
    st.dataframe(pd.DataFrame(bhrigu.bcp_cycle(chart, now)), width="stretch", hide_index=True)

    st.subheader("🪐 Bhrigu Nandi Nadi: what Jupiter and Saturn are touching now")
    st.caption("BNN reads a transit planet with the natal planets in the same sign, in trine (5th/9th), opposite "
               "(7th), and in the adjacent signs (2nd/12th). Strongest links are listed first.")
    contacts = bhrigu.bnn_contacts(chart, now)
    if contacts:
        for r in contacts:
            st.markdown(f"- {r['text']}")
    else:
        st.caption("Jupiter and Saturn are not touching any natal planet by these relations right now.")

# --------------------------------------------------------------------------------------
# Strength
# --------------------------------------------------------------------------------------
with tab_strength:
    st.markdown("> 💡 **Shadbala** is the classical six-fold strength of a planet (BPHS), measured in *rupas*. "
                "It adds up strength from **position** (Sthana), **direction** (Dig), **time of birth** (Kala), "
                "**motion** (Cheshta), **natural brightness** (Naisargika) and **aspects** (Drik). Each planet has a "
                "**required minimum**; above it, the planet can deliver its results, below it, its themes need effort.")
    order = sorted((p for p in sb if p != "_meta"), key=lambda p: sb[p]["rank"])
    m1, m2, m3 = st.columns(3)
    m1.metric("Strongest planet", order[0], f"{sb[order[0]]['ratio']:.2f}× required", delta_color="off")
    m2.metric("Weakest planet", order[-1], f"{sb[order[-1]]['ratio']:.2f}× required", delta_color="off")
    m3.metric("Planets above minimum", f"{sum(sb[p]['ratio'] >= 1 for p in order)} of 7")
    st.plotly_chart(shadbala_figure(sb), width="stretch")

    st.subheader("🧭 What this means for you")
    for line in ins.shadbala_insight(chart, sb):
        st.markdown(f"- {line}")

    st.subheader("Shadbala table (rupas)")
    st.dataframe(pd.DataFrame([{
        "Rank": sb[p]["rank"], "Planet": p,
        **{COMPONENT_LABELS[k]: round(v / 60, 2) for k, v in sb[p]["components"].items()},
        "Total": round(sb[p]["rupas"], 2), "Required": sb[p]["required"] / 60, "Ratio": round(sb[p]["ratio"], 2),
    } for p in order]), width="stretch", hide_index=True,
        column_config={"Ratio": st.column_config.ProgressColumn("Ratio (≥ 1 is strong)", format="%.2f",
                                                                min_value=0, max_value=2)})

    with st.expander("Sub-components (virupas; 60 virupas = 1 rupa)"):
        st.dataframe(pd.DataFrame([{"Planet": p, **{k: round(v, 1) for k, v in sb[p]["detail"].items()}}
                                   for p in order]), width="stretch", hide_index=True)
        st.markdown("**Saptavarga dignities** (used for Saptavargaja Bala)")
        st.dataframe(pd.DataFrame([{"Planet": p, **sb[p]["vargas"]} for p in order]),
                     width="stretch", hide_index=True)
        meta = sb["_meta"]
        st.caption(f"{'Day' if meta['day_birth'] else 'Night'} birth. Time lords: year {meta['abda']}, month "
                   f"{meta['masa']}, weekday {meta['vara']}, hora {meta['hora']}. Sunrise "
                   f"{to_local(jd_to_datetime(meta['sunrise']), tz_name):%H:%M}, sunset "
                   f"{to_local(jd_to_datetime(meta['sunset']), tz_name):%H:%M} (local)"
                   + (". The Sun does not rise or set on this date at this latitude, so 06:00 and 18:00 local solar "
                      "time are used." if meta["sun_approximated"] else "."))
    with st.expander("How Shadbala is calculated here"):
        st.markdown(
            "- **Sthana:** Uchcha (distance from debilitation), Saptavargaja (dignity in D1, D2, D3, D7, D9, D12, "
            "D30 using compound friendship), Ojha-Yugma (odd/even sign and navamsha), Kendradi (house type), "
            "Drekkana (which third of the sign).\n"
            "- **Dig:** distance from the planet's strongest house cusp (equal houses from the Ascendant).\n"
            "- **Kala:** Nathonnata (day/night), Paksha (lunar phase), Tribhaga (third of day/night), year, month, "
            "weekday and hora lords, Ayana (declination), and Yuddha (planetary war, if any).\n"
            "- **Cheshta:** chesta-kendra from mean and true positions; the Sun uses Ayana, the Moon uses Paksha.\n"
            "- **Naisargika:** fixed natural strengths.\n"
            "- **Drik:** degree-based aspects; benefics add, malefics subtract, divided by 4.\n\n"
            "Classical sources differ on a few conventions (year/month lord reckoning, sunrise definition, Mercury's "
            "nature), so totals can differ slightly from other software. The conventions used are listed at the top "
            "of `vedic/shadbala.py`.")

    st.divider()
    st.subheader("Quick indicator: dignity, direction, combustion and aspects")
    st.caption("A simpler score that also covers Rahu and Ketu (Shadbala does not). Starts from 50: exalted +35, "
               "own sign +20, debilitated −25, Dig Bala house +25, combust −15 (Mercury −5), Jupiter's aspect or "
               "company +10, combined malefic pressure −10.")
    strength = dignity_strength(chart)
    st.plotly_chart(strength_figure(strength), width="stretch")
    with st.expander("What the quick indicator says"):
        for line in ins.strength_insight(chart, strength):
            st.markdown(f"- {line}")
        st.dataframe(pd.DataFrame(strength), width="stretch", hide_index=True)

# --------------------------------------------------------------------------------------
# Remedies
# --------------------------------------------------------------------------------------
with tab_remedies:
    st.markdown("> 💡 **Remedies (upaya)** are traditional ways to work with a planet that is weak in your birth "
                "chart or is running your life right now. Every row below shows the exact chart fact that triggered "
                "it. Each planet has three tiers: a **practical** habit, a **devotional** practice, and (only where "
                "it is safe for your Lagna) a **gemstone** to discuss with an astrologer.")
    st.info(nar.REMEDY_DISCLAIMER)

    for heading, key, intro, empty in [
        ("⏱ Do now", "now",
         "Planets that are active at present: the lords of your current Dasha periods and any Saturn pressure "
         "on your Moon. These change over time, so each has an end date.",
         "Nothing time-bound is flagged right now."),
        ("🌱 Lifelong", "lifelong",
         "Planets that are weak in the birth chart itself. These do not expire; small, steady habits work best.",
         "No planet is flagged in your birth chart: none is debilitated, combust, under combined malefic pressure, "
         "below its required Shadbala, in the 8th or 12th house, or short of Ashtakavarga points where it sits."),
    ]:
        st.subheader(heading)
        st.caption(intro)
        entries = remedies[key]
        if not entries:
            st.success(empty)
            continue
        st.dataframe(pd.DataFrame(rem.table_rows(entries)), width="stretch", hide_index=True)
        for e in entries:
            with st.expander(f"{e['planet']} · {e['priority']} priority · {e['day']}"):
                st.markdown(rem.entry_markdown(e))

    with st.expander("How these remedies are chosen (and what is not checked)"):
        st.markdown(
            "| Trigger | Priority |\n|---|---|\n"
            "| Planet debilitated, weakness not cancelled | High |\n"
            "| Two or more Medium triggers on the same planet | High |\n"
            "| Planet in the 8th or 12th house (or a gentle planet in the 6th) | Medium |\n"
            "| 3 or fewer Ashtakavarga points in the sign it occupies | Medium |\n"
            "| Combust: too close to the Sun (Moon 12°, Mars 17°, Mercury 14°, Jupiter 11°, Venus 10°, Saturn 15°; "
            "Mercury 12° and Venus 8° when retrograde) | Medium (Low for Mercury) |\n"
            "| Two or more malefic influences (Saturn or Mars aspect; Saturn, Mars, Rahu or Ketu in the same sign) "
            "and no Jupiter aspect | Medium |\n"
            "| Debilitated but cancelled (Neecha Bhanga) | Low |\n"
            "| Lord of the current Mahadasha or Antardasha | Medium (High if also weak at birth) |\n"
            "| Tense relationship between the two period lords (2/12 or 6/8) | High for the sub-period lord |\n"
            "| Sade Sati peak or Ashtama Shani | High |\n"
            "| Sade Sati first or final phase, Ardhashtama Shani | Medium |\n"
            "| Shadbala below the planet's required minimum | Medium |\n\n"
            "**Gemstones** are shown only for your Lagna lord, or for a planet that rules a kendra or trikona and no "
            "difficult house. Rahu and Ketu never get one here.\n\n"
            "**Aspects** are whole-sign: every planet aspects the 7th sign from itself; Mars also the 4th and 8th, "
            "Jupiter the 5th and 9th, Saturn the 3rd and 10th. Rahu and Ketu count only when they share a sign, because "
            "traditions disagree on their aspects. A single malefic influence, or one eased by Jupiter, is listed as a "
            "note and does not raise the priority.\n\n"
            "A professional reading weighs these factors with judgement and may emphasise different planets.")

# --------------------------------------------------------------------------------------
# Match (compatibility)
# --------------------------------------------------------------------------------------
with tab_match:
    st.markdown("> 💡 **Ashtakoota (guna milan)** compares two people's Moon signs and nakshatras across 8 factors "
                "for a total of 36 points; 18 is the traditional minimum. The **Manglik** check looks at Mars. "
                "Matching is only one input: the full charts and the people themselves matter more.")
    role = st.radio("In this match, the person in the sidebar is the", ["Groom", "Bride"], horizontal=True,
                    key="match_role")
    st.markdown("**Partner's birth details**")
    q1, q2, q3 = st.columns(3)
    partner_name = q1.text_input("Partner's name", key="pt_name", placeholder="Optional")
    pt_dob = q2.date_input("Date of birth", value=dt.date(1988, 1, 1), min_value=dt.date(1900, 1, 1),
                           max_value=dt.date.today(), format="DD/MM/YYYY", key="pt_dob")
    pt_tob = q3.time_input("Time of birth", value=dt.time(12, 0), step=60, key="pt_tob")
    q4, q5 = st.columns([2, 1])
    pt_place = q4.text_input("Place of birth", value="", key="pt_place", placeholder="City, Country")
    pt_manual = q5.checkbox("Enter coordinates", key="pt_manual")
    pt_loc = None
    if pt_manual:
        r1, r2, r3 = st.columns(3)
        zones_m = sorted(zoneinfo.available_timezones())
        pt_loc = {"lat": r1.number_input("Latitude", value=12.9716, format="%.4f", key="pt_lat"),
                  "lon": r2.number_input("Longitude", value=77.5946, format="%.4f", key="pt_lon"),
                  "tz_name": r3.selectbox("Time zone", zones_m, index=zones_m.index("Asia/Kolkata"), key="pt_tz")}
    elif pt_place.strip():
        pt_loc = cached_geocode(pt_place.strip())
        if not pt_loc:
            st.warning("Couldn't find that place; tick 'Enter coordinates' instead.")
    if pt_loc:
        partner, _, _, _ = compute_core(pt_dob, pt_tob, pt_loc["lat"], pt_loc["lon"], pt_loc["tz_name"],
                                        ayanamsha, true_node)
        groom, bride = (chart, partner) if role == "Groom" else (partner, chart)
        res = compat.ashtakoota(groom, bride)
        k1, k2, k3 = st.columns(3)
        k1.metric("Guna milan", f"{res['total']:g} / 36", res["verdict"], delta_color="off")
        k2.metric("Groom's star", res["groom_star"])
        k3.metric("Bride's star", res["bride_star"])
        st.dataframe(pd.DataFrame(res["rows"]), width="stretch", hide_index=True,
                     column_config={"Points": st.column_config.ProgressColumn("Points", format="%.1f",
                                                                              min_value=0, max_value=8)})
        for note in res["notes"]:
            st.warning(note)
        st.markdown("**Manglik (Kuja dosha) check**")
        for who_label, ch_ in [(user_name or "You", chart), (partner_name or "Partner", partner)]:
            mg = compat.manglik(ch_)
            text = (f"**{who_label}:** Mars is {ordinal(mg['house_lagna'])} from Lagna and {ordinal(mg['house_moon'])} "
                    f"from the Moon: " + (f"Manglik (from {' and '.join(mg['from'])})" if mg["manglik"] else "not Manglik"))
            if mg["manglik"] and mg["cancellations"]:
                text += f"; softened because {'; '.join(mg['cancellations']).lower()}"
            st.markdown("- " + text + ".")
        st.caption("Tradition considers Manglik dosha balanced when both partners are Manglik. Koota tables vary a "
                   "little between traditions; this uses common North Indian values.")
    else:
        st.info("Enter the partner's birth place (or coordinates) to see the match.")

# --------------------------------------------------------------------------------------
# Journal
# --------------------------------------------------------------------------------------
with tab_journal:
    st.markdown("> 💡 Keep a short **journal** of what actually happened, then see how often the app's day ratings "
                "agreed. Over months this shows which parts of the forecast work for you.")
    st.info("Streamlit Cloud does not keep files between sessions, so **download your journal** after adding entries "
            "and **upload it** next time to continue.")
    if "journal" not in st.session_state:
        st.session_state["journal"] = jr.empty()
    up = st.file_uploader("Load a saved journal (CSV)", type="csv", key="jr_upload")
    if up is not None and st.session_state.get("jr_loaded") != up.name + str(up.size):
        try:
            st.session_state["journal"] = jr.from_csv(up)
            st.session_state["jr_loaded"] = up.name + str(up.size)
            st.success(f"Loaded {len(st.session_state['journal'])} entries.")
        except Exception as exc:
            st.error(f"Could not read that file: {exc}")

    with st.form("jr_form", clear_on_submit=True):
        f1, f2, f3 = st.columns([1, 1, 1])
        e_date = f1.date_input("Date", value=dt.date.today(), format="DD/MM/YYYY")
        e_area = f2.selectbox("Area of life", jr.AREAS)
        e_felt = f3.select_slider("How did it go?", options=[-2, -1, 0, 1, 2], value=0,
                                  format_func=lambda v: jr.FELT[v])
        e_text = st.text_input("What happened", placeholder="e.g. Job interview went well")
        if st.form_submit_button("Add entry"):
            st.session_state["journal"] = jr.add(st.session_state["journal"], e_date, e_area, e_text, e_felt)

    jdf = st.session_state["journal"]
    if len(jdf):
        result, summary = jr.evaluate(jdf, lambda d: cached_day(chart, av, schedule, d, tz_name))
        j1, j2, j3 = st.columns(3)
        j1.metric("Entries", summary["entries"])
        j2.metric("App agreed", f"{summary['agreement']:.0%}")
        if summary["avg_score_good"] is not None and summary["avg_score_bad"] is not None:
            j3.metric("Avg app score: good vs hard days",
                      f"{summary['avg_score_good']:+.1f} vs {summary['avg_score_bad']:+.1f}")
        st.dataframe(result, width="stretch", hide_index=True)
        st.caption("'Agree' means a good experience fell on a positively rated day, a hard one on a negatively rated "
                   "day, or a neutral one on a mixed day. A clear gap between good-day and hard-day scores means the "
                   "ratings are tracking your life.")
        st.download_button("📥 Download journal (CSV)", jr.to_csv(jdf), file_name="astro_journal.csv",
                           mime="text/csv")
    else:
        st.caption("No entries yet.")
