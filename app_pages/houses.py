"""Houses page: Arudha Padas, Argala and Bhava Chalit."""
from ui.common import ctx, HOUSE_INFO, hs, ordinal, pd, SIGNS, st

c = ctx()
chart = c.chart
P = c.P

st.markdown("> 💡 Three Parashari house techniques. **Arudha Padas** show how each area of life *appears* to the "
            "world (image, as opposed to reality). **Argala** shows which planets *intervene* in a house, helping or "
            "obstructing it. **Bhava Chalit** shows which house's matters a planet near a sign border actually "
            "delivers.")

st.subheader("🪞 Arudha Padas")
padas = hs.arudha_padas(chart)
for line in hs.arudha_insight(chart, padas):
    st.markdown(f"- {line}")
st.dataframe(pd.DataFrame([{
    "Pada": d["short"], "Name": d["name"], "Of house": ordinal(d["house"]), "Sign": d["sign"],
    "Falls in house": d["pada_house"], "Planets there": ", ".join(d["occupants"]) or "—", "Shows": d["meaning"],
} for d in padas]), width="stretch", hide_index=True)
st.caption("Method: count from the house to its lord, then the same count from the lord. If that lands on the house "
           "itself or the 7th from it, the 10th from there is taken. Scorpio and Aquarius use the stronger lord.")

st.subheader("🛡 Argala (planetary intervention)")
summary = hs.argala_summary(chart)
st.dataframe(pd.DataFrame([{
    "House": HOUSE_INFO[h][0], "Life area": HOUSE_INFO[h][1], "Effective argalas": eff,
    "of which benefic": ben, "Obstructed": obs,
} for h, (eff, obs, ben) in summary.items()]), width="stretch", hide_index=True)
pick = st.selectbox("Show the argalas on", list(range(1, 13)), key="argala_house",
                    format_func=lambda h: f"{HOUSE_INFO[h][0]} · {HOUSE_INFO[h][1]}")
rows = hs.argala(chart, pick)
if rows:
    st.dataframe(pd.DataFrame([{
        "From": f"{ordinal(r['from'])} house", "Planets": ", ".join(r["planets"]), "Nature": r["nature"],
        "Brings": r["theme"],
        "Obstruction": (f"{ordinal(r['obstructs'])}: {', '.join(r['obstructed_by']) or 'empty'}"
                        if r["obstructs"] else "cannot be obstructed"),
        "Result": r["status"],
    } for r in rows]), width="stretch", hide_index=True)
else:
    st.caption("No planets in the 2nd, 4th, 5th or 11th from this house, so no argala on it.")
st.caption("Planets in the 2nd, 4th and 11th (and 5th) from a house intervene in it; planets in the 12th, 10th and "
           "3rd (and 9th) obstruct them. An argala holds when it has more planets than its obstruction. Benefic "
           "argala supports the house; malefic argala still drives results, more harshly.")

st.subheader("🏛 Bhava Chalit (Sripati houses)")
bc = hs.bhava_chalit(chart)
for line in hs.chalit_insight(chart, bc):
    st.markdown(f"- {line}")
with st.expander("House middles and borders"):
    st.dataframe(pd.DataFrame([{
        "Bhava": ordinal(h + 1),
        "Begins": f"{SIGNS[int(bc['sandhi'][h] // 30)]} {bc['sandhi'][h] % 30:.2f}°",
        "Middle": f"{SIGNS[int(bc['madhya'][h] // 30)]} {bc['madhya'][h] % 30:.2f}°",
        "Planets": ", ".join(n for n, b in bc["planets"].items() if b == h + 1) or "—",
    } for h in range(12)]), width="stretch", hide_index=True)
st.caption("The rest of the app uses whole-sign houses (the most common reading of Parashara); this table shows "
           "where the unequal Sripati houses differ.")
