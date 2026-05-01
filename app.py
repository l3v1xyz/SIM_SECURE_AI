import streamlit as st
import pandas as pd
import time
from geopy.distance import geodesic
from datetime import datetime
import uuid
from streamlit_geolocation import streamlit_geolocation

# --- 1. SYSTEM CONFIGURATION ---
st.set_page_config(page_title="SIM-SECURE AI", layout="wide", page_icon="🌐")

# --- 2. CLOUD DATABASE (Persistent Memory) ---
# This allows you and your friend to see the same data if hosted on Streamlit Cloud
if 'live_transactions' not in st.session_state:
    st.session_state.live_transactions = []

if 'user_database' not in st.session_state:
    # We set Levi's baseline. For the demo, make sure to type around this speed!
    st.session_state.user_database = {
        "Levi (Owner)": {"base_lat": -1.286, "base_lon": 36.817, "base_wpm": 60}
    }

# Variables for the live typing test
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'wpm_result' not in st.session_state:
    st.session_state.wpm_result = None


# --- 3. CORE AI ENGINE ---
def evaluate_transaction(user_id, current_lat, current_lon, current_wpm, req_type):
    profile = st.session_state.user_database.get(user_id)
    risk_score = 0
    reasons = []

    # 1. LIVE Impossible Travel (Comparing GPS to Baseline)
    if current_lat is not None and current_lon is not None:
        dist = geodesic((profile["base_lat"], profile["base_lon"]), (current_lat, current_lon)).kilometers
        # If they are more than 50km from their baseline location instantly...
        if dist > 50:
            risk_score += 50
            reasons.append(f"🌍 LIVE GPS ANOMALY: Device located {dist:.0f}km from established baseline.")
    else:
        risk_score += 20
        reasons.append("🌍 LOCATION MASKED: User denied GPS access.")

    # 2. Rule-Based System
    if req_type == "SIM_REPLACEMENT":
        risk_score += 20
        reasons.append("⚠️ RULE VIOLATION: High-risk 'SIM Swap' requested.")

    # 3. LIVE Behavioral Biometrics
    if current_wpm:
        wpm_diff = abs(current_wpm - profile["base_wpm"])
        if wpm_diff > 20:  # Tight threshold for the demo
            risk_score += 30
            reasons.append(
                f"⌨️ BIOMETRIC MISMATCH: Live typing speed ({current_wpm:.0f} WPM) deviates from baseline ({profile['base_wpm']} WPM).")

    return min(risk_score, 100), reasons


# --- 4. NAVIGATION ---
st.sidebar.title("System Interfaces")
view = st.sidebar.radio("Select View:", ["📱 Live Mobile App (User View)", "📡 Security Command Center"])

# =====================================================================
# INTERFACE 1: LIVE MOBILE APP (Where you capture real hardware data)
# =====================================================================
if view == "📱 Live Mobile App (User View)":
    _, col2, _ = st.columns([1, 2, 1])

    with col2:
        st.markdown("<h2 style='text-align: center;'>Telecom Mobile Portal</h2>", unsafe_allow_html=True)
        st.divider()

        st.subheader("Step 1: Location Verification")
        st.write("Please allow location access to verify your device.")
        # LIVE GPS CAPTURE WIDGET
        location = streamlit_geolocation()

        if location and location['latitude'] is not None:
            st.success(f"GPS Locked: Lat {location['latitude']}, Lon {location['longitude']}")

        st.divider()

        st.subheader("Step 2: Identity Verification (Biometrics)")
        st.write("To verify your identity, please type the following phrase exactly as it appears:")

        target_phrase = "Security is not a product but a continuous process."
        st.info(f"**Phrase:** {target_phrase}")

        # Start the invisible stopwatch
        if st.session_state.start_time is None:
            st.session_state.start_time = time.time()

        user_input = st.text_input("Type here:")

        if user_input == target_phrase:
            end_time = time.time()
            time_taken_minutes = (end_time - st.session_state.start_time) / 60
            word_count = len(target_phrase.split())
            st.session_state.wpm_result = word_count / time_taken_minutes
            st.success(f"Biometric profile captured at {st.session_state.wpm_result:.0f} WPM.")
        elif user_input != "":
            st.warning("Please type the phrase exactly to proceed.")

        st.divider()

        st.subheader("Step 3: Submit Request")
        req_type = st.radio("Action Requested:", ["LOGIN", "SIM_REPLACEMENT"])

        if st.button("Transmit to Core Network", type="primary", use_container_width=True):
            if not st.session_state.wpm_result:
                st.error("Please complete the typing test first.")
            else:
                lat = location['latitude'] if location else None
                lon = location['longitude'] if location else None
                wpm = st.session_state.wpm_result

                # Run the AI
                score, reasons = evaluate_transaction("Levi (Owner)", lat, lon, wpm, req_type)

                # Log it
                transaction = {
                    "id": str(uuid.uuid4())[:8],
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "user": "Levi (Owner)",
                    "type": req_type,
                    "score": score,
                    "reasons": reasons
                }
                st.session_state.live_transactions.insert(0, transaction)

                # Reset stopwatch for next time
                st.session_state.start_time = None
                st.session_state.wpm_result = None

                if score >= 70:
                    st.error("🚨 ACCESS DENIED: Security anomalies detected. Dashboard updated.")
                else:
                    st.success("✅ APPROVED: Identity verified. Dashboard updated.")

# =====================================================================
# INTERFACE 2: SECURITY COMMAND CENTER
# =====================================================================
elif view == "📡 Security Command Center":
    st.title("🛡️ SIM-SECURE AI: Command Center")
    st.markdown("Live monitoring of all incoming identity verification requests.")

    if len(st.session_state.live_transactions) == 0:
        st.info("System Idle. Waiting for live telemetry.")
    else:
        for t in st.session_state.live_transactions:
            if t["score"] >= 70:
                with st.expander(f"🔴 CRITICAL ALERT | Risk: {t['score']}/100 | {t['timestamp']}", expanded=True):
                    st.write(f"**Request ID:** `{t['id']}` | **Action:** `{t['type']}`")
                    for r in t["reasons"]:
                        st.error(r)
            else:
                with st.expander(f"🟢 SECURE | Risk: {t['score']}/100 | {t['timestamp']}"):
                    st.success("No anomalies detected. Baseline matched.")