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

    /* Custom UI Elements */
    .stk-modal {background-color: #1e293b; border: 2px solid #ef4444; border-radius: 12px; padding: 25px; text-align: center; margin-top: 20px; box-shadow: 0px 0px 20px rgba(239, 68, 68, 0.4);}
    .stk-title {color: #f87171; font-size: 24px; font-weight: bold; margin-bottom: 10px;}
    .stk-text {color: #e2e8f0; font-size: 18px; margin-bottom: 20px;}

    .alert-card {padding: 20px; background: linear-gradient(145deg, #2b1111, #1a0a0a); border-left: 5px solid #ef4444; border-radius: 8px; margin-bottom: 15px;}
    .safe-card {padding: 20px; background: linear-gradient(145deg, #064e3b, #022c22); border-left: 5px solid #10b981; border-radius: 8px; margin-bottom: 15px;}
    .metric-box {background-color: #1f2937; padding: 15px; border-radius: 8px; text-align: center;}
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
    frequency = max(wpm / 40, 0.1)
    y = np.sin(x * frequency) + np.random.normal(0, 0.15, 100)
    return pd.DataFrame({"Cadence Force": y}, index=x)


# Session states
if 'test_active' not in st.session_state: st.session_state.test_active = False
if 'start_time' not in st.session_state: st.session_state.start_time = None
if 'wpm_result' not in st.session_state: st.session_state.wpm_result = None
if 'stk_active' not in st.session_state: st.session_state.stk_active = False


# --- 3. AI ENGINE (Decision Matrix) ---
def evaluate_transaction(current_lat, current_lon, current_wpm, req_type, current_hw_id):
    baseline = db["owner_baseline"]
    reasons = []
    spatial_risk, behavioral_risk, rule_risk, hardware_risk = 0, 0, 0, 0

    if current_lat and current_lon and baseline["lat"]:
        dist = geodesic((baseline["lat"], baseline["lon"]), (current_lat, current_lon)).kilometers
        if dist > 20:
            spatial_risk = 100
            reasons.append(f"🌍 GPS ANOMALY: {dist:.0f}km deviation from baseline.")
    else:
        spatial_risk = 50
        reasons.append("🌍 LOCATION MASKED: GPS unavailable.")

    if req_type == "SIM_REPLACEMENT":
        rule_risk = 80
        reasons.append("⚠️ HIGH-RISK ACTION: SIM Swap requested.")

    if current_wpm > 400:
        behavioral_risk = 100
        reasons.append("⌨️ NON-HUMAN TYPING: Copy-Paste detected.")
    elif current_wpm and baseline["wpm"]:
        percent_diff = abs(current_wpm - baseline["wpm"]) / baseline["wpm"]
        if percent_diff > 0.30:
            behavioral_risk = 90
            reasons.append(f"⌨️ BIOMETRIC MISMATCH: Cadence deviates by {percent_diff * 100:.0f}%.")

    if current_hw_id != baseline["hw_id"]:
        hardware_risk = 100
        reasons.append(f"📱 UNRECOGNIZED DEVICE: Hash {current_hw_id} does not match owner.")

    total_risk = (spatial_risk * 0.3) + (behavioral_risk * 0.3) + (rule_risk * 0.2) + (hardware_risk * 0.2)

    scores = {
        "spatial": spatial_risk, "behavioral": behavioral_risk,
        "rule": rule_risk, "hardware": hardware_risk,
        "total": min(int(total_risk), 100)
    }
    return scores, reasons


# --- 4. NAVIGATION ---
st.sidebar.markdown("## 🛡️ SIM-SECURE Core")
view = st.sidebar.radio("Navigation:", ["⚙️ Step 1: Identity Provisioning", "📱 Step 2: Threat Simulation",
                                        "📡 Step 3: Security Ops Center"])

st.sidebar.divider()
if st.sidebar.button("🗑️ System Master Reset", use_container_width=True):
    db["transactions"].clear()
    db["owner_baseline"] = {"lat": None, "lon": None, "wpm": None, "hw_id": None, "is_setup": False}
    st.session_state.stk_active = False
    st.sidebar.success("System Purged.")

# =====================================================================
# INTERFACE 1: PROFILE SETUP
# =====================================================================
if view == "⚙️ Step 1: Identity Provisioning":
    st.title("⚙️ Secure Baseline Initialization")
    st.markdown("Establish the legitimate user's physical and behavioral biometric anchors.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='metric-box'><h4>📱 Hardware & Spatial Anchors</h4></div>", unsafe_allow_html=True)
        st.write("")
        if not db["owner_baseline"]["hw_id"]:
            db["owner_baseline"]["hw_id"] = generate_hardware_id()
        st.info(f"**Authorized Device IMEI Hash:** `{db['owner_baseline']['hw_id']}`")

        st.write("**Capture Global Positioning:**")
        location = streamlit_geolocation()
        if location and location['latitude']:
            db["owner_baseline"]["lat"], db["owner_baseline"]["lon"] = location['latitude'], location['longitude']
            st.success(f"✅ GPS Locked: Lat {location['latitude']:.4f}, Lon {location['longitude']:.4f}")

    with col2:
        st.markdown("<div class='metric-box'><h4>⌨️ Behavioral Biometric Anchor</h4></div>", unsafe_allow_html=True)
        st.write("")
        st.info("Account Number: **ACC-211622**")

        if not st.session_state.test_active and not db["owner_baseline"]["wpm"]:
            if st.button("Start Cadence Capture", use_container_width=True):
                st.session_state.test_active, st.session_state.start_time = True, time.time()
                st.rerun()

        if st.session_state.test_active:
            user_input = st.text_input("Type the account number (Click button below when done):", key="setup_input")

            if st.button("Lock Signature", type="primary", use_container_width=True):
                if len(user_input) >= 6:  # Highly forgiving input logic
                    time_taken = max(time.time() - st.session_state.start_time, 0.1)
                    kps = (len(user_input) / time_taken) * 12
                    db["owner_baseline"]["wpm"] = kps
                    st.session_state.test_active = False
                    st.toast("✅ Signature Locked Successfully!", icon="🔐")
                    st.rerun()
                else:
                    st.error("⚠️ Input too short. Please type the full account number.")

        if db["owner_baseline"]["wpm"]:
            st.success(f"✅ Neural Cadence Captured")
            st.line_chart(generate_waveform(db["owner_baseline"]["wpm"]), height=150)

    st.divider()
    if db["owner_baseline"]["lat"] and db["owner_baseline"]["wpm"]:
        db["owner_baseline"]["is_setup"] = True
        st.success("### 🟢 AI Sentinel Armed & Ready")

# =====================================================================
# INTERFACE 2: LIVE MOBILE APP & STK SIMULATION
# =====================================================================
elif view == "📱 Step 2: Threat Simulation":
    if not db["owner_baseline"]["is_setup"]:
        st.error("⚠️ System Offline. Complete Step 1 Initialization first.")
        st.stop()

    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h2 style='text-align: center; color: #3b82f6;'>Safaricom Digital Portal</h2>",
                    unsafe_allow_html=True)

        # DEMO CONTROL
        st.markdown("---")
        is_hacker = st.toggle("🚨 DEMO CONTROL: Simulate Attack from Unrecognized Device", value=False)
        current_hw_id = generate_hardware_id() if is_hacker else db["owner_baseline"]["hw_id"]
        st.caption(f"Broadcasting Device Hash: `{current_hw_id}`")

        location = streamlit_geolocation()

        st.markdown("#### Identity Verification")
        st.info("Account Number: **ACC-211622**")

        if not st.session_state.test_active and not st.session_state.wpm_result:
            if st.button("Start Verification", use_container_width=True):
                st.session_state.test_active, st.session_state.start_time = True, time.time()
                st.rerun()

        if st.session_state.test_active:
            user_input = st.text_input("Type account number (Click button below when done):", key="live_input")
            if st.button("Verify Identity", type="primary", use_container_width=True):
                if len(user_input) >= 6:
                    time_taken = max(time.time() - st.session_state.start_time, 0.1)
                    st.session_state.wpm_result = (len(user_input) / time_taken) * 12
                    st.session_state.test_active = False
                    st.rerun()
                else:
                    st.error("⚠️ Input too short.")

        if st.session_state.wpm_result:
            st.success(f"Signature Captured")
            req_type = st.selectbox("Select Action:", ["LOGIN", "SIM_REPLACEMENT"])

            if st.button("Transmit to Core Network", type="primary", use_container_width=True):
                lat, lon = (location['latitude'], location['longitude']) if location else (None, None)
                scores, reasons = evaluate_transaction(lat, lon, st.session_state.wpm_result, req_type, current_hw_id)

                db["transactions"].insert(0, {
                    "id": str(uuid.uuid4())[:8], "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "type": req_type, "lat": lat, "lon": lon,
                    "scores": scores, "reasons": reasons
                })
                st.session_state.wpm_result = None

                if scores["total"] >= 60:
                    st.session_state.stk_active = True  # Trigger STK Modal
                    st.rerun()
                else:
                    st.success("✅ APPROVED: Request Processing.")
                    st.toast("Transaction Approved", icon="✅")

        # --- STK PUSH OVERLAY SIMULATION ---
        if st.session_state.stk_active:
            st.markdown("""
                <div class="stk-modal">
                    <div class="stk-title">⚠️ SAFARICOM SECURITY ALERT</div>
                    <div class="stk-text">Suspicious activity detected. Did you request a SIM Replacement or Login from a new device?</div>
                </div>
            """, unsafe_allow_html=True)

            sc1, sc2 = st.columns(2)
            with sc1:
                if st.button("✅ YES (Authorize)", use_container_width=True):
                    st.session_state.stk_active = False
                    st.success("Authorization forced by user.")
                    st.rerun()
            with sc2:
                if st.button("🛑 NO (Block & Report)", type="primary", use_container_width=True):
                    st.session_state.stk_active = False
                    st.error("Attack Intercepted. Identity Secured.")
                    st.toast("Threat Neutralized", icon="🛡️")
                    st.rerun()

# =====================================================================
# INTERFACE 3: SECURITY OPS CENTER (SOC)
# =====================================================================
elif view == "📡 Step 3: Security Ops Center":
    st.title("🛡️ Enterprise Command Center")

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Total Requests Processed", len(db["transactions"]))
    col_b.metric("Threats Intercepted", sum(1 for t in db["transactions"] if t["scores"]["total"] >= 60))
    col_c.metric("Active AI Modules", "3 (Spatial, Biometric, Rules)")

    st.divider()

    if len(db["transactions"]) == 0:
        st.info("System Idle. Awaiting incoming network telemetry.")
    else:
        for t in db["transactions"]:
            is_breach = t["scores"]["total"] >= 60
            card_class = "alert-card" if is_breach else "safe-card"
            status = "🔴 HIGH RISK: STK PUSH DEPLOYED" if is_breach else "🟢 LOW RISK: AUTHORIZED"
            color = "#ef4444" if is_breach else "#10b981"

            st.markdown(f"""
            <div class="{card_class}">
                <h3 style="color:{color}; margin-top:0;">{status} | Risk Score: {t['scores']['total']}/100</h3>
                <p style="color:#e5e7eb;"><b>Time:</b> {t['timestamp']} | <b>Trace ID:</b> {t['id']} | <b>Vector:</b> {t['type']}</p>
            </div>
            """, unsafe_allow_html=True)

            col_map, col_matrix = st.columns([1, 2])

            with col_map:
                if t["lat"] and t["lon"]:
                    st.map(pd.DataFrame({'lat': [t['lat']], 'lon': [t['lon']]}), zoom=12)
                else:
                    st.warning("Spatial data unavailable.")

            with col_matrix:
                st.write("**🧠 AI Confidence Matrix:**")
                st.progress(t["scores"]["spatial"] / 100, text=f"Spatial Anomaly Risk ({t['scores']['spatial']}%)")
                st.progress(t["scores"]["behavioral"] / 100,
                            text=f"Biometric Cadence Risk ({t['scores']['behavioral']}%)")
                st.progress(t["scores"]["hardware"] / 100, text=f"Hardware Spoofing Risk ({t['scores']['hardware']}%)")

                st.write("**Engine Heuristics Logs:**")
                for r in t["reasons"]: st.markdown(f"- {r}")

                with st.expander("👁️ View Raw JSON Telemetry"):
                    st.json(t)
            st.write("---")