import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="ESP32 Environmental Monitor",
    page_icon="🌡️",
    layout="wide"
)

st.title("ESP32 Environmental Monitor")

# Replace this with the IP shown in your Serial Monitor
ESP32_URL = "http://192.168.12.249/data"

if "history" not in st.session_state:
    st.session_state.history = []

try:
    response = requests.get(ESP32_URL, timeout=5)
    response.raise_for_status()
    data = response.json()

    temperature = data["temperature"]
    humidity = data["humidity"]
    pressure = data["pressure"]

    current_reading = {
        "Time": datetime.now(),
        "Temperature (°C)": temperature,
        "Humidity (%)": humidity,
        "Pressure (hPa)": pressure
    }

    st.session_state.history.append(current_reading)

    col1, col2, col3 = st.columns(3)

    col1.metric("Temperature", f"{temperature:.1f} °C")
    col2.metric("Humidity", f"{humidity:.1f} %")
    col3.metric("Pressure", f"{pressure:.1f} hPa")

    df = pd.DataFrame(st.session_state.history)

    st.subheader("Sensor History")
    st.line_chart(
        df,
        x="Time",
        y=["Temperature (°C)", "Humidity (%)", "Pressure (hPa)"]
    )

    st.dataframe(df, use_container_width=True)

except requests.exceptions.RequestException as error:
    st.error(f"Could not connect to the ESP32: {error}")
    st.info("Check that the ESP32 and computer are connected to the same Wi-Fi.")

if st.button("Refresh readings"):
    st.rerun()
