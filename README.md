# 🔮 Vedic Astrology & Ashtakavarga Engine

A personal Streamlit app: sidereal birth chart, Nakshatras, D9/D10, Jaimini karakas, yogas,
Vimshottari Dasha (to Pratyantardasha), classical Ashtakavarga (BAV/SAV), full Shadbala, a transit
timing engine that scores real Kakshya windows, Bhrigu techniques, remedies, a weekly forecast with daily
timings, an activity planner, South/North Indian charts and divisional charts, birth-time sensitivity,
Yogini and Chara Dasha, monthly forecasts by life area, a page per life area (Job, Health, Wealth, Relationships,
Children, Education, Home & Family, Travel & Foreign, Spirituality), all 16 Parashari divisional charts with Vimshopaka
Bala, Ashtakavarga Shodhana and Shodhya Pinda, Arudha Padas, Argala, Bhava Chalit and a prediction journal.

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
python tests/smoke_pages.py    # optional: opens every page and reports errors
```

`requirements.txt` pins exact versions. To upgrade, change a version, run the tests, and push;
the GitHub **tests** check must stay green.

## Project map

| File | What it does |
|---|---|
| `streamlit_app.py` | Entry point: sidebar inputs, saved people, header metrics, page navigation |
| `ui/common.py` | Cached calculations and helpers shared by every page (`ctx()` gives a page the current chart) |
| `ui/life_area.py` | Draws every life-area page (Health, Wealth, ...) from `vedic/lifeareas.py` |
| `app_pages/*.py` | One file per page (Summary, This Week, Month, Planner, Job, Health, Wealth, Houses, ...) |
| `vedic/constants.py` | Signs, lords, dignities, nakshatras, dasha years, house meanings, colours |
| `vedic/chart.py` | Place lookup, DST-aware UTC conversion, Swiss Ephemeris positions, D9/D10, karakas |
| `vedic/ashtakavarga.py` | Parashari BAV/SAV tables, Kakshya lords, Shodhana reductions and Shodhya Pinda |
| `vedic/dasha.py` | Vimshottari Mahadasha → Antardasha → Pratyantardasha |
| `vedic/transits.py` | Splits real transits into Kakshya windows and rates them |
| `vedic/yogas.py` | Yoga detection and the dignity strength score |
| `vedic/narratives.py` | All interpretation text (edit wording here) |
| `vedic/insights.py` | Builds the chart-specific "What this means for you" explanations on each page |
| `vedic/weekly.py` | Weekly forecast: daily Panchang, Tara/Chandra Bala day ratings, the week's events |
| `vedic/bhrigu.py` | Bhrigu Bindu, Bhrigu Chakra Paddhati and Bhrigu Nandi Nadi transit contacts |
| `vedic/vargas.py` | All 16 Parashari divisional charts (D1 to D60) |
| `vedic/vimshopaka.py` | Vimshopaka Bala: strength out of 20 across the divisional charts |
| `vedic/houses.py` | Arudha Padas, Argala and Bhava Chalit (Sripati) houses |
| `vedic/lifeareas.py` | Life-area readings: promise factors, Dasha periods, transits, double transit, classical checks |
| `vedic/chartviz.py` | South and North Indian chart drawings (SVG) |
| `vedic/sensitivity.py` | Birth-time sensitivity: minutes until the Lagna, D9 Lagna, Moon sign or nakshatra change |
| `vedic/muhurta.py` | Activity planner: best days for an activity in the coming weeks |
| `vedic/dasha_alt.py` | Yogini Dasha and Jaimini Chara Dasha |
| `vedic/monthly.py` | Month tab: area-by-area monthly outlook, key dates, eclipses, day calendar, 12-month heatmap |
| `vedic/career.py` | Job tab: 10th house, D10, Amatyakaraka, suitable fields, job vs business, career timeline |
| `vedic/compare.py` | Compare positions with other software and diagnose differences |
| `vedic/journal.py` | Prediction journal (CSV) and agreement with the day ratings |
| `vedic/shadbala.py` | Full six-fold Shadbala (BPHS) for the seven classical planets |
| `vedic/aspects.py` | Combustion and planetary aspects (graha drishti) |
| `vedic/remedies.py` | Remedies tab: which planets are flagged, why, and the three remedy tiers |
| `vedic/plots.py` | Plotly charts |
| `vedic/report.py` | Downloadable HTML report |
| `tests/test_engine.py` | Sanity checks (SAV = 337, BAV totals, dasha order, transit continuity, Parashari techniques, life areas) |
| `tests/smoke_pages.py` | Opens every page in a headless Streamlit and fails on any error |
| `.github/workflows/tests.yml` | Runs pyflakes, pytest and the page smoke test on every push |

**Tip when asking an AI to change the app:** paste this table plus only the file(s) involved,
e.g. "change the career wording in `vedic/narratives.py`". Small, targeted files are much easier
for any assistant to edit without losing earlier work.

## What's calculated vs. simplified

- **Real calculations:** planet and Ascendant positions (Swiss Ephemeris, Lahiri/Raman/KP), Nakshatra
  and pada, D9, D10, Chara Karakas, Vimshottari Dasha, Ashtakavarga (classical BPHS tables), and
  transit Kakshya timing, full Shadbala (conventions listed in `vedic/shadbala.py`), Panchang tithi and
  nakshatra, Bhrigu Bindu and transit contacts.
- **Interpretive rules:** weekly day ratings (Tara Bala, Chandra Bala, Moon Ashtakavarga, tithi, weekday lord)
  and all written readings follow classical rules but are guidance, not certainties.
- **Simplified:** the *quick indicator* on the Planet Strength tab and *Dhana Yoga* use simple rules.
  Houses and aspects (for remedies and planet stories) are whole-sign; Sripati Bhava Chalit is shown on the Houses page.
- **Life-area ratings** add up classical factors (+1 / 0 / −1 each); every factor is listed on the page.
- Interpretations are for reflection only.
