import streamlit as st
import pandas as pd
import time
from geopy.distance import geodesic
from datetime import datetime
import uuid
from streamlit_geolocation import streamlit_geolocation

# --- 1. SYSTEM CONFIGURATION & CSS OVERHAUL ---
st.set_page_config(page_title="SIM-SECURE AI", layout="wide", page_icon="🌐")

# Inject Custom CSS for a premium UI
st.markdown("""
    <style>
    .main {background-color: #0e1117;}
    .stButton>button {
        border-radius: 8px;
        transition: 0.3s;
        border: 1px solid #4CAF50;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
    }
    .alert-card {
        padding: 15px;
        background-color: #2b1111;
        border-left: 6px solid #ff4b4b;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    .safe-card {
        padding: 15px;
        background-color: #112b1a;
        border-left: 6px solid #00c853;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    .glitch-text {
        color: #ff4b4b;
        font-weight: bold;
        text-shadow: 0 0 5px #ff4b4b;
    }
    </style>
""", unsafe_allow_html=True)


# --- 2. THE MULTIPLAYER GLOBAL DATABASE ---
# This trick allows different devices (your laptop vs friend's phone) to share data!
@st.cache_resource
def get_global_database():
    return {
        "transactions": [],
        "owner_baseline": {"lat": None, "lon": None, "wpm": None, "is_setup": False}
    }


db = get_global_database()

# Session variables for the live typing test
if 'start_time' not in st.session_state: st.session_state.start_time = None
if 'wpm_result' not in st.session_state: st.session_state.wpm_result = None


# --- 3. CORE AI ENGINE ---
def evaluate_transaction(current_lat, current_lon, current_wpm, req_type):
    baseline = db["owner_baseline"]
    risk_score = 0
    reasons = []

    # 1. LIVE Impossible Travel
    if current_lat is not None and current_lon is not None and baseline["lat"] is not None:
        dist = geodesic((baseline["lat"], baseline["lon"]), (current_lat, current_lon)).kilometers
        if dist > 20:  # Trigger alert if more than 20km away
            risk_score += 50
            reasons.append(f"🌍 GPS ANOMALY: Device located {dist:.0f}km from established baseline.")
    else:
        risk_score += 20
        reasons.append("🌍 LOCATION MASKED: GPS data unavailable.")

    # 2. Rule-Based System
    if req_type == "SIM_REPLACEMENT":
        risk_score += 20
        reasons.append("⚠️ RULE VIOLATION: High-risk 'SIM Swap' requested.")

    # 3. LIVE Behavioral Biometrics (With Anti-Cheat)
    if current_wpm > 500:  # Catch copy-paste cheats
        risk_score += 40
        reasons.append("⌨️ FRAUD DETECTED: Copy-paste speed anomaly. Impossible human typing rate.")
    elif current_wpm and baseline["wpm"]:
        wpm_diff = abs(current_wpm - baseline["wpm"])
        if wpm_diff > 25:
            risk_score += 30
            reasons.append(
                f"⌨️ BIOMETRIC MISMATCH: Speed ({current_wpm:.0f} WPM) deviates from baseline ({baseline['wpm']:.0f} WPM).")

    return min(risk_score, 100), reasons


# --- 4. NAVIGATION ---
st.sidebar.image(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Globe_icon_2.svg/500px-Globe_icon_2.svg.png", width=50)
st.sidebar.title("Network Access")
view = st.sidebar.radio("Select Interface:", [
    "⚙️ Step 1: Owner Profile Setup",
    "📱 Step 2: Live Mobile App (User/Hacker)",
    "📡 Step 3: Security Command Center"
])

if st.sidebar.button("🗑️ Reset Global System"):
    db["transactions"].clear()
    db["owner_baseline"] = {"lat": None, "lon": None, "wpm": None, "is_setup": False}
    st.sidebar.success("System wiped. Ready for new demo.")

# =====================================================================
# INTERFACE 1: PROFILE SETUP (Establish your true baseline)
# =====================================================================
if view == "⚙️ Step 1: Owner Profile Setup":
    st.title("⚙️ Establish Owner Baseline")
    st.write("Before the demo begins, register the legitimate owner's real-time hardware data.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("1. Lock GPS Location")
        location = streamlit_geolocation()
        if location and location['latitude']:
            db["owner_baseline"]["lat"] = location['latitude']
            db["owner_baseline"]["lon"] = location['longitude']
            st.success("✅ Real-world coordinates locked.")

    with col2:
        st.subheader("2. Lock Typing Biometrics")
        target_phrase = "Establish my baseline."
        st.info(f"Type: **{target_phrase}**")

        if st.session_state.start_time is None: st.session_state.start_time = time.time()

        user_input = st.text_input("Type here:")

        if user_input == target_phrase:
            time_taken = max(0.1, time.time() - st.session_state.start_time)
            wpm = (len(target_phrase.split()) / (time_taken / 60))
            db["owner_baseline"]["wpm"] = wpm
            st.session_state.start_time = None  # reset
            st.success(f"✅ Biometric speed locked at {wpm:.0f} WPM.")

    st.divider()
    if db["owner_baseline"]["lat"] and db["owner_baseline"]["wpm"]:
        db["owner_baseline"]["is_setup"] = True
        st.markdown("### 🟢 Baseline Established. The system is armed.")
        st.json(db["owner_baseline"])
    else:
        st.warning("Please complete both GPS and Typing setup to arm the system.")

# =====================================================================
# INTERFACE 2: LIVE MOBILE APP (The Transaction Space)
# =====================================================================
elif view == "📱 Step 2: Live Mobile App (User/Hacker)":
    if not db["owner_baseline"]["is_setup"]:
        st.error("⚠️ Stop! Go to 'Owner Profile Setup' to arm the system first.")
        st.stop()

    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h2 style='text-align: center; color: #4CAF50;'>Telecom Self-Service</h2>", unsafe_allow_html=True)
        st.divider()

        st.write("🌍 **Location Verification**")
        location = streamlit_geolocation()

        st.write("⌨️ **Identity Verification**")
        target_phrase = "Authorize network access."
        st.info(f"Type: **{target_phrase}**")

        if st.session_state.start_time is None: st.session_state.start_time = time.time()
        user_input = st.text_input("Type here to verify:")

        if user_input == target_phrase:
            time_taken = max(0.1, time.time() - st.session_state.start_time)
            st.session_state.wpm_result = (len(target_phrase.split()) / (time_taken / 60))
            st.success("Hardware signature captured.")

        req_type = st.radio("Action Requested:", ["LOGIN", "SIM_REPLACEMENT"])

        if st.button("Transmit to Core Network", type="primary", use_container_width=True):
            if not st.session_state.wpm_result:
                st.error("Please complete the typing verification.")
            else:
                lat = location['latitude'] if location else None
                lon = location['longitude'] if location else None

                score, reasons = evaluate_transaction(lat, lon, st.session_state.wpm_result, req_type)

                transaction = {
                    "id": str(uuid.uuid4())[:8],
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "type": req_type,
                    "score": score,
                    "reasons": reasons
                }
                db["transactions"].insert(0, transaction)

                # Reset stopwatch
                st.session_state.start_time = None
                st.session_state.wpm_result = None

                if score >= 70:
                    st.markdown("<h3 class='glitch-text'>🚨 ACCESS DENIED: Anomalies Detected</h3>",
                                unsafe_allow_html=True)
                else:
                    st.success("✅ APPROVED: Identity verified.")

# =====================================================================
# INTERFACE 3: SECURITY COMMAND CENTER
# =====================================================================
elif view == "📡 Step 3: Security Command Center":
    st.title("🛡️ Command Center Dashboard")

    # Add a refresh button so you can instantly see your friend's hacks
    st.button("🔄 Refresh Live Feed", type="primary")
    st.divider()

    if len(db["transactions"]) == 0:
        st.info("System Idle. Waiting for live telemetry.")
    else:
        for t in db["transactions"]:
            if t["score"] >= 70:
                st.markdown(f"""
                <div class="alert-card">
                    <h4>🔴 CRITICAL ALERT | Risk: {t['score']}/100 | {t['timestamp']}</h4>
                    <p><b>Request ID:</b> {t['id']} | <b>Action:</b> {t['type']}</p>
                </div>
                """, unsafe_allow_html=True)
                for r in t["reasons"]:
                    st.error(r)
                st.write("---")
            else:
                st.markdown(f"""
                <div class="safe-card">
                    <h4>🟢 SECURE | Risk: {t['score']}/100 | {t['timestamp']}</h4>
                    <p><b>Request ID:</b> {t['id']} | <b>Action:</b> {t['type']}</p>
                    <p>No anomalies detected. Hardware signatures match baseline.</p>
                </div>
                """, unsafe_allow_html=True)