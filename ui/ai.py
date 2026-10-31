"""Personalised write-ups with Google Gemini.

The key is read from Streamlit secrets (GEMINI_API_KEY); without it the section explains how to add one.
Only calculated chart facts are sent: no name, birth date, birth time or place.
"""
import requests
import streamlit as st

DEFAULT_MODEL = "gemini-flash-latest"
URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
INSTRUCTIONS = (
    "You are an experienced Vedic astrologer of the Parashari school writing for a client. Using ONLY the chart "
    "facts provided (never invent placements, yogas or dates), write a warm, practical, personalised reading of "
    "about 350-450 words in plain English, with these markdown headings: Overview, Strengths, What needs care, "
    "Timing (refer to the dates given), Practical advice. Explain any Sanskrit term briefly. Be balanced and "
    "encouraging, never fatalistic; present astrology as guidance, not certainty. Do not give medical, legal or "
    "financial instructions; for health suggest seeing a doctor."
)


def _secret(name, default=None):
    try:
        return st.secrets.get(name, default)
    except Exception:  # no secrets file at all
        return default


@st.cache_data(ttl=7 * 86400, show_spinner=False)
def _generate(model, key, prompt):
    resp = requests.post(URL.format(model=model), headers={"x-goog-api-key": key}, timeout=90, json={
        "systemInstruction": {"parts": [{"text": INSTRUCTIONS}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7},
    })
    if resp.status_code != 200:
        raise RuntimeError(_explain(resp))
    parts = resp.json().get("candidates", [{}])[0].get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts).strip()
    if not text:
        raise RuntimeError("Gemini returned an empty answer. Try again in a minute.")
    return text


def _explain(resp):
    try:
        msg = resp.json()["error"]["message"]
    except Exception:
        msg = resp.text[:200]
    if resp.status_code in (400, 401, 403) and "key" in msg.lower():
        return "Gemini rejected the API key. Check GEMINI_API_KEY in the app's Secrets."
    if resp.status_code == 429:
        return "Gemini's free-tier limit was reached. Wait a minute (or until tomorrow for the daily limit)."
    if resp.status_code == 404:
        return f"The model isn't available ({msg}). Set GEMINI_MODEL in Secrets to a current model name."
    return f"Gemini error {resp.status_code}: {msg}"


def reading_section(topic, facts):
    """Draw the 'Personalised reading' section for `topic` from a list of fact lines (markdown is fine)."""
    st.subheader("✍️ Personalised reading (Google Gemini)")
    key = _secret("GEMINI_API_KEY")
    if not key:
        st.info("Add a free Google Gemini API key to get a written reading of this page: get a key at "
                "**aistudio.google.com/apikey**, then in Streamlit open **Manage app → ⋮ → Settings → Secrets** "
                "and paste `GEMINI_API_KEY = \"your-key\"`. Save, and this button appears.")
        return
    model = _secret("GEMINI_MODEL", DEFAULT_MODEL)
    prompt = f"Topic: {topic}\n\nChart facts:\n" + "\n".join(f"- {f}" for f in facts)
    state = f"ai_{topic}"
    if st.button(f"Write my {topic.lower()} reading", key=f"btn_{topic}", type="primary"):
        with st.spinner("Gemini is writing your reading…"):
            try:
                st.session_state[state] = (prompt, _generate(model, key, prompt))
            except (RuntimeError, requests.RequestException) as exc:
                st.error(str(exc) if isinstance(exc, RuntimeError) else "Couldn't reach Gemini. Try again shortly.")
    saved = st.session_state.get(state)
    if saved and saved[0] == prompt:  # hide a reading made for a different chart
        with st.container(border=True):
            st.markdown(saved[1])
        st.download_button("Download reading", saved[1], file_name=f"{topic.lower().replace(' ', '_')}_reading.md",
                           key=f"dl_{topic}")
    with st.expander("What is sent to Gemini"):
        st.caption(f"Model: {model}. Only these calculated facts are sent; no name, birth date, time or place. "
                   "On Google's free tier, prompts may be used to improve Google's products.")
        st.code(prompt, language=None)
