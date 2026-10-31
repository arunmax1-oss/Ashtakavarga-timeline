"""Job page."""
from ui.common import cached_muhurta, career, chart_svg, ctx, dt, fmt_date, fmt_span, ordinal, pd, st, varga_positions

c = ctx()
chart = c.chart
av = c.av
schedule = c.schedule
sb = c.sb
now = c.now
here_tz = c.here_tz
here_place = c.here_place

st.markdown("> 💡 Career in Vedic astrology is read from the **10th house** (work and status), its lord, planets "
            "in or aspecting it, the **Amatyakaraka** (career planet) and the **D10 (Dashamsa)** chart. The 6th "
            "house shows employment and competition, the 7th business and partnerships, and the 2nd and 11th "
            "income. Timing comes from the Dasha periods of these planets and from Jupiter and Saturn's transits.")
prof = career.profile(chart, av, sb)
j1, j2, j3, j4 = st.columns(4)
j1.metric("10th house", prof["h10_sign"], f"lord {prof['lord10']}", delta_color="off")
j2.metric("Career planet (AmK)", prof["amk"], f"{ordinal(prof['amk_house'])} house", delta_color="off")
j3.metric("10th house SAV", prof["sav10"], "strong" if prof["sav10"] >= 30 else "average" if prof["sav10"] >= 28
          else "below average", delta_color="off")
j4.metric("Job or business", "Business" if prof["business"] > prof["service"] + 2 else
          "Employment" if prof["service"] > prof["business"] + 2 else "Either",
          f"{prof['service']} vs {prof['business']}", delta_color="off",
          help="Employment score (6th house, Saturn, 10th lord in 6th/10th) vs business score (7th house, "
               "Mercury, 10th lord in 3rd/7th/11th).")

st.subheader("🧭 Your career profile")
for line in career.profile_text(chart, prof):
    st.markdown(f"- {line}")
st.markdown(f"- **Job or business:** {prof['leaning']}")

cj1, cj2 = st.columns([1, 1])
with cj1:
    st.subheader("🎯 Fields that suit you")
    st.caption("Ranked by the planets that rule and influence your career: the 10th lord and Amatyakaraka count "
               "most, then planets in or aspecting the 10th, then the D10 Lagna and 10th lords.")
    for f in prof["fields"]:
        st.markdown(f"**{f['planet']}** (weight {f['weight']}): " + ", ".join(f["fields"]))
with cj2:
    jstyle = st.radio("D10 chart style", ["South Indian", "North Indian"], horizontal=True, key="d10_style")
    st.markdown(chart_svg(jstyle, chart, varga_positions(chart, "D10"), "Dasamsa (D10)", False),
                unsafe_allow_html=True)

st.subheader("📈 Career timeline (Dasha periods)")
st.caption("Each Antardasha is tagged by the career role its lord holds in your chart (10th lord, Amatyakaraka, "
           "6th, 11th, 2nd, 12th or 8th lord); 'quality' comes from the lord's Shadbala.")
periods_c = career.career_periods(chart, schedule, sb, now, years=12)
st.dataframe(pd.DataFrame([{
    "Period": f"{p_['md']}–{p_['ad']}", "From": fmt_date(p_["start"]), "To": fmt_date(p_["end"]),
    "Theme": p_["theme"], "What to expect": p_["meaning"], "Quality": p_["quality"], "Career roles": p_["roles"],
    "Peak windows inside": ", ".join(f"{pd_['lord']} {pd_['start']:%b %Y}" for pd_ in p_["peaks"][:2]) or "—",
} for p_ in periods_c]), width="stretch", hide_index=True)
nxt = next((p_ for p_ in periods_c if p_["theme"] in ("Career peak", "Job change", "Career direction")
            and p_["start"] > now), None)
if nxt:
    st.info(f"**Next major career window:** {nxt['md']}–{nxt['ad']} from {fmt_date(nxt['start'])}: "
            f"{nxt['theme'].lower()} ({nxt['meaning']}).")

st.subheader("🪐 Transits over your career houses (next 3 years)")
ct = career.career_transits(chart, now)
if ct:
    st.dataframe(pd.DataFrame([{
        "Planet": t["planet"], "In": t["sign"], "From": fmt_date(t["start"]), "To": fmt_date(t["end"]),
        "Effect on career": t["what"], "What it brings": t["tone"],
    } for t in ct]), width="stretch", hide_index=True)
else:
    st.caption("Jupiter, Saturn and Rahu do not touch your 10th or 11th house in the next 3 years.")

st.subheader("📅 Good days for job moves")
jact = st.radio("Activity", ["Job interview or application", "Start a new job or business"], horizontal=True,
                key="job_act")
jtz, jplace = (here_tz, here_place)
jbest, _ = cached_muhurta(chart, av, schedule, jact, dt.date.today(), 45, jtz, jplace)
if jbest:
    st.dataframe(pd.DataFrame([{
        "Date": f"{d['date']:%a %d %b %Y}", "Score": d["muhurta_score"], "Nakshatra": d["nakshatra"],
        "Best slot (Abhijit)": fmt_span(d["timings"]["abhijit"]) if d["timings"] else "—",
        "Avoid (Rahu Kalam)": fmt_span(d["timings"]["rahu_kalam"]) if d["timings"] else "—",
        "Why": "; ".join(d["muhurta_reasons"]) or "Personal day rating",
    } for d in jbest[:6]]), width="stretch", hide_index=True)
st.caption("Career readings are classical guidance for reflection and planning, not certainties.")
