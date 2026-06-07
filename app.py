import streamlit as st
import pandas as pd
import numpy as np
import time
from geopy.distance import geodesic
from datetime import datetime
import uuid
import hashlib
import random
from streamlit_geolocation import streamlit_geolocation

# --- 1. SYSTEM CONFIGURATION & ENTERPRISE CSS ---
st.set_page_config(page_title="SIM-SECURE AI", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .main {background-color: #0b0f19;}
    [data-testid="stSidebar"] {background-color: #111827; border-right: 1px solid #1f2937;}

    /* Buttons */
    .stButton>button {background-color: #2563eb; color: white; border-radius: 8px; font-weight: 600; padding: 10px;}
    .stButton>button:hover {background-color: #1d4ed8; border-color: #1d4ed8;}

    /* Telecom Portal UI */
    .telecom-header {background: linear-gradient(90deg, #064e3b 0%, #047857 100%); padding: 25px; border-radius: 10px 10px 0 0; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.3); border-bottom: 4px solid #34d399;}
    .telecom-body {background-color: #1f2937; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #374151; border-top: none; box-shadow: 0 4px 6px rgba(0,0,0,0.3);}

    /* Cards and Alerts */
    .metric-box {background-color: #1f2937; padding: 20px; border-radius: 10px; border: 1px solid #374151; box-shadow: 0 4px 6px rgba(0,0,0,0.3);}
    .alert-card {padding: 20px; background: linear-gradient(145deg, #3f0f0f, #1a0505); border-left: 6px solid #ef4444; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 0 15px rgba(239, 68, 68, 0.2);}
    .safe-card {padding: 20px; background: linear-gradient(145deg, #064e3b, #022c22); border-left: 6px solid #10b981; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 0 15px rgba(16, 185, 129, 0.1);}

    /* STK Push Simulation */
    .stk-overlay {background-color: rgba(0,0,0,0.9); padding: 35px; border-radius: 15px; border: 2px solid #ef4444; text-align: center; box-shadow: 0px 0px 40px rgba(239, 68, 68, 0.8); animation: pulse 1.5s infinite;}
    .stk-header {color: #fca5a5; font-size: 24px; font-weight: 800; font-family: 'Courier New', monospace; letter-spacing: 1px;}
    .stk-body {color: #ffffff; font-size: 18px; margin: 20px 0;}

    h1, h2, h3 { font-family: 'Courier New', Courier, monospace; }
    </style>
""", unsafe_allow_html=True)


# --- 2. GLOBAL DATABASE & HELPERS ---
@st.cache_resource
def get_global_database():
    return {
        "transactions": [],
        "owner_baseline": {"lat": None, "lon": None, "wpm": None, "hw_id": None, "ip": None, "is_setup": False}
    }


db = get_global_database()


def generate_hardware_id():
    return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:12].upper()


def generate_ip(is_hacker=False):
    if is_hacker:
        return f"198.51.{random.randint(10, 99)}.{random.randint(100, 255)}"
    return f"105.163.{random.randint(10, 99)}.{random.randint(10, 255)}"


def generate_waveform(wpm):
    x = np.linspace(0, 10, 100)
    frequency = max(wpm / 40, 0.1)
    y = np.sin(x * frequency) + np.random.normal(0, 0.1, 100)
    return pd.DataFrame({"Cadence Force": y}, index=x)


# Session States
if 'start_time' not in st.session_state: st.session_state.start_time = None
if 'stk_active' not in st.session_state: st.session_state.stk_active = False
if 'pending_req' not in st.session_state: st.session_state.pending_req = None


# --- 3. AI ENGINE (Decision Matrix) ---
def evaluate_transaction(current_lat, current_lon, current_wpm, req_type, current_hw_id, current_ip):
    baseline = db["owner_baseline"]
    reasons = []
    spatial_risk, behavioral_risk, rule_risk, hardware_risk = 0, 0, 0, 0

    # 1. Spatial & Network
    if current_lat and current_lon and baseline["lat"]:
        dist = geodesic((baseline["lat"], baseline["lon"]), (current_lat, current_lon)).kilometers
        if dist > 20:
            spatial_risk = 100
            reasons.append(f"🌍 GPS ANOMALY: {dist:.0f}km deviation from baseline.")
    else:
        spatial_risk = 50
        reasons.append("🌍 LOCATION MASKED: GPS unavailable.")

    if current_ip != baseline["ip"]:
        reasons.append(f"🌐 IP MISMATCH: Request from unknown network ({current_ip}).")
        spatial_risk = min(spatial_risk + 30, 100)

    # 2. Rule
    if req_type == "SIM_REPLACEMENT":
        rule_risk = 80
        reasons.append("⚠️ HIGH-RISK ACTION: SIM Swap requested.")

    # 3. Behavioral
    if current_wpm > 300:
        behavioral_risk = 100
        reasons.append("⌨️ NON-HUMAN TYPING: Copy-Paste / Bot behavior detected.")
    elif current_wpm and baseline["wpm"]:
        percent_diff = abs(current_wpm - baseline["wpm"]) / baseline["wpm"]
        if percent_diff > 0.35:
            behavioral_risk = 90
            reasons.append(f"⌨️ BIOMETRIC MISMATCH: Cadence deviates by {percent_diff * 100:.0f}%.")

    # 4. Hardware Fingerprint
    if current_hw_id != baseline["hw_id"]:
        hardware_risk = 100
        reasons.append(f"📱 UNRECOGNIZED DEVICE: IMEI Hash {current_hw_id} rejected.")

    total_risk = (spatial_risk * 0.3) + (behavioral_risk * 0.3) + (rule_risk * 0.2) + (hardware_risk * 0.2)
    scores = {"spatial": spatial_risk, "behavioral": behavioral_risk, "rule": rule_risk, "hardware": hardware_risk,
              "total": min(int(total_risk), 100)}
    return scores, reasons


# --- 4. NAVIGATION ---
st.sidebar.markdown("## 🛡️ SIM-SECURE Core")
view = st.sidebar.radio("Navigation:", ["⚙️ Step 1: Identity Provisioning", "📱 Step 2: Threat Simulation",
                                        "📡 Step 3: Security Ops Center"])

st.sidebar.divider()
if st.sidebar.button("🗑️ System Master Reset", use_container_width=True):
    db["transactions"].clear()
    db["owner_baseline"] = {"lat": None, "lon": None, "wpm": None, "hw_id": None, "ip": None, "is_setup": False}
    st.session_state.stk_active = False
    st.sidebar.success("System Purged.")

# =====================================================================
# INTERFACE 1: PROFILE SETUP
# =====================================================================
if view == "⚙️ Step 1: Identity Provisioning":
    st.title("⚙️ Secure Baseline Initialization")
    st.markdown("Establish the legitimate user's physical, network, and biometric anchors.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='metric-box'><h4>📱 Network & Spatial Anchors</h4>", unsafe_allow_html=True)
        if not db["owner_baseline"]["hw_id"]:
            db["owner_baseline"]["hw_id"] = generate_hardware_id()
            db["owner_baseline"]["ip"] = generate_ip(is_hacker=False)

        st.info(
            f"**IMEI Hash:** `{db['owner_baseline']['hw_id']}`\n\n**ISP Assigned IP:** `{db['owner_baseline']['ip']}`")

        st.write("**Capture Global Positioning:**")
        location = streamlit_geolocation()
        if location and location.get('latitude'):
            db["owner_baseline"]["lat"], db["owner_baseline"]["lon"] = location['latitude'], location['longitude']
            st.success(f"✅ GPS Locked: Lat {location['latitude']:.4f}, Lon {location['longitude']:.4f}")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='metric-box'><h4>⌨️ Behavioral Biometric Anchor</h4>", unsafe_allow_html=True)
        target_phrase = "ACC211622"
        st.write(f"Account Number: **{target_phrase}**")

        if st.session_state.start_time is None:
            st.session_state.start_time = time.time()

        user_input = st.text_input("Type the account number to lock signature:")

        if st.button("Lock Signature", type="primary", use_container_width=True) or user_input:
            clean_input = user_input.upper().replace(" ", "").replace("-", "")
            if clean_input == target_phrase:
                time_taken = max(time.time() - st.session_state.start_time, 0.1)
                kps = (len(clean_input) / time_taken) * 12
                db["owner_baseline"]["wpm"] = kps
                st.session_state.start_time = None
                st.toast("✅ Signature Locked Successfully!", icon="🔐")
            elif user_input:
                st.error("⚠️ Typo detected. Check account number.")

        if db["owner_baseline"]["wpm"]:
            st.success("✅ Neural Cadence Captured")
            st.line_chart(generate_waveform(db["owner_baseline"]["wpm"]), height=100)
        st.markdown("</div>", unsafe_allow_html=True)

    if db["owner_baseline"]["lat"] and db["owner_baseline"]["wpm"]:
        db["owner_baseline"]["is_setup"] = True
        st.divider()
        st.success("### 🟢 AI Sentinel Armed & Ready. Proceed to Step 2.")

# =====================================================================
# INTERFACE 2: LIVE MOBILE APP & STK SIMULATION
# =====================================================================
elif view == "📱 Step 2: Threat Simulation":
    if not db["owner_baseline"]["is_setup"]:
        st.error("⚠️ System Offline. Complete Step 1 Initialization first.")
        st.stop()

    # --- STK PUSH MODAL (Renders on top if active) ---
    if st.session_state.stk_active:
        st.markdown(f"""
            <div class="stk-overlay">
                <div class="stk-header">🚨 SAFARICOM SECURITY ALERT 🚨</div>
                <div class="stk-body">
                    <b>Action Required:</b> An anomalous <b>{st.session_state.pending_req}</b> request was detected on your account.<br><br>
                    Did you authorize this network request?
                </div>
            </div>
            <br>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        if c1.button("✅ YES, I AUTHORIZE", use_container_width=True):
            st.session_state.stk_active = False
            st.success("Transaction Forced Approved by Owner.")
            st.rerun()
        if c2.button("🛑 NO, BLOCK & REPORT", type="primary", use_container_width=True):
            st.session_state.stk_active = False
            st.error("Threat Neutralized. Network Access Revoked.")
            st.toast("Fraud Attempt Blocked!", icon="🛡️")
            st.rerun()
        st.stop()  # Halts the rest of the UI rendering

    # --- NORMAL APP VIEW ---
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        # Developer / Hacker Control Panel
        with st.expander("🛠️ Developer Demo Controls (Simulate Hacker)"):
            is_hacker = st.toggle("🚨 Spoof Device and Network Connection", value=False)
            current_hw_id = generate_hardware_id() if is_hacker else db["owner_baseline"]["hw_id"]
            current_ip = generate_ip(is_hacker)
            st.caption(f"Broadcasting IMEI Hash: `{current_hw_id}` | IP: `{current_ip}`")

        # Telecom Portal UI
        st.markdown("""
            <div class="telecom-header">
                <h2 style='color: #ffffff; margin: 0;'>Safaricom Digital Identity</h2>
                <p style='color: #a7f3d0; margin: 0;'>Secure Customer Self-Service Portal</p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='telecom-body'>", unsafe_allow_html=True)

        # RESTORED: Prominent Location Capture right in the UI
        st.markdown("#### 🌍 Spatial Verification")
        st.caption("Capturing live device coordinates...")
        location = streamlit_geolocation()
        if location and location.get('latitude'):
            st.success(f"📍 Broadcasting from: Lat {location['latitude']:.4f}, Lon {location['longitude']:.4f}")
        else:
            st.warning("⚠️ Waiting for GPS signal... (Click the target icon)")

        st.markdown("---")

        # Realistic Form Fields
        req_type = st.radio("Select Portal Action:", ["LOGIN", "SIM_REPLACEMENT"], horizontal=True)
        st.text_input("Registered Phone Number:", value="+254 ")
        st.text_input("National ID Number:")

        st.markdown("---")
        st.markdown("#### 🔒 Identity Verification")
        target_phrase = "ACC211622"
        st.info(f"Verify Authorization Code: **{target_phrase}**")

        if st.session_state.start_time is None:
            st.session_state.start_time = time.time()

        user_input = st.text_input("Enter code below to proceed (Biometrics Active):")

        if st.button("Authenticate & Transmit Request", type="primary", use_container_width=True):
            clean_input = user_input.upper().replace(" ", "").replace("-", "")

            if clean_input == target_phrase:
                time_taken = max(time.time() - st.session_state.start_time, 0.1)
                wpm_result = (len(clean_input) / time_taken) * 12
                lat, lon = (location['latitude'], location['longitude']) if location and location.get('latitude') else (
                None, None)

                scores, reasons = evaluate_transaction(lat, lon, wpm_result, req_type, current_hw_id, current_ip)

                db["transactions"].insert(0, {
                    "id": str(uuid.uuid4())[:8], "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "type": req_type, "lat": lat, "lon": lon,
                    "scores": scores, "reasons": reasons
                })

                st.session_state.start_time = None

                if scores["total"] >= 60:
                    st.session_state.pending_req = req_type
                    st.session_state.stk_active = True
                    st.rerun()  # Instantly snap to STK screen
                else:
                    st.success("✅ BIOMETRICS MATCH: Request Sent to Core Network.")
                    st.toast("Transaction Approved", icon="✅")
            else:
                st.error("⚠️ Invalid Authorization Code.")

        st.markdown("</div>", unsafe_allow_html=True)

# =====================================================================
# INTERFACE 3: SECURITY OPS CENTER (SOC)
# =====================================================================
elif view == "📡 Step 3: Security Ops Center":
    st.title("🛡️ Enterprise Command Center")

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Total Requests Processed", len(db["transactions"]))
    col_b.metric("Threats Intercepted", sum(1 for t in db["transactions"] if t["scores"]["total"] >= 60))
    col_c.metric("Active AI Modules", "4 (Spatial, Net, Bio, Rules)")

    st.divider()
    st.button("🔄 Refresh Live Telemetry", type="primary", use_container_width=True)

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
                st.progress(t["scores"]["spatial"] / 100, text=f"Spatial & Network Risk ({t['scores']['spatial']}%)")
                st.progress(t["scores"]["behavioral"] / 100,
                            text=f"Biometric Cadence Risk ({t['scores']['behavioral']}%)")
                st.progress(t["scores"]["hardware"] / 100, text=f"Hardware Spoofing Risk ({t['scores']['hardware']}%)")

                st.write("**Engine Heuristics Logs:**")
                for r in t["reasons"]: st.markdown(f"- {r}")

                with st.expander("👁️ View Raw JSON Telemetry"):
                    st.json(t)
            st.write("---")