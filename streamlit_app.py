"""Vedic Astrology & Ashtakavarga Engine: entry point.

This file draws the sidebar (birth details and saved people), computes the chart once per run, shows
the header, and hands over to the selected page in app_pages/. Only the selected page is computed.
All calculations live in vedic/; shared helpers and cached functions in ui/common.py.
"""
import base64
import datetime as dt
import json
import zoneinfo

import streamlit as st

from ui import secure
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
# Saved profiles: kept in the page link (?p=...) so a bookmark reopens them
# --------------------------------------------------------------------------------------
PROFILE_KEYS = {"name": "k_name", "dob": "k_dob", "tob": "k_tob", "place": "k_place", "manual": "k_manual",
                "lat": "k_lat", "lon": "k_lon", "tz": "k_tz"}
DEFAULT_PROFILE = {"name": "", "dob": dt.date(1985, 6, 15), "tob": dt.time(14, 30), "place": "Bengaluru, India",
                   "manual": False, "lat": 12.9716, "lon": 77.5946, "tz": "Asia/Kolkata"}


def encode_profiles(profiles, passphrase):
    raw = [{**p, "dob": p["dob"].isoformat(), "tob": p["tob"].strftime("%H:%M")} for p in profiles]
    return secure.encrypt(json.dumps(raw, separators=(",", ":")), passphrase)


def _parse_profiles(text):
    raw = json.loads(text)
    return [{**DEFAULT_PROFILE, **p, "dob": dt.date.fromisoformat(p["dob"]),
             "tob": dt.datetime.strptime(p["tob"], "%H:%M").time()} for p in raw]


def decode_legacy(blob):
    """Links saved before encryption was added: plain base64 JSON."""
    try:
        return _parse_profiles(base64.urlsafe_b64decode(blob.encode()).decode())
    except Exception:
        return []


def write_link():
    """Store the saved people in the page link, encrypted, or drop the link if there are none."""
    if st.session_state["profiles"]:
        st.query_params["p"] = encode_profiles(st.session_state["profiles"], st.session_state["_pass"])
    else:
        st.query_params.pop("p", None)


def load_profile(profile):
    """Show `profile` in the sidebar. Bumping the version gives every field a fresh key, so each one is
    redrawn with the profile's value (Streamlit ignores a new default for a widget it already knows)."""
    st.session_state["_prof"] = dict(profile)
    st.session_state["_ver"] = st.session_state.get("_ver", 0) + 1


def field(name):
    """(key, starting value) for a sidebar field. Values live in our own copy (_prof) because Streamlit
    forgets a widget's value while it is hidden, e.g. the manual coordinates."""
    return {"key": f"{PROFILE_KEYS[name]}_{st.session_state['_ver']}", "value": st.session_state["_prof"][name]}


def remember(name, value):
    st.session_state["_prof"][name] = value
    return value


def on_pick_profile():
    choice = st.session_state["profile_pick"]
    if choice == "➕ New person":
        load_profile(DEFAULT_PROFILE)
    else:
        load_profile(next(p for p in st.session_state["profiles"] if p["name"] == choice))


def current_profile():
    return dict(st.session_state["_prof"])


if "profiles" not in st.session_state:
    blob = st.query_params.get("p", "")
    st.session_state["_locked"] = secure.is_encrypted(blob)
    st.session_state["profiles"] = [] if st.session_state["_locked"] else decode_legacy(blob)
    st.session_state["_legacy"] = bool(st.session_state["profiles"])
    first = st.session_state["profiles"][0] if st.session_state["profiles"] else DEFAULT_PROFILE
    load_profile(first)
    if st.session_state["profiles"]:
        st.session_state["profile_pick"] = first["name"]


# --------------------------------------------------------------------------------------
# Sidebar: birth details
# --------------------------------------------------------------------------------------
st.sidebar.header("👤 Birth Details")
if st.session_state["_locked"]:
    with st.sidebar.container(border=True):
        st.markdown("🔒 **Saved people are locked**")
        unlock = st.text_input("Passphrase", type="password", key="unlock_pass")
        if st.button("Unlock", width="stretch") and unlock:
            try:
                people = _parse_profiles(secure.decrypt(st.query_params.get("p", ""), unlock))
            except ValueError:
                st.error("That passphrase doesn't open this link.")
            else:
                st.session_state.update(profiles=people, _locked=False, _pass=unlock, _legacy=False)
                load_profile(people[0])
                st.session_state["pending_pick"] = people[0]["name"]
                st.rerun()
elif st.session_state.get("_legacy"):
    st.sidebar.warning("Your saved people are in an **unencrypted** link. Open 💾 below, set a passphrase and "
                       "save once to protect them.")

names = [p["name"] for p in st.session_state["profiles"]]
if "pending_pick" in st.session_state:  # set by Save/Remove on the previous run
    pick = st.session_state.pop("pending_pick")
    st.session_state["profile_pick"] = pick if pick in names else "➕ New person"
if names:
    st.sidebar.selectbox("Saved people", names + ["➕ New person"], key="profile_pick", on_change=on_pick_profile)
user_name = remember("name", st.sidebar.text_input("Name", placeholder="Needed to save a profile", **field("name")))
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
    st.caption("Houses: whole sign (Rasi = Bhava). Ephemeris: Swiss Ephemeris (Moshier).")

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

with st.sidebar.expander("💾 Save or remove this person"):
    st.caption("Saved people are kept in the page link, **encrypted with your passphrase**. After saving, "
               "**bookmark the page**; you'll enter the passphrase when you reopen it.")
    if st.session_state["_locked"]:
        st.info("Unlock your saved people first, so saving doesn't replace them.")
    elif not st.session_state.get("_pass"):
        new_pass = st.text_input(f"Choose a passphrase ({secure.MIN_LENGTH}+ characters)", type="password",
                                 key="new_pass")
        if new_pass and len(new_pass) < secure.MIN_LENGTH:
            st.caption(f"Use at least {secure.MIN_LENGTH} characters.")
        elif new_pass:
            st.session_state["_pass"] = new_pass
    ready = bool(st.session_state.get("_pass")) and not st.session_state["_locked"]
    s1, s2 = st.columns(2)
    if s1.button("Save", width="stretch", disabled=not (ready and user_name.strip())):
        prof = current_profile()
        if not manual:
            prof.update(lat=lat, lon=lon, tz=tz_name)
        others = [p for p in st.session_state["profiles"] if p["name"] != prof["name"]]
        st.session_state["profiles"] = others + [prof]
        st.session_state["_legacy"] = False
        write_link()
        st.session_state["pending_pick"] = prof["name"]
        st.rerun()
    if s2.button("Remove", width="stretch", disabled=not ready or user_name not in names):
        st.session_state["profiles"] = [p for p in st.session_state["profiles"] if p["name"] != user_name]
        write_link()
        st.session_state["pending_pick"] = "➕ New person"
        st.rerun()

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
    "Overview": [st.Page("app_pages/summary.py", title="Summary", icon="📜", default=True)],
    "Forecasts": [st.Page("app_pages/week.py", title="This Week", icon="🗓"),
                  st.Page("app_pages/month.py", title="Month", icon="📆"),
                  st.Page("app_pages/planner.py", title="Planner", icon="📅")],
    "Life areas": [st.Page("app_pages/job.py", title="Job", icon="💼"),
                   st.Page("app_pages/remedies.py", title="Remedies", icon="🪔")],
    "Chart & timing": [st.Page("app_pages/planets.py", title="Planets", icon="🪐"),
                       st.Page("app_pages/dasha.py", title="Dasha", icon="⏳"),
                       st.Page("app_pages/ashtakavarga.py", title="Ashtakavarga", icon="📊"),
                       st.Page("app_pages/strength.py", title="Strength", icon="⚡"),
                       st.Page("app_pages/timing.py", title="Timing", icon="🎯"),
                       st.Page("app_pages/bhrigu.py", title="Bhrigu", icon="🔱")],
    "Tools": [st.Page("app_pages/journal.py", title="Journal", icon="📓")],
}, position="top")
page.run()
