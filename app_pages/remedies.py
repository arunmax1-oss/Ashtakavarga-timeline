"""Remedies page."""
from ui.common import cached_remedy_triggers, ctx, fmt_date, nar, ordinal, pd, rem, st, today_utc

c = ctx()
chart = c.chart
remedies = c.remedies
roles, scores, doshas, vb = remedies["roles"], remedies["scores"], remedies["doshas"], remedies["vimshopaka"]

st.markdown("> 💡 **Remedies (upaya)** are traditional ways to work with a planet that is weak or afflicted in "
            "your chart, or is running your life right now. The app first evaluates each planet: its **role for "
            "your Lagna** decides whether it should be *strengthened* or *pacified*, and a **severity score** "
            "(0–100) shows how much attention it needs, with every factor listed. Doshas and upcoming trigger "
            "periods are checked too.")
st.info(nar.REMEDY_DISCLAIMER)

strengthen = [p for p in roles if roles[p]["approach"] == "Strengthen" and scores[p]["score"] >= 15]
pacify = [p for p in roles if roles[p]["approach"] == "Pacify" and scores[p]["score"] >= 15]
present = [d for d in doshas if d["present"]]
triggers = cached_remedy_triggers(chart, c.schedule, scores, roles, today_utc())
m = st.columns(4)
m[0].metric("Planets to strengthen", len(strengthen), ", ".join(strengthen) or "none", delta_color="off",
            help="Functional benefics for your Lagna with a severity of 15 or more.")
m[1].metric("Planets to pacify", len(pacify), ", ".join(pacify) or "none", delta_color="off",
            help="Functional malefics and the nodes with a severity of 15 or more.")
m[2].metric("Doshas present", len(present), f"{sum(not d['cancelled'] for d in present)} without cancellation",
            delta_color="off")
m[3].metric("Next trigger", fmt_date(triggers[0]["start"]) if triggers else "—",
            triggers[0]["planet"] if triggers else "none in 3 years", delta_color="off")

st.subheader("🧭 Your planets: role, approach and severity")
st.dataframe(pd.DataFrame([{
    "Planet": p, "Role for your Lagna": roles[p]["role"],
    "Rules": ", ".join(ordinal(h) for h in roles[p]["houses"]) or "—",
    "Also": ", ".join(t.split(" (")[0] for t in roles[p]["tags"]) or "—", "Approach": roles[p]["approach"],
    "Severity": scores[p]["score"], "Level": scores[p]["level"],
    "D9": chart["planets"][p]["d9_sign"],
    "Vimshopaka /20": vb[p]["scores"]["Shodashavarga (16)"] if p in vb else None,
} for p in roles]), width="stretch", hide_index=True, column_config={
    "Severity": st.column_config.ProgressColumn("Severity (0–100)", format="%d", min_value=0, max_value=100)})
st.caption("**Strengthen** a functional benefic (rules the Lagna or a trine) that is weak; **pacify** a functional "
           "malefic (rules the 3rd, 6th, 8th or 11th) or a node; **balance** a neutral or mixed planet. Badhaka = "
           "lord of obstruction for your Lagna; Maraka = lord of the 2nd or 7th, whose periods can drain vitality. "
           "Severity: 60+ High, 35–59 Medium, 15–34 Low.")
with st.expander("Why each planet has its severity score"):
    pick = st.selectbox("Planet", list(roles), key="sev_pick")
    st.markdown(f"**{pick}: {scores[pick]['score']}/100 ({scores[pick]['level']}).** {roles[pick]['why']}")
    st.markdown("\n".join(f"- {'+' if f['points'] > 0 else ''}{f['points']}: {f['text']}"
                          for f in scores[pick]["factors"]) or "- No factors: nothing weakens or afflicts it.")


def section(heading, key, intro, empty):
    st.subheader(heading)
    st.caption(intro)
    entries = remedies[key]
    if not entries:
        st.success(empty)
        return
    st.dataframe(pd.DataFrame(rem.table_rows(entries)), width="stretch", hide_index=True)
    for e in entries:
        with st.expander(f"{e['planet']} · {e['priority']} priority · severity {e['score']} · {e['approach']} · "
                         f"{e['day']}"):
            st.markdown(rem.entry_markdown(e))


section("⏱ Do now", "now",
        "Planets active at present: the lords of your current Dasha periods and any Saturn pressure on your Moon. "
        "Being active adds points to the birth-chart severity. Each has an end date.",
        "Nothing time-bound is flagged right now.")

st.subheader("📅 Coming up (next 3 years)")
st.caption("Sub-periods of planets that need care, Rahu/Ketu or Saturn crossing your Moon or Lagna, Saturn's phases "
           "from the Moon, and eclipses within 5° of a natal planet. Start the planet's remedy a month ahead "
           "(a few days ahead for an eclipse).")
if triggers:
    st.dataframe(pd.DataFrame([{
        "Begin remedy by": fmt_date(t["begin_by"]), "Starts": fmt_date(t["start"]), "Ends": fmt_date(t["end"]),
        "Planet": t["planet"], "What": t["what"], "Why it matters": t["why"],
        "Approach": roles[t["planet"]]["approach"] if t["planet"] in roles else "—",
    } for t in triggers]), width="stretch", hide_index=True)
else:
    st.success("No major trigger periods in the next three years.")

section("🌱 Lifelong", "lifelong",
        "Planets weak or afflicted in the birth chart itself (severity 10 or more). These do not expire; small, "
        "steady habits work best.",
        "No planet needs lifelong attention: none is significantly weakened or afflicted.")

st.subheader("🐍 Doshas")
st.caption("Classical afflictions, each checked with its traditional cancellations. 'Eased' means a cancellation "
           "applies, so the effect is milder.")
if present:
    for d in present:
        with st.expander(f"{'🟡' if d['cancelled'] else '🔴'} {d['name']}: {d['status']}"):
            st.markdown(f"**Condition:** {d['condition']}.")
            if d["cancellations"]:
                st.markdown("**Cancellations:**\n" + "\n".join(f"- {x}" for x in d["cancellations"]))
            st.markdown(f"**Traditional remedy:** {d['remedy']}")
else:
    st.success("None of the ten doshas checked is present in your chart.")
absent = [d["name"] for d in doshas if not d["present"]]
if absent:
    st.caption("Not present: " + ", ".join(absent) + ".")

with st.expander("How the evaluation works (and what is not checked)"):
    st.markdown(
        "**Role for your Lagna.** Lords of the 1st, 5th and 9th are benefic; lords of the 3rd, 6th and 11th "
        "malefic; the 8th lord malefic unless it also rules the Lagna; lords of the 4th, 7th and 10th neutral; "
        "a lord of both a kendra and a trine (other than the Lagna) is Yogakaraka; 2nd and 12th lords take on "
        "their other sign's nature. Rahu and Ketu are always pacified.\n\n"
        "**Severity (0–100)** adds up: debilitation (+25, or +8 if cancelled), a difficult house (+12), 3 or fewer "
        "Ashtakavarga points (+12 to +16), Shadbala below minimum (+8 to +20), combustion (+12; Mercury +4), "
        "malefic pressure (+5 or +12), a node in a sensitive house (+8), debilitation in the D9 (+10), Vimshopaka "
        "below 10 (+8), each dosha it is part of (+6 to +12, or +3 if eased), and +5 for an afflicted functional "
        "malefic. It subtracts protection: exaltation or own sign (−10), strength in the D9 (−10), vargottama (−8), "
        "strong Ashtakavarga (−6) or Shadbala (−6), Vimshopaka 15+ (−8) and Jupiter's aspect (−8).\n\n"
        "**Active now** adds +12 for the Mahadasha or Antardasha lord, +12 to +20 for Saturn's phases, and +15 "
        "when the two period lords are in a tense relationship.\n\n"
        "**Gemstones** are shown only for planets to *strengthen*, and then only for your Lagna lord or a lord of "
        "a kendra or trine that rules no difficult house. Rahu and Ketu never get one here.\n\n"
        "Kaal Sarp yoga is a later tradition, not in the classical Parashari texts. A professional reading weighs "
        "these factors with judgement and may emphasise different planets.")
