"""Open the app and every page with Streamlit's test runner; fail if any page raises an error.

Uses manual coordinates so it does not depend on the place-lookup service.
Run: python tests/smoke_pages.py
"""
import glob
import os
import sys

from streamlit.testing.v1 import AppTest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)  # page paths in st.navigation are relative to the app folder
at = AppTest.from_file(os.path.join(ROOT, "streamlit_app.py"), default_timeout=300)
at.run()
at.sidebar.checkbox[0].check().run()  # "Enter coordinates manually"
failures = [("main", e.value) for e in at.exception]
for page in sorted(glob.glob("app_pages/*.py")):
    at.switch_page(page).run()
    failures += [(page, e.value) for e in at.exception]
    print(f"{page}: {'OK' if not at.exception else 'ERROR'}")
for page, err in failures:
    print(f"\n--- {page} ---\n{err}")
sys.exit(1 if failures else 0)
