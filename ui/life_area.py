"""Draws one life-area page (Health, Wealth, Relationships...). Each app_pages/<area>.py calls render(key)."""
import plotly.graph_objects as go

from ui.ai import reading_section

from ui.common import (cached_area, cached_year, chart_svg, ctx, dt, fmt_date, la, ordinal, pd, SIGNS, st,
                       today_utc, VARGAS, varga_positions)

ICON = {1: "✅", 0: "▫️", -1: "⚠️"}


def _year_chart(rows, area):
    labels = [r["label"] for r in rows]
    vals = [r[area] for r in rows]
    colors = ["#2E9E5B" if v >= 0.8 else "#E8C547" if v > -0.8 else "#D8483E" for v in vals]
    fig = go.Figure(go.Bar(x=labels, y=vals, marker_color=colors, hovertemplate="%{x}: %{y:.2f}<extra></extra>"))
    fig.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), yaxis_title="Month score",
                      xaxis=dict(categoryorder="array", categoryarray=labels))
    return fig


def facts(c, key, data):
    """Plain fact lines for the AI write-up: no name, birth date, time or place."""
    P = c.chart["planets"]
    out = [f"Today is {dt.date.today():%d %b %Y}",
           f"Lagna {P['Ascendant']['sign']}; Moon sign {P['Moon']['sign']} ({P['Moon']['nakshatra']} nakshatra)",
           f"Running Vimshottari period: {c.md_now['lord']} Mahadasha, {c.ad_now['lord']} Antardasha until "
           f"{fmt_date(c.ad_now['end'])}" if c.md_now and c.ad_now else "Running period unknown"]
    out += la.summary_lines(c.chart, key, data["promise"])
    if key == "Home & Family":
        out += [f"{r['Area']}: {r['Rating']} ({r['Score']}/100). Helps: {r['Helps']}. Watch: {r['Watch']}"
                for r in data["extras"]]
    else:
        out += data["extras"]
    for group, fs in data["promise"]["groups"].items():
        out.append(f"{group}: " + "; ".join(f"{'+' if f['points'] > 0 else '-' if f['points'] < 0 else '='} "
                                            f"{f['text']}" for f in fs))
    out += [f"Dasha period {p['md']}-{p['ad']} {fmt_date(p['start'])} to {fmt_date(p['end'])}: {p['strength']} link, "
            f"{p['tone']} ({p['roles']})" for p in data["periods"][:8]]
    out += [f"Transit: {t['planet']} in {t['sign']} {fmt_date(t['start'])} to {fmt_date(t['end'])}, {t['what']}"
            for t in data["transits"][:8]]
    out += [f"Double-transit window: {fmt_date(a)} to {fmt_date(b)}" for a, b in data["double"]]
    return out


def render(key):
    c = ctx()
    chart, av, schedule, sb, now = c.chart, c.av, c.schedule, c.sb, c.now
    spec = la.AREAS[key]
    data = cached_area(chart, av, schedule, sb, key, today_utc())
    prom = data["promise"]

    st.markdown(f"> 💡 {spec['intro']}")
    main = spec["houses"][0]
    main_sign = SIGNS[(chart["asc_sign_idx"] + main - 1) % 12]
    m = st.columns(4)
    m[0].metric("Birth-chart promise", prom["label"], f"{prom['index']}/100", delta_color="off",
                help="Every factor below scores +1, 0 or −1; the index rescales their average to 0–100 (50 = neutral).")
    m[1].metric(f"{ordinal(main)} house", main_sign, f"lord {la.lord_of(chart, main)}", delta_color="off")
    m[2].metric(f"{ordinal(main)} house SAV", av["sav"][(chart["asc_sign_idx"] + main - 1) % 12],
                help="Sarvashtakavarga points; 28 is average.")
    cur = next((p for p in data["periods"] if p["start"] <= now < p["end"]), None)
    m[3].metric("Running now", f"{cur['md']}–{cur['ad']}" if cur else "—",
                f"{cur['tone']} for this area" if cur else "no area period running", delta_color="off")

    st.subheader("🧭 What this means for you")
    for line in la.summary_lines(chart, key, prom):
        st.markdown(f"- {line}")

    st.subheader(f"{spec['icon']} Classical checks")
    if key == "Home & Family":
        st.dataframe(pd.DataFrame(data["extras"]), width="stretch", hide_index=True,
                     column_config={"Score": st.column_config.ProgressColumn("Score", format="%d", min_value=0,
                                                                            max_value=100)})
        st.caption("Each relation is read from its house, its significator and its divisional chart.")
    else:
        for line in data["extras"]:
            st.markdown(f"- {line}")

    with st.expander("🔍 Why this rating: every factor"):
        for group, factors in prom["groups"].items():
            st.markdown(f"**{group}**")
            st.markdown("\n".join(f"- {ICON[f['points']]} {f['text'][0].upper() + f['text'][1:]}" for f in factors))

    if spec["varga"]:
        v, vh = spec["varga"]
        g1, g2 = st.columns([1, 1])
        with g1:
            style = st.radio("Chart style", ["South Indian", "North Indian"], horizontal=True, key=f"style_{key}")
            st.markdown(chart_svg(style, chart, varga_positions(chart, v), v, False), unsafe_allow_html=True)
        with g2:
            st.markdown(f"**{v} · {VARGAS[v][0]}**")
            st.markdown(f"The divisional chart for this area. Its {ordinal(vh)} house and that house's lord are "
                        "read alongside the birth chart: a well-placed lord here confirms the birth-chart promise, "
                        "a weak one asks for more effort. Divisional charts depend on an accurate birth time.")

    st.subheader("📈 When: Dasha periods for this area (next 15 years)")
    st.caption("Antardashas whose lord (or Mahadasha lord) rules, occupies or signifies this area. 'Strong' = both "
               "lords are linked to the area; tone comes from the main lord's dignity, Shadbala and house."
               + (" Periods of the 6th, 8th or 12th lord bring those houses' matters into focus even when the tone "
                  "is supportive (a strong lord helps you handle them well)." if set(spec["houses"]) & {6, 8, 12}
                  else ""))
    if data["periods"]:
        st.dataframe(pd.DataFrame([{
            "Period": f"{p['md']}–{p['ad']}", "From": fmt_date(p["start"]), "To": fmt_date(p["end"]),
            "Link": p["strength"], "Tone": p["tone"], "Why": p["roles"],
        } for p in data["periods"]]), width="stretch", hide_index=True)
        nxt = next((p for p in data["periods"] if p["start"] > now and p["strength"] != "Background"
                    and p["tone"] != "Testing"), None)
        if nxt:
            st.info(f"**Next supportive window:** {nxt['md']}–{nxt['ad']} from {fmt_date(nxt['start'])} to "
                    f"{fmt_date(nxt['end'])}.")

    st.subheader("🪐 Slow transits over these houses (next 3 years)")
    if data["transits"]:
        st.dataframe(pd.DataFrame([{
            "Planet": t["planet"], "In": t["sign"], "From": fmt_date(t["start"]), "To": fmt_date(t["end"]),
            "Effect": t["what"], "What it brings": t["tone"],
        } for t in data["transits"]]), width="stretch", hide_index=True)
    else:
        st.caption("Jupiter, Saturn and Rahu do not touch these houses in the next 3 years.")
    if data["double"]:
        st.markdown(f"**🎯 Double-transit windows for the {ordinal(main)} house** (Jupiter and Saturn both influence "
                    "the house or its lord; events promised by the Dasha tend to happen in these windows): "
                    + "; ".join(f"{fmt_date(a)} – {fmt_date(b)}" for a, b in data["double"]) + ".")

    st.subheader("📆 The next 12 months")
    today = dt.date.today()
    rows = cached_year(chart, av, schedule, sb, today.year, today.month, c.here_tz)
    st.plotly_chart(_year_chart(rows, spec["monthly"]), width="stretch")
    st.caption(f"Monthly '{spec['monthly']}' score from the Month page (above 0.8 good, below −0.8 challenging). "
               "Open the Month page for the details of any month.")
    st.caption("Readings are classical Parashari guidance for reflection and planning, not certainties.")
    st.divider()
    reading_section(key, facts(c, key, data))
