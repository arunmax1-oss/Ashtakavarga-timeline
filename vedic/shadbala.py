"""Shadbala: the six-fold planetary strength of Brihat Parashara Hora Shastra (BPHS).

All values are in virupas (shashtiamsas); 60 virupas = 1 rupa. Only the seven classical planets get Shadbala.

    1. Sthana Bala  (positional)   Uchcha, Saptavargaja, Ojha-Yugma, Kendradi, Drekkana
    2. Dig Bala     (directional)
    3. Kala Bala    (temporal)     Nathonnata, Paksha, Tribhaga, Abda/Masa/Vara/Hora lords, Ayana, Yuddha
    4. Cheshta Bala (motional)
    5. Naisargika   (natural)
    6. Drik Bala    (aspectual)

Conventions where classical sources differ (stated so results can be compared with other software):
- Dig Bala strongest points are the equal-house cusps from the Ascendant (1st, 4th, 7th, 10th).
- Abda (year) and Masa (month) lords are the weekday lords of the day the current 360-day year and
  30-day month began, counted from the Kali Yuga epoch (JD 588465.5), as in the Surya Siddhanta ahargana.
- Hora lords use equal 1-hour horas from local sunrise. Sunrise is the upper limb with refraction.
- Cheshta Bala uses the chesta-kendra method with mean longitudes from standard J2000 elements;
  the Sun's Cheshta Bala is its Ayana Bala and the Moon's is its (undoubled) Paksha Bala.
- Mercury is treated as a benefic; the Moon is a benefic when waxing.
- In a planetary war (two of Mars-Saturn within 1°) the planet with the more northerly latitude wins.
"""
import swisseph as swe

from .chart import navamsha_sign, set_ayanamsha
from .constants import CLASSICAL_PLANETS, OWN_SIGNS, SIGN_LORDS, SIGNS

_FLAGS = swe.FLG_MOSEPH
_IDS = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY,
        "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN}

# Deep exaltation points (sidereal degrees); deep debilitation is 180° away.
DEEP_EXALTATION = {"Sun": 10, "Moon": 33, "Mars": 298, "Mercury": 165, "Jupiter": 95, "Venus": 357, "Saturn": 200}

NATURAL_FRIENDS = {
    "Sun": (["Moon", "Mars", "Jupiter"], ["Mercury"], ["Venus", "Saturn"]),
    "Moon": (["Sun", "Mercury"], ["Mars", "Jupiter", "Venus", "Saturn"], []),
    "Mars": (["Sun", "Moon", "Jupiter"], ["Venus", "Saturn"], ["Mercury"]),
    "Mercury": (["Sun", "Venus"], ["Mars", "Jupiter", "Saturn"], ["Moon"]),
    "Jupiter": (["Sun", "Moon", "Mars"], ["Saturn"], ["Mercury", "Venus"]),
    "Venus": (["Mercury", "Saturn"], ["Mars", "Jupiter"], ["Sun", "Moon"]),
    "Saturn": (["Mercury", "Venus"], ["Jupiter"], ["Sun", "Moon", "Mars"]),
}
# Moolatrikona: (sign index, start degree, end degree)
MOOLATRIKONA = {"Sun": (4, 0, 20), "Moon": (1, 3, 30), "Mars": (0, 0, 12), "Mercury": (5, 15, 20),
                "Jupiter": (8, 0, 10), "Venus": (6, 0, 15), "Saturn": (10, 0, 20)}
SAPTAVARGA_POINTS = {"Moolatrikona": 45, "Own": 30, "Great friend": 22.5, "Friend": 15,
                     "Neutral": 7.5, "Enemy": 3.75, "Great enemy": 1.875}

NAISARGIKA = {"Sun": 60.0, "Moon": 51.43, "Venus": 42.86, "Jupiter": 34.29,
              "Mercury": 25.71, "Mars": 17.14, "Saturn": 8.57}
# Minimum total (virupas) for a planet to be considered strong enough.
REQUIRED = {"Sun": 390, "Moon": 360, "Mars": 300, "Mercury": 420, "Jupiter": 390, "Venus": 330, "Saturn": 300}

MALE, FEMALE = ["Sun", "Mars", "Jupiter"], ["Moon", "Venus"]
WEEKDAY_LORDS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]  # Sunday first
HORA_ORDER = ["Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"]
KALI_EPOCH_JD = 588465.5

# Mean tropical longitudes at J2000.0 and mean daily motion (degrees).
MEAN_ELEMENTS = {"Sun": (280.46646, 0.98564736), "Mercury": (252.25084, 4.09233880),
                 "Venus": (181.97973, 1.60213047), "Mars": (355.43300, 0.52402068),
                 "Jupiter": (34.35151, 0.08308529), "Saturn": (50.07744, 0.03344414)}

COMPONENT_LABELS = {
    "sthana": "Sthana (position)", "dig": "Dig (direction)", "kala": "Kala (time)",
    "cheshta": "Cheshta (motion)", "naisargika": "Naisargika (natural)", "drik": "Drik (aspects)",
}


def _arc(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


# --------------------------------------------------------------------------------------
# Divisional signs used by Saptavargaja Bala (D1 and D9 come from chart.py)
# --------------------------------------------------------------------------------------
def _hora(lon):
    s, d = int(lon // 30), lon % 30
    odd = s % 2 == 0
    return 4 if (d < 15) == odd else 3  # Leo (Sun's hora) or Cancer (Moon's hora)


def _drekkana(lon):
    return (int(lon // 30) + 4 * int((lon % 30) // 10)) % 12


def _saptamsa(lon):
    s = int(lon // 30)
    start = s if s % 2 == 0 else (s + 6) % 12
    return (start + int((lon % 30) // (30 / 7))) % 12


def _dwadasamsa(lon):
    return (int(lon // 30) + int((lon % 30) // 2.5)) % 12


def _trimsamsa(lon):
    s, d = int(lon // 30), lon % 30
    if s % 2 == 0:  # odd sign
        for limit, sign in [(5, 0), (10, 10), (18, 8), (25, 2), (30, 6)]:
            if d < limit:
                return sign
    for limit, sign in [(5, 1), (12, 5), (20, 11), (25, 9), (30, 7)]:
        if d < limit:
            return sign
    return s


VARGAS = {"D1": lambda lon: int(lon // 30), "D2": _hora, "D3": _drekkana, "D7": _saptamsa,
          "D9": navamsha_sign, "D12": _dwadasamsa, "D30": _trimsamsa}


# --------------------------------------------------------------------------------------
# Friendship
# --------------------------------------------------------------------------------------
def compound_relation(chart, planet, other):
    friends, neutrals, _enemies = NATURAL_FRIENDS[planet]
    natural = 1 if other in friends else 0 if other in neutrals else -1
    dist = (chart["planets"][other]["sign_idx"] - chart["planets"][planet]["sign_idx"]) % 12 + 1
    temporary = 1 if dist in (2, 3, 4, 10, 11, 12) else -1
    return {2: "Great friend", 1: "Friend", 0: "Neutral", -1: "Enemy", -2: "Great enemy"}[natural + temporary]


def _varga_dignity(chart, planet, varga, sign_idx):
    if varga == "D1":
        mt_sign, lo, hi = MOOLATRIKONA[planet]
        if sign_idx == mt_sign and lo <= chart["planets"][planet]["degree"] < hi:
            return "Moolatrikona"
    if SIGNS[sign_idx] in OWN_SIGNS[planet]:
        return "Own"
    lord = SIGN_LORDS[SIGNS[sign_idx]]
    return compound_relation(chart, planet, lord)


# --------------------------------------------------------------------------------------
# Time helpers
# --------------------------------------------------------------------------------------
class _NoSunrise(Exception):
    pass


def _sun_events(chart):
    """(previous sunrise, sunset after it, next sunrise, approximated?) around birth, as JD UT.

    Near the poles the Sun may not rise or set; then 06:00 and 18:00 local apparent time are used.
    """
    geo = (chart["lon"], chart["lat"], 0)
    jd = chart["jd"]

    def nxt(start, kind):
        flag, tret = swe.rise_trans(start, swe.SUN, kind, geo, 0, 0, _FLAGS)
        if flag < 0 or tret[0] < start or tret[0] - start > 2:
            raise _NoSunrise
        return tret[0]

    try:
        rise = nxt(jd - 1, swe.CALC_RISE)
        if rise > jd:
            rise = nxt(jd - 2, swe.CALC_RISE)
        sset = nxt(rise, swe.CALC_SET)
        next_rise = nxt(sset, swe.CALC_RISE)
        return rise, sset, next_rise, False
    except (_NoSunrise, swe.Error):
        # local apparent midnight before birth, then fixed 06:00 / 18:00
        lat_hours = ((jd + 0.5) % 1 * 24 + chart["lon"] / 15 + swe.time_equ(jd) * 24) % 24
        midnight = jd - lat_hours / 24
        rise, sset = midnight + 0.25, midnight + 0.75
        if jd < rise:
            rise, sset = rise - 1, sset - 1
        return rise, sset, rise + 1, True


def _weekday_lord(jd_ut, lon):
    """Weekday lord of the civil date at the given moment (local mean time)."""
    monday0 = swe.day_of_week(jd_ut + lon / 360.0)  # 0 = Monday
    return WEEKDAY_LORDS[(monday0 + 1) % 7]


# --------------------------------------------------------------------------------------
# The six balas
# --------------------------------------------------------------------------------------
def _sthana(chart, planet):
    p = chart["planets"][planet]
    uchcha = _arc(p["lon"], (DEEP_EXALTATION[planet] + 180) % 360) / 3

    saptavarga, varga_detail = 0.0, {}
    for name, fn in VARGAS.items():
        dignity = _varga_dignity(chart, planet, name, fn(p["lon"]))
        varga_detail[name] = dignity
        saptavarga += SAPTAVARGA_POINTS[dignity]

    want_even = planet in FEMALE
    ojha = sum(15 for s in (p["sign_idx"], navamsha_sign(p["lon"])) if (s % 2 == 1) == want_even)

    kendradi = 60 if p["house"] in (1, 4, 7, 10) else 30 if p["house"] in (2, 5, 8, 11) else 15

    third = int(p["degree"] // 10)
    drekkana = 15 if third == (0 if planet in MALE else 2 if planet in FEMALE else 1) else 0

    parts = {"Uchcha": uchcha, "Saptavargaja": saptavarga, "Ojha-Yugma": ojha,
             "Kendradi": kendradi, "Drekkana": drekkana}
    return sum(parts.values()), parts, varga_detail


def _dig(chart, planet):
    asc = chart["planets"]["Ascendant"]["lon"]
    strongest = {"Jupiter": 0, "Mercury": 0, "Moon": 90, "Venus": 90, "Saturn": 180, "Sun": 270, "Mars": 270}
    weakest = (asc + strongest[planet] + 180) % 360
    return _arc(chart["planets"][planet]["lon"], weakest) / 3


def _elongation(chart):
    p = chart["planets"]
    return (p["Moon"]["lon"] - p["Sun"]["lon"]) % 360


def _declination(jd, planet):
    return swe.calc_ut(jd, _IDS[planet], _FLAGS | swe.FLG_EQUATORIAL)[0][1]


def _ayana(chart, planet):
    dec = _declination(chart["jd"], planet)
    eff = abs(dec) if planet == "Mercury" else (-dec if planet in ("Moon", "Saturn") else dec)
    value = (24 + eff) / 48 * 60
    return value * 2 if planet == "Sun" else value


def _paksha(chart, planet):
    e = _elongation(chart)
    e = 360 - e if e > 180 else e
    benefic = e / 3
    if planet == "Moon":
        return 2 * benefic
    return benefic if planet in ("Mercury", "Jupiter", "Venus") else 60 - benefic


def _kala(chart, planet, sun):
    rise, sset, next_rise, _approx = sun
    jd = chart["jd"]
    day_birth = rise <= jd < sset

    # Nathonnata: distance from local apparent midnight
    lat_hours = ((jd + 0.5) % 1 * 24 + chart["lon"] / 15 + swe.time_equ(jd) * 24) % 24
    from_midnight = min(lat_hours, 24 - lat_hours)  # 0..12
    diurnal = from_midnight * 5
    nathonnata = 60.0 if planet == "Mercury" else diurnal if planet in ("Sun", "Jupiter", "Venus") else 60 - diurnal

    paksha = _paksha(chart, planet)

    if planet == "Jupiter":
        tribhaga = 60.0
    elif day_birth:
        part = min(int((jd - rise) / (sset - rise) * 3), 2)
        tribhaga = 60.0 if planet == ["Mercury", "Sun", "Saturn"][part] else 0.0
    else:
        part = min(int((jd - sset) / (next_rise - sset) * 3), 2)
        tribhaga = 60.0 if planet == ["Moon", "Venus", "Mars"][part] else 0.0

    ahargana = int(rise + chart["lon"] / 360.0 - KALI_EPOCH_JD)
    abda_lord = _weekday_lord(KALI_EPOCH_JD + (ahargana // 360) * 360, 0)
    masa_lord = _weekday_lord(KALI_EPOCH_JD + (ahargana // 30) * 30, 0)
    vara_lord = _weekday_lord(rise, chart["lon"])
    hora_lord = HORA_ORDER[(HORA_ORDER.index(vara_lord) + int((jd - rise) * 24)) % 7]
    lords = (15.0 if planet == abda_lord else 0) + (30.0 if planet == masa_lord else 0) + \
            (45.0 if planet == vara_lord else 0) + (60.0 if planet == hora_lord else 0)

    ayana = _ayana(chart, planet)
    parts = {"Nathonnata": nathonnata, "Paksha": paksha, "Tribhaga": tribhaga,
             "Year/Month/Day/Hora lord": lords, "Ayana": ayana}
    meta = {"day_birth": day_birth, "abda": abda_lord, "masa": masa_lord, "vara": vara_lord, "hora": hora_lord}
    return parts, meta


def _mean_longitude(jd, body):
    l0, rate = MEAN_ELEMENTS[body]
    return (l0 + rate * (jd - 2451545.0)) % 360


def _cheshta(chart, planet, kala_parts):
    if planet == "Sun":
        return kala_parts["Ayana"]
    if planet == "Moon":
        return kala_parts["Paksha"] / 2
    jd = chart["jd"]
    true_trop = (chart["planets"][planet]["lon"] + chart["ayanamsha_deg"]) % 360
    mean_sun = _mean_longitude(jd, "Sun")
    if planet in ("Mars", "Jupiter", "Saturn"):
        seegrocca, mean_planet = mean_sun, _mean_longitude(jd, planet)
    else:  # Mercury, Venus: their heliocentric mean motion is the seegrocca
        seegrocca, mean_planet = _mean_longitude(jd, planet), mean_sun
    avg = (mean_planet + true_trop) / 2 if abs(mean_planet - true_trop) <= 180 else \
        ((mean_planet + true_trop + 360) / 2) % 360
    return _arc(seegrocca, avg) / 3


def drishti_value(aspector, angle):
    """Degree-based aspect strength (0-60) cast by `aspector` across `angle` degrees (BPHS sputa drishti)."""
    a = angle % 360
    if 30 <= a < 60:
        v = (a - 30) / 2
    elif 60 <= a < 90:
        v = a - 45
    elif 90 <= a < 120:
        v = 30 + (120 - a) / 2
    elif 120 <= a < 150:
        v = 150 - a
    elif 150 <= a < 180:
        v = (a - 150) * 2
    elif 180 <= a < 300:
        v = (300 - a) / 2
    else:
        v = 0.0
    special = {"Saturn": [(60, 90), (270, 300)], "Jupiter": [(120, 150), (240, 270)], "Mars": [(90, 120), (210, 240)]}
    if any(lo <= a < hi for lo, hi in special.get(aspector, [])):
        v = 60.0
    return v


def _drik(chart, planet):
    p = chart["planets"]
    waxing = _elongation(chart) < 180
    total = 0.0
    for other in CLASSICAL_PLANETS:
        if other == planet:
            continue
        v = drishti_value(other, p[planet]["lon"] - p[other]["lon"])
        benefic = other in ("Jupiter", "Venus", "Mercury") or (other == "Moon" and waxing)
        total += v if benefic else -v
    return total / 4


def _war(chart, sthana, dig, kala):
    """Yuddha Bala adjustments: {planet: virupas} for planets within 1° of each other (Mars-Saturn)."""
    p = chart["planets"]
    fighters = ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    adj = {}
    for i, a in enumerate(fighters):
        for b in fighters[i + 1:]:
            if _arc(p[a]["lon"], p[b]["lon"]) <= 1.0:
                lat_a = swe.calc_ut(chart["jd"], _IDS[a], _FLAGS)[0][1]
                lat_b = swe.calc_ut(chart["jd"], _IDS[b], _FLAGS)[0][1]
                win, lose = (a, b) if lat_a >= lat_b else (b, a)
                diff = abs((sthana[a] + dig[a] + kala[a]) - (sthana[b] + dig[b] + kala[b]))
                adj[win] = adj.get(win, 0) + diff
                adj[lose] = adj.get(lose, 0) - diff
    return adj


# --------------------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------------------
def shadbala(chart):
    """Full Shadbala for the 7 classical planets.

    Returns {planet: {"total", "rupas", "required", "ratio", "components": {...},
    "detail": {sub-component: virupas}, "vargas": {varga: dignity}}} plus "_meta" with the time lords.
    """
    set_ayanamsha(chart["ayanamsha"])
    sun = _sun_events(chart)
    sthana, dig, kala_parts, kala_meta, sth_parts, vargas = {}, {}, {}, None, {}, {}
    for pl in CLASSICAL_PLANETS:
        sthana[pl], sth_parts[pl], vargas[pl] = _sthana(chart, pl)
        dig[pl] = _dig(chart, pl)
        kala_parts[pl], kala_meta = _kala(chart, pl, sun)
    kala = {pl: sum(kala_parts[pl].values()) for pl in CLASSICAL_PLANETS}
    war = _war(chart, sthana, dig, kala)

    out = {}
    for pl in CLASSICAL_PLANETS:
        kala_total = kala[pl] + war.get(pl, 0)
        comps = {
            "sthana": sthana[pl], "dig": dig[pl], "kala": kala_total,
            "cheshta": _cheshta(chart, pl, kala_parts[pl]),
            "naisargika": NAISARGIKA[pl], "drik": _drik(chart, pl),
        }
        total = sum(comps.values())
        detail = {**sth_parts[pl], **kala_parts[pl]}
        if pl in war:
            detail["Yuddha (planetary war)"] = war[pl]
        out[pl] = {"total": total, "rupas": total / 60, "required": REQUIRED[pl], "ratio": total / REQUIRED[pl],
                   "components": comps, "detail": detail, "vargas": vargas[pl]}
    ranked = sorted(CLASSICAL_PLANETS, key=lambda x: out[x]["ratio"], reverse=True)
    for i, pl in enumerate(ranked, 1):
        out[pl]["rank"] = i
    out["_meta"] = {**kala_meta, "sunrise": sun[0], "sunset": sun[1], "sun_approximated": sun[3]}
    return out
