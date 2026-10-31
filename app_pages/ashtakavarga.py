"""Ashtakavarga page."""
from ui.common import bav_heatmap, ctx, HOUSE_INFO, ins, nar, pd, sav_figure, sign_table, SIGNS, st

c = ctx()
chart = c.chart
av = c.av
sav_house = c.sav_house

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
           "is weak. The Timing page uses these numbers.")
with st.expander("BAV / SAV table by sign"):
    st.dataframe(pd.DataFrame(sign_table(av)), width="stretch", hide_index=True)
