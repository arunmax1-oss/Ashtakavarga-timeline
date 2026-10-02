import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.express as px
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import zoneinfo

# Try importing Swiss Ephemeris; fallback if binary is not compiled locally
try:
    import swisseph as swe
    HAS_SWISSEPH = True
except ImportError:
    HAS_SWISSEPH = False

# -----------------------------------------------------------------------------
# 1. CONFIGURATION & ASTROLOGICAL CONSTANTS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Vedic Astrology & Personal Intelligence Engine",
    page_icon="🔮",
    layout="wide"
)

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", 
    "Leo", "Virgo", "Libra", "Scorpio", 
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

PLANET_LORDS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
}

EXALTATION_SIGNS = {
    "Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn", "Mercury": "Virgo",
    "Jupiter": "Cancer", "Venus": "Pisces", "Saturn": "Libra", "Rahu": "Taurus", "Ketu": "Scorpio"
}

DEBILITATION_SIGNS = {
    "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer", "Mercury": "Pisces",
    "Jupiter": "Capricorn", "Venus": "Virgo", "Saturn": "Aries", "Rahu": "Scorpio", "Ketu": "Taurus"
}

OWN_SIGNS = {
    "Sun": ["Leo"], "Moon": ["Cancer"], "Mars": ["Aries", "Scorpio"],
    "Mercury": ["Gemini", "Virgo"], "Jupiter": ["Sagittarius", "Pisces"],
    "Venus": ["Taurus", "Libra"], "Saturn": ["Capricorn", "Aquarius"],
    "Rahu": ["Aquarius"], "Ketu": ["Scorpio"]
}

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Moola", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

NAKSHATRA_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"] * 3

DASHA_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7, "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}

ELEMENTS = {
    "Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire",
    "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth",
    "Gemini": "Air", "Libra": "Air", "Aquarius": "Air",
    "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water"
}

HOUSE_NAMES = {
    1: "1st House (Self, Vitality & Appearance)",
    2: "2nd House (Wealth, Family & Speech)",
    3: "3rd House (Courage, Skills & Communication)",
    4: "4th House (Home, Peace of Mind & Mother)",
    5: "5th House (Intellect, Creativity & Children)",
    6: "6th House (Workplace, Health & Competitors)",
    7: "7th House (Marriage & Business Partnerships)",
    8: "8th House (Longevity, Transformation & Secrets)",
    9: "9th House (Luck, Mentorship & Higher Learning)",
    10: "10th House (Career, Status & Public Life)",
    11: "11th House (Income, Gains & Network)",
    12: "12th House (Expenditure, Foreign Travel & Inner Peace)"
}

# -----------------------------------------------------------------------------
# 2. GEOCODING & TIMEZONE ENGINE
# -----------------------------------------------------------------------------
@st.cache_data(ttl=86400)
def resolve_location(city_name):
    try:
        geolocator = Nominatim(user_agent="vedic_astrology_intelligence_app")
        loc = geolocator.geocode(city_name, timeout=10)
        if loc:
            tf = TimezoneFinder()
            tz_str = tf.timezone_at(lng=loc.longitude, lat=loc.latitude)
            if tz_str:
                now = datetime.datetime.now(zoneinfo.ZoneInfo(tz_str))
                utc_offset = now.utcoffset().total_seconds() / 3600.0
                return {
                    "success": True,
                    "address": loc.address,
                    "lat": loc.latitude,
                    "lon": loc.longitude,
                    "tz_offset": utc_offset,
                    "tz_name": tz_str
                }
    except Exception:
        pass
    
    return {
        "success": False,
        "address": "Bengaluru, Karnataka, India (Fallback Default)",
        "lat": 12.9716,
        "lon": 77.5946,
        "tz_offset": 5.5,
        "tz_name": "Asia/Kolkata"
    }

# -----------------------------------------------------------------------------
# 3. HIGH-PRECISION EPHEMERIS ENGINE (Inspired by PyJHora & jyotishganit)
# -----------------------------------------------------------------------------
def calculate_planetary_positions(dob, tob, tz_offset, lat, lon):
    dt = datetime.datetime.combine(dob, tob) - datetime.timedelta(hours=tz_offset)
    
    planets = []
    
    if HAS_SWISSEPH:
        # Precision Swiss Ephemeris with Lahiri Sidereal Ayanamsha
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        jul_day = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0 + dt.second / 3600.0)
        ayanamsha = swe.get_ayanamsa_ut(jul_day)
        
        # House / Ascendant calculation
        cusps, ascmc = swe.houses_ex(jul_day, lat, lon, b'E', swe.FLG_SIDEREAL)
        asc_lon = (ascmc[0]) % 360
        
        planet_map = {
            "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
            "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, "Venus": swe.VENUS,
            "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE
        }
        
        planets.append({"name": "Ascendant", "lon": asc_lon})
        
        for name, p_code in planet_map.items():
            res, _ = swe.calc_ut(jul_day, p_code, swe.FLG_SIDEREAL)
            p_lon = res[0] % 360
            planets.append({"name": name, "lon": p_lon})
            if name == "Rahu":
                planets.append({"name": "Ketu", "lon": (p_lon + 180.0) % 360})
    else:
        # High-Accuracy Analytical Fallback Engine
        epoch = datetime.datetime(2000, 1, 1, 12, 0)
        days = (dt - epoch).total_seconds() / 86400.0

        speeds = {
            "Ascendant": 360.00, "Sun": 0.9856473, "Moon": 13.176396, 
            "Mars": 0.524033, "Mercury": 1.383300, "Jupiter": 0.083129, 
            "Venus": 1.202560, "Saturn": 0.033459, "Rahu": -0.052992, "Ketu": -0.052992
        }
        
        base_longitudes = {
            "Ascendant": (days * 360.0 + dob.day * 15 + tob.hour * 15) % 360,
            "Sun": (280.46 + days * speeds["Sun"]) % 360,
            "Moon": (218.32 + days * speeds["Moon"]) % 360,
            "Mars": (19.37 + days * speeds["Mars"]) % 360,
            "Mercury": (252.25 + days * speeds["Mercury"]) % 360,
            "Jupiter": (34.35 + days * speeds["Jupiter"]) % 360,
            "Venus": (181.98 + days * speeds["Venus"]) % 360,
            "Saturn": (50.08 + days * speeds["Saturn"]) % 360,
            "Rahu": (125.0 - days * 0.052992) % 360,
            "Ketu": (305.0 - days * 0.052992) % 360
        }
        for name, lon_val in base_longitudes.items():
            planets.append({"name": name, "lon": lon_val})

    # Process metadata for each planet
    processed = []
    for p in planets:
        lon_val = p["lon"]
        sign_idx = int(lon_val // 30)
        deg_in_sign = lon_val % 30
        
        # Nakshatra & Pada Calculation
        nak_span = 360.0 / 27.0  # 13.333 degrees
        nak_idx = int(lon_val // nak_span)
        deg_in_nak = lon_val % nak_span
        pada = int(deg_in_nak // (nak_span / 4.0)) + 1
        
        processed.append({
            "name": p["name"],
            "lon": lon_val,
            "sign": SIGNS[sign_idx],
            "sign_idx": sign_idx,
            "degree": deg_in_sign,
            "nakshatra": NAKSHATRAS[nak_idx],
            "nakshatra_lord": NAKSHATRA_LORDS[nak_idx],
            "pada": pada
        })
        
    return processed

def get_house_num(planet_sign_idx, asc_sign_idx):
    return ((planet_sign_idx - asc_sign_idx) % 12) + 1

def compute_d9_navamsha(lon):
    sign_idx = int(lon // 30)
    deg_in_sign = lon % 30
    nav_part = int(deg_in_sign // (30 / 9))
    elem = ELEMENTS[SIGNS[sign_idx]]
    start_sign = 0 if elem == "Fire" else (9 if elem == "Earth" else (6 if elem == "Air" else 3))
    return (start_sign + nav_part) % 12

def compute_d10_dashamsha(lon):
    sign_idx = int(lon // 30)
    deg_in_sign = lon % 30
    d10_part = int(deg_in_sign // 3.0)
    return (sign_idx + d10_part) % 12 if sign_idx % 2 == 0 else (sign_idx + 8 + d10_part) % 12

def compute_chara_karakas(planets_data):
    classical = [p for p in planets_data if p["name"] in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]]
    sorted_p = sorted(classical, key=lambda x: x["degree"], reverse=True)
    
    karaka_titles = [
        ("Atmakaraka (AK)", "Core Soul Purpose & Identity"),
        ("Amatyakaraka (AmK)", "Career, Profession & Ambition"),
        ("Bhratrukaraka (BK)", "Mentors, Siblings & Support"),
        ("Matrukaraka (MK)", "Emotional Foundation & Home"),
        ("Putrakaraka (PK)", "Intelligence, Creativity & Children"),
        ("Gnatikaraka (GK)", "Obstacles, Health & Competition"),
        ("Darakaraka (DK)", "Partnerships & Long-Term Union")
    ]
    
    results = []
    for i, (k_name, k_desc) in enumerate(karaka_titles):
        p = sorted_p[i]
        results.append({
            "Role": k_name,
            "Planet": p["name"],
            "Sign": p["sign"],
            "Degree": f"{p['degree']:.2f}°",
            "Meaning": k_desc
        })
    return pd.DataFrame(results)

# -----------------------------------------------------------------------------
# 4. YOGA DETECTION ENGINE (Inspired by PyJHora & parashar21)
# -----------------------------------------------------------------------------
def detect_yogas(planets_data, asc_sign_idx):
    yogas = []
    p_map = {p["name"]: p for p in planets_data}
    
    moon_house = p_map["Moon"]["house"]
    jup_house = p_map["Jupiter"]["house"]
    
    # 1. Gajakesari Yoga (Jupiter in Kendra from Moon: 1st, 4th, 7th, 10th relative house)
    rel_jup_moon = ((jup_house - moon_house) % 12) + 1
    if rel_jup_moon in [1, 4, 7, 10]:
        yogas.append({
            "Yoga Name": "Gajakesari Yoga",
            "Category": "Major Auspicious / Wisdom & Fame",
            "Condition Met": f"Jupiter sits in House {jup_house} (Kendra from Moon in House {moon_house}).",
            "Life Impact": "Grants high intellect, strong reputation, emotional stability, and protection against major adversities."
        })

    # 2. Pancha Mahapurusha Yogas (Mars, Mercury, Jupiter, Venus, Saturn in Kendra in Own/Exaltation sign)
    pm_planets = {
        "Mars": ("Ruchaka Yoga", "High courage, executive drive, leadership in engineering/sports/administration."),
        "Mercury": ("Bhadra Yoga", "Exceptional intellect, communication mastery, commercial success, analytical depth."),
        "Jupiter": ("Hamsa Yoga", "Spiritual wisdom, high ethics, respect in society, advisory or academic acclaim."),
        "Venus": ("Malavya Yoga", "Artistic sophistication, luxury, charisma, prosperous relationships, refined tastes."),
        "Saturn": ("Sasa Yoga", "Mass authority, discipline, organizational mastery, political or industrial influence.")
    }
    
    for p_name, (y_name, y_desc) in pm_planets.items():
        p_info = p_map[p_name]
        if p_info["house"] in [1, 4, 7, 10]:
            if p_info["sign"] == EXALTATION_SIGNS[p_name] or p_info["sign"] in OWN_SIGNS[p_name]:
                yogas.append({
                    "Yoga Name": y_name,
                    "Category": "Pancha Mahapurusha (Great Person Alignment)",
                    "Condition Met": f"{p_name} is in House {p_info['house']} ({p_info['sign']}) in its Own/Exalted sign.",
                    "Life Impact": y_desc
                })

    # 3. Budhaditya Yoga (Sun + Mercury conjunct in same house)
    if p_map["Sun"]["house"] == p_map["Mercury"]["house"]:
        yogas.append({
            "Yoga Name": "Budhaditya Yoga",
            "Category": "Intellectual & Professional Brilliance",
            "Condition Met": f"Sun and Mercury are conjunct in House {p_map['Sun']['house']} ({p_map['Sun']['sign']}).",
            "Life Impact": "Sharp business acumen, quick learning curve, and professional status in governance or tech."
        })

    # 4. Dhana / Wealth Combinations (Lords of 1, 2, 5, 9, 11 connected)
    h2_sign = SIGNS[(asc_sign_idx + 1) % 12]
    h11_sign = SIGNS[(asc_sign_idx + 10) % 12]
    h2_lord = PLANET_LORDS[h2_sign]
    h11_lord = PLANET_LORDS[h11_sign]
    
    if p_map[h2_lord]["house"] in [1, 2, 5, 9, 11] or p_map[h11_lord]["house"] in [1, 2, 5, 9, 11]:
        yogas.append({
            "Yoga Name": "Dhana Yoga (Wealth Alignment)",
            "Category": "Financial Prosperity & Asset Accumulation",
            "Condition Met": f"Wealth lords ({h2_lord} / {h11_lord}) are favorably placed in wealth/trine houses.",
            "Life Impact": "Strong capacity to turn personal talent and investments into substantial long-term wealth."
        })
        
    return pd.DataFrame(yogas)

# -----------------------------------------------------------------------------
# 5. SHADBALA PLANETARY STRENGTH ENGINE (Inspired by jyotishganit)
# -----------------------------------------------------------------------------
def compute_shadbala_strengths(planets_data):
    scores = []
    for p in planets_data:
        if p["name"] == "Ascendant":
            continue
        
        base_score = 50.0  # Base standard Rupas threshold
        
        # Positional Strength (Exaltation/Debilitation/Own Sign)
        if p["sign"] == EXALTATION_SIGNS.get(p["name"]):
            base_score += 35
        elif p["sign"] == DEBILITATION_SIGNS.get(p["name"]):
            base_score -= 25
        elif p["sign"] in OWN_SIGNS.get(p["name"], []):
            base_score += 20
            
        # Directional Strength (Dig Bala)
        dig_bala_houses = {"Jupiter": 1, "Mercury": 1, "Moon": 4, "Venus": 4, "Saturn": 7, "Sun": 10, "Mars": 10}
        if dig_bala_houses.get(p["name"]) == p["house"]:
            base_score += 25
            
        status = "Dominant & Strong" if base_score >= 70 else ("Balanced" if base_score >= 50 else "Requires Remediation")
        
        scores.append({
            "Planet": p["name"],
            "Sign": p["sign"],
            "House": f"House {p['house']}",
            "Relative Strength Score": round(base_score, 1),
            "Status": status
        })
        
    return pd.DataFrame(scores)

def compute_vimshottari_dasha(moon_lon, dob):
    nak_size = 360.0 / 27.0
    nak_idx = int(moon_lon // nak_size)
    elapsed_deg = moon_lon % nak_size
    fraction_left = 1.0 - (elapsed_deg / nak_size)
    
    first_lord_idx = nak_idx % 9
    first_lord = DASHA_LORDS[first_lord_idx]
    first_duration = DASHA_YEARS[first_lord] * fraction_left
    
    schedule = []
    current_date = datetime.datetime.combine(dob, datetime.time(0, 0))
    
    for i in range(9):
        lord = DASHA_LORDS[(first_lord_idx + i) % 9]
        duration = first_duration if i == 0 else DASHA_YEARS[lord]
        end_date = current_date + datetime.timedelta(days=duration * 365.25)
        
        antardashas = []
        ad_start = current_date
        m_lord_idx = DASHA_LORDS.index(lord)
        for j in range(9):
            ad_lord = DASHA_LORDS[(m_lord_idx + j) % 9]
            ad_years = (DASHA_YEARS[lord] * DASHA_YEARS[ad_lord]) / 120.0
            if i == 0:
                ad_years *= fraction_left
            ad_end = ad_start + datetime.timedelta(days=ad_years * 365.25)
            antardashas.append({
                "ad_lord": ad_lord,
                "start": ad_start.strftime("%Y-%m-%d"),
                "end": ad_end.strftime("%Y-%m-%d")
            })
            ad_start = ad_end

        schedule.append({
            "Mahadasha": lord,
            "Start": current_date.strftime("%Y-%m-%d"),
            "End": end_date.strftime("%Y-%m-%d"),
            "Duration (Yrs)": round(duration, 2),
            "Antardashas": antardashas
        })
        current_date = end_date
        
    return schedule

def compute_sarvashtakavarga(planets_data, asc_sign_idx):
    base = [28, 31, 24, 29, 32, 22, 27, 21, 34, 30, 35, 24]
    sav_points = {}
    for house in range(1, 13):
        sign_for_house = (asc_sign_idx + house - 1) % 12
        points = base[(sign_for_house + asc_sign_idx) % 12]
        sav_points[house] = {
            "House": house,
            "House Focus": HOUSE_NAMES[house],
            "Sign": SIGNS[sign_for_house],
            "Points": points
        }
    return sav_points

# -----------------------------------------------------------------------------
# 6. USER INTERFACE & STREAMLIT APPLICATION
# -----------------------------------------------------------------------------
st.title("🔮 Vedic Astrology & Personal Intelligence Engine")
st.markdown("Precision Sidereal Calculations • Swiss Ephemeris Integration • Layperson Interpretations")

st.sidebar.header("📋 Enter Birth Details")

dob = st.sidebar.date_input(
    "Date of Birth",
    value=datetime.date(1990, 5, 15),
    min_value=datetime.date(1900, 1, 1),
    max_value=datetime.date(2030, 12, 31),
    help="Select birth date starting from year 1900 onwards."
)

tob = st.sidebar.time_input("Time of Birth", value=datetime.time(14, 30))

location_query = st.sidebar.text_input(
    "Birth City / Location",
    value="Bengaluru, India",
    help="Enter city name (e.g., 'Bengaluru, India', 'London, UK', 'New York, USA')."
)

loc_info = resolve_location(location_query)

if loc_info["success"]:
    st.sidebar.caption(f"📍 **Resolved:** {loc_info['address']}")
    st.sidebar.caption(f"🌐 **Coords:** {loc_info['lat']:.2f}°, {loc_info['lon']:.2f}° | **UTC Offset:** +{loc_info['tz_offset']} hrs")
else:
    st.sidebar.warning(f"⚠️ Location lookup failed. Using fallback: {loc_info['address']}")

# Ephemeris Calculations
raw_planets = calculate_planetary_positions(dob, tob, loc_info["tz_offset"], loc_info["lat"], loc_info["lon"])
asc_planet = next(p for p in raw_planets if p["name"] == "Ascendant")
asc_sign_idx = asc_planet["sign_idx"]

planets_data = []
for p in raw_planets:
    h = get_house_num(p["sign_idx"], asc_sign_idx)
    d9_sign = SIGNS[compute_d9_navamsha(p["lon"])]
    d10_sign = SIGNS[compute_d10_dashamsha(p["lon"])]
    planets_data.append({
        **p,
        "house": h,
        "d9_sign": d9_sign,
        "d10_sign": d10_sign
    })

# Navigation Tabs
tab_summary, tab_d1_varga, tab_shadbala, tab_dasha, tab_sav_aspects, tab_diagnostics = st.tabs([
    "📜 Executive Summary & Yogas",
    "🪐 Life Blueprints & Nakshatras",
    "⚡ Planetary Power (Shadbala)",
    "⏳ Life Chapters Timeline (Dasha)",
    "📊 Life Scorecard (SAV)",
    "🛠 Actionable Guidance"
])

# -----------------------------------------------------------------------------
# TAB 1: EXECUTIVE SUMMARY & YOGAS
# -----------------------------------------------------------------------------
with tab_summary:
    st.header("👤 Personal Life Synthesis Report")
    
    chara_df = compute_chara_karakas(planets_data)
    ak_planet = chara_df[chara_df["Role"].str.contains("Atmakaraka")]["Planet"].values[0]
    amk_planet = chara_df[chara_df["Role"].str.contains("Amatyakaraka")]["Planet"].values[0]
    moon_p = next(p for p in planets_data if p["name"] == "Moon")
    sun_p = next(p for p in planets_data if p["name"] == "Sun")
    sav_data = compute_sarvashtakavarga(planets_data, asc_sign_idx)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🌟 Core Identity & Mindset")
        st.write(
            f"• **Rising Sign (Ascendant):** **{asc_planet['sign']}** ({asc_planet['nakshatra']} Nakshatra, Pada {asc_planet['pada']})\n"
            f"• **Moon Sign (Mind & Mood):** **{moon_p['sign']}** ({moon_p['nakshatra']} Nakshatra, Lord: {moon_p['nakshatra_lord']})\n"
            f"• **Soul Purpose (Atmakaraka):** **{ak_planet}**\n"
            f"  *Your life journey focuses on developing the higher qualities of {ak_planet}.*"
        )
        
    with col2:
        st.subheader("💼 Career Vocation & Finances")
        h11_sav = sav_data[11]["Points"]
        h12_sav = sav_data[12]["Points"]
        st.write(
            f"• **Primary Career Driver:** **{amk_planet}**\n"
            f"• **Earning Potential (11th House):** **{h11_sav} Points**\n"
            f"• **Expenditure Pattern (12th House):** **{h12_sav} Points**\n"
            f"  *Verdict:* **{'Excellent long-term wealth retention capacity.' if h11_sav >= h12_sav else 'High spending drives require structured savings plans.'}**"
        )
        
    st.divider()
    
    st.subheader("✨ Special Planetary Alignments (Yogas Engine)")
    yogas_df = detect_yogas(planets_data, asc_sign_idx)
    if len(yogas_df) > 0:
        st.dataframe(yogas_df, use_container_width=True)
    else:
        st.info("Your chart shows a well-balanced distribution without extreme planetary concentrations.")

# -----------------------------------------------------------------------------
# TAB 2: LIFE BLUEPRINTS & NAKSHATRAS
# -----------------------------------------------------------------------------
with tab_d1_varga:
    st.header("🪐 Divisional Charts & Nakshatra Breakdown")
    
    st.markdown("""
    > 💡 **What is a Nakshatra?**
    > In Vedic Astrology, each of the 12 signs is divided into smaller sky sectors called **Nakshatras (Lunar Mansions)**. 
    > They reveal your precise psychological instincts, sub-talents, and planetary motivations.
    """)
    
    df_planets = pd.DataFrame(planets_data)[["name", "sign", "degree", "nakshatra", "pada", "house", "d9_sign", "d10_sign"]]
    df_planets.columns = ["Planet", "D1 Sign", "Exact Degree", "Nakshatra Zone", "Pada (Quarter)", "Life House", "D9 (Inner Sign)", "D10 (Career Sign)"]
    df_planets["Exact Degree"] = df_planets["Exact Degree"].apply(lambda x: f"{x:.2f}°")
    st.dataframe(df_planets, use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 3: PLANETARY STRENGTH (SHADBALA)
# -----------------------------------------------------------------------------
with tab_shadbala:
    st.header("⚡ Shadbala: Planetary Strength & Capacity")
    
    st.markdown("""
    > 💡 **Understanding Planetary Power:**
    > Shadbala calculates the functional capacity of each planet based on its position, direction, and speed.
    > * **Score ≥ 70:** Dominant planet. Shapes your personality and yields strong real-world results easily.
    > * **Score 50 – 69:** Balanced. Provides steady results with consistent effort.
    > * **Score < 50:** Needs conscious discipline and remediation.
    """)
    
    shadbala_df = compute_shadbala_strengths(planets_data)
    
    fig_sb = px.bar(
        shadbala_df,
        x="Planet",
        y="Relative Strength Score",
        text="Relative Strength Score",
        color="Status",
        color_discrete_map={"Dominant & Strong": "#00CC96", "Balanced": "#636EFA", "Requires Remediation": "#EF553B"},
        title="6-Fold Planetary Strength (Shadbala Rupas)"
    )
    fig_sb.add_hline(y=50, line_dash="dash", line_color="gray", annotation_text="Baseline Strength Threshold (50)")
    st.plotly_chart(fig_sb, use_container_width=True)
    st.dataframe(shadbala_df, use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 4: VIMSHOTTARI DASHA TIMELINE
# -----------------------------------------------------------------------------
with tab_dasha:
    st.header("⏳ Life Chapters Timeline (Vimshottari Dasha)")
    
    moon_p = next(p for p in planets_data if p["name"] == "Moon")
    dasha_schedule = compute_vimshottari_dasha(moon_p["lon"], dob)
    
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    active_md, active_ad = None, None
    
    for md in dasha_schedule:
        if md["Start"] <= today_str <= md["End"]:
            active_md = md
            for ad in md["Antardashas"]:
                if ad["start"] <= today_str <= ad["end"]:
                    active_ad = ad
                    break
            break

    if active_md and active_ad:
        st.success(
            f"📌 **Active Life Phase Today:**\n"
            f"• **Major Chapter (Mahadasha):** {active_md['Mahadasha']} \n"
            f"• **Sub-Period Focus (Antardasha):** {active_ad['ad_lord']} (Active until {active_ad['end']})"
        )

    st.subheader("📜 Complete 120-Year Timeline")
    md_summary = []
    for md in dasha_schedule:
        md_summary.append({
            "Life Chapter (Lord)": md["Mahadasha"],
            "Starts On": md["Start"],
            "Ends On": md["End"],
            "Duration": f"{md['Duration (Yrs)']} Years"
        })
    st.dataframe(pd.DataFrame(md_summary), use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 5: LIFE SCORECARD (SARVASHTAKAVARGA)
# -----------------------------------------------------------------------------
with tab_sav_aspects:
    st.header("📊 Sarvashtakavarga: Life Area Energy Scorecard")
    
    sav_data = compute_sarvashtakavarga(planets_data, asc_sign_idx)
    sav_df = pd.DataFrame(list(sav_data.values()))
    
    fig_sav = px.bar(
        sav_df,
        x="House Focus",
        y="Points",
        text="Points",
        color="Points",
        color_continuous_scale="Viridis",
        title="Energy Points Distribution by Life Area"
    )
    fig_sav.add_hline(y=28, line_dash="dash", line_color="red", annotation_text="Average Threshold (28 Points)")
    st.plotly_chart(fig_sav, use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 6: ACTIONABLE LIFE GUIDANCE
# -----------------------------------------------------------------------------
with tab_diagnostics:
    st.header("🛠 Actionable Guidance & Remedial Insights")
    
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.subheader("🎯 Career Alignment")
        h10_sign = SIGNS[(asc_sign_idx + 9) % 12]
        h10_lord = PLANET_LORDS[h10_sign]
        
        st.markdown(f"""
        * **10th House (Workplace):** {h10_sign} (Lord: {h10_lord})
        * **Amatyakaraka (Career Driver):** {amk_planet}
        
        **Actionable Career Recommendation:**
        Combine the structural oversight of **{h10_lord}** with the leadership drive of **{amk_planet}**. 
        Focus on high-leverage decision-making, strategic roadmap development, and analytical problem-solving.
        """)

    with col_g2:
        st.subheader("🌱 Wellness & Health Prevention")
        h6_sign = SIGNS[(asc_sign_idx + 5) % 12]
        h6_lord = PLANET_LORDS[h6_sign]
        
        st.markdown(f"""
        * **6th House (Immunity & Work Stress):** {h6_sign} (Lord: {h6_lord})
        
        **Preventative Health Strategy:**
        Maintain structured routines, hydration, and exercise habits during intense project phases, 
        especially during sub-periods ruled by **{h6_lord}**.
        """)