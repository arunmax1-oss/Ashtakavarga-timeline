"""Vedic Astrology & Ashtakavarga Timing Engine — Streamlit UI.

All calculations live in the `vedic/` package; this file only gathers input and lays out results.
"""
import datetime as dt
import zoneinfo

import pandas as pd
import streamlit as st

from vedic import narratives as nar
from vedic.ashtakavarga import compute_ashtakavarga, sav_by_house, sign_table
from vedic.chart import build_chart, geocode
from vedic.constants import AYANAMSHAS, DASHA_YEARS, HOUSE_INFO, SIGNS
from vedic.dasha import active_periods, dasha_balance, periods_in_window, sub_periods, vimshottari
from vedic.plots import bav_heatmap, sav_figure, strength_figure, timeline_figure, to_local
from vedic.report import build_report
from vedic.transits import transit_segments, utc_now
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
    return chart, av, vimshottari(chart)


@st.cache_data(show_spinner=False)
def cached_transits(chart, av, planet, start, end):
    return transit_segments(chart, av, planet, start, end)


def fmt_date(d):
    return d.strftime("%d %b %Y")


# --------------------------------------------------------------------------------------
# Sidebar: birth details
# --------------------------------------------------------------------------------------
st.sidebar.header("👤 Birth Details")
user_name = st.sidebar.text_input("Name", value="", placeholder="Optional")
dob = st.sidebar.date_input("Date of Birth", value=dt.date(1985, 6, 15),
                            min_value=dt.date(1900, 1, 1), max_value=dt.date.today(), format="DD/MM/YYYY")
tob = st.sidebar.time_input("Time of Birth (24h, local)", value=dt.time(14, 30), step=60)
place = st.sidebar.text_input("Place of Birth", value="Bengaluru, India",
                              help="City and country, e.g. 'Chennai, India' or 'London, UK'.")
manual = st.sidebar.checkbox("Enter coordinates manually", help="Use if the place lookup fails.")

if manual:
    c1, c2 = st.sidebar.columns(2)
    lat = c1.number_input("Latitude", value=12.9716, min_value=-90.0, max_value=90.0, format="%.4f")
    lon = c2.number_input("Longitude", value=77.5946, min_value=-180.0, max_value=180.0, format="%.4f")
    zones = sorted(zoneinfo.available_timezones())
    tz_name = st.sidebar.selectbox("Time zone", zones, index=zones.index("Asia/Kolkata"))
    address = f"{lat:.4f}, {lon:.4f}"
else:
    loc = cached_geocode(place.strip()) if place.strip() else None
    if not loc:
        st.sidebar.error("Couldn't find that place. Try 'City, Country', or tick *Enter coordinates manually*.")
        st.stop()
    lat, lon, tz_name, address = loc["lat"], loc["lon"], loc["tz_name"], loc["address"]

with st.sidebar.expander("⚙ Calculation settings"):
    ayanamsha = st.selectbox("Ayanamsha", AYANAMSHAS, index=0)
    true_node = st.radio("Rahu/Ketu", ["Mean node", "True node"], horizontal=True) == "True node"
    st.caption("Houses: whole sign (Rasi = Bhava). Ephemeris: Swiss Ephemeris (Moshier).")

chart, av, schedule = compute_core(dob, tob, lat, lon, tz_name, ayanamsha, true_node)
P = chart["planets"]
sav_house = sav_by_house(chart, av)
now = utc_now()
md_now, ad_now, pd_now = active_periods(schedule, now)

st.sidebar.caption(f"📍 {address}")
st.sidebar.caption(f"🌐 {lat:.2f}°, {lon:.2f}° · {tz_name} (UTC{chart['utc_offset']:+.2f} at birth)")

# --------------------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------------------
st.title("🔮 Vedic Astrology & Ashtakavarga Engine")
who = f"**{user_name}** · " if user_name else ""
st.caption(f"{who}Born {fmt_date(dob)} at {tob.strftime('%H:%M')} · {address} · "
           f"{ayanamsha} ayanamsha {chart['ayanamsha_deg']:.4f}°")

m = st.columns(5)
m[0].metric("Lagna", P["Ascendant"]["sign"], f"{P['Ascendant']['degree']:.1f}° {P['Ascendant']['nakshatra']}",
            delta_color="off")
m[1].metric("Moon Sign", P["Moon"]["sign"], P["Moon"]["nakshatra"], delta_color="off")
m[2].metric("Atmakaraka", nar.karaka(chart, "AK")["planet"])
m[3].metric("Amatyakaraka", nar.karaka(chart, "AmK")["planet"])
m[4].metric("Mahadasha", md_now["lord"] if md_now else "—",
            f"{ad_now['lord']} AD until {fmt_date(ad_now['end'])}" if ad_now else None, delta_color="off")

tabs = st.tabs(["📜 Summary & Yogas", "🪐 Planets & Nakshatras", "⏳ Dasha", "📊 Ashtakavarga",
                "🎯 Timing Engine", "⚡ Planet Strength"])

# --------------------------------------------------------------------------------------
# Summary
# --------------------------------------------------------------------------------------
with tabs[0]:
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
        st.dataframe(pd.DataFrame(yogas), use_container_width=True, hide_index=True)
    else:
        st.info("None of the tracked yogas are present: a well-balanced distribution without extreme concentrations.")

# --------------------------------------------------------------------------------------
# Planets & Nakshatras
# --------------------------------------------------------------------------------------
with tabs[1]:
    st.markdown("> 💡 Each sign is divided into **Nakshatras** (lunar mansions) of 13°20'. They reveal instincts, "
                "sub-talents and planetary motivations. **D9** (Navamsha) shows inner strength and partnerships; "
                "**D10** (Dashamsha) shows career.")
    rows = [{
        "Planet": n + (" ℞" if p["retrograde"] else ""), "Sign": p["sign"], "Degree": f"{p['degree']:.2f}°",
        "House": p["house"], "Nakshatra": p["nakshatra"], "Pada": p["pada"], "Nak. Lord": p["nakshatra_lord"],
        "Dignity": p["dignity"], "D9": p["d9_sign"], "D10": p["d10_sign"],
    } for n, p in P.items()]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.subheader("Jaimini Chara Karakas")
    st.dataframe(pd.DataFrame([{"Role": k["role"], "Planet": k["planet"], "Sign": k["sign"],
                                "Degree": f"{k['degree']:.2f}°", "Meaning": k["meaning"]} for k in chart["karakas"]]),
                 use_container_width=True, hide_index=True)

# --------------------------------------------------------------------------------------
# Dasha
# --------------------------------------------------------------------------------------
with tabs[2]:
    if md_now:
        st.success(f"📌 **Running now:** {md_now['lord']} Mahadasha · {ad_now['lord']} Antardasha "
                   f"(until {fmt_date(ad_now['end'])}) · {pd_now['lord']} Pratyantardasha (until {fmt_date(pd_now['end'])})")
    st.caption(f"Dasha balance at birth: {schedule[0]['lord']} {dasha_balance(chart, schedule):.2f} years "
               f"(Moon in {P['Moon']['nakshatra']}).")

    st.subheader("Dasha Narrative")
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
    st.markdown(f"#### 1. Overarching theme ({md_sel['lord']} Mahadasha, {DASHA_YEARS[md_sel['lord']]} years)")
    st.info(nar.DASHA_DESCRIPTIONS[md_sel["lord"]])
    st.markdown(f"#### 2. Sub-period manifestation ({ad_sel['lord']} Antardasha)")
    st.success(nar.DASHA_DESCRIPTIONS[ad_sel["lord"]])
    st.markdown(f"#### 3. Interplay: {axis}")
    st.write(f"In your chart {md_sel['lord']} sits in {P[md_sel['lord']]['sign']} (house {P[md_sel['lord']]['house']}) "
             f"and {ad_sel['lord']} in {P[ad_sel['lord']]['sign']} (house {P[ad_sel['lord']]['house']}). {axis_text}")

    with st.expander("Pratyantardashas in this Antardasha"):
        st.dataframe(pd.DataFrame([{"Pratyantardasha": p["lord"], "Starts": fmt_date(p["start"]),
                                    "Ends": fmt_date(p["end"])} for p in sub_periods(ad_sel["lord"], ad_sel["start"], ad_sel["end"])]),
                     use_container_width=True, hide_index=True)

    st.subheader("📜 Mahadasha Timeline")
    st.dataframe(pd.DataFrame([{
        "Mahadasha": md["lord"], "Starts": fmt_date(max(md["start"], chart["birth_utc"])), "Ends": fmt_date(md["end"]),
        "Years": round((md["end"] - max(md["start"], chart["birth_utc"])).days / 365.25, 2),
        "Status": "▶ Running" if md is md_now else ("Past" if md["end"] < now else ""),
    } for md in schedule]), use_container_width=True, hide_index=True)

# --------------------------------------------------------------------------------------
# Ashtakavarga
# --------------------------------------------------------------------------------------
with tabs[3]:
    st.markdown("> 💡 **Sarvashtakavarga (SAV)** totals the benefic points every planet gives each sign "
                "(337 in all; 28 is average). Higher points mean that life area — and planets transiting it — "
                "deliver more easily.")
    st.plotly_chart(sav_figure(sav_house), use_container_width=True)

    house_df = pd.DataFrame([{
        "House": HOUSE_INFO[h + 1][0], "Sign": SIGNS[(chart["asc_sign_idx"] + h) % 12], "SAV": sav_house[h],
        "Strength": nar.house_strength_label(sav_house[h]), "Life Domain": HOUSE_INFO[h + 1][1],
    } for h in range(12)])
    st.dataframe(house_df, use_container_width=True, hide_index=True, column_config={
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
    d[3].metric("8th House", f"{s[7]} pts", "Controlled risk" if s[7] < 28 else "Elevated risk", delta_color="off")

    st.plotly_chart(bav_heatmap(av, chart["asc_sign_idx"]), use_container_width=True)
    with st.expander("BAV / SAV table by sign"):
        st.dataframe(pd.DataFrame(sign_table(av)), use_container_width=True, hide_index=True)

# --------------------------------------------------------------------------------------
# Timing engine
# --------------------------------------------------------------------------------------
with tabs[4]:
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
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Windows")
    only_strong = st.toggle("Strong windows only", value=True)
    rows = [{
        "Planet": t["planet"], "Sign": t["sign"], "House": t["house"], "Kakshya Lord": t["kakshya_lord"],
        "Bindu": "✓" if t["bindu"] else "", "BAV": t["bav"], "SAV": t["sav"], "Score": t["score"],
        "Rating": t["rating"], "Starts": to_local(t["start"], show_tz), "Ends": to_local(t["end"], show_tz),
    } for t in sorted(segments, key=lambda t: t["start"]) if not only_strong or t["rating"] == "Strong"]
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, column_config={
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
                  ("🩺 Health & Vitality", nar.health_narrative(chart, sav_house))],
        figures=[fig, sav_figure(sav_house)],
    )
    st.download_button("📥 Download HTML report", report, file_name="vedic_astrology_report.html", mime="text/html")

# --------------------------------------------------------------------------------------
# Strength
# --------------------------------------------------------------------------------------
with tabs[5]:
    st.markdown("> 💡 A quick strength indicator from **dignity** (exalted +35, own sign +20, debilitated −25) and "
                "**directional strength** (+25 in the Dig Bala house), starting from 50. It is a simplification, "
                "not the full six-fold Shadbala.")
    strength = dignity_strength(chart)
    st.plotly_chart(strength_figure(strength), use_container_width=True)
    st.dataframe(pd.DataFrame(strength), use_container_width=True, hide_index=True)
