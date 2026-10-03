"""Plain-English interpretation text. Edit wording here without touching any calculations."""
from .constants import HOUSE_INFO, SIGN_LORDS, SIGNS, ordinal

DASHA_DESCRIPTIONS = {
    "Sun": "Focuses on ego integration, core identity, leadership, professional status, and authority dynamics.",
    "Moon": "Highlights emotional stability, public interactions, mind clarity, maternal ties, and shifting perceptions.",
    "Mars": "Drives ambition, physical execution, real estate, courage, and technical problem-solving.",
    "Rahu": "Triggers rapid worldly expansion, unconventional growth, digital/foreign horizons, and intense focus.",
    "Jupiter": "Expands wisdom, academic/philosophical depth, financial growth, mentorship, and legal alignment.",
    "Saturn": "Demands discipline, structure, accountability, long-term endurance, and systemic groundwork.",
    "Mercury": "Sharpens intellect, commercial transactions, strategic communication, analytics, and business ties.",
    "Ketu": "Induces internal reflection, detachment from outcomes, spiritual research, and pruning redundant paths.",
    "Venus": "Enhances artistic creation, luxury, wealth accumulation, partnership dynamics, and social refinement.",
}

# Keyed by the house distance between the Mahadasha lord and Antardasha lord in the natal chart.
AXIS_DESCRIPTIONS = {
    "Conjunction (same sign)": (
        "info", "Both period lords share a sign, so their themes fuse: results arrive bundled and intensely, "
                "for better or worse depending on their natural relationship."),
    "1/7 Axis (Direct Mutual Aspect)": (
        "info", "Creates dynamic interpersonal focus and active negotiation between personal goals and external partnerships."),
    "3/11 Axis (Growth Alignment)": (
        "success", "Excellent flow for financial gains, skill acquisition, networking, and executing strategic initiatives with low friction."),
    "4/10 Axis (Kendra Action)": (
        "info", "Focuses heavily on balancing internal security (home/foundations) with external output (career/reputation)."),
    "5/9 Axis (Trikona Prosperity)": (
        "success", "Highly auspicious period bringing creative flow, fortunate breakthroughs, intellectual clarity, and alignment."),
    "2/12 Axis (Dwirdwadasa)": (
        "warning", "Indicates higher financial churn, unexpected expenses, personal detachment, or long-distance shifts."),
    "6/8 Axis (Shashtashtaka)": (
        "warning", "Transformational period requiring conflict management, health vigilance, and structural adjustments."),
}

_DISTANCE_TO_AXIS = {
    1: "Conjunction (same sign)", 7: "1/7 Axis (Direct Mutual Aspect)",
    3: "3/11 Axis (Growth Alignment)", 11: "3/11 Axis (Growth Alignment)",
    4: "4/10 Axis (Kendra Action)", 10: "4/10 Axis (Kendra Action)",
    5: "5/9 Axis (Trikona Prosperity)", 9: "5/9 Axis (Trikona Prosperity)",
    2: "2/12 Axis (Dwirdwadasa)", 12: "2/12 Axis (Dwirdwadasa)",
    6: "6/8 Axis (Shashtashtaka)", 8: "6/8 Axis (Shashtashtaka)",
}

CAREER_ARCHETYPES = {
    "Sun": ("Executive Leadership & Public Authority",
            "leading institutional strategy, corporate policy, government relations, and high-visibility direction."),
    "Moon": ("Operations, Experience & Client Management",
             "enterprise client experience, public relations, organisational communication, and operational diplomacy."),
    "Mars": ("Competitive Strategy & Technological Execution",
             "market intelligence, competitive analysis, engineering leadership, and high-stakes problem solving."),
    "Mercury": ("Data Architecture, Research & Strategic Analytics",
                "competitive intelligence, product market analysis, commercial research, and workflow automation."),
    "Jupiter": ("Enterprise Advisory & Product Strategy",
                "senior advisory roles, corporate architecture, financial planning, legal counsel, and mentorship."),
    "Venus": ("Brand Equity & Design Operations",
              "brand positioning, customer experience design, media partnerships, and high-value product management."),
    "Saturn": ("Governance, Infrastructure & Enterprise Operations",
               "large-scale systems architecture, supply chain execution, process optimisation, and long-term governance."),
}

HEALTH_FOCUS = {
    "Sun": ("Cardiovascular, Ocular & Bone Density",
            "arterial pressure, eye strain, and circadian rhythm imbalances."),
    "Moon": ("Fluid Balance, Lymphatic System & Sleep",
             "fluid fluctuations, digestive sluggishness, anxiety, and sleep-cycle disruption."),
    "Mars": ("Inflammation, Heat & Acid Balance",
             "high metabolic heat, acidity, blood-pressure spikes, or inflammatory conditions."),
    "Mercury": ("Nervous System & Gut-Brain Axis",
                "stress-induced gut flare-ups, nervous tension, and respiratory/allergy responsiveness."),
    "Jupiter": ("Metabolic, Liver & Lipid Health",
                "lipid imbalance, liver congestion, and metabolic sluggishness during high-stress phases."),
    "Venus": ("Kidney, Reproductive & Hormonal Balance",
              "kidney filtration, fluid retention, and hormone regulation."),
    "Saturn": ("Joints, Bones & Lower Digestion",
               "chronic dryness, joint/spinal stiffness, sluggish circulation, and constipation."),
}


def dasha_axis(chart, md_lord, ad_lord):
    p = chart["planets"]
    distance = (p[ad_lord]["sign_idx"] - p[md_lord]["sign_idx"]) % 12 + 1
    name = _DISTANCE_TO_AXIS[distance]
    tone, text = AXIS_DESCRIPTIONS[name]
    return name, tone, text


def karaka(chart, short):
    return next(k for k in chart["karakas"] if k["short"] == short)


def career_narrative(chart, sav_house):
    asc = chart["asc_sign_idx"]
    h10_sign = SIGNS[(asc + 9) % 12]
    h10_lord = SIGN_LORDS[h10_sign]
    lord_house = chart["planets"][h10_lord]["house"]
    amk = karaka(chart, "AmK")
    title, desc = CAREER_ARCHETYPES[amk["planet"]]
    s10, s11, s12 = sav_house[9], sav_house[10], sav_house[11]

    if s10 >= 30:
        cap = f"The 10th house holds a powerful **{s10} SAV bindus** (above the 28 baseline): strong backing for leadership, visibility and smooth execution."
    elif s10 >= 28:
        cap = f"The 10th house holds **{s10} SAV bindus**: steady capacity; growth tracks consistent output."
    else:
        cap = f"The 10th house holds **{s10} SAV bindus** (below 28): growth needs deliberate strategy, upskilling and careful relationship management."

    if s11 > s10 > s12:
        wealth = f"11th ({s11}) > 10th ({s10}) > 12th ({s12}) meets the classical prosperity ratio: income comfortably exceeds outflow."
    elif s11 > s12:
        wealth = f"11th ({s11}) exceeds 12th ({s12}): gains outpace expenses, though not in the full classical 11 > 10 > 12 order."
    else:
        wealth = f"12th ({s12}) is at or above 11th ({s11}): spending pressure is high; savings need structured boundaries."

    return f"""
**Primary archetype:** {title}

- **Amatyakaraka (career driver):** {amk['planet']} at {amk['degree']:.2f}° {amk['sign']}
- **10th house:** {h10_sign}, ruled by {h10_lord} placed in the {ordinal(lord_house)} house ({HOUSE_INFO[lord_house][1].lower()})

1. **Core focus:** with {amk['planet']} as Amatyakaraka, sustained success comes through {desc}
2. **Karma sthana capacity:** {cap}
3. **Wealth axis:** {wealth}
4. **Execution:** advancement leans on the themes of the {ordinal(lord_house)} house, where your 10th lord sits.
"""


def health_narrative(chart, sav_house):
    gk = karaka(chart, "GK")
    title, desc = HEALTH_FOCUS[gk["planet"]]
    asc = chart["asc_sign_idx"]
    s1, s6, s8 = sav_house[0], sav_house[5], sav_house[7]
    vitality = ("Lagna is at least as strong as the 6th: constitution handles workload stress and recovers quickly."
                if s1 >= s6 else
                "The 6th exceeds the Lagna: burnout, inflammation or lifestyle fatigue can lower resilience during busy phases.")
    eighth_label, eighth_text = eighth_house_reading(s8)
    eighth = f"{eighth_label}. {eighth_text}"
    return f"""
**Sensitivity focus:** {title}

- **Gnatikaraka (obstacles & health):** {gk['planet']}
- **6th house (acute issues):** {SIGNS[(asc + 5) % 12]}, {s6} SAV
- **8th house (chronic issues):** {SIGNS[(asc + 7) % 12]}, {s8} SAV

1. **Watch area:** {gk['planet']} as Gnatikaraka points to {desc}
2. **Vitality (1st {s1} vs 6th {s6}):** {vitality}
3. **8th house ({s8}):** {eighth}
"""


def house_strength_label(points):
    if points >= 30:
        return "Strong (≥30)"
    if points >= 28:
        return "Average (28–29)"
    return "Weak (<28)"


# --------------------------------------------------------------------------------------
# Reference text used by vedic/insights.py to explain each tab in context
# --------------------------------------------------------------------------------------
PLANET_SIGNIFIES = {
    "Sun": "authority, self-confidence, father, vitality and dealings with government or seniors",
    "Moon": "mind, emotions, mother, comfort and how you connect with the public",
    "Mars": "energy, courage, property, siblings and technical or competitive drive",
    "Mercury": "intellect, communication, trade, analysis and learning",
    "Jupiter": "wisdom, growth, teachers, children, wealth and good fortune",
    "Venus": "relationships, comfort, art, luxury and refinement",
    "Saturn": "discipline, hard work, longevity, responsibility and slow, lasting results",
    "Rahu": "ambition, foreign or unconventional paths, technology and intense desire",
    "Ketu": "detachment, spirituality, research and skills carried from the past",
    "Ascendant": "your body, temperament and the lens through which you meet life",
}

SIGN_KEYWORDS = {
    "Aries": "bold, pioneering and quick to act", "Taurus": "steady, practical and value-building",
    "Gemini": "curious, communicative and versatile", "Cancer": "nurturing, protective and emotional",
    "Leo": "confident, generous and visible", "Virgo": "analytical, precise and service-minded",
    "Libra": "balanced, diplomatic and relationship-oriented", "Scorpio": "intense, investigative and transformative",
    "Sagittarius": "philosophical, expansive and principled", "Capricorn": "disciplined, ambitious and structured",
    "Aquarius": "innovative, networked and humanitarian", "Pisces": "intuitive, compassionate and imaginative",
}

NAKSHATRA_KEYWORDS = {
    "Ashwini": "speed, healing and fresh starts", "Bharani": "creativity, restraint and carrying responsibility",
    "Krittika": "sharpness, purification and decisive action", "Rohini": "growth, beauty and material comfort",
    "Mrigashira": "curiosity, searching and gentle restlessness", "Ardra": "intellect and breakthroughs after upheaval",
    "Punarvasu": "renewal, optimism and returning to what works", "Pushya": "nourishment, care and steady support",
    "Ashlesha": "insight, strategy and intensity", "Magha": "lineage, authority and tradition",
    "Purva Phalguni": "pleasure, creativity and relationships", "Uttara Phalguni": "commitment, patronage and reliable partnerships",
    "Hasta": "skill, craftsmanship and wit", "Chitra": "design, brilliance and building beautiful things",
    "Swati": "independence, flexibility and trade", "Vishakha": "ambition and single-minded pursuit of goals",
    "Anuradha": "devotion, friendship and organisation", "Jyeshtha": "seniority, protection and responsibility",
    "Moola": "getting to the root of things through research", "Purva Ashadha": "conviction, persuasion and invincibility",
    "Uttara Ashadha": "lasting victory and principled leadership", "Shravana": "listening, learning and reputation",
    "Dhanishta": "wealth, rhythm and group achievement", "Shatabhisha": "healing, science and solitude",
    "Purva Bhadrapada": "idealism, intensity and transformation", "Uttara Bhadrapada": "depth, patience and stable wisdom",
    "Revati": "guidance, compassion and safe completion",
}

DIGNITY_TEXT = {
    "Exalted": "exalted — at its strongest, so it delivers its themes generously",
    "Own Sign": "in its own sign — comfortable, reliable and self-directed",
    "Debilitated": "debilitated — its themes need more effort and tend to mature later",
    "Neutral": "in a neutral sign — it takes on the flavour of the sign and its lord",
}

# Simple, practical ways to work with each planet when it needs support.
PLANET_SUPPORT = {
    "Sun": "take visible responsibility, keep a morning routine and get daylight",
    "Moon": "protect sleep, stay hydrated and keep emotional routines steady",
    "Mars": "channel energy into regular exercise and decisive, time-boxed action",
    "Mercury": "read, write and learn something structured; keep commitments in writing",
    "Jupiter": "teach, mentor or study; give generously and keep ethical clarity",
    "Venus": "invest in relationships, art and aesthetics; avoid overindulgence",
    "Saturn": "build disciplined routines, serve others and be patient with slow results",
    "Rahu": "focus ambitions, avoid shortcuts and keep a grounding practice",
    "Ketu": "meditate, simplify and let go of what no longer serves",
}

# Classical transit results counted from the natal Moon (Gochara).
GOCHARA_GOOD_FROM_MOON = {
    "Saturn": [3, 6, 11], "Jupiter": [2, 5, 7, 9, 11], "Mars": [3, 6, 11],
    "Sun": [3, 6, 10, 11], "Venus": [1, 2, 3, 4, 5, 8, 9, 11, 12], "Mercury": [2, 4, 6, 8, 10, 11],
}


def eighth_house_reading(points):
    """One reading of 8th-house SAV, shared by the Summary and Ashtakavarga tabs so they never disagree.

    The app treats the difficult houses (6th, 8th, 12th) the same way everywhere: fewer points = quieter.
    """
    if points < 28:
        return ("Contained", "Below 28: sudden changes and long-running strain tend to stay manageable. "
                             "Keep ordinary care; no special caution is indicated.")
    return ("More active", "At or above 28: this house is lively, so sudden changes and stress are felt more strongly. "
                           "The same energy gives depth for research and staying power. "
                           "Prioritise recovery and buffers (rest, savings, insurance) during difficult transits.")


# --------------------------------------------------------------------------------------
# Glossary: plain-English meanings of the terms used across the tabs
# --------------------------------------------------------------------------------------
GLOSSARY = {
    "Lagna (Ascendant, Rising sign)": "The zodiac sign rising on the eastern horizon at your birth. It is the starting "
                                      "point of the chart and describes your body, temperament and approach to life.",
    "Rashi (Moon sign)": "The sign the Moon was in at birth. It describes your mind, moods and emotional needs. "
                         "Most Indian horoscopes are read from it.",
    "House (Bhava)": "One of 12 areas of life (self, money, home, career and so on). The 1st house is the Lagna sign, "
                     "the 2nd is the next sign, and so on.",
    "Nakshatra": "One of 27 star groups, each 13°20' wide, that the zodiac is divided into. It adds finer detail to a "
                 "planet's sign. Your Moon's nakshatra is your birth star.",
    "Pada": "A quarter of a nakshatra (3°20'). Each nakshatra has 4 padas.",
    "Dignity": "How comfortable a planet is in its sign. Exalted = strongest, Own Sign = comfortable, "
               "Neutral = ordinary, Debilitated = weakest.",
    "Neecha Bhanga": "'Cancelled debilitation': a weak planet gets support from another planet, so early difficulty "
                     "in its area tends to turn into strength later.",
    "Retrograde (℞)": "The planet appears to move backwards as seen from Earth. Its themes come through review, "
                      "delay and second attempts.",
    "Vargottama": "A planet in the same sign in the main chart and in the D9 chart. Treated as extra strong and reliable.",
    "D9 (Navamsha)": "A secondary chart made by dividing each sign into 9 parts. Shows inner strength and marriage.",
    "D10 (Dashamsha)": "A secondary chart made by dividing each sign into 10 parts. Shows career.",
    "Karaka (Atmakaraka, Amatyakaraka ...)": "'Significator'. The 7 planets ranked by degree each take a role: the "
                                             "Atmakaraka (highest degree) is the soul planet, the Amatyakaraka (second) "
                                             "is the career planet, and so on.",
    "Yoga": "A named combination of planets that gives a specific result, for example Gajakesari Yoga.",
    "Kendra / Trikona / Dusthana": "House groups. Kendras (1, 4, 7, 10) are pillars of the chart. Trikonas (1, 5, 9) "
                                   "are houses of fortune. Dusthanas (6, 8, 12) are houses of difficulty.",
    "Functional benefic": "A planet that is helpful for your particular Lagna because of the houses it rules.",
    "Dasha (Vimshottari)": "A 120-year sequence of planetary periods. It shows which planet is 'running' your life "
                           "at any time.",
    "Mahadasha / Antardasha / Pratyantardasha": "Main period (years) / sub-period (months to a few years) / "
                                                "sub-sub-period (weeks to months).",
    "Ashtakavarga": "A points system. Each planet gives or withholds a point (bindu) to each sign. More points = "
                    "that area of life works more easily.",
    "Bindu": "One benefic point in Ashtakavarga.",
    "BAV (Bhinna Ashtakavarga)": "One planet's own scorecard: 0 to 8 points per sign. 4 is average.",
    "SAV (Sarvashtakavarga)": "All planets' points added up per sign. 28 is average, 30 or more is strong.",
    "Kakshya": "One eighth of a sign (3°45'). Each has a ruling planet. Used to time transits precisely.",
    "Transit (Gochara)": "Where the planets are in the sky now (or on any date), compared with your birth chart.",
    "Sade Sati": "Saturn's roughly 7½ year passage through the sign before your Moon, your Moon sign, and the sign "
                 "after. A period of pressure, responsibility and maturing.",
    "Ashtama Shani / Ardhashtama Shani": "Saturn in the 8th / 4th sign from your Moon. Shorter periods of pressure "
                                         "(about 2½ years each).",
    "Combust (Asta)": "A planet so close to the Sun that it is 'burnt' by its light. Its themes get overshadowed. "
                      "Mercury is nearly always close to the Sun, so its combustion is treated lightly.",
    "Aspect (Drishti)": "A planet's gaze on other signs. Every planet aspects the 7th sign from itself; Mars also "
                        "the 4th and 8th, Jupiter the 5th and 9th, Saturn the 3rd and 10th. Jupiter's aspect protects; "
                        "Saturn's and Mars's add pressure.",
    "Ayanamsha": "The correction that converts Western (tropical) positions into Indian (sidereal) ones. "
                 "Lahiri is the standard in India.",
    "Rahu / Ketu": "The Moon's two nodes (points where eclipses happen). Not physical planets, but treated as "
                   "planets: Rahu = worldly hunger, Ketu = detachment.",
}

# --------------------------------------------------------------------------------------
# Traditional remedies (upaya). Tier 1 (practical) reuses PLANET_SUPPORT above.
# --------------------------------------------------------------------------------------
REMEDIES = {
    "Sun": {"day": "Sunday", "mantra": "Om Suryaya Namah", "deity": "Surya",
            "practice": "offer water to the rising Sun", "charity": "wheat or jaggery", "gem": "Ruby"},
    "Moon": {"day": "Monday", "mantra": "Om Chandraya Namah", "deity": "Shiva",
             "practice": "offer water or milk at a Shiva temple", "charity": "rice, milk or white cloth", "gem": "Pearl"},
    "Mars": {"day": "Tuesday", "mantra": "Om Mangalaya Namah", "deity": "Hanuman",
             "practice": "recite the Hanuman Chalisa", "charity": "red lentils (masoor dal)", "gem": "Red Coral"},
    "Mercury": {"day": "Wednesday", "mantra": "Om Budhaya Namah", "deity": "Vishnu",
                "practice": "recite the Vishnu Sahasranama or feed green fodder to cows",
                "charity": "green moong dal or books for students", "gem": "Emerald"},
    "Jupiter": {"day": "Thursday", "mantra": "Om Gurave Namah", "deity": "Brihaspati / your teachers",
                "practice": "honour a teacher or elder and offer yellow flowers",
                "charity": "chana dal, turmeric or yellow cloth", "gem": "Yellow Sapphire"},
    "Venus": {"day": "Friday", "mantra": "Om Shukraya Namah", "deity": "Lakshmi",
              "practice": "offer white flowers to Lakshmi", "charity": "white sweets, rice or curd", "gem": "Diamond or White Sapphire"},
    "Saturn": {"day": "Saturday", "mantra": "Om Shanaishcharaya Namah", "deity": "Shani / Hanuman",
               "practice": "light a sesame-oil lamp at dusk", "charity": "black sesame, mustard oil, or help for labourers and the elderly",
               "gem": "Blue Sapphire"},
    "Rahu": {"day": "Saturday", "mantra": "Om Rahave Namah", "deity": "Durga",
             "practice": "recite a Durga prayer", "charity": "black urad dal or blankets", "gem": None},
    "Ketu": {"day": "Tuesday", "mantra": "Om Ketave Namah", "deity": "Ganesha",
             "practice": "offer durva grass to Ganesha", "charity": "blankets, or food for stray dogs", "gem": None},
}

REMEDY_DISCLAIMER = ("Remedies are traditional practices offered for reflection. They are optional, they are not a "
                     "substitute for medical, legal or financial advice, and nothing here promises an outcome. "
                     "Start with the practical step: it costs nothing and carries no risk.")
GEM_CAUTION = ("Gemstones strengthen a planet for better or worse, are costly, and are easy to get wrong. "
               "Treat this as a question to take to an astrologer you trust, not as an instruction.")
