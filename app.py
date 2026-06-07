import streamlit as st
import pandas as pd
import numpy as np
import time
from geopy.distance import geodesic
from datetime import datetime
import uuid
import hashlib
from streamlit_geolocation import streamlit_geolocation

# --- 1. SYSTEM CONFIGURATION & ENTERPRISE CSS ---
st.set_page_config(page_title="SIM-SECURE AI", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .main {background-color: #0b0f19;}
    [data-testid="stSidebar"] {background-color: #111827; border-right: 1px solid #1f2937;}
    .stButton>button {background-color: #2563eb; color: white; border-radius: 6px; font-weight: 600;}
    .alert-card {padding: 20px; background: linear-gradient(145deg, #2b1111, #1a0a0a); border-left: 5px solid #ef4444; border-radius: 8px; margin-bottom: 15px;}
    .safe-card {padding: 20px; background: linear-gradient(145deg, #064e3b, #022c22); border-left: 5px solid #10b981; border-radius: 8px; margin-bottom: 15px;}
    h1, h2, h3 { font-family: 'Courier New', Courier, monospace; }
    </style>
""", unsafe_allow_html=True)


# --- 2. GLOBAL DATABASE & HELPERS ---
@st.cache_resource
def get_global_database():
    return {
        "transactions": [],
        "owner_baseline": {"lat": None, "lon": None, "wpm": None, "hw_id": None, "is_setup": False}
    }


db = get_global_database()


# Generate a fake hardware IMEI hash
def generate_hardware_id():
    return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:12].upper()


# Generate a visual waveform based on typing speed
def generate_waveform(wpm):
    x = np.linspace(0, 10, 100)
    frequency = max(wpm / 40, 0.1)  # Faster cadence = tighter waves
    y = np.sin(x * frequency) + np.random.normal(0, 0.15, 100)
    return pd.DataFrame({"Cadence Force": y}, index=x)


# Session states
if 'test_active' not in st.session_state: st.session_state.test_active = False
if 'start_time' not in st.session_state: st.session_state.start_time = None
if 'wpm_result' not in st.session_state: st.session_state.wpm_result = None


# --- 3. AI ENGINE (Decision Matrix) ---
def evaluate_transaction(current_lat, current_lon, current_wpm, req_type, current_hw_id):
    baseline = db["owner_baseline"]
    reasons = []

    # Individual Risk Vectors
    spatial_risk, behavioral_risk, rule_risk, hardware_risk = 0, 0, 0, 0

    # 1. Spatial
    if current_lat and current_lon and baseline["lat"]:
        dist = geodesic((baseline["lat"], baseline["lon"]), (current_lat, current_lon)).kilometers
        if dist > 20:
            spatial_risk = 100
            reasons.append(f"🌍 GPS ANOMALY: {dist:.0f}km deviation from baseline.")
    else:
        spatial_risk = 50
        reasons.append("🌍 LOCATION MASKED: GPS unavailable.")

    # 2. Rule
    if req_type == "SIM_REPLACEMENT":
        rule_risk = 80
        reasons.append("⚠️ HIGH-RISK ACTION: SIM Swap requested.")

    # 3. Behavioral
    if current_wpm > 400:
        behavioral_risk = 100
        reasons.append("⌨️ NON-HUMAN TYPING: Copy-Paste detected.")
    elif current_wpm and baseline["wpm"]:
        percent_diff = abs(current_wpm - baseline["wpm"]) / baseline["wpm"]
        if percent_diff > 0.30:
            behavioral_risk = 90
            reasons.append(f"⌨️ BIOMETRIC MISMATCH: Cadence deviates by {percent_diff * 100:.0f}%.")

    # 4. Hardware Fingerprint
    if current_hw_id != baseline["hw_id"]:
        hardware_risk = 100
        reasons.append(f"📱 UNRECOGNIZED DEVICE: Hash {current_hw_id} does not match owner.")

    # Weighted Total Score
    total_risk = (spatial_risk * 0.3) + (behavioral_risk * 0.3) + (rule_risk * 0.2) + (hardware_risk * 0.2)

    scores = {
        "spatial": spatial_risk, "behavioral": behavioral_risk,
        "rule": rule_risk, "hardware": hardware_risk,
        "total": min(int(total_risk), 100)
    }
    return scores, reasons


# --- 4. NAVIGATION ---
st.sidebar.markdown("## 🛡️ SIM-SECURE Core")
view = st.sidebar.radio("Navigation:",
                        ["⚙️ Step 1: Owner Profile Setup", "📱 Step 2: Live Mobile App", "📡 Step 3: Command Center",
                         "📊 Step 4: Historical Audit"])

st.sidebar.divider()
if st.sidebar.button("🗑️ Reset Live System", use_container_width=True):
    db["transactions"].clear()
    db["owner_baseline"] = {"lat": None, "lon": None, "wpm": None, "hw_id": None, "is_setup": False}
    st.sidebar.success("Memory wiped.")
    st.toast("System Memory Wiped", icon="🗑️")

# =====================================================================
# INTERFACE 1: PROFILE SETUP
# =====================================================================
if view == "⚙️ Step 1: Owner Profile Setup":
    st.title("⚙️ System Initialization")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("1. Device & Spatial Anchors")
        if not db["owner_baseline"]["hw_id"]:
            db["owner_baseline"]["hw_id"] = generate_hardware_id()
        st.info(f"📱 **Authorized Device Hash:** `{db['owner_baseline']['hw_id']}`")

        location = streamlit_geolocation()
        if location and location['latitude']:
            db["owner_baseline"]["lat"], db["owner_baseline"]["lon"] = location['latitude'], location['longitude']
            st.success(f"✅ GPS Locked: Lat {location['latitude']:.4f}, Lon {location['longitude']:.4f}")

    with col2:
        st.subheader("2. Biometric Anchor (Typing)")
        target_phrase = "ACC-211622"
        st.info(f"Account Number: **{target_phrase}**")

        if not st.session_state.test_active:
            if st.button("Start Cadence Test", use_container_width=True):
                st.session_state.test_active, st.session_state.start_time = True, time.time()
                st.rerun()

        if st.session_state.test_active:
            # Wrapped in an st.form to capture "Enter" key presses securely
            with st.form(key="setup_form"):
                user_input = st.text_input("Type the account number exactly:")
                submit_btn = st.form_submit_button("Submit Baseline Signature", type="primary",
                                                   use_container_width=True)

                if submit_btn:
                    clean_input = user_input.replace(" ", "").upper()
                    clean_target = target_phrase.replace(" ", "").upper()

                    if clean_input == clean_target:
                        time_taken = max(time.time() - st.session_state.start_time, 0.1)
                        kps = (len(clean_target) / time_taken) * 12
                        db["owner_baseline"]["wpm"] = kps
                        st.session_state.test_active = False
                        st.toast("✅ Signature Locked Successfully!", icon="🔐")
                        st.rerun()
                    else:
                        st.error("⚠️ Mismatch. Please check the account number.")
                        st.toast("Typo detected, try again.", icon="⚠️")

        if db["owner_baseline"]["wpm"]:
            st.success(f"✅ Biometrics Locked: Signature Captured")
            st.line_chart(generate_waveform(db["owner_baseline"]["wpm"]), height=150)

    st.divider()
    if db["owner_baseline"]["lat"] and db["owner_baseline"]["wpm"]:
        db["owner_baseline"]["is_setup"] = True
        st.markdown("### 🟢 System Armed & Ready")

# =====================================================================
# INTERFACE 2: LIVE MOBILE APP
# =====================================================================
elif view == "📱 Step 2: Live Mobile App":
    if not db["owner_baseline"]["is_setup"]:
        st.error("⚠️ System Offline. Initialize Step 1 first.")
        st.stop()

    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h2 style='text-align: center; color: #3b82f6;'>Safaricom Digital Portal</h2>",
                    unsafe_allow_html=True)

        is_hacker = st.toggle("🚨 DEMO: Simulate Attack from Unrecognized Device", value=False)
        current_hw_id = generate_hardware_id() if is_hacker else db["owner_baseline"]["hw_id"]
        st.caption(f"Current Device Hash: `{current_hw_id}`")

        st.divider()
        location = streamlit_geolocation()
        if location and location['latitude']:
            st.info(f"🌍 Location Captured: {location['latitude']:.4f}, {location['longitude']:.4f}")

        st.markdown("#### ⌨️ Step 2: Identity Verification")
        target_phrase = "ACC-211622"
        st.info(f"Account Number: **{target_phrase}**")

        if not st.session_state.test_active:
            if st.button("Start Verification", use_container_width=True):
                st.session_state.test_active, st.session_state.start_time = True, time.time()
                st.rerun()

        if st.session_state.test_active:
            # Wrapped in an st.form to capture "Enter" key presses securely
            with st.form(key="live_form"):
                user_input = st.text_input("Type account number:")
                submit_btn = st.form_submit_button("Verify Identity", type="primary", use_container_width=True)

                if submit_btn:
                    clean_input = user_input.replace(" ", "").upper()
                    clean_target = target_phrase.replace(" ", "").upper()

                    if clean_input == clean_target:
                        time_taken = max(time.time() - st.session_state.start_time, 0.1)
                        st.session_state.wpm_result = (len(clean_target) / time_taken) * 12
                        st.session_state.test_active = False
                        st.toast("✅ Identity Verified!", icon="🟢")
                        st.rerun()
                    else:
                        st.error("⚠️ Mismatch. Please check the account number.")
                        st.toast("Typo detected, try again.", icon="⚠️")

        if st.session_state.wpm_result:
            st.success(f"Signature Captured")
            st.line_chart(generate_waveform(st.session_state.wpm_result), height=150)

        req_type = st.selectbox("Select Action:", ["LOGIN", "SIM_REPLACEMENT"])

        if st.button("Transmit to Core Network", type="primary", use_container_width=True):
            if not st.session_state.wpm_result:
                st.error("Complete the typing verification first.")
            else:
                lat, lon = (location['latitude'], location['longitude']) if location else (None, None)
                scores, reasons = evaluate_transaction(lat, lon, st.session_state.wpm_result, req_type, current_hw_id)

                db["transactions"].insert(0, {
                    "id": str(uuid.uuid4())[:8], "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "type": req_type, "lat": lat, "lon": lon,
                    "scores": scores, "reasons": reasons
                })
                st.session_state.wpm_result = None

                # Threshold set to 60 for strict security
                if scores["total"] >= 60:
                    st.error("🚨 ACCESS DENIED: Anomalies Detected.")
                    st.toast("Transaction Blocked!", icon="🔴")
                else:
                    st.success("✅ APPROVED: Request Processing.")
                    st.toast("Transaction Approved", icon="✅")

# =====================================================================
# INTERFACE 3: COMMAND CENTER
# =====================================================================
elif view == "📡 Step 3: Command Center":
    st.title("🛡️ Security Command Center")
    st.button("🔄 Refresh Live Feed", type="primary", use_container_width=True)
    st.divider()

    if len(db["transactions"]) == 0:
        st.info("System Idle. Awaiting incoming transactions.")
    else:
        for t in db["transactions"]:
            is_breach = t["scores"]["total"] >= 60
            card_class = "alert-card" if is_breach else "safe-card"
            status = "🔴 BREACH ATTEMPT" if is_breach else "🟢 SECURE"
            color = "#ef4444" if is_breach else "#10b981"

            st.markdown(f"""
            <div class="{card_class}">
                <h3 style="color:{color}; margin-top:0;">{status} | Total Risk: {t['scores']['total']}/100</h3>
                <p style="color:#e5e7eb;"><b>Time:</b> {t['timestamp']} | <b>Request ID:</b> {t['id']} | <b>Action:</b> {t['type']}</p>
            </div>
            """, unsafe_allow_html=True)

            col_map, col_matrix = st.columns([1, 2])

            with col_map:
                if t["lat"] and t["lon"]:
                    st.map(pd.DataFrame({'lat': [t['lat']], 'lon': [t['lon']]}), zoom=12)
                else:
                    st.warning("No spatial data available for mapping.")

            with col_matrix:
                st.write("**🧠 AI Confidence Matrix:**")
                c1, c2, c3, c4 = st.columns(4)
                c1.caption("Spatial Risk");
                c1.progress(t["scores"]["spatial"] / 100)
                c2.caption("Biometric Risk");
                c2.progress(t["scores"]["behavioral"] / 100)
                c3.caption("Hardware Risk");
                c3.progress(t["scores"]["hardware"] / 100)
                c4.caption("Rule Risk");
                c4.progress(t["scores"]["rule"] / 100)

                st.write("**Engine Logs:**")
                for r in t["reasons"]: st.markdown(f"- {r}")
            st.write("---")

# =====================================================================
# INTERFACE 4: HISTORICAL AUDIT
# =====================================================================
elif view == "📊 Step 4: Historical Audit":
    st.title("📊 Decentralized Audit Trail")
    try:
        df = pd.read_csv("simulated_logs.csv")
        st.metric("Total Records Analyzed", len(df))
        st.dataframe(
            df.style.map(lambda x: "background-color: rgba(239, 68, 68, 0.2)" if x == 'SIM_REPLACEMENT' else "",
                         subset=['request_type']), use_container_width=True)
    except FileNotFoundError:
        st.error("No historical data found. Please ensure 'simulated_logs.csv' is present.")