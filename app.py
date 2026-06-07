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

    /* Cards and Alerts */
    .metric-box {background-color: #1f2937; padding: 20px; border-radius: 10px; border: 1px solid #374151; box-shadow: 0 4px 6px rgba(0,0,0,0.3);}
    .alert-card {padding: 20px; background: linear-gradient(145deg, #3f0f0f, #1a0505); border-left: 6px solid #ef4444; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 0 15px rgba(239, 68, 68, 0.2);}
    .safe-card {padding: 20px; background: linear-gradient(145deg, #064e3b, #022c22); border-left: 6px solid #10b981; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 0 15px rgba(16, 185, 129, 0.1);}

    /* STK Push Simulation */
    .stk-overlay {background-color: rgba(0,0,0,0.8); padding: 30px; border-radius: 15px; border: 2px solid #ef4444; text-align: center; box-shadow: 0px 0px 30px rgba(239, 68, 68, 0.6); animation: pulse 2s infinite;}
    .stk-header {color: #fca5a5; font-size: 22px; font-weight: 800; font-family: 'Courier New', monospace; letter-spacing: 1px;}
    .stk-body {color: #ffffff; font-size: 16px; margin: 20px 0;}

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
        return f"198.51.{random.randint(10, 99)}.{random.randint(100, 255)}"  # Suspicious VPN IP
    return f"105.163.{random.randint(10, 99)}.{random.randint(10, 255)}"  # Standard Kenyan Telecom IP


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

    # 3. Behavioral (The Copy-Paste Trap)
    if current_wpm > 300:  # Super fast = Copy Paste
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
        if location and location['latitude']:
            db["owner_baseline"]["lat"], db["owner_baseline"]["lon"] = location['latitude'], location['longitude']
            st.success(f"✅ GPS Locked: Lat {location['latitude']:.4f}, Lon {location['longitude']:.4f}")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='metric-box'><h4>⌨️ Behavioral Biometric Anchor</h4>", unsafe_allow_html=True)
        target_phrase = "ACC211622"
        st.write(f"Account Number: **{target_phrase}**")

        # We start the timer the moment this text box renders
        if st.session_state.start_time is None:
            st.session_state.start_time = time.time()

        user_input = st.text_input("Type the account number to lock signature:")

        if st.button("Lock Signature", type="primary", use_container_width=True) or user_input:
            clean_input = user_input.upper().replace(" ", "").replace("-", "")
            if clean_input == target_phrase:
                with st.spinner("Encrypting biometric signature..."):
                    time.sleep(1)
                time_taken = max(time.time() - st.session_state.start_time, 0.1)
                kps = (len(clean_input) / time_taken) * 12
                db["owner_baseline"]["wpm"] = kps
                st.session_state.start_time = None  # Reset timer
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

    # STK PUSH MODAL (Renders on top if active)
    if st.session_state.stk_active:
        st.markdown(f"""
            <div class="stk-overlay">
                <div class="stk-header">🚨 SAFARICOM STK PUSH 🚨</div>
                <div class="stk-body">
                    <b>Critical Alert:</b> An anomalous <b>{st.session_state.pending_req}</b> request was detected on your account.<br><br>
                    Did you authorize this request?
                </div>
            </div>
            <br>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        if c1.button("✅ YES, I AUTHORIZE THIS", use_container_width=True):
            st.session_state.stk_active = False
            st.success("Transaction Forced Approved by Owner.")
            st.rerun()
        if c2.button("🛑 NO, BLOCK AND REPORT!", type="primary", use_container_width=True):
            st.session_state.stk_active = False
            st.error("Threat Neutralized. Account Locked for Security.")
            st.toast("Fraud Attempt Blocked!", icon="🛡️")
            st.rerun()
        st.stop()  # Stops rendering the rest of the app while STK is active

    # NORMAL APP VIEW
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h2 style='text-align: center; color: #3b82f6;'>Safaricom Digital Portal</h2>",
                    unsafe_allow_html=True)

        # DEMO CONTROL
        st.markdown("---")
        is_hacker = st.toggle("🚨 DEMO CONTROL: Simulate Attack from Unrecognized Device", value=False)
        current_hw_id = generate_hardware_id() if is_hacker else db["owner_baseline"]["hw_id"]
        current_ip = generate_ip(is_hacker)
        st.caption(f"Broadcasting IMEI Hash: `{current_hw_id}` | IP: `{current_ip}`")

        location = streamlit_geolocation()

        st.markdown("#### Identity Verification")
        target_phrase = "ACC211622"
        st.info(f"Account Number: **{target_phrase}**")

        if st.session_state.start_time is None:
            st.session_state.start_time = time.time()

        user_input = st.text_input("Type account number (Try Copy-Pasting to trigger Hacker Trap!):")
        req_type = st.selectbox("Select Action:", ["LOGIN", "SIM_REPLACEMENT"])

        if st.button("Transmit to Core Network", type="primary", use_container_width=True):
            clean_input = user_input.upper().replace(" ", "").replace("-", "")

            if clean_input == target_phrase:
                with st.spinner("Analyzing IPRS Identity and Biometric Cadence..."):
                    time.sleep(1.5)  # Simulate Network Latency

                time_taken = max(time.time() - st.session_state.start_time, 0.1)
                wpm_result = (len(clean_input) / time_taken) * 12
                lat, lon = (location['latitude'], location['longitude']) if location else (None, None)

                scores, reasons = evaluate_transaction(lat, lon, wpm_result, req_type, current_hw_id, current_ip)

                db["transactions"].insert(0, {
                    "id": str(uuid.uuid4())[:8], "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "type": req_type, "lat": lat, "lon": lon,
                    "scores": scores, "reasons": reasons
                })

                st.session_state.start_time = None  # Reset

                if scores["total"] >= 60:
                    st.session_state.pending_req = req_type
                    st.session_state.stk_active = True
                    st.rerun()
                else:
                    st.success("✅ APPROVED: Request Processing.")
                    st.toast("Transaction Approved", icon="✅")
            else:
                st.error("⚠️ Invalid Account Number.")

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
    st.button("🔄 Refresh Live Feed", type="primary", use_container_width=True)

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