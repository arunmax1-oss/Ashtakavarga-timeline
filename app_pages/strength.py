"""Strength page."""
from ui.common import (COMPONENT_LABELS, ctx, dignity_strength, ins, jd_to_datetime, pd, shadbala_figure, st,
                        strength_figure, to_local)

c = ctx()
chart = c.chart
sb = c.sb
tz_name = c.tz_name

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
