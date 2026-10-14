"""Divisional charts (vargas). Each function maps a sidereal longitude to a sign index (0 = Aries)."""
from .chart import dashamsha_sign, navamsha_sign


def rasi(lon):
    return int(lon // 30)


def hora(lon):
    """D2 (Parashara): odd signs give Leo (Sun) then Cancer (Moon); even signs the reverse."""
    s, d = int(lon // 30), lon % 30
    return 4 if (d < 15) == (s % 2 == 0) else 3


def drekkana(lon):
    """D3: the sign itself, then the 5th, then the 9th."""
    return (int(lon // 30) + 4 * int((lon % 30) // 10)) % 12


def chaturthamsa(lon):
    """D4: the sign, 4th, 7th and 10th from it."""
    return (int(lon // 30) + 3 * int((lon % 30) // 7.5)) % 12


def saptamsa(lon):
    """D7: odd signs count from the sign, even signs from the 7th."""
    s = int(lon // 30)
    start = s if s % 2 == 0 else (s + 6) % 12
    return (start + int((lon % 30) // (30 / 7))) % 12


def dwadasamsa(lon):
    """D12: counted from the sign itself."""
    return (int(lon // 30) + int((lon % 30) // 2.5)) % 12


def trimsamsa(lon):
    """D30 (Parashara): unequal parts ruled by Mars, Saturn, Jupiter, Mercury, Venus."""
    s, d = int(lon // 30), lon % 30
    parts = [(5, 0), (10, 10), (18, 8), (25, 2), (30, 6)] if s % 2 == 0 else \
            [(5, 1), (12, 5), (20, 11), (25, 9), (30, 7)]
    return next(sign for limit, sign in parts if d < limit)


VARGAS = {
    "D1": ("Rasi: the birth chart", rasi),
    "D2": ("Hora: wealth", hora),
    "D3": ("Drekkana: siblings and courage", drekkana),
    "D4": ("Chaturthamsa: property and fortune", chaturthamsa),
    "D7": ("Saptamsa: children", saptamsa),
    "D9": ("Navamsa: marriage and inner strength", navamsha_sign),
    "D10": ("Dasamsa: career", dashamsha_sign),
    "D12": ("Dwadasamsa: parents", dwadasamsa),
    "D30": ("Trimsamsa: health and misfortunes", trimsamsa),
}


def varga_positions(chart, varga):
    """{body: sign index} in the given divisional chart, including the Ascendant."""
    fn = VARGAS[varga][1]
    return {name: fn(p["lon"]) for name, p in chart["planets"].items()}
