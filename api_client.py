import os
from html import escape

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_ORIGIN = os.getenv("TASKFLOW_API_ORIGIN", "http://localhost:8000").rstrip("/")
API_URL = os.getenv("TASKFLOW_API_URL", API_ORIGIN).rstrip("/")


def browser_link(label, path, sidebar=False):
    url = escape(f"{API_ORIGIN}{path}", quote=True)
    container = st.sidebar if sidebar else st
    container.markdown(
        f'<a href="{url}" target="_self">{escape(label)}</a>',
        unsafe_allow_html=True,
    )


def api(method, path, *, authenticated=True, **kwargs):
    token = st.context.cookies.get("taskflow_session")
    headers = {"Authorization": f"Bearer {token}"} if authenticated and token else {}

    try:
        with st.spinner("Contacting TaskFlow…"):
            response = requests.request(
                method, f"{API_URL}{path}", headers=headers, timeout=8, **kwargs
            )
    except requests.Timeout:
        st.error("The API did not respond in time. Please try again.")
        return None
    except requests.RequestException:
        st.error("Could not reach the TaskFlow API.")
        return None

    if response.status_code == 401 and authenticated:
        st.warning("Your session expired. Sign in again to continue.")
        browser_link("Sign in", "/browser-login")
        return None

    try:
        data = response.json()
    except ValueError:
        st.error("TaskFlow returned an unexpected response.")
        return None

    if not response.ok:
        detail = data.get("detail") if isinstance(data, dict) else None
        if isinstance(detail, list):
            detail = "\n\n".join(
                f"{' → '.join(str(part) for part in item['loc'])}: {item['msg']}"
                for item in detail
        )
        st.error(detail or f"Request failed (HTTP {response.status_code}).")
        return None

    return data