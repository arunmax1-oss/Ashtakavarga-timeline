"""Dasha page."""
from ui.common import (chara_dasha, ctx, dasha_balance, fmt_date, HOUSE_INFO, ins, nar, ordinal, pd, running, SIGNS,
                        st, sub_periods, yogini_dasha)

c = ctx()
chart = c.chart
av = c.av
schedule = c.schedule
P = c.P
now = c.now
md_now = c.md_now
ad_now = c.ad_now
pd_now = c.pd_now

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
