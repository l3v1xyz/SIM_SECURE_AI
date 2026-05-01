import streamlit as st
import pandas as pd
import time
from geopy.distance import geodesic
from datetime import datetime
import uuid
from streamlit_geolocation import streamlit_geolocation

# --- 1. SYSTEM CONFIGURATION & ENTERPRISE CSS ---
st.set_page_config(page_title="SIM-SECURE AI", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    /* Global Dark Theme Refinements */
    .main {background-color: #0b0f19;}

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #1f2937;
    }

    /* Premium Buttons */
    .stButton>button {
        background-color: #2563eb;
        color: white;
        border-radius: 6px;
        border: none;
        transition: all 0.3s ease;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #1d4ed8;
        box-shadow: 0 0 15px rgba(37, 99, 235, 0.4);
    }

    /* Alert Cards */
    .alert-card {
        padding: 20px;
        background: linear-gradient(145deg, #2b1111, #1a0a0a);
        border-left: 5px solid #ef4444;
        border-radius: 8px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .safe-card {
        padding: 20px;
        background: linear-gradient(145deg, #064e3b, #022c22);
        border-left: 5px solid #10b981;
        border-radius: 8px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }

    h1, h2, h3 { font-family: 'Courier New', Courier, monospace; }
    </style>
""", unsafe_allow_html=True)


# --- 2. GLOBAL DATABASE ---
@st.cache_resource
def get_global_database():
    return {
        "transactions": [],
        "owner_baseline": {"lat": None, "lon": None, "wpm": None, "is_setup": False}
    }


db = get_global_database()

# Session states for the fixed typing test
if 'test_active' not in st.session_state: st.session_state.test_active = False
if 'start_time' not in st.session_state: st.session_state.start_time = None
if 'wpm_result' not in st.session_state: st.session_state.wpm_result = None


# --- 3. CORE AI ENGINE (V4 - Percentage Based) ---
def evaluate_transaction(current_lat, current_lon, current_wpm, req_type):
    baseline = db["owner_baseline"]
    risk_score = 0
    reasons = []

    # 1. Heuristic: Impossible Travel
    if current_lat is not None and current_lon is not None and baseline["lat"] is not None:
        dist = geodesic((baseline["lat"], baseline["lon"]), (current_lat, current_lon)).kilometers
        if dist > 20:
            risk_score += 50
            reasons.append(f"🌍 GPS ANOMALY: Device is {dist:.0f}km from established baseline.")
    else:
        risk_score += 20
        reasons.append("🌍 LOCATION MASKED: GPS data unavailable.")

    # 2. Rule-Based: High-Risk Action
    if req_type == "SIM_REPLACEMENT":
        risk_score += 20
        reasons.append("⚠️ RULE VIOLATION: High-risk 'SIM Swap' requested.")

    # 3. Biometric: Percentage Deviation (Fixed Math)
    if current_wpm > 400:
        risk_score += 40
        reasons.append("⌨️ FRAUD DETECTED: Non-human typing rate (Copy-Paste detected).")
    elif current_wpm and baseline["wpm"]:
        # Calculate percentage difference instead of flat difference
        percent_diff = abs(current_wpm - baseline["wpm"]) / baseline["wpm"]
        if percent_diff > 0.30:  # If speed varies by more than 30%
            risk_score += 30
            reasons.append(
                f"⌨️ BIOMETRIC MISMATCH: Speed ({current_wpm:.0f} WPM) deviates from baseline ({baseline['wpm']:.0f} WPM) by {percent_diff * 100:.0f}%.")

    return min(risk_score, 100), reasons


# --- 4. SIDEBAR NAVIGATION ---
st.sidebar.markdown("## 🛡️ SIM-SECURE Core")
view = st.sidebar.radio("Navigation:", [
    "⚙️ Step 1: Owner Profile Setup",
    "📱 Step 2: Live Mobile App",
    "📡 Step 3: Command Center",
    "📊 Step 4: Historical Audit (Sim Data)"
])

st.sidebar.divider()
if st.sidebar.button("🗑️ Reset Live System", use_container_width=True):
    db["transactions"].clear()
    db["owner_baseline"] = {"lat": None, "lon": None, "wpm": None, "is_setup": False}
    st.sidebar.success("Memory wiped.")

# =====================================================================
# INTERFACE 1: PROFILE SETUP
# =====================================================================
if view == "⚙️ Step 1: Owner Profile Setup":
    st.title("⚙️ System Initialization")
    st.markdown("Authenticate the legitimate device and user biometrics to arm the AI.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("1. Spatial Anchor (GPS)")
        location = streamlit_geolocation()
        if location and location['latitude']:
            db["owner_baseline"]["lat"] = location['latitude']
            db["owner_baseline"]["lon"] = location['longitude']
            st.success(f"✅ GPS Locked: Lat {location['latitude']:.4f}, Lon {location['longitude']:.4f}")

    with col2:
        st.subheader("2. Biometric Anchor (Typing)")
        target_phrase = "Security is a continuous process."
        st.info(f"Target Phrase: **{target_phrase}**")

        # Fixed Timer Logic
        if not st.session_state.test_active:
            if st.button("Start Typing Test"):
                st.session_state.test_active = True
                st.session_state.start_time = time.time()
                st.rerun()

        if st.session_state.test_active:
            user_input = st.text_input("Type the phrase now:", key="setup_input")
            if user_input == target_phrase:
                time_taken = time.time() - st.session_state.start_time
                wpm = (len(target_phrase.split()) / (time_taken / 60))
                db["owner_baseline"]["wpm"] = wpm
                st.session_state.test_active = False  # reset
                st.success(f"✅ Biometrics Locked: {wpm:.0f} WPM")

    st.divider()
    if db["owner_baseline"]["lat"] and db["owner_baseline"]["wpm"]:
        db["owner_baseline"]["is_setup"] = True
        st.markdown("### 🟢 System Armed & Ready")
    else:
        st.warning("Awaiting spatial and biometric anchors...")

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
        st.divider()

        st.markdown("#### 🌍 Step 1: Provide Location Data")
        location = streamlit_geolocation()
        # Explicitly show the captured location here now!
        if location and location['latitude']:
            st.info(f"Location Captured: {location['latitude']:.4f}, {location['longitude']:.4f}")

        st.markdown("#### ⌨️ Step 2: Identity Verification")
        target_phrase = "Authorize my network request."
        st.info(f"Phrase: **{target_phrase}**")

        if not st.session_state.test_active:
            if st.button("Start Verification"):
                st.session_state.test_active = True
                st.session_state.start_time = time.time()
                st.rerun()

        if st.session_state.test_active:
            user_input = st.text_input("Type phrase:")
            if user_input == target_phrase:
                time_taken = time.time() - st.session_state.start_time
                st.session_state.wpm_result = (len(target_phrase.split()) / (time_taken / 60))
                st.session_state.test_active = False
                st.success(f"Signature Captured ({st.session_state.wpm_result:.0f} WPM)")

        st.markdown("#### 🔄 Step 3: Action Request")
        req_type = st.selectbox("Select Action:", ["LOGIN", "SIM_REPLACEMENT"])

        if st.button("Transmit to Core Network", type="primary", use_container_width=True):
            if not st.session_state.wpm_result:
                st.error("Complete the typing verification first.")
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
                st.session_state.wpm_result = None  # reset for next time

                if score >= 70:
                    st.error("🚨 ACCESS DENIED: Anomalies Detected.")
                else:
                    st.success("✅ APPROVED: Request Processing.")

# =====================================================================
# INTERFACE 3: COMMAND CENTER
# =====================================================================
elif view == "📡 Step 3: Command Center":
    st.title("🛡️ Security Command Center")
    st.button("🔄 Refresh Live Feed Feed", type="primary")
    st.divider()

    if len(db["transactions"]) == 0:
        st.info("System Idle. Awaiting incoming transactions.")
    else:
        for t in db["transactions"]:
            if t["score"] >= 70:
                st.markdown(f"""
                <div class="alert-card">
                    <h3 style="color:#ef4444; margin-top:0;">🔴 BREACH ATTEMPT | Risk: {t['score']}/100</h3>
                    <p style="color:#e5e7eb;"><b>Time:</b> {t['timestamp']} | <b>Request ID:</b> {t['id']} | <b>Action:</b> {t['type']}</p>
                    <hr style="border-color:#7f1d1d;">
                """, unsafe_allow_html=True)
                for r in t["reasons"]: st.markdown(f"<span style='color:#fca5a5;'>- {r}</span>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="safe-card">
                    <h3 style="color:#10b981; margin-top:0;">🟢 SECURE | Risk: {t['score']}/100</h3>
                    <p style="color:#e5e7eb;"><b>Time:</b> {t['timestamp']} | <b>Request ID:</b> {t['id']} | <b>Action:</b> {t['type']}</p>
                    <hr style="border-color:#064e3b;">
                    <span style='color:#6ee7b7;'>- Hardware signatures match established baseline.</span>
                </div>
                """, unsafe_allow_html=True)

# =====================================================================
# INTERFACE 4: HISTORICAL AUDIT (Your Simulated Data!)
# =====================================================================
elif view == "📊 Step 4: Historical Audit (Sim Data)":
    st.title("📊 Decentralized Audit Trail")
    st.markdown("Batch processing of historical node data (Simulated Environment).")

    try:
        df = pd.read_csv("simulated_logs.csv")
        st.metric("Total Records Analyzed", len(df))
        st.dataframe(
            df.style.map(lambda x: "background-color: rgba(239, 68, 68, 0.2)" if x == 'SIM_REPLACEMENT' else "",
                         subset=['request_type']), use_container_width=True)
    except FileNotFoundError:
        st.error("No historical data found. Please ensure 'simulated_logs.csv' is uploaded to your repository.")