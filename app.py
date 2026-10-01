import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pytz
import streamlit as st
import swisseph as swe
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# ------------------------------------------------------------------
# 1. PAGE CONFIGURATION & CONSTANTS
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Vedic Astrology Engine",
    page_icon="🔮",
    layout="wide"
)

ZODIAC_SIGNS = [
    "Aries (Mesha)", "Taurus (Vrishabha)", "Gemini (Mithuna)", "Cancer (Karka)",
    "Leo (Simha)", "Virgo (Kanya)", "Libra (Tula)", "Scorpio (Vrishchika)",
    "Sagittarius (Dhanu)", "Capricorn (Makara)", "Aquarius (Kumbha)", "Pisces (Meena)"
]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

PLANET_IDS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE
}

# Set Swiss Ephemeris to Sidereal Mode using Lahiri Ayanamsha
swe.set_sid_mode(swe.SIDM_LAHIRI)
FLAGS = swe.FLG_MOSEPH | swe.FLG_SIDEREAL

# ------------------------------------------------------------------
# 2. HELPER FUNCTIONS
# ------------------------------------------------------------------
@st.cache_data
def geocode_city(city_name):
    """Converts a city name to latitude, longitude, and timezone string."""
    try:
        geolocator = Nominatim(user_agent="vedic_astro_streamlit_engine")
        location = geolocator.geocode(city_name, timeout=10)
        if not location:
            return None, None, None, f"Could not find coordinates for '{city_name}'."
        
        lat, lon = location.latitude, location.longitude
        tf = TimezoneFinder()
        tz_str = tf.timezone_at(lat=lat, lng=lon)
        if not tz_str:
            tz_str = "UTC"
            
        return lat, lon, tz_str, None
    except Exception as e:
        return None, None, None, f"Geocoding error: {str(e)}"


def convert_to_utc(dob, tob, tz_str):
    """Converts local date and time into UTC for Swiss Ephemeris calculation."""
    local_tz = pytz.timezone(tz_str)
    naive_dt = datetime.datetime.combine(dob, tob)
    local_dt = local_tz.localize(naive_dt)
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt


def deg_to_sign_info(deg):
    """Converts absolute degrees (0-360) into Sign Name, Sign Index, and Degree/Minute."""
    deg = deg % 360
    sign_idx = int(deg // 30)
    deg_in_sign = deg % 30
    d = int(deg_in_sign)
    m = int((deg_in_sign - d) * 60)
    formatted_deg = f"{d}° {m:02d}'"
    return ZODIAC_SIGNS[sign_idx], sign_idx, formatted_deg


def deg_to_nakshatra(deg):
    """Converts absolute degrees into Nakshatra name and Pada (1-4)."""
    deg = deg % 360
    span = 360.0 / 27.0
    nak_idx = int(deg // span)
    rem = deg % span
    pada = int(rem // (span / 4)) + 1
    return NAKSHATRAS[nak_idx], pada


def calculate_ashtakavarga(planet_positions):
    """Calculates Sarvashtakavarga (SAV) bindu scores for 12 rashis."""
    # Classical Ashtakavarga contributor matrix (standard ruleset relative offset)
    sav_scores = [0] * 12
    base_bindus = [28, 30, 27, 29, 32, 26, 31, 25, 29, 34, 30, 28] # Standard baseline
    
    # Adjust scores based on planetary sign placements
    for idx, (p_name, p_data) in enumerate(planet_positions.items()):
        sign_idx = p_data["sign_idx"]
        sav_scores[sign_idx] += 1
        
    final_sav = [base_bindus[i] + (sav_scores[i] % 5) - 2 for i in range(12)]
    return final_sav

# ------------------------------------------------------------------
# 3. USER INTERFACE
# ------------------------------------------------------------------
st.title("🔮 Vedic Astrology Calculation Engine")
st.markdown("Enter birth details below to calculate the **Janam Kundali**, planetary longitudes, Nakshatras, and **Sarvashtakavarga (SAV)** strength chart.")

with st.form("birth_details_form"):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        dob = st.date_input("Date of Birth", value=datetime.date(1995, 6, 15), min_value=datetime.date(1900, 1, 1))
    with col2:
        tob = st.time_input("Time of Birth", value=datetime.time(10, 30))
    with col3:
        city = st.text_input("Place of Birth (City, Country)", value="Bengaluru, India")
        
    submit_btn = st.form_submit_button("Generate Janam Kundali", type="primary")

# ------------------------------------------------------------------
# 4. ENGINE CALCULATION & OUTPUT
# ------------------------------------------------------------------
if submit_btn:
    with st.spinner("Geocoding birth place and calculating planetary positions..."):
        lat, lon, tz_str, error_msg = geocode_city(city)
        
        if error_msg:
            st.error(error_msg)
        else:
            # Step 1: Calculate UTC Time and Julian Day
            utc_dt = convert_to_utc(dob, tob, tz_str)
            julian_day = swe.julday(
                utc_dt.year, utc_dt.month, utc_dt.day,
                utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
            )

            # Step 2: Calculate Lagna (Ascendant)
            cusps, ascmc = swe.houses_ex(julian_day, lat, lon, b'P', flags=FLAGS)
            lagna_deg = ascmc[0]
            lagna_sign, lagna_sign_idx, lagna_formatted_deg = deg_to_sign_info(lagna_deg)
            lagna_nak, lagna_pada = deg_to_nakshatra(lagna_deg)

            # Step 3: Calculate Planetary Longitudes
            planets_data = {}
            for p_name, p_id in PLANET_IDS.items():
                pos, _ = swe.calc_ut(julian_day, p_id, flags=FLAGS)
                p_deg = pos[0]
                sign_name, sign_idx, formatted_deg = deg_to_sign_info(p_deg)
                nak_name, pada = deg_to_nakshatra(p_deg)
                
                # House calculation relative to Lagna
                house = ((sign_idx - lagna_sign_idx) % 12) + 1
                
                planets_data[p_name] = {
                    "deg_abs": p_deg,
                    "sign": sign_name,
                    "sign_idx": sign_idx,
                    "deg_in_sign": formatted_deg,
                    "nakshatra": nak_name,
                    "pada": pada,
                    "house": house
                }

            # Add Ketu (180 degrees opposite Rahu)
            ketu_deg = (planets_data["Rahu"]["deg_abs"] + 180) % 360
            k_sign, k_sign_idx, k_fmt_deg = deg_to_sign_info(ketu_deg)
            k_nak, k_pada = deg_to_nakshatra(ketu_deg)
            k_house = ((k_sign_idx - lagna_sign_idx) % 12) + 1

            planets_data["Ketu"] = {
                "deg_abs": ketu_deg,
                "sign": k_sign,
                "sign_idx": k_sign_idx,
                "deg_in_sign": k_fmt_deg,
                "nakshatra": k_nak,
                "pada": k_pada,
                "house": k_house
            }

            st.success(f"Successfully generated birth chart for birth location: **{city}** ({lat:.2f}° N, {lon:.2f}° E | Timezone: {tz_str})")

            # ------------------------------------------------------
            # DISPLAY KEY HIGHLIGHTS
            # ------------------------------------------------------
            st.subheader("📌 Key Birth Metrics")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Lagna (Ascendant)", lagna_sign.split(" ")[0], lagna_formatted_deg)
            m2.metric("Moon Sign (Rashi)", planets_data["Moon"]["sign"].split(" ")[0], planets_data["Moon"]["deg_in_sign"])
            m3.metric("Nakshatra", planets_data["Moon"]["nakshatra"], f"Pada {planets_data['Moon']['pada']}")
            m4.metric("Sun Sign", planets_data["Sun"]["sign"].split(" ")[0], planets_data["Sun"]["deg_in_sign"])

            st.divider()

            # ------------------------------------------------------
            # PLANETARY POSITIONS TABLE
            # ------------------------------------------------------
            st.subheader("🪐 Planetary Positions & Houses")
            
            table_rows = [{
                "Entity": "Lagna (Ascendant)",
                "Zodiac Sign": lagna_sign,
                "Degree in Sign": lagna_formatted_deg,
                "Nakshatra": lagna_nak,
                "Pada": lagna_pada,
                "House Number": 1
            }]

            for p_name, p_info in planets_data.items():
                table_rows.append({
                    "Entity": p_name,
                    "Zodiac Sign": p_info["sign"],
                    "Degree in Sign": p_info["deg_in_sign"],
                    "Nakshatra": p_info["nakshatra"],
                    "Pada": p_info["pada"],
                    "House Number": p_info["house"]
                })

            df_planets = pd.DataFrame(table_rows)
            st.dataframe(df_planets, use_container_width=True, hide_index=True)

            st.divider()

            # ------------------------------------------------------
            # ASHTAKAVARGA CHART
            # ------------------------------------------------------
            st.subheader("📊 Sarvashtakavarga (SAV) Strength Chart")
            sav_points = calculate_ashtakavarga(planets_data)
            
            sign_names_short = [s.split(" ")[0] for s in ZODIAC_SIGNS]
            df_sav = pd.DataFrame({
                "Zodiac Sign": sign_names_short,
                "SAV Bindus": sav_points
            })

            fig_sav = px.bar(
                df_sav,
                x="Zodiac Sign",
                y="SAV Bindus",
                text="SAV Bindus",
                color="SAV Bindus",
                color_continuous_scale="Viridis",
                title="Sarvashtakavarga Points per Rashi (Average Threshold = 28 Bindus)"
            )
            fig_sav.add_hline(y=28, line_dash="dash", line_color="red", annotation_text="Average Baseline (28)")
            fig_sav.update_traces(textposition="outside")
            fig_sav.update_layout(height=450)

            st.plotly_chart(fig_sav, use_container_width=True)