"""Vedic Astrology & Ashtakavarga Timing Engine — Streamlit UI.

All calculations live in the `vedic/` package; this file only gathers input and lays out results.
"""
import datetime as dt
import zoneinfo

import pandas as pd
import streamlit as st

from vedic import bhrigu
from vedic import insights as ins
from vedic import narratives as nar
from vedic import remedies as rem
from vedic.aspects import aspects_on, combustion
from vedic.ashtakavarga import compute_ashtakavarga, sav_by_house, sign_table
from vedic.chart import build_chart, geocode, jd_to_datetime
from vedic.constants import AYANAMSHAS, HOUSE_INFO, SIGNS, ordinal
from vedic.dasha import active_periods, dasha_balance, periods_in_window, sub_periods, vimshottari
from vedic.plots import (bav_heatmap, sav_figure, shadbala_figure, strength_figure, timeline_figure, to_local,
                         week_figure)
from vedic.report import build_report
from vedic.shadbala import COMPONENT_LABELS, shadbala
from vedic.transits import transit_segments, utc_now
from vedic.weekly import week_forecast
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
def cached_week(chart, av, schedule, week_start, tz, sb):
    return week_forecast(chart, av, schedule, week_start, tz, sb)


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

chart, av, schedule, sb = compute_core(dob, tob, lat, lon, tz_name, ayanamsha, true_node)
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

remedies = rem.build_remedies(chart, av, (md_now, ad_now), now, sb)

(tab_summary, tab_week, tab_planets, tab_dasha, tab_av, tab_timing, tab_bhrigu, tab_strength,
 tab_remedies) = st.tabs(["📜 Summary", "🗓 This Week", "🪐 Planets", "⏳ Dasha", "📊 Ashtakavarga",
                          "🎯 Timing", "🔱 Bhrigu", "⚡ Strength", "🪔 Remedies"])

# --------------------------------------------------------------------------------------
# Summary
# --------------------------------------------------------------------------------------
with tab_summary:
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
    zones_w = sorted(zoneinfo.available_timezones())
    week_tz = c2.selectbox("Your current time zone", zones_w, index=zones_w.index(tz_name), key="week_tz",
                           help="Days and times are shown in this zone. Change it if you now live elsewhere.")
    wk = cached_week(chart, av, schedule, week_start, week_tz, sb)
    st.subheader(f"🧭 {week_start:%a %d %b} – {week_start + dt.timedelta(days=6):%a %d %b %Y}")
    for line in wk["summary"]:
        st.markdown(f"- {line}")

    st.plotly_chart(week_figure(wk["days"]), use_container_width=True)
    st.dataframe(pd.DataFrame([{
        "Day": f"{d['icon']} {d['date']:%a %d %b}", "Rating": d["rating"], "Tithi": d["tithi"]["name"],
        "Nakshatra": d["nakshatra"], "Moon": f"{d['moon_sign']} ({ordinal(d['from_lagna'])} house)",
        "Tara": d["tara"]["name"], "Best for": d["best_use"],
    } for d in wk["days"]]), use_container_width=True, hide_index=True)

    st.subheader("Day by day")
    for d in wk["days"]:
        with st.expander(f"{d['icon']} {d['date']:%A %d %b} · {d['rating']} · {d['nakshatra']} · {d['tithi']['name']}"):
            st.markdown(f"**Best for:** {d['best_use']}.  \n**Tithi:** {d['tithi']['name']} "
                        f"({d['tithi']['group']}: {d['tithi']['group_use']}). **Weekday lord:** {d['weekday_lord']}.")
            st.markdown("**Why this rating**\n" + "\n".join(f"- {r}" for r in d["reasons"]))
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
        } for c in wk["climate"]]), use_container_width=True, hide_index=True)
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
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption("Combust = degrees from the Sun when inside the classical limit. Aspected by = whole-sign aspects "
               "received (Rahu/Ketu aspects are informational and not scored).")

    st.subheader("Jaimini Chara Karakas")
    st.dataframe(pd.DataFrame([{"Role": k["role"], "Planet": k["planet"], "Sign": k["sign"],
                                "Degree": f"{k['degree']:.2f}°", "Meaning": k["meaning"]} for k in chart["karakas"]]),
                 use_container_width=True, hide_index=True)
    st.markdown(ins.karaka_insight(chart))

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
with tab_av:
    st.markdown("> 💡 **Sarvashtakavarga (SAV)** totals the benefic points every planet gives each sign "
                "(337 in all; 28 is average). Higher points mean that life area — and planets transiting it — "
                "deliver more easily.")
    st.subheader("🧭 What this means for you")
    for line in ins.ashtakavarga_insight(chart, av, sav_house):
        st.markdown(f"- {line}")
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
    d[3].metric("8th House (sudden change)", f"{s[7]} pts", nar.eighth_house_reading(s[7])[0], delta_color="off",
                help=nar.eighth_house_reading(s[7])[1])

    st.plotly_chart(bav_heatmap(av, chart["asc_sign_idx"]), use_container_width=True)
    st.caption("How to read: each row is one planet's own scorecard (Bhinna Ashtakavarga). A bright cell (5–8) means "
               "that planet gives good results when it transits that house; a dark cell (0–3) means its transit there "
               "is weak. The Timing Engine tab uses these numbers.")
    with st.expander("BAV / SAV table by sign"):
        st.dataframe(pd.DataFrame(sign_table(av)), use_container_width=True, hide_index=True)

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
    st.plotly_chart(fig, use_container_width=True)
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
                  ("🩺 Health & Vitality", nar.health_narrative(chart, sav_house)),
                  ("🪔 Remedies", rem.remedies_markdown(remedies) + "\n\n*" + nar.REMEDY_DISCLAIMER + "*")],
        figures=[fig, sav_figure(sav_house)],
    )
    st.download_button("📥 Download HTML report", report, file_name="vedic_astrology_report.html", mime="text/html")

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
        } for w in bb_windows]), use_container_width=True, hide_index=True)
    else:
        st.caption("No slow-planet contacts with your Bhrigu Bindu in the next 6 years.")

    st.subheader("🔄 Bhrigu Chakra Paddhati (yearly house)")
    st.markdown(bhrigu.bcp_reading(chart, now))
    st.dataframe(pd.DataFrame(bhrigu.bcp_cycle(chart, now)), use_container_width=True, hide_index=True)

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
    st.plotly_chart(shadbala_figure(sb), use_container_width=True)

    st.subheader("🧭 What this means for you")
    for line in ins.shadbala_insight(chart, sb):
        st.markdown(f"- {line}")

    st.subheader("Shadbala table (rupas)")
    st.dataframe(pd.DataFrame([{
        "Rank": sb[p]["rank"], "Planet": p,
        **{COMPONENT_LABELS[k]: round(v / 60, 2) for k, v in sb[p]["components"].items()},
        "Total": round(sb[p]["rupas"], 2), "Required": sb[p]["required"] / 60, "Ratio": round(sb[p]["ratio"], 2),
    } for p in order]), use_container_width=True, hide_index=True,
        column_config={"Ratio": st.column_config.ProgressColumn("Ratio (≥ 1 is strong)", format="%.2f",
                                                                min_value=0, max_value=2)})

    with st.expander("Sub-components (virupas; 60 virupas = 1 rupa)"):
        st.dataframe(pd.DataFrame([{"Planet": p, **{k: round(v, 1) for k, v in sb[p]["detail"].items()}}
                                   for p in order]), use_container_width=True, hide_index=True)
        st.markdown("**Saptavarga dignities** (used for Saptavargaja Bala)")
        st.dataframe(pd.DataFrame([{"Planet": p, **sb[p]["vargas"]} for p in order]),
                     use_container_width=True, hide_index=True)
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
    st.plotly_chart(strength_figure(strength), use_container_width=True)
    with st.expander("What the quick indicator says"):
        for line in ins.strength_insight(chart, strength):
            st.markdown(f"- {line}")
        st.dataframe(pd.DataFrame(strength), use_container_width=True, hide_index=True)

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
        st.dataframe(pd.DataFrame(rem.table_rows(entries)), use_container_width=True, hide_index=True)
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
