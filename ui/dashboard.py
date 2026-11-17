import pandas as pd
import requests
import streamlit as st

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="solar_view", layout="wide")
st.title("solar_view")

if "diagnosis_text" not in st.session_state:
    st.session_state.diagnosis_text = None

if "user_tz" not in st.session_state or not st.session_state.user_tz:
    st.session_state.user_tz = st.context.timezone or "UTC"

user_tz = st.session_state.user_tz

col_btn, col_info = st.columns([1, 4])
with col_btn:
    if st.button("Analyze Live Array", type="primary"):
        with st.spinner("Evaluating live inverter stream..."):
            resp = requests.post(f"{API_BASE}/diagnose", timeout=60)
            if resp.status_code == 200:
                st.session_state.diagnosis_text = resp.json().get("diagnosis")
            else:
                st.error(resp.json().get("detail", "Diagnosis failed"))

with col_info:
    if st.session_state.diagnosis_text:
        st.info(st.session_state.diagnosis_text)


@st.fragment(run_every=2)
def live_panel():
    try:
        resp = requests.get(f"{API_BASE}/live", timeout=5)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        st.error(f"Waiting for backend stream: {exc}")
        return

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Array Output", f"{data['total_watts']} W")
    m2.metric("Avg Panel Temp", f"{data['avg_temp']} °C")
    m3.metric("Active Inverters", f"{len(data['latest'])} / 4")
    m4.metric("Active Alerts", data["active_alerts"])

    df = pd.DataFrame(data["readings"])
    if not df.empty:
        local_dt = pd.to_datetime(df["recorded_at"], utc=True).dt.tz_convert(user_tz)
        df["time"] = local_dt.dt.strftime("%H:%M:%S")

        c1, c2 = st.columns(2)
        with c1:
            st.subheader(f"AC Power Output (W) - {user_tz}")
            power_pivot = df.pivot_table(index="time", columns="inverter_id", values="ac_power_watts", aggfunc="last")
            st.line_chart(power_pivot, height=300)

        with c2:
            st.subheader(f"Panel Temperature (°C) - {user_tz}")
            temp_pivot = df.pivot_table(index="time", columns="inverter_id", values="panel_temp_c", aggfunc="last")
            st.line_chart(temp_pivot, height=300)

        st.subheader("Inverter Status")
        status_cols = st.columns(len(data["latest"]))
        for idx, inv in enumerate(data["latest"]):
            with status_cols[idx]:
                state = inv["status_code"]
                label = f"**{inv['inverter_id']}** - {inv['ac_power_watts']} W | {inv['dc_voltage']} V | {inv['panel_temp_c']} °C"
                if state == "NORMAL":
                    st.success(f"{label} ({state})")
                else:
                    st.warning(f"{label} ({state})")


live_panel()