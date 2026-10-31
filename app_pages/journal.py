"""Journal page."""
from ui.common import cached_day, ctx, dt, jr, st

c = ctx()
chart = c.chart
av = c.av
schedule = c.schedule
tz_name = c.tz_name

st.markdown("> 💡 Keep a short **journal** of what actually happened, then see how often the app's day ratings "
            "agreed. Over months this shows which parts of the forecast work for you.")
st.info("Streamlit Cloud does not keep files between sessions, so **download your journal** after adding entries "
        "and **upload it** next time to continue.")
if "journal" not in st.session_state:
    st.session_state["journal"] = jr.empty()
up = st.file_uploader("Load a saved journal (CSV)", type="csv", key="jr_upload")
if up is not None and st.session_state.get("jr_loaded") != up.name + str(up.size):
    try:
        st.session_state["journal"] = jr.from_csv(up)
        st.session_state["jr_loaded"] = up.name + str(up.size)
        st.success(f"Loaded {len(st.session_state['journal'])} entries.")
    except Exception as exc:
        st.error(f"Could not read that file: {exc}")

with st.form("jr_form", clear_on_submit=True):
    f1, f2, f3 = st.columns([1, 1, 1])
    e_date = f1.date_input("Date", value=dt.date.today(), format="DD/MM/YYYY")
    e_area = f2.selectbox("Area of life", jr.AREAS)
    e_felt = f3.select_slider("How did it go?", options=[-2, -1, 0, 1, 2], value=0,
                              format_func=lambda v: jr.FELT[v])
    e_text = st.text_input("What happened", placeholder="e.g. Job interview went well")
    if st.form_submit_button("Add entry"):
        st.session_state["journal"] = jr.add(st.session_state["journal"], e_date, e_area, e_text, e_felt)

jdf = st.session_state["journal"]
if len(jdf):
    result, summary = jr.evaluate(jdf, lambda d: cached_day(chart, av, schedule, d, tz_name))
    j1, j2, j3 = st.columns(3)
    j1.metric("Entries", summary["entries"])
    j2.metric("App agreed", f"{summary['agreement']:.0%}")
    if summary["avg_score_good"] is not None and summary["avg_score_bad"] is not None:
        j3.metric("Avg app score: good vs hard days",
                  f"{summary['avg_score_good']:+.1f} vs {summary['avg_score_bad']:+.1f}")
    st.dataframe(result, width="stretch", hide_index=True)
    st.caption("'Agree' means a good experience fell on a positively rated day, a hard one on a negatively rated "
               "day, or a neutral one on a mixed day. A clear gap between good-day and hard-day scores means the "
               "ratings are tracking your life.")
    st.download_button("📥 Download journal (CSV)", jr.to_csv(jdf), file_name="astro_journal.csv",
                       mime="text/csv")
else:
    st.caption("No entries yet.")
