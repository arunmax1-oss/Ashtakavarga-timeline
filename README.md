# 🔮 Vedic Astrology & Ashtakavarga Engine

A personal Streamlit app: sidereal birth chart, Nakshatras, D9/D10, Jaimini karakas, yogas,
Vimshottari Dasha (to Pratyantardasha), classical Ashtakavarga (BAV/SAV) and a transit timing
engine that scores real Kakshya windows for Saturn, Jupiter, Mars and the Moon.

## Deploy on Streamlit Community Cloud

1. Create a GitHub repository and upload **everything in this folder** (keep the folder structure:
   `streamlit_app.py`, `requirements.txt`, the `vedic/` folder and the `.streamlit/` folder at the top level).
   - With the GitHub website: *Add file → Upload files*, then drag the folder contents in.
     Hidden folders like `.streamlit/` may not drag on some systems; it only sets the dark theme, so the app works without it.
2. Go to <https://share.streamlit.io>, click **Create app → Deploy a public app from GitHub**.
3. Pick the repository and branch, set **Main file path** to `streamlit_app.py`.
4. Under **Advanced settings**, choose Python **3.12**, then **Deploy**.

To keep it private, set the app's sharing to "Only specific people" in the Streamlit app settings.

## Run locally

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
pip install pytest && pytest   # optional: checks the calculations
```

## Project map

| File | What it does |
|---|---|
| `streamlit_app.py` | UI only: sidebar inputs, tabs, tables, download button |
| `vedic/constants.py` | Signs, lords, dignities, nakshatras, dasha years, house meanings, colours |
| `vedic/chart.py` | Place lookup, DST-aware UTC conversion, Swiss Ephemeris positions, D9/D10, karakas |
| `vedic/ashtakavarga.py` | Parashari BAV/SAV tables and Kakshya lords |
| `vedic/dasha.py` | Vimshottari Mahadasha → Antardasha → Pratyantardasha |
| `vedic/transits.py` | Splits real transits into Kakshya windows and rates them |
| `vedic/yogas.py` | Yoga detection and the dignity strength score |
| `vedic/narratives.py` | All interpretation text (edit wording here) |
| `vedic/insights.py` | Builds the chart-specific "What this means for you" explanations on each tab |
| `vedic/aspects.py` | Combustion and planetary aspects (graha drishti) |
| `vedic/remedies.py` | Remedies tab: which planets are flagged, why, and the three remedy tiers |
| `vedic/plots.py` | Plotly charts |
| `vedic/report.py` | Downloadable HTML report |
| `tests/test_engine.py` | Sanity checks (SAV = 337, BAV totals, dasha order, transit continuity) |

**Tip when asking an AI to change the app:** paste this table plus only the file(s) involved,
e.g. "change the career wording in `vedic/narratives.py`". Small, targeted files are much easier
for any assistant to edit without losing earlier work.

## What's calculated vs. simplified

- **Real calculations:** planet and Ascendant positions (Swiss Ephemeris, Lahiri/Raman/KP), Nakshatra
  and pada, D9, D10, Chara Karakas, Vimshottari Dasha, Ashtakavarga (classical BPHS tables), and
  transit Kakshya timing.
- **Simplified:** the *Planet Strength* tab is a dignity + directional-strength score, not full
  Shadbala; *Dhana Yoga* uses a simplified rule. Houses and aspects are whole-sign.
- Interpretations are for reflection only.
