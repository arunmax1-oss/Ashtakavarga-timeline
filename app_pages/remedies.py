"""Remedies page."""
from ui.common import ctx, nar, pd, rem, st

c = ctx()
remedies = c.remedies

st.markdown("> 💡 **Remedies (upaya)** are traditional ways to work with a planet that is weak in your birth "
            "chart or is running your life right now. Every row below shows the exact chart fact that triggered "
            "it. Each planet has three tiers: a **practical** habit, a **devotional** practice, and (only where "
            "it is safe for your Lagna) a **gemstone** to discuss with an astrologer.")
st.info(nar.REMEDY_DISCLAIMER)

for heading, key, intro, empty in [
    ("⏱ Do now", "now",
     "Planets that are active at present: the lords of your current Dasha periods and any Saturn pressure "
     "on your Moon. These change over time, so each has an end date.",
     "Nothing time-bound is flagged right now."),
    ("🌱 Lifelong", "lifelong",
     "Planets that are weak in the birth chart itself. These do not expire; small, steady habits work best.",
     "No planet is flagged in your birth chart: none is debilitated, combust, under combined malefic pressure, "
     "below its required Shadbala, in the 8th or 12th house, or short of Ashtakavarga points where it sits."),
]:
    st.subheader(heading)
    st.caption(intro)
    entries = remedies[key]
    if not entries:
        st.success(empty)
        continue
    st.dataframe(pd.DataFrame(rem.table_rows(entries)), width="stretch", hide_index=True)
    for e in entries:
        with st.expander(f"{e['planet']} · {e['priority']} priority · {e['day']}"):
            st.markdown(rem.entry_markdown(e))

with st.expander("How these remedies are chosen (and what is not checked)"):
    st.markdown(
        "| Trigger | Priority |\n|---|---|\n"
        "| Planet debilitated, weakness not cancelled | High |\n"
        "| Two or more Medium triggers on the same planet | High |\n"
        "| Planet in the 8th or 12th house (or a gentle planet in the 6th) | Medium |\n"
        "| 3 or fewer Ashtakavarga points in the sign it occupies | Medium |\n"
        "| Combust: too close to the Sun (Moon 12°, Mars 17°, Mercury 14°, Jupiter 11°, Venus 10°, Saturn 15°; "
        "Mercury 12° and Venus 8° when retrograde) | Medium (Low for Mercury) |\n"
        "| Two or more malefic influences (Saturn or Mars aspect; Saturn, Mars, Rahu or Ketu in the same sign) "
        "and no Jupiter aspect | Medium |\n"
        "| Debilitated but cancelled (Neecha Bhanga) | Low |\n"
        "| Lord of the current Mahadasha or Antardasha | Medium (High if also weak at birth) |\n"
        "| Tense relationship between the two period lords (2/12 or 6/8) | High for the sub-period lord |\n"
        "| Sade Sati peak or Ashtama Shani | High |\n"
        "| Sade Sati first or final phase, Ardhashtama Shani | Medium |\n"
        "| Shadbala below the planet's required minimum | Medium |\n\n"
        "**Gemstones** are shown only for your Lagna lord, or for a planet that rules a kendra or trikona and no "
        "difficult house. Rahu and Ketu never get one here.\n\n"
        "**Aspects** are whole-sign: every planet aspects the 7th sign from itself; Mars also the 4th and 8th, "
        "Jupiter the 5th and 9th, Saturn the 3rd and 10th. Rahu and Ketu count only when they share a sign, because "
        "traditions disagree on their aspects. A single malefic influence, or one eased by Jupiter, is listed as a "
        "note and does not raise the priority.\n\n"
        "A professional reading weighs these factors with judgement and may emphasise different planets.")
