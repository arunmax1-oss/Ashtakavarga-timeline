"""Personalised write-ups with Google Gemini.

The key is read from Streamlit secrets (GEMINI_API_KEY); without it the section explains how to add one.
Only calculated chart facts are sent: no name, birth date, birth time or place.
"""
import time

import requests
import streamlit as st

DEFAULT_MODEL = "gemini-flash-latest"
# Tried in order when the chosen model is busy; names Google doesn't recognise are skipped.
FALLBACK_MODELS = ["gemini-flash-lite-latest", "gemini-2.5-flash", "gemini-2.5-flash-lite"]
BUSY = {404, 429, 500, 502, 503, 504}
RETRY_WAITS = (0, 4)  # seconds before each attempt on one model
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


def clean_key(raw):
    """The key as pasted, minus stray spaces, line breaks and quotes that would break the request."""
    return str(raw or "").strip().strip("\"'“”‘’").strip()


def network_message(exc):
    """Plain-English reason for a failed request."""
    if isinstance(exc, requests.Timeout):
        return "Gemini took too long to answer. Try again; if it keeps happening, set GEMINI_MODEL to a faster model."
    if isinstance(exc, requests.exceptions.InvalidHeader):
        return ("The API key contains a space, line break or other stray character. In Secrets, retype it as "
                "GEMINI_API_KEY = \"AIza...\" on one line with plain straight quotes.")
    if isinstance(exc, requests.ConnectionError):
        return "Couldn't connect to Gemini (network problem). Try again in a minute."
    return f"Couldn't get a reading from Gemini ({type(exc).__name__}: {str(exc)[:200]})."


class _Busy(Exception):
    """This model can't answer right now (overloaded, rate-limited or unknown): try the next one."""


def _call(model, key, system, contents):
    resp = requests.post(URL.format(model=model), headers={"x-goog-api-key": key}, timeout=150, json={
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": role, "parts": [{"text": text}]} for role, text in contents],
        "generationConfig": {"temperature": 0.7},
    })
    if resp.status_code in BUSY:
        raise _Busy(resp.status_code)
    if resp.status_code != 200:
        raise RuntimeError(_explain(resp))
    parts = resp.json().get("candidates", [{}])[0].get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts).strip()
    if not text:
        raise _Busy("empty")
    return text


@st.cache_data(ttl=7 * 86400, show_spinner=False)
def _generate(models, key, system, contents):
    """(model used, text) for a conversation: `contents` is a tuple of (role, text), role "user" or "model". Busy models are retried with a short wait, then the next model is tried.
    Failures are not cached, so a later click tries again."""
    seen = []
    for model in models:
        for wait in RETRY_WAITS:
            time.sleep(wait)
            try:
                return model, _call(model, key, system, contents)
            except _Busy as exc:
                seen.append(exc.args[0])
                if exc.args[0] in (404, 429):  # unknown model or its quota used up: retrying won't help
                    break
    if seen and all(code == 404 for code in seen):
        raise RuntimeError("Google doesn't recognise any of the model names. Set GEMINI_MODEL in Secrets to a current "
                           "model listed at ai.google.dev/gemini-api/docs/models.")
    if seen and all(code == 429 for code in seen if code != 404):
        raise RuntimeError("Gemini's free-tier limit is used up on every model for now. Wait a minute, or until "
                           "tomorrow for the daily limit.")
    raise RuntimeError("Gemini is overloaded right now (all models tried). This is on Google's side and usually "
                       "passes within minutes; please try again shortly.")


def _explain(resp):
    try:
        msg = resp.json()["error"]["message"]
    except Exception:
        msg = resp.text[:200]
    if resp.status_code in (400, 401, 403) and "key" in msg.lower():
        return "Gemini rejected the API key. Check GEMINI_API_KEY in the app's Secrets."
    return f"Gemini error {resp.status_code}: {msg}"


SETUP_HELP = ("Add a free Google Gemini API key to use this: get a key at **aistudio.google.com/apikey**, then in "
              "Streamlit open **Manage app → ⋮ → Settings → Secrets** and paste `GEMINI_API_KEY = \"your-key\"`.")


def settings():
    """(key, models to try) from Secrets, or (None, None) if no key is set."""
    key = clean_key(_secret("GEMINI_API_KEY"))
    if not key:
        return None, None
    model = clean_key(_secret("GEMINI_MODEL")) or DEFAULT_MODEL
    return key, tuple(dict.fromkeys([model] + FALLBACK_MODELS))


def converse(system, contents):
    """(model used, text) or raises RuntimeError with a plain-English message."""
    key, models = settings()
    try:
        return _generate(models, key, system, tuple(contents))
    except (requests.RequestException, ValueError) as exc:
        raise RuntimeError(network_message(exc)) from exc


def reading_section(topic, facts):
    """Draw the 'Personalised reading' section for `topic` from a list of fact lines (markdown is fine)."""
    st.subheader("✍️ Personalised reading (Google Gemini)")
    key = clean_key(_secret("GEMINI_API_KEY"))
    if not key:
        st.info("Add a free Google Gemini API key to get a written reading of this page: get a key at "
                "**aistudio.google.com/apikey**, then in Streamlit open **Manage app → ⋮ → Settings → Secrets** "
                "and paste `GEMINI_API_KEY = \"your-key\"`. Save, and this button appears.")
        return
    model = clean_key(_secret("GEMINI_MODEL")) or DEFAULT_MODEL
    models = tuple(dict.fromkeys([model] + FALLBACK_MODELS))
    prompt = f"Topic: {topic}\n\nChart facts:\n" + "\n".join(f"- {f}" for f in facts)
    state = f"ai_{topic}"
    if st.button(f"Write my {topic.lower()} reading", key=f"btn_{topic}", type="primary"):
        with st.spinner("Gemini is writing your reading…"):
            try:
                st.session_state[state] = (prompt, *_generate(models, key, INSTRUCTIONS, (("user", prompt),)))
            except RuntimeError as exc:
                st.error(str(exc))
            except (requests.RequestException, ValueError) as exc:
                st.error(network_message(exc))
    saved = st.session_state.get(state)
    if saved and saved[0] == prompt:  # hide a reading made for a different chart
        with st.container(border=True):
            st.markdown(saved[2])
            st.caption(f"Written by {saved[1]}.")
        st.download_button("Download reading", saved[2], file_name=f"{topic.lower().replace(' ', '_')}_reading.md",
                           key=f"dl_{topic}")
    with st.expander("What is sent to Gemini"):
        st.caption(f"Model: {model}, with {', '.join(FALLBACK_MODELS)} as backups when it is busy. Only these calculated facts are sent; no name, birth date, time or place. "
                   "On Google's free tier, prompts may be used to improve Google's products.")
        st.code(prompt, language=None)
