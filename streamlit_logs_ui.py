# logs_app.py
import os
from datetime import datetime
import httpx
import streamlit as st
from streamlit_autorefresh import st_autorefresh

DEFAULT_SERVICES = {
    "root_agent":      os.getenv("ROOT_URL",      "http://localhost:10022"),
    "discovery_agent": os.getenv("DISCOVERY_URL", "http://localhost:10020"),
    "routing_agent":   os.getenv("ROUTING_URL",   "http://localhost:10021"),
}

LEVEL_ICON = {"DEBUG":"⚙️","INFO":"ℹ️","WARNING":"⚠️","ERROR":"❌","CRITICAL":"🚨"}

st.set_page_config(page_title="Local Explorer – Logs", layout="wide", page_icon="📜")
st.title("📜 Local Explorer — Live Logs")

# ---- Sidebar controls ----
with st.sidebar:
    st.header("Backends")
    services = {}
    for name, url in DEFAULT_SERVICES.items():
        services[name] = st.text_input(name, url)
    level_filter = st.selectbox("Level filter", ["ALL","DEBUG","INFO","WARNING","ERROR","CRITICAL"], index=2)
    interval_ms = st.slider("Refresh interval (ms)", 500, 5000, 2000, 100)
    st.caption("Each tab refreshes independently.")

# ---- Session state init / sync ----
for key, factory in [
    ("cursors", lambda: {n: 0.0 for n in services}),
    ("logs",    lambda: {n: []  for n in services}),
    ("paused",  lambda: {n: False for n in services}),
]:
    if key not in st.session_state or not isinstance(st.session_state[key], dict):
        st.session_state[key] = factory()

# ensure keys exist for all current services
for n in services.keys():
    st.session_state.cursors.setdefault(n, 0.0)
    st.session_state.logs.setdefault(n, [])
    st.session_state.paused.setdefault(n, False)
# optionally drop keys for removed services
for dkey in ("cursors","logs","paused"):
    for n in list(st.session_state[dkey].keys()):
        if n not in services:
            del st.session_state[dkey][n]

def fetch_logs(base_url: str, since: float, level: str):
    url = base_url.rstrip("/") + "/ops/logs"
    with httpx.Client(timeout=5.0) as client:
        r = client.get(url, params={"since": since, "limit": 300, "level": level})
        r.raise_for_status()
        return r.json()

# ---- Tabs ----
names = list(services.keys())
tabs = st.tabs(names)

for (name, base_url), tab in zip(services.items(), tabs):
    with tab:
        st.subheader(name)
        c1, c2, c3, c4 = st.columns([1,1,1,6])

        with c1:
            paused_default = st.session_state.paused.get(name, False)
            paused = st.checkbox("Pause", value=paused_default, key=f"pause_{name}")
            st.session_state.paused[name] = paused

        with c2:
            if st.button("Clear logs", key=f"clear_{name}"):
                st.session_state.logs[name] = []
                st.session_state.cursors[name] = 0.0
                st.toast(f"Cleared logs for {name}")

        with c3:
            do_manual = st.button("Refresh now", key=f"refresh_{name}")

        # Per-tab auto refresh
        tick = st_autorefresh(interval=interval_ms, key=f"tick_{name}")

        should_fetch = (not st.session_state.paused[name]) or do_manual or tick
        if should_fetch:
            try:
                data = fetch_logs(base_url, st.session_state.cursors[name], level_filter)
                items = data.get("items", [])
                if items:
                    st.session_state.cursors[name] = data.get("next_since", st.session_state.cursors[name])
                    st.session_state.logs[name].extend(items)
                    # bound memory
                    if len(st.session_state.logs[name]) > 2000:
                        st.session_state.logs[name] = st.session_state.logs[name][-1000:]
            except Exception as e:
                st.warning(f"Fetch error from {base_url}: {e}")

        # Render last 300 entries from local buffer
        for row in st.session_state.logs[name][-300:]:
            level = row.get("level", "INFO")
            icon = LEVEL_ICON.get(level, "•")
            when = row.get("time") or datetime.fromtimestamp(row["ts"]).isoformat(timespec="seconds")
            logger = row.get("logger", "")
            msg = row.get("message", "")
            st.markdown(f"{icon} **{when}** `{level}` [{logger}] — {msg}")
