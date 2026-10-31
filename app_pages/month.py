"""Month page."""
from ui.common import (build_report, cached_month, cached_year, calendar, ctx, dt, fmt_date, month_calendar_html, st,
                        year_heatmap)

c = ctx()
chart = c.chart
av = c.av
schedule = c.schedule
sb = c.sb
address = c.address
user_name = c.user_name
dob = c.dob
tob = c.tob
here_tz = c.here_tz
here_place = c.here_place

st.markdown("> 💡 A **calendar-month forecast** for each area of life. Every area is tied to its houses and "
            "significators: the month's transits through those houses (judged by Ashtakavarga points), Jupiter's "
            "protective and Saturn's or Mars's testing aspects, your running Dasha lords, and Sade Sati all feed "
            "its rating. Key dates, eclipses and a day-by-day calendar follow.")
today = dt.date.today()
options = []
y_, m_ = (today.year, today.month - 1) if today.month > 1 else (today.year - 1, 12)
for _ in range(14):
    options.append((y_, m_))
    y_, m_ = (y_, m_ + 1) if m_ < 12 else (y_ + 1, 1)
default_idx = 2 if today.day >= 25 else 1  # near month end, default to next month
sel_y, sel_m = st.selectbox("Month", options, index=default_idx, key="month_pick",
                            format_func=lambda ym: f"{calendar.month_name[ym[1]]} {ym[0]}")
m_tz, m_place = (here_tz, here_place)
mf = cached_month(chart, av, schedule, sb, sel_y, sel_m, m_tz, m_place)

st.subheader(f"🧭 {calendar.month_name[sel_m]} {sel_y} at a glance")
for line in mf["summary"]:
    st.markdown(f"- {line}")

st.subheader("Areas of life")
for row_start in range(0, len(mf["areas"]), 2):
    cols = st.columns(2)
    for col, a in zip(cols, mf["areas"][row_start:row_start + 2]):
        with col.container(border=True):
            st.markdown(f"#### {a['icon']} {a['area']} · {a['rating_icon']} {a['rating']}")
            st.markdown(a["text"])

st.subheader("📌 Key dates")
if mf["events"]:
    for e in mf["events"]:
        st.markdown(f"- **{e['when']:%a %d %b, %H:%M}:** {e['text']}")
else:
    st.caption("No major planetary events this month.")

st.subheader("🗓 Day by day")
st.markdown(month_calendar_html(mf["days"]), unsafe_allow_html=True)
st.caption("Colours show each day's personal rating (Tara Bala, Chandra Bala, the Moon's Ashtakavarga points, "
           "tithi and weekday lord). ⚠ = Chandrashtama. Hover a day for details; the This Week page explains them.")

st.subheader("📈 12-month outlook")
yr = cached_year(chart, av, schedule, sb, today.year, today.month, m_tz)
st.plotly_chart(year_heatmap(yr), width="stretch")
st.caption("Green months favour the area, red months call for care. Use it to plan big moves in each area.")

month_report = build_report(
    title=f"{calendar.month_name[sel_m]} {sel_y} Forecast{' — ' + user_name if user_name else ''}",
    subtitle=f"Born {fmt_date(dob)} {tob.strftime('%H:%M')} · {address}",
    metrics=[(a["area"], a["rating"]) for a in mf["areas"]],
    sections=[("This month", "\n".join(f"- {x}" for x in mf["summary"]))]
    + [(f"{a['icon']} {a['area']}: {a['rating']}", a["text"]) for a in mf["areas"]]
    + [("Key dates", "\n".join(f"- {e['when']:%a %d %b %H:%M}: {e['text']}" for e in mf["events"]) or "- None")],
    figures=[year_heatmap(yr)],
)
st.download_button("📥 Download this month (HTML)", month_report,
                   file_name=f"forecast_{sel_y}_{sel_m:02d}.html", mime="text/html")
st.caption("Monthly readings combine classical Jyotish rules for reflection and planning; they are not "
           "certainties. Health notes are not medical advice.")
