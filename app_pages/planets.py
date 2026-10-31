"""Planets page."""
from ui.common import aspects_on, chart_svg, cmp, combustion, ctx, ins, ordinal, pd, st, varga_positions, VARGAS

c = ctx()
chart = c.chart
av = c.av
P = c.P
sens_rows = c.sens_rows
dasha_days_per_min = c.dasha_days_per_min

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
st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
st.caption("Combust = degrees from the Sun when inside the classical limit. Aspected by = whole-sign aspects "
           "received (Rahu/Ketu aspects are informational and not scored).")

st.subheader("Jaimini Chara Karakas")
st.dataframe(pd.DataFrame([{"Role": k["role"], "Planet": k["planet"], "Sign": k["sign"],
                            "Degree": f"{k['degree']:.2f}°", "Meaning": k["meaning"]} for k in chart["karakas"]]),
             width="stretch", hide_index=True)
st.markdown(ins.karaka_insight(chart))

st.subheader("🗺 Divisional charts")
v1, v2 = st.columns([1, 1])
varga = v1.selectbox("Chart", list(VARGAS), format_func=lambda k: f"{k} · {VARGAS[k][0]}", index=5,
                     key="varga_pick")
vstyle = v2.radio("Style", ["South Indian", "North Indian"], horizontal=True, key="varga_style")
g1, g2 = st.columns(2)
g1.markdown(chart_svg(vstyle, chart, varga_positions(chart, "D1"), "Rasi (D1)"), unsafe_allow_html=True)
g2.markdown(chart_svg(vstyle, chart, varga_positions(chart, varga), varga, False), unsafe_allow_html=True)
vpos = varga_positions(chart, varga)
same = [n for n in P if n != "Ascendant" and vpos[n] == P[n]["sign_idx"]]
st.caption(f"{VARGAS[varga][0]}. Planets in the same sign as in D1 (vargottama in this chart): "
           f"{', '.join(same) or 'none'}.")

st.subheader("⏱ Birth-time sensitivity")
st.markdown("How many minutes the birth time can move before each factor changes. Small numbers mean those "
            "readings depend on a precise birth time.")
st.dataframe(pd.DataFrame([{
    "Factor": r["factor"], "Now": r["value"],
    "If born earlier": f"{r['earlier'][1]} after {r['earlier'][0]} min" if r["earlier"][0] else "no change within 4 h",
    "If born later": f"{r['later'][1]} after {r['later'][0]} min" if r["later"][0] else "no change within 4 h",
    "What it affects": r["impact"],
} for r in sens_rows]), width="stretch", hide_index=True)
st.caption(f"Each minute of birth-time error shifts all Vimshottari Dasha dates by about "
           f"{dasha_days_per_min:.1f} days.")

with st.expander("🔍 Compare with other software (e.g. Jagannatha Hora)"):
    st.markdown("Paste planet positions from another program, one per line, e.g. `Sun 0°33' Gemini`, "
                "`Moon Ar 25:29:24`, `Lagna 2 Li 06` or an absolute longitude like `Mars 70.30`.")
    pasted = st.text_area("Positions", height=180, key="cmp_text",
                          placeholder="Lagna 2 Li 06\nSun 0 Ge 33\nMoon 25 Ar 29\n...")
    if pasted.strip():
        theirs, unread = cmp.parse_positions(pasted)
        if theirs:
            crow = cmp.compare(chart, theirs)
            st.dataframe(pd.DataFrame(crow), width="stretch", hide_index=True)
            st.info(cmp.diagnose(crow))
        if unread:
            st.caption("Could not read: " + "; ".join(unread))
