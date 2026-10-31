"""Timing page."""
from ui.common import (build_report, cached_saturn, cached_transits, ctx, dt, fmt_date, ins, nar, pd,
                        periods_in_window, rem, sav_figure, st, timeline_figure, to_local, zoneinfo)

c = ctx()
chart = c.chart
av = c.av
schedule = c.schedule
P = c.P
sav_house = c.sav_house
now = c.now
md_now = c.md_now
ad_now = c.ad_now
tz_name = c.tz_name
address = c.address
user_name = c.user_name
dob = c.dob
tob = c.tob
ayanamsha = c.ayanamsha
remedies = c.remedies

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
           "Strength and Ashtakavarga pages).")
