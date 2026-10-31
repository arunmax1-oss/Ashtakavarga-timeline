"""Planner page."""
from ui.common import cached_muhurta, ctx, dt, fmt_span, mh, pd, st

c = ctx()
chart = c.chart
av = c.av
schedule = c.schedule
here_tz = c.here_tz
here_place = c.here_place

st.markdown("> 💡 **Muhurta** is choosing a good time to begin something. Pick an activity and the planner ranks "
            "the coming days by your personal day rating plus the classical rules for that activity: suitable "
            "nakshatras, favourable weekdays and good tithis. Days with Chandrashtama, a difficult Tara or a "
            "Rikta/new-moon tithi are ruled out. Start within Abhijit Muhurta if you can, and avoid Rahu Kalam.")
p1, p2, p3 = st.columns([2, 1, 1])
activity = p1.selectbox("Activity", list(mh.ACTIVITIES), key="mh_activity")
mh_start = p2.date_input("From", value=dt.date.today(), format="DD/MM/YYYY", key="mh_start")
mh_days = p3.slider("Days to search", 14, 90, 45, key="mh_days")
ctx_tz, ctx_place = (here_tz, here_place)
best, ruled_out = cached_muhurta(chart, av, schedule, activity, mh_start, mh_days, ctx_tz, ctx_place)
st.caption(f"{mh.ACTIVITIES[activity]['why']} {ruled_out} of {mh_days} days were ruled out. Timings use the "
           "place set under '📍 Where you are now' in the sidebar (or your birth place).")
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
