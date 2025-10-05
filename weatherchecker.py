# app.py
# Simple Weather Checker with dynamic background based on temperature

import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="WeatherCheckerPro — Simple Weather", page_icon="⛅")

st.title("⛅ WeatherCheckerPro — Simple City Weather")
st.caption("Type a city name and get current weather + 24-hour forecast. Background changes with temperature!")

# --- Weather code descriptions ------------------------------------------------
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
    """Find city coordinates (lat/lon)."""
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
    """Get current weather + hourly data."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true",
        "hourly": "temperature_2m,precipitation_probability,weathercode",
        "timezone": "auto",
    }
    try:
        r = requests.get(FORECAST_URL, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.RequestException:
        return None

# --- Choose city form ----------------------------------------------------------
with st.form("city_form"):
    city_input = st.text_input("City name", value="Sydney", help="Try Melbourne, Brisbane, London, Tokyo, etc.")
    submitted = st.form_submit_button("Get weather")

if submitted:
    if not city_input.strip():
        st.warning("Please type a city name.")
        st.stop()

    with st.spinner("Finding your city…"):
        place = geocode_city(city_input.strip())

    if not place:
        st.error("Sorry, I couldn't find that city. Try again.")
        st.stop()

    st.success(f"Found: **{place['name']}**, {place.get('admin1') or ''} {place['country']}")

    with st.spinner("Fetching weather…"):
        data = fetch_weather(place["lat"], place["lon"])

    if not data:
        st.error("Could not fetch weather data. Try again.")
        st.stop()

    # --- Current weather -------------------------------------------------------
    cw = data.get("current_weather") or {}
    temp_now = cw.get("temperature")
    windspeed = cw.get("windspeed")
    winddir = cw.get("winddirection")
    code = cw.get("weathercode")
    desc = WEATHERCODE_TEXT.get(code, "N/A")

    # ✅ Dynamic background color
    if temp_now is not None:
        if temp_now < 10:
            bg_color = "#b3daff"   # Cold = light blue
        elif temp_now < 25:
            bg_color = "#d4f1c5"   # Mild = light green
        else:
            bg_color = "#ffb3b3"   # Hot = light red
    else:
        bg_color = "#ffffff"       # Default white

    # Inject CSS dynamically
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {bg_color};
            transition: background-color 0.8s ease;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

    st.subheader("Current weather")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Temperature (°C)", f"{temp_now if temp_now is not None else '—'}")
    c2.metric("Wind (km/h)", f"{windspeed if windspeed is not None else '—'}")
    c3.metric("Wind dir (°)", f"{winddir if winddir is not None else '—'}")
    c4.metric("Sky", desc)

    # --- Next 24 hours chart ---------------------------------------------------
    st.subheader("Next 24 hours")
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    pops = hourly.get("precipitation_probability")

    df = pd.DataFrame({"time": pd.to_datetime(times), "temperature_2m": temps})
    if pops is not None:
        df["precipitation_probability"] = pops
    df_24 = df.head(24).copy()

    st.line_chart(df_24.set_index("time")["temperature_2m"], height=220)

    nice_table = df_24.copy()
    nice_table["time"] = nice_table["time"].dt.strftime("%Y-%m-%d %H:%M")
    if "precipitation_probability" not in nice_table.columns:
        nice_table["precipitation_probability"] = None
    nice_table.rename(columns={
        "time": "Local time",
        "temperature_2m": "Temp (°C)",
        "precipitation_probability": "Rain chance (%)"
    }, inplace=True)
    st.dataframe(nice_table, use_container_width=True)

    st.caption("Data source: Open-Meteo (free). Background changes with temperature 🌡️")