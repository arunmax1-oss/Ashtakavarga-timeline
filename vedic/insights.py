"""Chart-specific explanations ("What this means for you") for each tab.

Every function takes already-computed data and returns Markdown. No Streamlit here.
"""
from collections import Counter

from .aspects import aspected_houses, aspects_on, combustion, influences
from .chart import house_from, julian_day, planet_longitude, set_ayanamsha
from .constants import ALL_PLANETS, CLASSICAL_PLANETS, HOUSE_INFO, SIGN_LORDS, SIGNS, ordinal
from .narratives import (
    DASHA_DESCRIPTIONS, DIGNITY_TEXT, GOCHARA_GOOD_FROM_MOON, NAKSHATRA_KEYWORDS,
    PLANET_SIGNIFIES, PLANET_SUPPORT, SIGN_KEYWORDS, dasha_axis,
)

KENDRAS = [1, 4, 7, 10]
TRIKONAS = [1, 5, 9]
DUSTHANAS = [6, 8, 12]


def _domain(house):
    return HOUSE_INFO[house][1].lower()


def _houses_text(houses):
    names = [ordinal(h) for h in sorted(houses)]
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def ruled_houses(chart, planet):
    asc = chart["asc_sign_idx"]
    return [h for h in range(1, 13) if SIGN_LORDS[SIGNS[(asc + h - 1) % 12]] == planet]


def lordship_note(chart, planet):
    houses = ruled_houses(chart, planet)
    if not houses:
        return ""
    good = [h for h in houses if h in TRIKONAS or h in KENDRAS]
    hard = [h for h in houses if h in DUSTHANAS]
    tone = ("a functional benefic for you" if good and not hard else
            "a mixed influence for you (it rules both supportive and challenging houses)" if good and hard else
            "a planet whose periods bring tests that build resilience" if hard else "a neutral influence")
    return (f"It rules your {_houses_text(houses)} house{'s' if len(houses) > 1 else ''} "
            f"({'; '.join(_domain(h) for h in houses)}), making it {tone}.")


def neecha_bhanga(chart, planet):
    """Simplified cancellation of debilitation: the sign's lord sits in a kendra from Lagna or Moon."""
    p = chart["planets"]
    if p[planet]["dignity"] != "Debilitated":
        return False
    lord = SIGN_LORDS[p[planet]["sign"]]
    return (p[lord]["house"] in KENDRAS or
            house_from(p[lord]["sign_idx"], p["Moon"]["sign_idx"]) in KENDRAS)


# --------------------------------------------------------------------------------------
# Planets & Nakshatras
# --------------------------------------------------------------------------------------
def planets_highlights(chart):
    p = chart["planets"]
    out = []
    asc = p["Ascendant"]
    out.append(f"**Ascendant {asc['sign']}** ({SIGN_KEYWORDS[asc['sign']]}) in {asc['nakshatra']} "
               f"({NAKSHATRA_KEYWORDS[asc['nakshatra']]}) sets your basic temperament. Its lord "
               f"**{SIGN_LORDS[asc['sign']]}** sits in your {ordinal(p[SIGN_LORDS[asc['sign']]]['house'])} house, so life keeps "
               f"pulling you toward {_domain(p[SIGN_LORDS[asc['sign']]]['house'])}.")

    strong = [n for n in ALL_PLANETS if p[n]["dignity"] in ("Exalted", "Own Sign")]
    if strong:
        out.append("**Naturally strong:** " + ", ".join(f"{n} ({p[n]['dignity'].lower()} in {p[n]['sign']})" for n in strong)
                   + ". These planets deliver their themes with little friction.")
    for n in [n for n in ALL_PLANETS if p[n]["dignity"] == "Debilitated"]:
        cancel = neecha_bhanga(chart, n)
        out.append(f"**{n} is debilitated in {p[n]['sign']}**"
                   + (f", but its sign lord {SIGN_LORDS[p[n]['sign']]} is in a kendra, a classic sign of *Neecha Bhanga* "
                      "(cancelled debilitation): early struggle in its areas that turns into strength."
                      if cancel else f": {PLANET_SIGNIFIES[n]} need extra, conscious effort."))

    varg = [n for n in ALL_PLANETS if p[n]["sign"] == p[n]["d9_sign"]]
    if varg:
        out.append("**Vargottama** (same sign in D1 and D9): " + ", ".join(varg)
                   + ". These planets are consistent inside and out, and much stronger than they look.")

    combust = [n for n in CLASSICAL_PLANETS if combustion(chart, n)]
    if combust:
        out.append("**Combust** (too close to the Sun): " + ", ".join(
            f"{n} ({combustion(chart, n)['distance']:.1f}°)" for n in combust)
            + ". Their themes are overshadowed by the Sun's: ego, authority or the father figure"
            + (". Mercury's combustion is common and mild." if "Mercury" in combust else "."))

    pressured = [n for n in CLASSICAL_PLANETS
                 if len(influences(chart, n)["malefic"]) >= 2 and not influences(chart, n)["jupiter"]]
    if pressured:
        out.append("**Under combined malefic pressure:** " + "; ".join(
            f"{n}, from {' and '.join(influences(chart, n)['malefic'])}" for n in pressured)
            + ". These areas carry more strain and benefit most from steady effort.")
    protected = [n for n in CLASSICAL_PLANETS if n != "Jupiter" and influences(chart, n)["jupiter"]]
    if protected:
        out.append("**Protected by Jupiter's aspect:** " + ", ".join(protected)
                   + ". Jupiter's gaze softens difficulties and adds wisdom to these planets' themes.")

    retro = [n for n in CLASSICAL_PLANETS if p[n]["retrograde"]]
    if retro:
        out.append("**Retrograde:** " + ", ".join(retro) + ". Their themes turn inward: revisiting, rethinking "
                   "and redoing until mastered, often with unusual results later in life.")

    counts = Counter(p[n]["house"] for n in ALL_PLANETS)
    for house, c in counts.items():
        if c >= 3:
            names = [n for n in ALL_PLANETS if p[n]["house"] == house]
            out.append(f"**Stellium in your {ordinal(house)} house** ({', '.join(names)}): heavy focus on {_domain(house)}.")
    return out


def planet_story(chart, av, name):
    p = chart["planets"][name]
    if name == "Ascendant":
        return planets_highlights(chart)[0]
    parts = [
        f"**{name}** signifies {PLANET_SIGNIFIES[name]}. In your chart it is in **{p['sign']}** "
        f"({SIGN_KEYWORDS[p['sign']]}), in your **{ordinal(p['house'])} house** of {_domain(p['house'])}, "
        f"so these themes play out through that area of life.",
        f"It is {DIGNITY_TEXT[p['dignity']]}." if p["dignity"] else "",
        f"Its nakshatra **{p['nakshatra']}** (pada {p['pada']}, ruled by {p['nakshatra_lord']}) adds "
        f"{NAKSHATRA_KEYWORDS[p['nakshatra']]}.",
        lordship_note(chart, name),
    ]
    if p["sign"] == p["d9_sign"]:
        parts.append("It is **vargottama**: unusually dependable.")
    else:
        parts.append(f"In the D9 (inner strength) it moves to {p['d9_sign']}; in the D10 (career) to {p['d10_sign']}.")
    if p["retrograde"]:
        parts.append("Being retrograde, its results come through review and persistence.")
    comb = combustion(chart, name)
    if comb:
        parts.append(f"It is **combust**, {comb['distance']:.1f}° from the Sun (limit {comb['orb']}°), so its themes are "
                     "overshadowed by the Sun's" + (" (mild for Mercury)." if name == "Mercury" else "."))
    asp = aspects_on(chart, name)
    if asp:
        parts.append("It receives aspects from " + ", ".join(f"{n} ({ordinal(h)})" for n, h in asp)
                     + (" (Rahu/Ketu aspects vary by tradition and are shown for information only, not scored)"
                        if any(n in ("Rahu", "Ketu") for n, _ in asp) else "") + ".")
    if name not in ("Rahu", "Ketu"):
        inf = influences(chart, name)
        if inf["jupiter"] and name != "Jupiter":
            parts.append("Jupiter's influence protects it.")
        if len(inf["malefic"]) >= 2 and not inf["jupiter"]:
            parts.append(f"It is under combined pressure from {', '.join(inf['malefic'])}.")
    gaze = sorted(aspected_houses(chart, name))
    parts.append(f"It aspects your {_houses_text(gaze)} house{'s' if len(gaze) > 1 else ''} "
                 f"({'; '.join(_domain(h) for h in gaze)}), adding its influence there.")
    if name in CLASSICAL_PLANETS:
        bav = av["bav"][name][p["sign_idx"]]
        parts.append(f"It has **{bav}/8 bindus** in its own Ashtakavarga where it sits "
                     f"({'well supported' if bav >= 5 else 'average support' if bav == 4 else 'thin support'}).")
    return " ".join(x for x in parts if x)


def karaka_insight(chart):
    k = {x["short"]: x for x in chart["karakas"]}
    return (f"Your **Atmakaraka {k['AK']['planet']}** (highest degree) is the soul's main lesson: mastering "
            f"{PLANET_SIGNIFIES[k['AK']['planet']]}. **Amatyakaraka {k['AmK']['planet']}** guides career choices, and "
            f"**Darakaraka {k['DK']['planet']}** describes what you seek in a partner: {PLANET_SIGNIFIES[k['DK']['planet']]}.")


# --------------------------------------------------------------------------------------
# Dasha
# --------------------------------------------------------------------------------------
def lord_capacity(chart, av, lord):
    p = chart["planets"][lord]
    sav = av["sav"][p["sign_idx"]]
    line = (f"**{lord}** sits in your {ordinal(p['house'])} house ({p['sign']}, {p['dignity'].lower()}), "
            f"so it brings results in {_domain(p['house'])}. ")
    note = lordship_note(chart, lord)
    line += f"{note} " if note else ""
    line += (f"Its sign holds **{sav} SAV**, "
             + ("so it has good capacity to deliver." if sav >= 30 else
                "so delivery is average and steady." if sav >= 28 else
                "so results need extra effort and patience."))
    return line


def dasha_insight(chart, av, md, ad):
    name, tone, text = dasha_axis(chart, md["lord"], ad["lord"])
    return "\n\n".join([
        f"**The big chapter, {md['lord']} Mahadasha.** {DASHA_DESCRIPTIONS[md['lord']]} " + lord_capacity(chart, av, md["lord"]),
        f"**The current sub-chapter, {ad['lord']} Antardasha.** {DASHA_DESCRIPTIONS[ad['lord']]} " + lord_capacity(chart, av, ad["lord"]),
        f"**How they combine.** The two lords form a {name.lower()}: {text[0].lower()}{text[1:]}",
    ])


def upcoming_antardashas(chart, av, schedule, md, ad, count=4):
    ads = md["antardashas"]
    i = ads.index(ad)
    rows = []
    for nxt in ads[i + 1:i + 1 + count]:
        p = chart["planets"][nxt["lord"]]
        sav = av["sav"][p["sign_idx"]]
        rows.append(f"- **{nxt['lord']}** ({nxt['start']:%b %Y} – {nxt['end']:%b %Y}): focus on {_domain(p['house'])}"
                    f"{'; rules your ' + _houses_text(ruled_houses(chart, nxt['lord'])) if ruled_houses(chart, nxt['lord']) else ''}. "
                    f"{'Strong delivery' if sav >= 30 else 'Steady' if sav >= 28 else 'Needs effort'} ({sav} SAV).")
    if len(rows) < count and schedule.index(md) + 1 < len(schedule):
        nxt = schedule[schedule.index(md) + 1]
        rows.append(f"- Then the **{nxt['lord']} Mahadasha** begins on {nxt['start']:%d %b %Y} for "
                    f"{(nxt['end'] - nxt['start']).days / 365.25:.0f} years: {DASHA_DESCRIPTIONS[nxt['lord']]}")
    return "\n".join(rows)


# --------------------------------------------------------------------------------------
# Ashtakavarga
# --------------------------------------------------------------------------------------
def ashtakavarga_insight(chart, av, sav_house):
    """Rank the supportive houses by SAV; read the difficult houses (6, 8, 12) the other way round.

    Same rule as narratives.eighth_house_reading: in a dusthana, fewer points = quieter.
    """
    above = sum(1 for s in sav_house if s >= 28)
    good = sorted((h for h in range(12) if h + 1 not in DUSTHANAS), key=lambda h: sav_house[h], reverse=True)
    lines = [
        f"**{above} of 12 houses** are at or above the 28 average. In most houses more points mean that area of life "
        "cooperates. The difficult houses (6th, 8th, 12th) read the other way: fewer points keep their troubles quieter.",
        "**Where life flows most easily:** " + "; ".join(
            f"{ordinal(h + 1)} house, {_domain(h + 1)} ({sav_house[h]})" for h in good[:3]) + ".",
        "**Where to be deliberate:** " + "; ".join(
            f"{ordinal(h + 1)} house, {_domain(h + 1)} ({sav_house[h]})" for h in good[-3:][::-1]) + ".",
    ]
    quiet = [h for h in (6, 8, 12) if sav_house[h - 1] < 28]
    lively = [h for h in (6, 8, 12) if sav_house[h - 1] >= 28]
    lines.append("**Difficult houses:** "
                 + (f"{_houses_text(quiet)} {'is' if len(quiet) == 1 else 'are'} below 28, so obstacles there stay contained. "
                    if quiet else "")
                 + (f"{_houses_text(lively)} {'is' if len(lively) == 1 else 'are'} at or above 28, so "
                    f"{'its' if len(lively) == 1 else 'their'} themes are more active; keep buffers in "
                    f"{'that area' if len(lively) == 1 else 'those areas'}."
                    if lively else ""))
    asc = chart["asc_sign_idx"]
    best = []
    for planet in ["Saturn", "Jupiter", "Mars"]:
        top = max(range(12), key=lambda s: av["bav"][planet][s])
        best.append(f"{planet} in {SIGNS[top]} (your {ordinal(house_from(top, asc))} house, "
                    f"{av['bav'][planet][top]}/8)")
    lines.append("**Best transit zones** (signs where each slow planet has the most bindus, so its transit there "
                 "brings its best results): " + "; ".join(best) + ".")
    return lines


# --------------------------------------------------------------------------------------
# Timing engine
# --------------------------------------------------------------------------------------
def current_transits(chart, av, when):
    """Where the slow planets are right now, judged from Lagna, Moon and Ashtakavarga."""
    set_ayanamsha(chart["ayanamsha"])
    jd = julian_day(when)
    asc, moon = chart["asc_sign_idx"], chart["planets"]["Moon"]["sign_idx"]
    lines = []
    for planet in ["Saturn", "Jupiter", "Rahu", "Mars"]:
        lon, _ = planet_longitude(jd, planet, chart["true_node"])
        s = int(lon // 30)
        h_l, h_m = house_from(s, asc), house_from(s, moon)
        line = (f"**{planet}** is in {SIGNS[s]}: your {ordinal(h_l)} house ({_domain(h_l)}) "
                f"and {ordinal(h_m)} from your Moon.")
        if planet in CLASSICAL_PLANETS:
            good = h_m in GOCHARA_GOOD_FROM_MOON.get(planet, [])
            bav, sav = av["bav"][planet][s], av["sav"][s]
            line += (f" Classically {'favourable' if good else 'testing'} from the Moon; "
                     f"{bav}/8 BAV and {sav} SAV here mean it "
                     + ("delivers well." if bav >= 4 and sav >= 28 else
                        "gives mixed results." if bav >= 4 or sav >= 28 else "is a period to go slow."))
        if planet == "Saturn":
            phase = {12: "rising (first) phase", 1: "peak (second) phase", 2: "setting (final) phase"}.get(h_m)
            if phase:
                line += (f" **Sade Sati {phase}:** Saturn's 7½-year transit over your Moon, a time of "
                         "restructuring, responsibility and maturity rather than misfortune.")
            elif h_m == 8:
                line += " **Ashtama Shani** (8th from Moon): manage health, debts and stress carefully."
            elif h_m == 4:
                line += " **Ardhashtama Shani** (4th from Moon): pressure on home, peace of mind and vehicles."
        lines.append(line)
    return lines


def upcoming_strong(segments, when, per_planet=3):
    out = []
    for planet in ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]:
        wins = [t for t in segments if t["planet"] == planet and t["rating"] == "Strong" and t["end"] > when]
        for t in sorted(wins, key=lambda t: t["start"])[:per_planet]:
            out.append(f"- **{planet}** {t['start']:%d %b %Y} → {t['end']:%d %b %Y}: in {t['sign']} "
                       f"(your {ordinal(t['house'])} house, {_domain(t['house'])}) through the {t['kakshya_lord']} kakshya "
                       f"(BAV {t['bav']}, SAV {t['sav']}).")
    return "\n".join(out)


# --------------------------------------------------------------------------------------
# Strength
# --------------------------------------------------------------------------------------
def strength_insight(chart, rows):
    out = []
    for r in sorted(rows, key=lambda r: r["Strength Score"], reverse=True):
        n = r["Planet"]
        reasons = []
        if r["Dignity"] != "Neutral":
            reasons.append(r["Dignity"].lower())
        if r["Dig Bala"]:
            reasons.append(f"directional strength in the {ordinal(r['House'])} house")
        if r["Combust"]:
            reasons.append(f"combust, {r['Combust']}")
        if r["Jupiter Support"]:
            reasons.append(f"supported by {r['Jupiter Support']}")
        if r["Malefic Influence"] and not r["Jupiter Support"] and r["Malefic Influence"].count(",") >= 1:
            reasons.append(f"pressured by {r['Malefic Influence']}")
        why = f" ({', '.join(reasons)})" if reasons else ""
        houses = ruled_houses(chart, n)
        areas = f" The areas it rules for you, {'; '.join(_domain(h) for h in houses)}, " if houses else " Its themes "
        if r["Status"] == "Dominant & Strong":
            verdict = f"**{n}: strong{why}.**{areas}tend to flow and can be leaned on."
        elif r["Status"] == "Balanced":
            verdict = f"**{n}: balanced{why}.**{areas}give steady results with consistent effort."
        else:
            verdict = (f"**{n}: needs support{why}.**{areas}need more conscious work. "
                       f"Helpful: {PLANET_SUPPORT[n]}."
                       + (" Its debilitation looks cancelled (Neecha Bhanga), so it often improves with age."
                          if neecha_bhanga(chart, n) else ""))
        out.append(verdict)
    return out
