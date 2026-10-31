"""Vedic Astrology & Ashtakavarga Engine: entry point.

This file draws the sidebar (birth details), computes the chart once per run, shows
the header, and hands over to the selected page in app_pages/. Only the selected page is computed.
All calculations live in vedic/; shared helpers and cached functions in ui/common.py.
"""
import datetime as dt
import zoneinfo

import streamlit as st

from ui.common import cached_geocode, cached_sensitivity, compute_core, fmt_date
from vedic import narratives as nar
from vedic import remedies as rem
from vedic.ashtakavarga import sav_by_house
from vedic.constants import AYANAMSHAS
from vedic.dasha import active_periods
from vedic.sensitivity import warning
from vedic.transits import utc_now

st.set_page_config(page_title="Vedic Astrology & Ashtakavarga Engine", page_icon="🔮", layout="wide")


# --------------------------------------------------------------------------------------
# Sidebar field memory
# --------------------------------------------------------------------------------------
PROFILE_KEYS = {"name": "k_name", "dob": "k_dob", "tob": "k_tob", "place": "k_place", "manual": "k_manual",
                "lat": "k_lat", "lon": "k_lon", "tz": "k_tz"}
DEFAULT_PROFILE = {"name": "", "dob": dt.date(1985, 6, 15), "tob": dt.time(14, 30), "place": "Bengaluru, India",
                   "manual": False, "lat": 12.9716, "lon": 77.5946, "tz": "Asia/Kolkata"}


def load_profile(profile):
    """Start the sidebar fields from `profile`. Bumping the version gives every field a fresh key."""
    st.session_state["_prof"] = dict(profile)
    st.session_state["_ver"] = st.session_state.get("_ver", 0) + 1


def field(name):
    """(key, starting value) for a sidebar field. Values live in our own copy (_prof) because Streamlit
    forgets a widget's value while it is hidden, e.g. the manual coordinates."""
    return {"key": f"{PROFILE_KEYS[name]}_{st.session_state['_ver']}", "value": st.session_state["_prof"][name]}


def remember(name, value):
    st.session_state["_prof"][name] = value
    return value


if "_prof" not in st.session_state:
    load_profile(DEFAULT_PROFILE)


# --------------------------------------------------------------------------------------
# Sidebar: birth details
# --------------------------------------------------------------------------------------
st.sidebar.header("👤 Birth Details")
user_name = remember("name", st.sidebar.text_input("Name", placeholder="Optional", **field("name")))
dob = remember("dob", st.sidebar.date_input("Date of Birth", min_value=dt.date(1900, 1, 1), max_value=dt.date.today(),
                                            format="DD/MM/YYYY", **field("dob")))
tob = remember("tob", st.sidebar.time_input("Time of Birth (24h, local)", step=60, **field("tob")))
place = remember("place", st.sidebar.text_input("Place of Birth", **field("place"),
                                                help="City and country, e.g. 'Chennai, India' or 'London, UK'."))
manual = remember("manual", st.sidebar.checkbox("Enter coordinates manually", **field("manual"),
                                                help="Use if the place lookup fails."))

if manual:
    c1, c2 = st.sidebar.columns(2)
    lat = remember("lat", c1.number_input("Latitude", min_value=-90.0, max_value=90.0, format="%.4f",
                                          **field("lat")))
    lon = remember("lon", c2.number_input("Longitude", min_value=-180.0, max_value=180.0, format="%.4f",
                                          **field("lon")))
    zones = sorted(zoneinfo.available_timezones())
    tz_field = field("tz")
    tz_name = remember("tz", st.sidebar.selectbox("Time zone", zones, key=tz_field["key"],
                                                  index=zones.index(tz_field["value"])))
    address = f"{lat:.4f}, {lon:.4f}"
else:
    loc = cached_geocode(place.strip()) if place.strip() else None
    if not loc:
        st.sidebar.error("Couldn't find that place. Try 'City, Country', or tick *Enter coordinates manually*.")
        st.stop()
    lat, lon, tz_name, address = loc["lat"], loc["lon"], loc["tz_name"], loc["address"]
    st.session_state["_prof"].update(lat=lat, lon=lon, tz=tz_name)  # pre-fills the manual fields if ticked later

with st.sidebar.expander("⚙ Calculation settings"):
    ayanamsha = st.selectbox("Ayanamsha", AYANAMSHAS, index=0)
    true_node = st.radio("Rahu/Ketu", ["Mean node", "True node"], horizontal=True) == "True node"
    st.caption("Houses: whole sign (Rasi = Bhava); Sripati Bhava Chalit is on the Houses page. "
                   "Ephemeris: Swiss Ephemeris (Moshier).")

with st.sidebar.expander("📍 Where you are now"):
    here = st.text_input("Current city", key="here_place_input", placeholder="Leave blank to use the birth place",
                         help="Used for sunrise, Rahu Kalam and the dates in the Week, Month, Planner and Job pages.")
    here_loc = cached_geocode(here.strip()) if here.strip() else None
    if here.strip() and not here_loc:
        st.warning("Couldn't find that place; using the birth place.")

chart, av, schedule, sb = compute_core(dob, tob, lat, lon, tz_name, ayanamsha, true_node)
P = chart["planets"]
sav_house = sav_by_house(chart, av)
now = utc_now()
md_now, ad_now, pd_now = active_periods(schedule, now)
here_tz = here_loc["tz_name"] if here_loc else tz_name
here_place = (here_loc["lat"], here_loc["lon"]) if here_loc else (lat, lon)

st.sidebar.caption(f"📍 {address}")
st.sidebar.caption(f"🌐 {lat:.2f}°, {lon:.2f}° · {tz_name} (UTC{chart['utc_offset']:+.2f} at birth)")

# --------------------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------------------
st.title("🔮 Vedic Astrology & Ashtakavarga Engine")
who = f"**{user_name}** · " if user_name else ""
st.caption(f"{who}Born {fmt_date(dob)} at {tob.strftime('%H:%M')} · {address} · "
           f"{ayanamsha} ayanamsha {chart['ayanamsha_deg']:.4f}°")

m = st.columns(5)
m[0].metric("Lagna", P["Ascendant"]["sign"], f"{P['Ascendant']['degree']:.1f}° {P['Ascendant']['nakshatra']}",
            delta_color="off", help="Your rising sign: the starting point of the chart. Describes body and temperament.")
m[1].metric("Moon Sign", P["Moon"]["sign"], P["Moon"]["nakshatra"], delta_color="off",
            help="Your Rashi: mind and emotions. The second line is your birth star (nakshatra).")
m[2].metric("Atmakaraka", nar.karaka(chart, "AK")["planet"],
            help="Your 'soul planet': the planet with the highest degree. Its themes are your main life lesson.")
m[3].metric("Amatyakaraka", nar.karaka(chart, "AmK")["planet"],
            help="Your 'career planet': the second-highest degree. It shapes the kind of work that suits you.")
m[4].metric("Mahadasha", md_now["lord"] if md_now else "—",
            f"{ad_now['lord']} AD until {fmt_date(ad_now['end'])}" if ad_now else None, delta_color="off",
            help="The planet running your current multi-year life chapter. AD = Antardasha, the current sub-chapter.")

with st.expander("📖 New to this? Plain-English glossary of the terms used on every page"):
    st.markdown("\n".join(f"- **{k}:** {v}" for k, v in nar.GLOSSARY.items()))

sens_rows, dasha_days_per_min = cached_sensitivity(chart)
sens_warning = warning(sens_rows)
if sens_warning:
    st.warning(sens_warning + " Details are on the Planets page.")

remedies = rem.build_remedies(chart, av, (md_now, ad_now), now, sb)

# --------------------------------------------------------------------------------------
# Hand over to the selected page
# --------------------------------------------------------------------------------------
st.session_state["ctx"] = {
    "chart": chart, "av": av, "schedule": schedule, "sb": sb, "P": P, "sav_house": sav_house, "now": now,
    "md_now": md_now, "ad_now": ad_now, "pd_now": pd_now, "tz_name": tz_name, "lat": lat, "lon": lon,
    "address": address, "user_name": user_name, "dob": dob, "tob": tob, "ayanamsha": ayanamsha,
    "true_node": true_node, "sens_rows": sens_rows, "dasha_days_per_min": dasha_days_per_min, "remedies": remedies,
    "here_tz": here_tz, "here_place": here_place,
}

page = st.navigation({
    "Overview": [st.Page("app_pages/summary.py", title="Summary", icon="📜", default=True),
                 st.Page("app_pages/ask.py", title="Ask", icon="💬")],
    "Forecasts": [st.Page("app_pages/week.py", title="This Week", icon="🗓"),
                  st.Page("app_pages/month.py", title="Month", icon="📆"),
                  st.Page("app_pages/planner.py", title="Planner", icon="📅")],
    "Life areas": [st.Page("app_pages/job.py", title="Job", icon="💼"),
                   st.Page("app_pages/health.py", title="Health", icon="🩺"),
                   st.Page("app_pages/wealth.py", title="Wealth", icon="💰"),
                   st.Page("app_pages/relationships.py", title="Relationships", icon="💞"),
                   st.Page("app_pages/children.py", title="Children", icon="👶"),
                   st.Page("app_pages/education.py", title="Education", icon="🎓"),
                   st.Page("app_pages/home_family.py", title="Home & Family", icon="🏠"),
                   st.Page("app_pages/travel.py", title="Travel & Foreign", icon="✈️"),
                   st.Page("app_pages/spirituality.py", title="Spirituality", icon="🕉"),
                   st.Page("app_pages/remedies.py", title="Remedies", icon="🪔")],
    "Chart & timing": [st.Page("app_pages/planets.py", title="Planets", icon="🪐"),
                       st.Page("app_pages/dasha.py", title="Dasha", icon="⏳"),
                       st.Page("app_pages/ashtakavarga.py", title="Ashtakavarga", icon="📊"),
                       st.Page("app_pages/strength.py", title="Strength", icon="⚡"),
                       st.Page("app_pages/houses.py", title="Houses", icon="🏛"),
                       st.Page("app_pages/timing.py", title="Timing", icon="🎯"),
                       st.Page("app_pages/bhrigu.py", title="Bhrigu", icon="🔱")],
    "Tools": [st.Page("app_pages/journal.py", title="Journal", icon="📓")],
}, position="top")
page.run()
