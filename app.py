import datetime
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Vedic Astrology & Ashtakavarga Engine",
    page_icon="🔮",
    layout="wide",
)

# ---------------------------------------------------------------------
# DATA DICTIONARIES
# ---------------------------------------------------------------------
DASHA_DESCRIPTIONS = {
    "Sun": (
        "Focuses on ego integration, core identity, leadership,"
        " professional status, and authority dynamics."
    ),
    "Moon": (
        "Highlights emotional stability, public interactions, mind clarity,"
        " maternal ties, and shifting perceptions."
    ),
    "Mars": (
        "Drives ambition, physical execution, real estate, courage, and"
        " technical problem-solving."
    ),
    "Rahu": (
        "Triggers rapid worldly expansion, unconventional growth,"
        " digital/foreign horizons, and intense focus."
    ),
    "Jupiter": (
        "Expands wisdom, academic/philosophical depth, financial growth,"
        " mentorship, and legal alignment."
    ),
    "Saturn": (
        "Demands discipline, structure, accountability, long-term endurance,"
        " and systemic groundwork."
    ),
    "Mercury": (
        "Sharpens intellect, commercial transactions, strategic communication,"
        " analytics, and business ties."
    ),
    "Ketu": (
        "Induces internal reflection, detachment from outcomes, spiritual"
        " research, and pruning redundant paths."
    ),
    "Venus": (
        "Enhances artistic creation, luxury, wealth accumulation, partnership"
        " dynamics, and social refinement."
    ),
}

RELATIONSHIP_DESCRIPTIONS = {
    "1/7 Axis (Direct Mutual Aspect)": (
        "Creates dynamic interpersonal focus and active negotiation between"
        " personal goals and external partnerships."
    ),
    "3/11 Axis (Growth Alignment)": (
        "Excellent flow for financial gains, skill acquisition, networking,"
        " and executing strategic initiatives with low friction."
    ),
    "4/10 Axis (Kendra Action)": (
        "Focuses heavily on balancing internal security (home/foundations) with"
        " external output (career/reputation)."
    ),
    "5/9 Axis (Trikona Prosperity)": (
        "Highly auspicious period bringing creative flow, fortunate"
        " breakthroughs, intellectual clarity, and alignment."
    ),
    "2/12 Axis (Dwirdwadasa)": (
        "Indicates higher financial churn, unexpected expenses, personal"
        " detachment, or long-distance shifts."
    ),
    "6/8 Axis (Shashtashtaka)": (
        "Transformational period requiring conflict management, health"
        " vigilance, and structural adjustments."
    ),
}

HOUSE_METADATA = [
    {
        "num": 1,
        "name": "1st (Lagna)",
        "domain": "Self, Physical Health, Vitality & Identity",
    },
    {
        "num": 2,
        "name": "2nd (Dhana)",
        "domain": "Accumulated Wealth, Speech & Family Assets",
    },
    {
        "num": 3,
        "name": "3rd (Vikrama)",
        "domain": "Courage, Initiatives, Siblings & Short Journeys",
    },
    {
        "num": 4,
        "name": "4th (Matri)",
        "domain": "Home, Peace of Mind, Property & Mother",
    },
    {
        "num": 5,
        "name": "5th (Putra)",
        "domain": "Intelligence, Creativity, Children & Speculation",
    },
    {
        "num": 6,
        "name": "6th (Ari)",
        "domain": "Debts, Disease, Obstacles & Daily Work Friction",
    },
    {
        "num": 7,
        "name": "7th (Yuvati)",
        "domain": "Partnerships, Marriage & Foreign Commerce",
    },
    {
        "num": 8,
        "name": "8th (Randhra)",
        "domain": "Longevity, Transformation, Sudden Events & Research",
    },
    {
        "num": 9,
        "name": "9th (Dharma)",
        "domain": "Higher Knowledge, Fortune, Father & Mentorship",
    },
    {
        "num": 10,
        "name": "10th (Karma)",
        "domain": "Career Status, Public Standing & Authority",
    },
    {
        "num": 11,
        "name": "11th (Labha)",
        "domain": "Gains, Income, Professional Network & Wish Fulfillment",
    },
    {
        "num": 12,
        "name": "12th (Vyaya)",
        "domain": "Expenses, Losses, Foreign Lands & Spiritual Solitude",
    },
]

# ---------------------------------------------------------------------
# SIDEBAR: BIRTH DETAILS INPUT
# ---------------------------------------------------------------------
st.sidebar.header("👤 Birth Details Input")
st.sidebar.caption("Enter birth parameters to generate chart context.")

user_name = st.sidebar.text_input("Full Name", value="Arun Singh")
dob = st.sidebar.date_input(
    "Date of Birth",
    value=datetime.date(1985, 6, 15),
    min_value=datetime.date(1920, 1, 1),
    max_value=datetime.date(2026, 12, 31),
)
tob = st.sidebar.time_input("Time of Birth (24h)", value=datetime.time(14, 30))
pob = st.sidebar.text_input("Place of Birth (City, Country)", value="Bengaluru, India")
tz = st.sidebar.selectbox(
    "Timezone Offset",
    ["UTC+05:30 (IST)", "UTC+00:00 (GMT)", "UTC-05:00 (EST)", "UTC-08:00 (PST)", "UTC+01:00 (CET)"],
    index=0
)

st.sidebar.divider()
st.sidebar.success("✅ Birth profile active")

# ---------------------------------------------------------------------
# MAIN LAYOUT & TABS
# ---------------------------------------------------------------------
st.title("🔮 Vedic Astrology Narrative & Ashtakavarga Engine")
st.caption(f"Active Profile: **{user_name}** | Born: **{dob.strftime('%d %b %Y')}** at **{tob.strftime('%H:%M')}** ({pob})")

tab_profile, tab_dasha, tab_ashtak = st.tabs([
    "👤 Birth Profile & Chart Specs",
    "📜 Dasha Narrative Analysis",
    "📊 Ashtakavarga Chart & Diagnostics"
])

# ---------------------------------------------------------------------
# TAB 1: BIRTH PROFILE & CHART SPECS
# ---------------------------------------------------------------------
with tab_profile:
    st.subheader("Natal Birth Data Summary")
    
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    col_p1.metric("Name", user_name)
    col_p2.metric("Date of Birth", dob.strftime("%d-%b-%Y"))
    col_p3.metric("Time of Birth", tob.strftime("%H:%M:%S"))
    col_p4.metric("Location", pob)

    st.divider()
    
    st.markdown("### 🪐 Ephemeris & Ayanamsha Configuration")
    col_e1, col_e2 = st.columns(2)
    
    with col_e1:
        ayanamsha = st.selectbox(
            "Ayanamsha System",
            ["Lahiri (Chitrapaksha)", "Raman", "Krishnamurti (KP)", "Tropical"],
            index=0
        )
        house_system = st.selectbox(
            "House Calculation System",
            ["Equal House (Rasi = Bhava)", "Sripati / Porphyry", "Placidus"],
            index=0
        )

    with col_e2:
        st.info(
            f"**Calculation Coordinates:** Latitude/Longitude auto-resolved for **{pob}**.\n\n"
            f"• **Selected Ayanamsha:** {ayanamsha}\n"
            f"• **House System:** {house_system}\n"
            f"• **Timezone:** {tz}"
        )

# ---------------------------------------------------------------------
# TAB 2: MAHADASHA & ANTARDASHA NARRATIVE
# ---------------------------------------------------------------------
with tab_dasha:
    st.subheader("Vimshottari Dasha Configuration")
    col1, col2 = st.columns([1, 1])

    planets = ["Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury", "Ketu", "Venus"]

    with col1:
        maha = st.selectbox("Select Mahadasha Lord (Major Period)", planets, index=3)
        antar = st.selectbox("Select Antardasha Lord (Sub Period)", planets, index=4)
        rel_options = list(RELATIONSHIP_DESCRIPTIONS.keys())
        rel = st.selectbox("Mutual House Relationship Axis", rel_options, index=1)

    with col2:
        st.markdown("### Operating Energy Dynamics")
        if "5/9" in rel or "3/11" in rel:
            st.success("✨ Harmonious & Growth-Oriented Period")
        elif "6/8" in rel or "2/12" in rel:
            st.warning("⚠ Transformational / High Friction Period")
        else:
            st.info("⚡ Action-Oriented Period")

        st.write(f"**Operating State for {user_name}:** **{maha}** Mahadasha with **{antar}** Antardasha.")
        st.caption(f"Focus centers on executing {antar}'s portfolio within {maha}'s overarching lifecycle boundaries.")

    st.divider()

    st.markdown(f"#### 1. Overarching Lifecycle Theme ({maha} Mahadasha)")
    st.info(DASHA_DESCRIPTIONS[maha])

    st.markdown(f"#### 2. Sub-Period Manifestation ({antar} Antardasha)")
    st.success(DASHA_DESCRIPTIONS[antar])

    st.markdown(f"#### 3. Structural Interplay ({rel})")
    st.write(RELATIONSHIP_DESCRIPTIONS[rel])

# ---------------------------------------------------------------------
# TAB 3: ASHTAKAVARGA PLOTLY CHART & DETAILED ANALYSIS
# ---------------------------------------------------------------------
with tab_ashtak:
    st.subheader("12-House Samudaya Ashtakavarga (SAV) Evaluation")

    default_sav = [30, 26, 28, 31, 29, 24, 27, 21, 32, 32, 35, 22]

    with st.expander("⚙ Adjust / Override SAV Scores for All 12 Houses", expanded=False):
        cols = st.columns(6)
        sav_scores = []
        for idx, h_info in enumerate(HOUSE_METADATA):
            col = cols[idx % 6]
            val = col.number_input(
                f"H{idx+1}: {h_info['name'].split()[0]}",
                min_value=0,
                max_value=56,
                value=default_sav[idx],
                key=f"house_{idx+1}",
            )
            sav_scores.append(val)

    # DataFrame for Plotly and Analysis
    df_sav = pd.DataFrame({
        "House": [h["name"] for h in HOUSE_METADATA],
        "House_Num": [h["num"] for h in HOUSE_METADATA],
        "SAV": sav_scores,
        "Domain": [h["domain"] for h in HOUSE_METADATA],
    })

    def classify_strength(score):
        if score >= 30:
            return "Strong (>=30)"
        elif score >= 28:
            return "Average (28-29)"
        else:
            return "Weak (<28)"

    df_sav["Strength"] = df_sav["SAV"].apply(classify_strength)

    color_map = {
        "Strong (>=30)": "#2E7D32",  # Green
        "Average (28-29)": "#0288D1",  # Blue
        "Weak (<28)": "#D32F2F",  # Red
    }

    # Plotly Chart
    fig = px.bar(
        df_sav,
        x="House",
        y="SAV",
        color="Strength",
        color_discrete_map=color_map,
        text="SAV",
        title=f"Samudaya Ashtakavarga Distribution for {user_name}",
        labels={"SAV": "SAV Points", "House": "House Number & Name"},
    )

    fig.add_hline(
        y=28,
        line_dash="dash",
        line_color="orange",
        annotation_text="Average Baseline (28 Pts)",
        annotation_position="top left",
    )

    fig.update_traces(textposition="outside")
    fig.update_layout(
        xaxis_tickangle=-30,
        yaxis=dict(range=[0, max(sav_scores) + 8 if sav_scores else 50]),
        height=450,
        legend_title_text="Strength Classification",
        margin=dict(l=20, r=20, t=50, b=20),
    )

    # Render Plotly Graph
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Detailed Analysis Section
    st.markdown("## 📊 Comprehensive Ashtakavarga Chart Analysis")
    st.caption("Detailed breakdown of house potentials, career dynamics, financial flows, and vitality indicators.")

    # 1. House-by-House Potentials
    st.markdown("### 1. House-by-House Potentials & Domain Strengths")

    display_df = df_sav[["House_Num", "House", "SAV", "Strength", "Domain"]].rename(
        columns={
            "House_Num": "House #",
            "House": "House Title",
            "SAV": "SAV Score",
            "Domain": "Life Domain & Focus Area",
        }
    )

    st.dataframe(
        display_df,
        column_config={
            "SAV Score": st.column_config.ProgressColumn(
                "SAV Score (Baseline: 28)",
                help="Average threshold is 28 points.",
                format="%d pts",
                min_value=0,
                max_value=56,
            ),
        },
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. Specific Domain Diagnostics
    st.markdown("### 2. Specific Domain Diagnostics")
    col_c, col_h = st.columns(2)

    sav_1 = sav_scores[0]
    sav_6 = sav_scores[5]
    sav_8 = sav_scores[7]
    sav_10 = sav_scores[9]
    sav_11 = sav_scores[10]
    sav_12 = sav_scores[11]

    # Career Diagnostics
    with col_c:
        st.markdown("#### 💼 Career & Wealth Architecture")
        c1, c2 = st.columns(2)
        c1.metric(
            "10th House Status",
            f"{sav_10} pts",
            "Strong" if sav_10 >= 28 else "Challenging",
        )
        c2.metric(
            "Gains Hierarchy",
            f"{sav_11} vs {sav_12}",
            "Optimal Flow" if sav_11 > sav_12 else "Leaking Value",
        )

        career_text = f"• **Career Momentum (10th House):** Holds **{sav_10} points**. "
        if sav_10 >= 30:
            career_text += "Strong innate backing for leadership, high visibility, and smooth execution."
        elif sav_10 >= 28:
            career_text += "Moderate stability; growth aligns steadily with consistent output."
        else:
            career_text += "Professional growth demands active strategy, upskilling, and careful relationship management."

        career_text += (
            f"\n\n• **Wealth Axis (11th vs 12th House):** 11th House (**{sav_11} pts**) vs 12th House (**{sav_12} pts**). "
        )
        if sav_11 > sav_10 and sav_11 > sav_12:
            career_text += "Meets the classical prosperity ratio (**11th > 10th > 12th**). Revenue generation comfortably exceeds overhead."
        else:
            career_text += "Financial leaks or high operational costs detected; savings require structured budget boundaries."

        st.info(career_text)

    # Health Diagnostics
    with col_h:
        st.markdown("#### 🩺 Physical Vitality & Resistance")
        h1, h2 = st.columns(2)
        h1.metric(
            "Immunity vs Stress",
            f"{sav_1} vs {sav_6}",
            "Robust Resilience" if sav_1 >= sav_6 else "Vulnerable",
        )
        h2.metric(
            "8th House Vulnerability",
            f"{sav_8} pts",
            "Controlled Risk" if sav_8 < 28 else "Elevated Risk",
        )

        health_text = (
            f"• **Vitality Baseline (1st vs 6th House):** Lagna holds **{sav_1} pts** vs 6th House **{sav_6} pts**. "
        )
        if sav_1 >= sav_6:
            health_text += "Constitutional immunity is strong. Body handles workload stress effectively and recovers quickly."
        else:
            health_text += "6th house exceeds Lagna; acute burnout, inflammation, or lifestyle fatigue can lower resilience."

        health_text += f"\n\n• **Transformational Pressure (8th House):** Holds **{sav_8} pts**. "
        if sav_8 >= 28:
            health_text += "Elevated score; monitor metabolic parameters and prioritize stress recovery."
        else:
            health_text += "Below threshold score; provides dynamic shield against unexpected physiological disruptions."

        st.warning(health_text)