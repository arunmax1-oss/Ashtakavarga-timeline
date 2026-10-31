"""This Week page."""
from ui.common import build_report, cached_week, ctx, dt, fmt_date, fmt_span, ordinal, pd, st, week_figure

c = ctx()
chart = c.chart
av = c.av
schedule = c.schedule
sb = c.sb
lat = c.lat
lon = c.lon
address = c.address
user_name = c.user_name
dob = c.dob
tob = c.tob
here_tz = c.here_tz
here_place = c.here_place

st.markdown("> 💡 A **weekly forecast** built from your chart. Each day is rated from the Moon's transit: its "
            "**Tara Bala** (the Moon's nakshatra counted from your birth star), **Chandra Bala** (its house from "
            "your natal Moon; the 8th, *Chandrashtama*, is the hardest), the Moon's own Ashtakavarga points, the "
            "**tithi** (lunar day) and whether the weekday is ruled by one of your Dasha lords. The week adds "
            "sign changes, retrograde stations, Dasha changes, strong Kakshya windows and Bhrigu Bindu contacts.")
week_start = st.date_input("7 days starting", value=dt.date.today(), format="DD/MM/YYYY", key="week_pick")
wk = cached_week(chart, av, schedule, week_start, here_tz, sb, here_place)
st.caption(f"Times shown in {here_tz} for {'your current place' if here_place != (lat, lon) else 'your birth place'}; "
           "change it under '📍 Where you are now' in the sidebar.")
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
