"""Bhrigu page."""
from ui.common import bhrigu, cached_bb_windows, ctx, dt, pd, st, to_local

c = ctx()
chart = c.chart
now = c.now
tz_name = c.tz_name

st.markdown("> 💡 Three techniques from the **Bhrigu** tradition. The **Bhrigu Bindu** is a sensitive point "
            "midway between Rahu and the Moon. **Bhrigu Chakra Paddhati** activates one house for each year of "
            "life. **Bhrigu Nandi Nadi** reads the natal planets that Jupiter and Saturn are touching by sign.")
st.subheader("🎯 Bhrigu Bindu")
st.markdown(bhrigu.bhrigu_bindu_reading(chart))
bb_windows = cached_bb_windows(chart, now, now + dt.timedelta(days=round(365.25 * 6)))
if bb_windows:
    st.markdown("**Coming activations** (Saturn, Jupiter, Rahu or Ketu within 2° of your Bhrigu Bindu, next 6 years):")
    st.dataframe(pd.DataFrame([{
        "Planet": w["planet"], "From": to_local(w["start"], tz_name).date(), "To": to_local(w["end"], tz_name).date(),
        "Exact around": to_local(w["exact"], tz_name).date(),
        "Meaning": {"Saturn": "a karmic turning point: responsibilities and lasting change",
                    "Jupiter": "an opening: growth, opportunity and protection",
                    "Rahu": "a sudden push: ambition, change and the unexpected",
                    "Ketu": "a release: endings, letting go and inner turns"}[w["planet"]],
    } for w in bb_windows]), width="stretch", hide_index=True)
else:
    st.caption("No slow-planet contacts with your Bhrigu Bindu in the next 6 years.")

st.subheader("🔄 Bhrigu Chakra Paddhati (yearly house)")
st.markdown(bhrigu.bcp_reading(chart, now))
st.dataframe(pd.DataFrame(bhrigu.bcp_cycle(chart, now)), width="stretch", hide_index=True)

st.subheader("🪐 Bhrigu Nandi Nadi: what Jupiter and Saturn are touching now")
st.caption("BNN reads a transit planet with the natal planets in the same sign, in trine (5th/9th), opposite "
           "(7th), and in the adjacent signs (2nd/12th). Strongest links are listed first.")
contacts = bhrigu.bnn_contacts(chart, now)
if contacts:
    for r in contacts:
        st.markdown(f"- {r['text']}")
else:
    st.caption("Jupiter and Saturn are not touching any natal planet by these relations right now.")
