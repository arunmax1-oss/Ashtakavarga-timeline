"""Divisional charts (vargas): the full Parashari Shodashavarga (16 charts).

Each function maps a sidereal longitude to a sign index (0 = Aries). Sign index parity: an even index
(Aries, Gemini...) is an odd sign. Index % 3 gives movable (0), fixed (1) and dual (2) signs.
"""
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


def _by_modality(lon, parts, starts):
    """Equal parts counted from a start sign that depends on whether the sign is movable, fixed or dual."""
    s = int(lon // 30)
    return (starts[s % 3] + int((lon % 30) // (30 / parts))) % 12


def shodashamsa(lon):
    """D16: movable signs from Aries, fixed from Leo, dual from Sagittarius."""
    return _by_modality(lon, 16, (0, 4, 8))


def vimshamsa(lon):
    """D20: movable signs from Aries, fixed from Sagittarius, dual from Leo."""
    return _by_modality(lon, 20, (0, 8, 4))


def chaturvimshamsa(lon):
    """D24: odd signs from Leo, even signs from Cancer."""
    s = int(lon // 30)
    return ((4 if s % 2 == 0 else 3) + int((lon % 30) // 1.25)) % 12


def bhamsa(lon):
    """D27: fire signs from Aries, earth from Cancer, air from Libra, water from Capricorn."""
    return (int(lon // 30) * 27 + int((lon % 30) // (30 / 27))) % 12


def khavedamsa(lon):
    """D40: odd signs from Aries, even signs from Libra."""
    s = int(lon // 30)
    return ((0 if s % 2 == 0 else 6) + int((lon % 30) // 0.75)) % 12


def akshavedamsa(lon):
    """D45: movable signs from Aries, fixed from Leo, dual from Sagittarius."""
    return _by_modality(lon, 45, (0, 4, 8))


def shashtiamsa(lon):
    """D60: counted from the sign itself."""
    return (int(lon // 30) + int((lon % 30) // 0.5)) % 12


VARGAS = {
    "D1": ("Rasi: the birth chart", rasi),
    "D2": ("Hora: wealth", hora),
    "D3": ("Drekkana: siblings and courage", drekkana),
    "D4": ("Chaturthamsa: property and fortune", chaturthamsa),
    "D7": ("Saptamsa: children", saptamsa),
    "D9": ("Navamsa: marriage and inner strength", navamsha_sign),
    "D10": ("Dasamsa: career", dashamsha_sign),
    "D12": ("Dwadasamsa: parents", dwadasamsa),
    "D16": ("Shodashamsa: vehicles, comforts and happiness", shodashamsa),
    "D20": ("Vimshamsa: spiritual life and worship", vimshamsa),
    "D24": ("Chaturvimshamsa: education and learning", chaturvimshamsa),
    "D27": ("Bhamsa: strengths and weaknesses", bhamsa),
    "D30": ("Trimsamsa: health and misfortunes", trimsamsa),
    "D40": ("Khavedamsa: maternal legacy, auspicious and inauspicious effects", khavedamsa),
    "D45": ("Akshavedamsa: paternal legacy and character", akshavedamsa),
    "D60": ("Shashtiamsa: past karma; the finest division (needs an exact birth time)", shashtiamsa),
}


def varga_positions(chart, varga):
    """{body: sign index} in the given divisional chart, including the Ascendant."""
    fn = VARGAS[varga][1]
    return {name: fn(p["lon"]) for name, p in chart["planets"].items()}
