import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from sklearn.ensemble import IsolationForest

# --------------------------------------------------
# Page settings
# --------------------------------------------------
st.set_page_config(
    page_title="ESP32 Environmental Monitor",
    page_icon="🌿",
    layout="wide"
)

ESP32_URL = "http://192.168.12.249/data"

# --------------------------------------------------
# Styling
# --------------------------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f4f7f5;
    }

    .main-title {
        font-size: 40px;
        font-weight: 700;
        color: #173f35;
        margin-bottom: 0;
    }

    .subtitle {
        color: #60736e;
        font-size: 17px;
        margin-bottom: 25px;
    }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #dce7e2;
        border-radius: 14px;
        padding: 18px;
        box-shadow: 0 4px 12px rgba(20, 70, 55, 0.06);
    }

    .normal-box {
        background: #ddf7e8;
        color: #17683b;
        border: 1px solid #a8e2c0;
        border-radius: 12px;
        padding: 15px;
        font-weight: 600;
    }

    .warning-box {
        background: #ffe8e8;
        color: #a52626;
        border: 1px solid #f3b0b0;
        border-radius: 12px;
        padding: 15px;
        font-weight: 600;
    }

    .learning-box {
        background: #fff4d6;
        color: #805d00;
        border: 1px solid #ead18b;
        border-radius: 12px;
        padding: 15px;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# Store sensor history
# --------------------------------------------------
if "sensor_history" not in st.session_state:
    st.session_state.sensor_history = []

st.markdown(
    '<p class="main-title">Environmental Monitor</p>',
    unsafe_allow_html=True
)

st.markdown(
    '<p class="subtitle">ESP32 live monitoring and anomaly detection</p>',
    unsafe_allow_html=True
)


# --------------------------------------------------
# Automatically update every 2 seconds
# --------------------------------------------------
@st.fragment(run_every=2)
def live_dashboard():

    try:
        response = requests.get(ESP32_URL, timeout=3)
        response.raise_for_status()
        sensor_data = response.json()

        temperature = float(sensor_data["temperature"])
        humidity = float(sensor_data["humidity"])
        pressure = float(sensor_data["pressure"])

        new_reading = {
            "Time": datetime.now(),
            "Temperature": temperature,
            "Humidity": humidity,
            "Pressure": pressure
        }

        st.session_state.sensor_history.append(new_reading)

        # Keep the most recent 300 readings
        st.session_state.sensor_history = (
            st.session_state.sensor_history[-300:]
        )

        df = pd.DataFrame(st.session_state.sensor_history)

        # ------------------------------------------
        # Connection indicator
        # ------------------------------------------
        st.success(
            f"ESP32 connected • Last update: "
            f"{datetime.now().strftime('%I:%M:%S %p')}"
        )

        # ------------------------------------------
        # Metric cards
        # ------------------------------------------
        col1, col2, col3 = st.columns(3)

        previous_temperature = None
        previous_humidity = None
        previous_pressure = None

        if len(df) > 1:
            previous_temperature = df.iloc[-2]["Temperature"]
            previous_humidity = df.iloc[-2]["Humidity"]
            previous_pressure = df.iloc[-2]["Pressure"]

        temperature_change = None
        humidity_change = None
        pressure_change = None

        if previous_temperature is not None:
            temperature_change = temperature - previous_temperature
            humidity_change = humidity - previous_humidity
            pressure_change = pressure - previous_pressure

        col1.metric(
            "Temperature",
            f"{temperature:.1f} °C",
            None if temperature_change is None
            else f"{temperature_change:+.1f} °C"
        )

        col2.metric(
            "Humidity",
            f"{humidity:.1f} %",
            None if humidity_change is None
            else f"{humidity_change:+.1f} %"
        )

        col3.metric(
            "Pressure",
            f"{pressure:.1f} hPa",
            None if pressure_change is None
            else f"{pressure_change:+.1f} hPa"
        )

        st.write("")

        # ------------------------------------------
        # Simple AI: Isolation Forest
        # ------------------------------------------
        st.subheader("AI Anomaly Detection")

        if len(df) >= 20:
            features = df[
                ["Temperature", "Humidity", "Pressure"]
            ]

            model = IsolationForest(
                contamination=0.10,
                random_state=42
            )

            predictions = model.fit_predict(features)
            df["AI Result"] = predictions

            current_prediction = predictions[-1]

            if current_prediction == -1:
                st.markdown(
                    """
                    <div class="warning-box">
                    ⚠️ Unusual environmental reading detected.
                    The current combination of temperature,
                    humidity, and pressure differs from the
                    recent pattern.
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    """
                    <div class="normal-box">
                    ✓ Current conditions appear normal based
                    on the recent sensor pattern.
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            readings_needed = 20 - len(df)

            st.markdown(
                f"""
                <div class="learning-box">
                🧠 AI is learning the normal environment.
                Collecting {readings_needed} more readings
                before anomaly detection begins.
                </div>
                """,
                unsafe_allow_html=True
            )

        st.write("")

        # ------------------------------------------
        # Charts and data table
        # ------------------------------------------
        chart_tab, data_tab = st.tabs(
            ["Live Charts", "Sensor Log"]
        )

        with chart_tab:
            left_chart, right_chart = st.columns(2)

            with left_chart:
                st.markdown("#### Temperature")
                st.line_chart(
                    df.set_index("Time")[["Temperature"]],
                    color="#e56b4a"
                )

                st.markdown("#### Pressure")
                st.line_chart(
                    df.set_index("Time")[["Pressure"]],
                    color="#5577cc"
                )

            with right_chart:
                st.markdown("#### Humidity")
                st.line_chart(
                    df.set_index("Time")[["Humidity"]],
                    color="#3aa981"
                )

                st.markdown("#### System Information")
                st.write(f"**ESP32 address:** `{ESP32_URL}`")
                st.write(f"**Stored readings:** {len(df)}")
                st.write("**Update interval:** 2 seconds")
                st.write("**AI model:** Isolation Forest")

        with data_tab:
            display_df = df.copy()
            display_df["Time"] = display_df["Time"].dt.strftime(
                "%H:%M:%S"
            )

            st.dataframe(
                display_df.iloc[::-1],
                use_container_width=True,
                hide_index=True
            )

            csv_data = df.to_csv(index=False).encode("utf-8")

            st.download_button(
                "Download sensor data",
                data=csv_data,
                file_name="esp32_sensor_data.csv",
                mime="text/csv"
            )

    except requests.exceptions.RequestException as error:
        st.error("ESP32 connection lost.")
        st.code(str(error))

        st.info(
            "Make sure this dashboard is running at "
            "localhost:8501 and that the ESP32 and laptop "
            "are connected to the same Wi-Fi."
        )

    except (KeyError, ValueError) as error:
        st.error("The ESP32 returned invalid sensor data.")
        st.code(str(error))


live_dashboard()
