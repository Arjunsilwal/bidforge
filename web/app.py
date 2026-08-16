"""
BidForge v1 Review Workspace (Streamlit).
Allows estimators to upload bid packages, inspect calibrated price distributions,
view RAG spec grounding & historical comparable bids, override line item prices, and export to Excel/CSV.
"""
import os
import requests
import streamlit as st
import pandas as pd

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="BidForge | Preconstruction Estimating Engine",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Styling
st.markdown(
    """
    <style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 16px;
        border-left: 5px solid #2563eb;
    }
    .badge-approved {
        background-color: #dcfce7;
        color: #166534;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
    .badge-draft {
        background-color: #fef3c7;
        color: #92400e;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🏗️ BidForge v1 Review Workspace")
st.caption("AI Preconstruction Estimating Engine • Quantile Cost Models • Historical Grounding")

# Sidebar - Project Selection & Upload
with st.sidebar:
    st.header("Project Management")

    mode = st.radio("Actions", ["📂 Active Estimates", "⚡ Instant Demo Package", "📤 Upload New Package"])

    if mode == "⚡ Instant Demo Package":
        st.subheader("Generate Demo")
        demo_name = st.text_input("Project Name", value="US-101 Highway Realignment & Drainage Upgrade")
        demo_region = st.selectbox(
            "Region",
            ["District 1 (Northwest)", "District 2 (Central)", "District 3 (Southwest)", "District 4 (Eastern)"],
        )
        item_count = st.slider("Number of Line Items", min_value=4, max_value=12, value=8)

        if st.button("Generate & Estimate", type="primary"):
            with st.spinner("Processing bid package & running ML models..."):
                try:
                    resp = requests.post(
                        f"{API_URL}/api/v1/estimates/synthetic",
                        params={"project_name": demo_name, "region": demo_region, "item_count": item_count},
                        timeout=15,
                    )
                    if resp.status_code == 200:
                        st.success("Demo estimate ready!")
                        st.session_state["selected_estimate_id"] = resp.json()["id"]
                    else:
                        st.error(f"Error: {resp.text}")
                except Exception as e:
                    st.error(f"Connection failed: {e}")

    elif mode == "📤 Upload New Package":
        st.subheader("Upload Bid Package")
        up_name = st.text_input("Project Name", value="New Civil Project")
        up_region = st.text_input("Location / Region", value="District 1 (Northwest)")
        boq_file = st.file_uploader("Bill of Quantities (CSV / Excel)", type=["csv", "xlsx", "xls"])
        spec_file = st.file_uploader("Project Specifications (PDF / TXT)", type=["pdf", "txt"])

        if st.button("Upload & Estimate", type="primary", disabled=boq_file is None):
            with st.spinner("Parsing specifications and computing unit price distributions..."):
                try:
                    files = {"boq_file": (boq_file.name, boq_file.getvalue(), "application/octet-stream")}
                    if spec_file:
                        files["spec_file"] = (spec_file.name, spec_file.getvalue(), "application/octet-stream")
                    data = {"project_name": up_name, "location_region": up_region}

                    resp = requests.post(f"{API_URL}/api/v1/estimates/upload", data=data, files=files, timeout=30)
                    if resp.status_code == 200:
                        st.success("Package estimated successfully!")
                        st.session_state["selected_estimate_id"] = resp.json()["id"]
                    else:
                        st.error(f"Upload failed: {resp.text}")
                except Exception as e:
                    st.error(f"Request failed: {e}")


# Main Content Area - Active Estimate Review
selected_id = st.session_state.get("selected_estimate_id")

try:
    list_resp = requests.get(f"{API_URL}/api/v1/estimates", timeout=5)
    estimates_list = list_resp.json() if list_resp.status_code == 200 else []
except Exception:
    estimates_list = []

if estimates_list:
    est_options = {f"{e['project_name']} ({e['id']})": e["id"] for e in estimates_list}
    chosen_label = st.selectbox(
        "Select Estimate to Review:",
        options=list(est_options.keys()),
        index=0 if not selected_id else [i for i, k in enumerate(est_options.values()) if k == selected_id][0] if selected_id in est_options.values() else 0,
    )
    selected_id = est_options[chosen_label]

if selected_id:
    try:
        detail_resp = requests.get(f"{API_URL}/api/v1/estimates/{selected_id}", timeout=10)
        if detail_resp.status_code == 200:
            est = detail_resp.json()

            # Header metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Low (10th %ile)", f"${est['total_cost_low']:,.2f}")
            with col2:
                st.metric("Expected Total (50th %ile)", f"${est['total_cost_expected']:,.2f}")
            with col3:
                st.metric("Total High (90th %ile)", f"${est['total_cost_high']:,.2f}")
            with col4:
                status_color = "🟢" if est["status"] == "approved" else "🟡"
                st.metric("Status", f"{status_color} {est['status'].upper()}")

            st.divider()

            # Actions & Export Bar
            btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 4])
            with btn_col1:
                if est["status"] != "approved":
                    if st.button("✅ Approve Estimate", type="primary"):
                        requests.post(f"{API_URL}/api/v1/estimates/{selected_id}/approve")
                        st.rerun()
            with btn_col2:
                csv_url = f"{API_URL}/api/v1/estimates/{selected_id}/export/csv"
                excel_url = f"{API_URL}/api/v1/estimates/{selected_id}/export/excel"
                st.link_button("📥 Export Excel", excel_url)

            st.subheader(f"📋 Line Items Breakdown ({len(est['line_items'])} items)")

            # Tabular breakdown & overrides
            for idx, item in enumerate(est["line_items"], 1):
                with st.expander(
                    f"{idx}. [{item['item_code']}] {item['item_description']} — {item['quantity']:,.2f} {item['unit_of_measure']} @ ${item['unit_price_expected']:,.2f} (Total: ${item['extended_cost']:,.2f})",
                    expanded=False,
                ):
                    c1, c2, c3 = st.columns([2, 1, 1])
                    with c1:
                        st.markdown(f"**Matched Spec Section:** `{item['matched_spec_section'] or 'General Standard Spec'}`")
                        st.markdown(f"**Model Justification:** {item['justification_text']}")
                        if item.get("comparable_bids"):
                            st.caption("🔍 Comparable Historical DOT Bids:")
                            comp_df = pd.DataFrame(item["comparable_bids"])
                            st.dataframe(comp_df, hide_index=True, use_container_width=True)

                    with c2:
                        st.write("📊 **Quantile Price Bands**")
                        st.write(f"• Low (10%): `${item['unit_price_low']:,.2f}`")
                        st.write(f"• Expected (50%): `${item['unit_price_expected']:,.2f}`")
                        st.write(f"• High (90%): `${item['unit_price_high']:,.2f}`")

                    with c3:
                        st.write("✏️ **Manual Price Override**")
                        new_price = st.number_input(
                            f"Unit Price ($/{item['unit_of_measure']})",
                            min_value=0.01,
                            value=float(item["unit_price_expected"]),
                            key=f"override_{item['id']}",
                        )
                        if st.button("Apply Override", key=f"btn_{item['id']}"):
                            requests.patch(
                                f"{API_URL}/api/v1/estimates/{selected_id}/line-items/{item['id']}",
                                json={"overridden_unit_price": new_price},
                            )
                            st.success("Price updated!")
                            st.rerun()

    except Exception as e:
        st.error(f"Could not load estimate details: {e}")
else:
    st.info("👋 No estimates found yet. Use the sidebar to generate an instant demo package or upload a custom BOQ.")
