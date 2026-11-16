"""Remedies page."""
from ui import ai
from ui.common import (jr, cached_remedy_triggers, cached_start_days, ctx, dt, fmt_date, fmt_span, nar, ordinal, pd, rem,
                       rplan, st, today_utc)

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
            links = rplan.life_links(chart, e["planet"])
            st.markdown(f"**Life areas it touches:** {links['text']} Most relevant pages: "
                        f"{', '.join(links['areas'][:4]) or '—'}.")
            st.markdown("**Fuller guidance**\n\n| Practice | Guidance |\n|---|---|\n" + "\n".join(
                f"| {k} | {v} |" for k, v in rplan.guidance_rows(e["planet"], e["approach"], e["gem"])))


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

st.subheader("🗓 When to start")
flagged = list(dict.fromkeys(e["planet"] for e in remedies["now"] + remedies["lifelong"]))
if flagged:
    st.caption("A remedy is traditionally begun on the planet's own weekday, in its planetary hour (hora), on a day "
               "that is good for you personally, and outside Rahu Kalam. Strengthening remedies prefer the waxing "
               "Moon. Times are for where you are now (set in the sidebar).")
    when_pick = st.selectbox("Planet", flagged, key="start_pick",
                             format_func=lambda p: f"{p} ({roles[p]['approach'].lower()})")
    days = cached_start_days(chart, c.av, c.schedule, when_pick, roles[when_pick]["approach"], dt.date.today(),
                             c.here_tz, c.here_place)
    if days:
        best = days[0]
        hora = f", in its hora {fmt_span(best['horas'][0])}" if best["horas"] else ""
        st.success(f"**Best start in the next six weeks:** {best['date']:%A %d %b %Y}{hora}"
                   + (f" (avoid Rahu Kalam {fmt_span(best['rahu_kalam'])})" if best["rahu_kalam"] else "") + ".")
        st.dataframe(pd.DataFrame([{
            "Date": f"{d['date']:%a %d %b %Y}", "Your day": d["rating"], "Tithi": d["tithi"],
            "Nakshatra": d["nakshatra"], "Planet's hours": ", ".join(fmt_span(h) for h in d["horas"]) or "—",
            "Avoid (Rahu Kalam)": fmt_span(d["rahu_kalam"]) if d["rahu_kalam"] else "—",
            "Notes": "; ".join(d["notes"]) or "—",
        } for d in sorted(days, key=lambda d: d["date"])]), width="stretch", hide_index=True)
        if when_pick in ("Rahu", "Ketu"):
            st.caption(f"{when_pick} has no hora of its own; {'Saturn' if when_pick == 'Rahu' else 'Mars'}'s hora "
                       "is used, as is customary.")
else:
    st.caption("No planet is flagged, so there is nothing to schedule.")

st.subheader("💎 Gemstone plan")
plan = rplan.gem_plan(chart, remedies)
st.caption("At most two stones, only for planets to strengthen that need it (severity 15+), your Lagna lord "
           "first, and never two stones whose planets are natural enemies (e.g. ruby with blue sapphire).")
if plan["wear"]:
    for g in plan["wear"]:
        d = g["details"]
        st.markdown(f"- ✅ **{g['stone']}** for {g['planet']}: {g['reason']}. Commonly {d['carats']} carats in "
                    f"{d['metal']}, on the {d['finger']}, first worn {d['start']}. Substitutes: {d['substitutes']}.")
else:
    st.markdown("- No gemstone is recommended for your chart right now: the practical and devotional remedies are "
                "enough.")
for g in plan["skip"]:
    st.markdown(f"- ▫️ {g['stone']} ({g['planet']}): {g['reason']}.")
st.caption(nar.GEM_CAUTION)

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

st.subheader("📿 Remedy tracker")
st.caption("Log each time you practise a remedy. Entries are saved in the same file as the **Journal** page, so one "
           "download keeps both. Streamlit Cloud does not keep files: **download after logging** and load the file "
           "on the Journal page next time. Log life events on the Journal page too, and the tracker shows how they "
           "felt before and after you started.")
if "journal" not in st.session_state:
    st.session_state["journal"] = jr.empty()
planets_for_log = flagged + [p for p in roles if p not in flagged]
with st.form("remedy_log_form", clear_on_submit=True):
    t1, t2, t3, t4 = st.columns([1, 1, 1.3, 0.8])
    log_date = t1.date_input("Date", value=dt.date.today(), format="DD/MM/YYYY")
    log_planet = t2.selectbox("Planet", planets_for_log)
    log_practice = t3.selectbox("Practice", jr.PRACTICES)
    log_count = t4.number_input("Repetitions", min_value=0, value=108, step=108,
                                help="Mantra repetitions; ignored for other practices.")
    log_note = st.text_input("Note (optional)", placeholder="e.g. donated rice at the temple")
    if st.form_submit_button("Log practice"):
        st.session_state["journal"] = jr.add_remedy(
            st.session_state["journal"], log_date, log_planet, log_practice,
            log_count if log_practice == "Mantra (japa)" else 0, log_note)
journal = st.session_state["journal"]
log = jr.remedy_log(journal)
progress_rows, effects = [], []
for p in dict.fromkeys(log["planet"]):
    pr = jr.remedy_progress(journal, p, rplan.REMEDY_DETAILS[p]["japa"],
                            rplan.WEEKDAYS.index(rplan.REMEDIES[p]["day"]))
    progress_rows.append({"Planet": p, "Sessions": pr["sessions"], "Days practised": pr["days"],
                          "Current streak (days)": pr["streak"],
                          "On its weekday": pr["on_weekday"], "Japa": f"{pr['japa']:,} / {pr['japa_target']:,}",
                          "Japa course": pr["japa_pct"], "Since": fmt_date(pr["first"]),
                          "Last": fmt_date(pr["last"])})
    eff = jr.remedy_effect(journal, p, rplan.life_links(chart, p)["areas"])
    if eff:
        effects.append((p, eff))
if progress_rows:
    st.dataframe(pd.DataFrame(progress_rows), width="stretch", hide_index=True, column_config={
        "Japa course": st.column_config.ProgressColumn("Japa course", format="percent", min_value=0, max_value=1)})
    for p, eff in effects:
        if eff["ready"]:
            delta = eff["after"] - eff["before"]
            st.markdown(f"- **{p}**: journal events in {', '.join(eff['areas'])} averaged {eff['before']:+.1f} before "
                        f"you started ({eff['n_before']} entries) and **{eff['after']:+.1f}** since "
                        f"({eff['n_after']} entries): "
                        + ("things have felt better." if delta > 0.25 else
                           "things have felt harder; give it time and keep the practical step going."
                           if delta < -0.25 else "no clear change yet."))
        else:
            st.caption(f"{p}: log at least two Journal events in {', '.join(eff['areas']) or 'its life areas'} "
                       f"before and after {fmt_date(eff['start'])} to see a before/after comparison "
                       f"(now {eff['n_before']} before, {eff['n_after']} after).")
    with st.expander("Remedy log"):
        st.dataframe(log[["date", "planet", "practice", "count", "event"]].rename(columns={
            "date": "Date", "planet": "Planet", "practice": "Practice", "count": "Repetitions", "event": "Note"}),
            width="stretch", hide_index=True)
    st.download_button("📥 Download journal and remedy log (CSV)", jr.to_csv(journal), file_name="astro_journal.csv",
                       mime="text/csv", key="rem_dl")
else:
    st.caption("Nothing logged yet.")

st.divider()
facts = [f"Today is {dt.date.today():%d %b %Y}",
         f"Lagna {chart['planets']['Ascendant']['sign']}; Moon sign {chart['planets']['Moon']['sign']}"]
for p in roles:
    sc = scores[p]
    facts.append(f"{p}: {roles[p]['role']} for this Lagna ({roles[p]['why']}"
                 + (f"; {', '.join(roles[p]['tags'])}" if roles[p]["tags"] else "") + f"); approach "
                 f"{roles[p]['approach']}; severity {sc['score']}/100 ({sc['level']}); factors: "
                 + ("; ".join(f"{f['points']:+d} {f['text']}" for f in sc["factors"]) or "none")
                 + f"; {rplan.life_links(chart, p)['text']}")
for label, key in (("Do now", "now"), ("Lifelong", "lifelong")):
    for e in remedies[key]:
        facts.append(f"{label} remedy for {e['planet']} ({e['priority']} priority, {e['approach']}): reasons "
                     f"{'; '.join(e['reasons'])}. Practical step: {e['practical']} Devotional: on {e['day']}s "
                     f"{e['practice']}, mantra {e['mantra']}, donate {e['charity']}."
                     + (f" Until {fmt_date(e['until'])}." if e["until"] else ""))
facts += [f"Dosha: {d['name']} {d['status'].lower()}: {d['condition']}"
          + (f"; cancellations: {', '.join(d['cancellations'])}" if d["cancellations"] else "")
          + f"; traditional remedy: {d['remedy']}" for d in doshas if d["present"]] or ["No doshas present"]
facts += [f"Coming up: {t['what']} from {fmt_date(t['start'])} to {fmt_date(t['end'])} ({t['why']}); begin the "
          f"{t['planet']} remedy by {fmt_date(t['begin_by'])}" for t in triggers]
for p in flagged:
    days_ = cached_start_days(chart, c.av, c.schedule, p, roles[p]["approach"], dt.date.today(), c.here_tz,
                              c.here_place)
    if days_:
        facts.append(f"Best start day for {p}: {days_[0]['date']:%A %d %b %Y}"
                     + (f", in its hora {fmt_span(days_[0]['horas'][0])}" if days_[0]["horas"] else ""))
facts += [f"Gemstone recommended: {g['stone']} for {g['planet']} ({g['reason']})" for g in plan["wear"]] or \
    ["No gemstone recommended"]
facts += [f"Gemstone not recommended: {g['stone']} for {g['planet']} ({g['reason']})" for g in plan["skip"]]
facts += [f"Practice so far for {r['Planet']}: {r['Sessions']} sessions over {r['Days practised']} days, japa "
          f"{r['Japa']}" for r in progress_rows]
ai.reading_section("Remedies", facts, ai.REMEDY_INSTRUCTIONS, button="Explain my remedies")

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
