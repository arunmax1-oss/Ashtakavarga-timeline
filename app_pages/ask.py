"""Ask page: questions about your chart, answered by Google Gemini from the app's own calculations."""
import hashlib

from ui import ai
from ui.common import (aspects_on, cached_saturn, career, combustion, ctx, detect_yogas, dt, fmt_date, HOUSE_INFO,
                       ins, la, ordinal, st, SIGNS, vim)

c = ctx()
chart, av, sb, schedule, now = c.chart, c.av, c.sb, c.schedule, c.now
P = chart["planets"]

SYSTEM = (
    "You are an experienced, kind Vedic astrologer of the Parashari school answering a client's questions about "
    "their own birth chart. The chart facts below were calculated by the client's app; treat them as correct and "
    "base every answer on them, citing the specific placements, periods and dates you rely on. Never invent "
    "placements, yogas or dates. If the facts don't cover something, say so plainly, then give the general "
    "Parashari principle, clearly labelled as general. Answer the question asked, in plain English, in about 150-300 "
    "words unless the client asks for more; use short paragraphs or bullets. Explain Sanskrit terms briefly. Be "
    "balanced and encouraging, never fatalistic; astrology is guidance, not certainty. Do not predict death or "
    "serious illness, and do not give medical, legal or financial instructions: suggest a professional instead. "
    "If the question is not about astrology or this chart, politely steer back.\n\nCHART FACTS\n"
)
SUGGESTIONS = ["What does my current Dasha period mean for me?", "When is a good time to change jobs?",
               "What are my biggest strengths in this chart?", "How will the next 12 months look for money?",
               "Which planet should I strengthen with remedies, and why?"]


def chart_facts():
    """A compact fact sheet of the whole chart. No name, birth date, time or place."""
    out = [f"Today: {dt.date.today():%d %b %Y}. Ayanamsha {c.ayanamsha}; whole-sign houses.",
           f"Lagna {P['Ascendant']['sign']} {P['Ascendant']['degree']:.1f}° ({P['Ascendant']['nakshatra']})."]
    for n, p in P.items():
        if n == "Ascendant":
            continue
        extra = [p["dignity"]] if p["dignity"] not in ("Neutral", "") else []
        extra += ["retrograde"] if p["retrograde"] else []
        extra += ["combust"] if combustion(chart, n) else []
        if n in sb:
            extra.append(f"Shadbala {sb[n]['ratio']:.2f}x required")
        asp = ", ".join(f"{a} ({ordinal(h)})" for a, h in aspects_on(chart, n))
        out.append(f"{n}: {p['sign']} {p['degree']:.1f}°, {ordinal(p['house'])} house, {p['nakshatra']} pada "
                   f"{p['pada']}, D9 {p['d9_sign']}, D10 {p['d10_sign']}"
                   + (f"; {', '.join(extra)}" if extra else "") + (f"; aspected by {asp}" if asp else ""))
    out.append("House lords and SAV points (28 average): " + "; ".join(
        f"{ordinal(h)} {SIGNS[(chart['asc_sign_idx'] + h - 1) % 12]} (lord {la.lord_of(chart, h)}, "
        f"SAV {c.sav_house[h - 1]})" for h in range(1, 13)))
    out.append("Jaimini karakas: " + ", ".join(f"{k['short']} {k['planet']}" for k in chart["karakas"]))
    vb = vim.vimshopaka(chart)
    out.append("Vimshopaka Bala (16 charts, of 20): " + ", ".join(
        f"{p} {vb[p]['scores']['Shodashavarga (16)']:.1f}" for p in vb))
    out.append("Yogas: " + "; ".join(f"{y['Yoga']} ({y['Condition Met']})" for y in detect_yogas(chart)))
    if c.md_now:
        out.append(f"Running Vimshottari: {c.md_now['lord']} Mahadasha until {fmt_date(c.md_now['end'])}, "
                   f"{c.ad_now['lord']} Antardasha until {fmt_date(c.ad_now['end'])}"
                   + (f", {c.pd_now['lord']} Pratyantardasha until {fmt_date(c.pd_now['end'])}." if c.pd_now else "."))
    upcoming = [(md["lord"], ad) for md in schedule for ad in md["antardashas"]
                if now < ad["end"] and ad["start"] < now + dt.timedelta(days=365.25 * 12)]
    out.append("Antardashas for the next 12 years: " + "; ".join(
        f"{m}-{ad['lord']} {fmt_date(max(ad['start'], now))} to {fmt_date(ad['end'])}" for m, ad in upcoming))
    out += [f"Current transit: {line}".replace("**", "") for line in ins.current_transits(chart, av, now)]
    phases, _ = cached_saturn(chart)
    cur = next((ph for ph in phases if ph["start"] <= now < ph["end"]), None)
    nxt = next((ph for ph in phases if ph["start"] > now), None)
    out.append(f"Saturn phase now: {cur['phase']} until {fmt_date(cur['end'])}." if cur else
               "Saturn phase now: no Sade Sati, Ashtama or Ardhashtama.")
    if nxt:
        out.append(f"Next Saturn phase: {nxt['phase']} from {fmt_date(nxt['start'])} to {fmt_date(nxt['end'])}.")
    prof = career.profile(chart, av, sb)
    out += [f"Career: {line}".replace("**", "") for line in career.profile_text(chart, prof)]
    out.append(f"Career leaning: {prof['leaning']}".replace("**", ""))
    for key in la.AREAS:
        pr = la.promise(chart, av, sb, key)
        plus = list(dict.fromkeys(f["text"] for fs in pr["groups"].values() for f in fs if f["points"] > 0))[:3]
        minus = list(dict.fromkeys(f["text"] for fs in pr["groups"].values() for f in fs if f["points"] < 0))[:3]
        out.append(f"{key}: {pr['label']} ({pr['index']}/100). Helps: {'; '.join(plus) or '-'}. "
                   f"Needs care: {'; '.join(minus) or '-'}.")
    for label, part in (("now", "for the current period"), ("lifelong", "from the birth chart")):
        entries = c.remedies.get(label) or []
        entries = entries.values() if isinstance(entries, dict) else entries
        if entries:
            out.append(f"Remedies suggested {part}: " + "; ".join(
                f"{r['planet']} ({r['priority']} priority: {', '.join(r['reasons'][:2])})" for r in entries))
    out.append("House meanings: " + "; ".join(f"{h} {HOUSE_INFO[h][1]}" for h in range(1, 13)))
    return out


st.markdown("> 💬 Ask anything about your chart in plain English: timing, career, relationships, strengths, "
            "remedies. Answers come from **Google Gemini**, which is given the app's own calculations for your "
            "chart (not your name, birth date, time or place) and told to base every answer on them.")

key, models = ai.settings()
if not key:
    st.info(ai.SETUP_HELP)
    st.stop()

facts = chart_facts()
system = SYSTEM + "\n".join(f"- {f}" for f in facts)
chart_id = hashlib.sha1(system.split("Today:")[1].split("\n", 1)[1].encode()).hexdigest()
if st.session_state.get("ask_chart") != chart_id:  # new chart: start a fresh conversation
    st.session_state["ask_chart"] = chart_id
    st.session_state["ask_history"] = []
history = st.session_state["ask_history"]

for role, text in history:
    with st.chat_message("user" if role == "user" else "assistant"):
        st.markdown(text)

question = st.chat_input("Ask a question about your chart…")
if not history and not question:
    st.caption("Try one of these:")
    cols = st.columns(len(SUGGESTIONS))
    for col, s in zip(cols, SUGGESTIONS):
        if col.button(s, width="stretch"):
            question = s

if question:
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Reading your chart…"):
            try:
                model, answer = ai.converse(system, history[-10:] + [("user", question)])
            except RuntimeError as exc:
                st.error(str(exc))
            else:
                st.markdown(answer)
                history += [("user", question), ("model", answer)]
                st.rerun()

if history:
    b1, b2 = st.columns([1, 1])
    if b1.button("🗑 Start a new conversation"):
        st.session_state["ask_history"] = []
        st.rerun()
    b2.download_button("Download conversation", "\n\n".join(
        f"{'**You:**' if r == 'user' else '**Astrologer:**'} {t}" for r, t in history),
        file_name="chart_conversation.md")

with st.expander("What Gemini is told about your chart"):
    st.caption(f"Model: {models[0]} (backups: {', '.join(models[1:])}). No name, birth date, time or place is sent. "
               "On Google's free tier, prompts may be used to improve Google's products.")
    st.code("\n".join(facts), language=None)
st.caption("Answers are AI-written interpretations of your chart for reflection, not certainties. Check dates against "
           "the Dasha and Timing pages.")
