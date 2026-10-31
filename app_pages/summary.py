"""Summary page."""
from ui.common import chart_svg, ctx, detect_yogas, nar, pd, st, varga_positions

c = ctx()
chart = c.chart
P = c.P
sav_house = c.sav_house

style = st.radio("Chart style", ["South Indian", "North Indian"], horizontal=True, key="chart_style")
cA, cB = st.columns(2)
cA.markdown(chart_svg(style, chart, varga_positions(chart, "D1"), "Rasi (D1)"), unsafe_allow_html=True)
cB.markdown(chart_svg(style, chart, varga_positions(chart, "D9"), "Navamsa (D9)", False), unsafe_allow_html=True)
st.caption("℞ = retrograde. Numbers in the North Indian chart are sign numbers (1 = Aries); the top diamond is "
           "the 1st house. More divisional charts are on the Planets page.")
st.divider()
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
    st.dataframe(pd.DataFrame(yogas), width="stretch", hide_index=True)
else:
    st.info("None of the tracked yogas are present: a well-balanced distribution without extreme concentrations.")
