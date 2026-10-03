"""Birth chart calculation: location lookup, Swiss Ephemeris positions, vargas and karakas.

All longitudes are sidereal degrees in [0, 360). Houses are whole-sign (Rasi = Bhava),
counted from the Ascendant's sign.
"""
import datetime as dt
import zoneinfo

import swisseph as swe

from .constants import (
    AYANAMSHAS, CLASSICAL_PLANETS, DEBILITATION_SIGNS, ELEMENTS, EXALTATION_SIGNS,
    NAKSHATRA_SPAN, NAKSHATRAS, DASHA_LORDS, OWN_SIGNS, SIGNS,
)

_SIDEREAL_MODES = {
    "Lahiri (Chitrapaksha)": swe.SIDM_LAHIRI,
    "Raman": swe.SIDM_RAMAN,
    "Krishnamurti (KP)": swe.SIDM_KRISHNAMURTI,
}
# Moshier ephemeris is built into pyswisseph, so no data files are needed on Streamlit Cloud.
_FLAGS = swe.FLG_MOSEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED

SWE_IDS = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN,
}


# --------------------------------------------------------------------------------------
# Location & time
# --------------------------------------------------------------------------------------
def geocode(query):
    """Return {address, lat, lon, tz_name} for a place name, or None if it can't be found."""
    from geopy.geocoders import Nominatim
    from timezonefinder import TimezoneFinder

    try:
        loc = Nominatim(user_agent="vedic_astrology_personal_app").geocode(query, timeout=10)
    except Exception:
        return None
    if not loc:
        return None
    tz_name = TimezoneFinder().timezone_at(lng=loc.longitude, lat=loc.latitude)
    if not tz_name:
        return None
    return {"address": loc.address, "lat": loc.latitude, "lon": loc.longitude, "tz_name": tz_name}


def to_utc(date, time, tz_name):
    """Local birth date/time -> naive UTC datetime, using the zone's rules *on that date* (DST-aware)."""
    local = dt.datetime.combine(date, time).replace(tzinfo=zoneinfo.ZoneInfo(tz_name))
    return local.astimezone(dt.timezone.utc).replace(tzinfo=None)


def utc_offset_hours(date, time, tz_name):
    local = dt.datetime.combine(date, time).replace(tzinfo=zoneinfo.ZoneInfo(tz_name))
    return local.utcoffset().total_seconds() / 3600.0


def julian_day(utc_dt):
    hour = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
    return swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, hour)


def jd_to_datetime(jd):
    y, m, d, h = swe.revjul(jd)
    return dt.datetime(y, m, d) + dt.timedelta(seconds=round(h * 3600))


# --------------------------------------------------------------------------------------
# Ephemeris
# --------------------------------------------------------------------------------------
def set_ayanamsha(ayanamsha):
    swe.set_sid_mode(_SIDEREAL_MODES[ayanamsha])


def planet_longitude(jd, planet, true_node=False):
    """Sidereal longitude and daily speed of one body (incl. Rahu/Ketu). Call set_ayanamsha first."""
    if planet in ("Rahu", "Ketu"):
        res, _ = swe.calc_ut(jd, swe.TRUE_NODE if true_node else swe.MEAN_NODE, _FLAGS)
        lon = res[0] if planet == "Rahu" else (res[0] + 180.0) % 360.0
        return lon, res[3]
    res, _ = swe.calc_ut(jd, SWE_IDS[planet], _FLAGS)
    return res[0] % 360.0, res[3]


def ascendant_longitude(jd, lat, lon):
    _, ascmc = swe.houses_ex(jd, lat, lon, b"E", swe.FLG_SIDEREAL)
    return ascmc[0] % 360.0


# --------------------------------------------------------------------------------------
# Derived positions
# --------------------------------------------------------------------------------------
def nakshatra_of(lon):
    idx = int(lon // NAKSHATRA_SPAN)
    pada = int((lon % NAKSHATRA_SPAN) // (NAKSHATRA_SPAN / 4)) + 1
    return NAKSHATRAS[idx], DASHA_LORDS[idx % 9], pada


def navamsha_sign(lon):
    """D9: Fire signs start from Aries, Earth from Capricorn, Air from Libra, Water from Cancer."""
    sign_idx = int(lon // 30)
    part = int((lon % 30) // (30 / 9))
    start = {"Fire": 0, "Earth": 9, "Air": 6, "Water": 3}[ELEMENTS[SIGNS[sign_idx]]]
    return (start + part) % 12


def dashamsha_sign(lon):
    """D10: odd signs count from the sign itself, even signs from the 9th sign."""
    sign_idx = int(lon // 30)
    part = int((lon % 30) // 3)
    return (sign_idx + part) % 12 if sign_idx % 2 == 0 else (sign_idx + 8 + part) % 12


def dignity(planet, sign):
    if sign == EXALTATION_SIGNS.get(planet):
        return "Exalted"
    if sign == DEBILITATION_SIGNS.get(planet):
        return "Debilitated"
    if sign in OWN_SIGNS.get(planet, []):
        return "Own Sign"
    return "Neutral"


def house_from(sign_idx, ref_sign_idx):
    return (sign_idx - ref_sign_idx) % 12 + 1


def _position(name, lon, asc_sign_idx, speed=None):
    sign_idx = int(lon // 30)
    nak, nak_lord, pada = nakshatra_of(lon)
    return {
        "name": name,
        "lon": lon,
        "sign_idx": sign_idx,
        "sign": SIGNS[sign_idx],
        "degree": lon % 30,
        "nakshatra": nak,
        "nakshatra_lord": nak_lord,
        "pada": pada,
        "house": house_from(sign_idx, asc_sign_idx),
        "retrograde": speed is not None and speed < 0 and name not in ("Rahu", "Ketu"),
        "d9_sign": SIGNS[navamsha_sign(lon)],
        "d10_sign": SIGNS[dashamsha_sign(lon)],
        "dignity": dignity(name, SIGNS[sign_idx]) if name != "Ascendant" else "",
    }


def chara_karakas(planets):
    """7-karaka Jaimini scheme: classical planets ranked by degree within their sign."""
    roles = [
        ("Atmakaraka (AK)", "Core Soul Purpose & Identity"),
        ("Amatyakaraka (AmK)", "Career, Profession & Ambition"),
        ("Bhratrukaraka (BK)", "Mentors, Siblings & Support"),
        ("Matrukaraka (MK)", "Emotional Foundation & Home"),
        ("Putrakaraka (PK)", "Intelligence, Creativity & Children"),
        ("Gnatikaraka (GK)", "Obstacles, Health & Competition"),
        ("Darakaraka (DK)", "Partnerships & Long-Term Union"),
    ]
    ranked = sorted(CLASSICAL_PLANETS, key=lambda p: planets[p]["degree"], reverse=True)
    return [
        {"role": role, "short": role.split("(")[1].rstrip(")"), "planet": p,
         "sign": planets[p]["sign"], "degree": planets[p]["degree"], "meaning": meaning}
        for (role, meaning), p in zip(roles, ranked)
    ]


def build_chart(date, time, lat, lon, tz_name, ayanamsha=AYANAMSHAS[0], true_node=False):
    """Compute the full natal chart. Returns a plain dict (safe to cache)."""
    set_ayanamsha(ayanamsha)
    utc = to_utc(date, time, tz_name)
    jd = julian_day(utc)

    asc_lon = ascendant_longitude(jd, lat, lon)
    asc_sign_idx = int(asc_lon // 30)

    planets = {"Ascendant": _position("Ascendant", asc_lon, asc_sign_idx)}
    for name in CLASSICAL_PLANETS + ["Rahu", "Ketu"]:
        p_lon, speed = planet_longitude(jd, name, true_node)
        planets[name] = _position(name, p_lon, asc_sign_idx, speed)

    return {
        "birth_date": date,
        "birth_time": time,
        "birth_utc": utc,
        "jd": jd,
        "lat": lat,
        "lon": lon,
        "tz_name": tz_name,
        "utc_offset": utc_offset_hours(date, time, tz_name),
        "ayanamsha": ayanamsha,
        "ayanamsha_deg": swe.get_ayanamsa_ut(jd),
        "true_node": true_node,
        "asc_sign_idx": asc_sign_idx,
        "planets": planets,
        "karakas": chara_karakas(planets),
    }
