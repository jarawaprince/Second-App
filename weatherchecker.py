# app.py
# A super simple weather checker (no API key needed) using Open-Meteo

import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="WeatherCheckerPro — Simple Weather", page_icon="⛅")

st.title("⛅ WeatherCheckerPro — Simple City Weather")
st.caption("Type a city name and get current weather + the next 24 hours (free, no API key).")

# --- Small helper: map Open-Meteo weather codes to text -----------------------
WEATHERCODE_TEXT = {
    0: "Clear",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Freezing drizzle (light)", 57: "Freezing drizzle (dense)",
    61: "Light rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Freezing rain (light)", 67: "Freezing rain (heavy)",
    71: "Light snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains",
    80: "Rain showers (slight)", 81: "Rain showers (moderate)", 82: "Rain showers (violent)",
    85: "Snow showers (slight)", 86: "Snow showers (heavy)",
    95: "Thunderstorm (slight/moderate)", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

@st.cache_data(show_spinner=False, ttl=600)
def geocode_city(name: str):
    """Find the first matching city (lat/lon). Returns dict or None."""
    try:
        r = requests.get(GEOCODE_URL, params={"name": name, "count": 1, "language": "en"}, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data.get("results"):
            return None
        item = data["results"][0]
        return {
            "name": item.get("name"),
            "country": item.get("country"),
            "admin1": item.get("admin1"),
            "lat": item.get("latitude"),
            "lon": item.get("longitude"),
        }
    except requests.RequestException:
        return None

@st.cache_data(show_spinner=False, ttl=300)
def fetch_weather(lat: float, lon: float):
    """
    Get current weather + hourly for next days.
    We use `current_weather=true` (simple & reliable) and a few hourly vars.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true",
        "hourly": "temperature_2m,precipitation_probability,weathercode",
        "timezone": "auto",  # times come already in the local timezone of the location
    }
    try:
        r = requests.get(FORECAST_URL, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.RequestException:
        return None

# ----------------------------- UI --------------------------------------------
with st.form("city_form"):
    city_input = st.text_input("City name", value="Sydney", help="Try: Melbourne, Brisbane, New York, London, Tokyo…")
    submitted = st.form_submit_button("Get weather")

if submitted:
    if not city_input.strip():
        st.warning("Please type a city name.")
        st.stop()

    with st.spinner("Finding your city…"):
        place = geocode_city(city_input.strip())

    if not place:
        st.error("Sorry, I couldn't find that city. Try a different spelling (e.g., 'Sydney, AU').")
        st.stop()

    st.success(f"Found: **{place['name']}**, {place.get('admin1') or ''} {place['country']}  "
               f"({place['lat']:.2f}, {place['lon']:.2f})")

    with st.spinner("Fetching weather…"):
        data = fetch_weather(place["lat"], place["lon"])

    if not data:
        st.error("Could not fetch weather data. Please try again.")
        st.stop()

    # --------- Current weather block -----------------------------------------
    cw = data.get("current_weather") or {}
    temp_now = cw.get("temperature")
    windspeed = cw.get("windspeed")
    winddir = cw.get("winddirection")
    code = cw.get("weathercode")
    desc = WEATHERCODE_TEXT.get(code, "N/A")

    st.subheader("Current weather")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Temperature (°C)", f"{temp_now if temp_now is not None else '—'}")
