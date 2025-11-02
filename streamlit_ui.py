import streamlit as st
import requests
import os
from datetime import datetime
import httpx

API_URL = "http://localhost:8000/plan"  # Adjust if FastAPI runs elsewhere

DEFAULT_SERVICES = {
    "root_agent":      os.getenv("ROOT_URL",      "http://localhost:10022"),
    "discovery_agent": os.getenv("DISCOVERY_URL", "http://localhost:10020"),
    "routing_agent":   os.getenv("ROUTING_URL",   "http://localhost:10021")
}
if "cursors" not in st.session_state:
    st.session_state.cursors = {name: 0.0 for name in DEFAULT_SERVICES}

st.set_page_config(page_title='Local explorer', 
                    page_icon = "assets/ADK.png",
                    initial_sidebar_state = 'auto',
                    layout="wide")

with st.sidebar:
    st.image("assets/a2a.png")
    st.image("assets/ADK.png")


st.title("🗺️ Local Explorer Assistant")
st.markdown("Plan your personalized day trip with AI.")

with st.form("trip_form"):
    query = st.text_input("Describe your request:", "")
    submitted = st.form_submit_button("Plan My Trip")

if submitted:
    with st.spinner("Contacting your travel assistant..."):
        try:
            payload = {
                "query": query
            }
            response = requests.post(API_URL, json=payload)
            if response.status_code == 200:
                itinerary = response.json().get("itinerary", "No response from agent.")
                st.success("Here's your local exploration plan:")
                st.markdown(itinerary, unsafe_allow_html=True)
            else:
                st.error(f"Error: {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"Request failed: {e}")

