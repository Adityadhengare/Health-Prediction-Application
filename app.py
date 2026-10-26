"""
Health Prediction Application - Streamlit Frontend
---------------------------------------------------
A clean, professional, beginner-friendly web application for managing patient health records
and generating AI-assisted health-risk remarks.

Key Functional Modules:
1. Medical Disclaimer Banner (permanent).
2. Assessment Evaluation & Test Runner:
   - Displays all 10 raw assessment records verbatim.
   - Shows live validation outcomes and exact error messages for invalid records.
   - Idempotent Import: Prevents repeated imports from creating duplicate sets on re-runs.
   - Preserves Record #6 duplicate as a distinct entry in the batch.
   - Includes Safe Reset actions with clear confirmation warnings.
3. All Saved Patient Records:
   - Formats dates as DD/MM/YYYY.
   - Shows all required fields + AI remarks and explicit source badges.
4. Add New Patient Record:
   - Live validation, immediate user feedback, remarks generation, and database insert.
5. Edit Record:
   - Select any record and update fields, including changing email to gokul@infocare.com.
6. Delete Record:
   - Delete any selected record with immediate list refresh.
"""

import streamlit as st
from datetime import date
from database import db_manager
from services import validator, ai_service
from data.test_records import get_assessment_records

# ------------------------------------------------------------------------------
# App Configuration & Initialization
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Health Prediction Application",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Ensure database tables and columns are initialized
db_manager.init_db()

# ------------------------------------------------------------------------------
# Header & Medical Disclaimer
# ------------------------------------------------------------------------------
st.title("🩺 Health Prediction Application")
st.caption("AI Growth & Automation Associate Assessment | Task 2")

st.info(
    "⚠️ **Medical Disclaimer**: This application provides automated health-risk observations "
    "for informational and educational purposes only based on blood test results. It does not provide "
    "a confirmed medical diagnosis, clinical opinion, or treatment plan. Always consult a qualified healthcare professional.",
    icon="ℹ️",
)

# ------------------------------------------------------------------------------
# Sidebar Navigation & System Status
# ------------------------------------------------------------------------------
st.sidebar.title("Navigation")
menu_selection = st.sidebar.radio(
    "Go to Section:",
    [
        "📋 Assessment Test Data & Validation",
        "👥 All Saved Patient Records",
        "➕ Add New Patient",
        "✏️ Edit Patient Record",
        "🗑️ Delete Patient Record",
        "⚙️ Database & Demo Reset",
    ],
)

saved_count = db_manager.count_patients()
st.sidebar.metric(label="Saved Records in Database", value=saved_count)

st.sidebar.divider()
st.sidebar.markdown("### 🔑 AI Service Status")
if ai_service.is_api_key_configured():
    st.sidebar.success("Gemini API Key Detected", icon="✅")
    if st.sidebar.button("Test AI Connection", type="secondary"):
        with st.sidebar.spinner("Testing API connection (no patient data sent)..."):
            connected, msg = ai_service.test_gemini_connection()
            if connected:
                st.sidebar.success(msg, icon="🎉")
            else:
                st.sidebar.error(msg, icon="❌")
else:
    st.sidebar.warning("Using Local Clinical Fallback (Offline Mode)", icon="⚠️")
    st.sidebar.caption("No active `.env` file found. Create `.env` from `.env.example` to enable live Gemini AI.")


# ------------------------------------------------------------------------------
# SECTION 1: Assessment Test Data & Validation
# ------------------------------------------------------------------------------
if menu_selection == "📋 Assessment Test Data & Validation":
    st.header("📋 Task 2 Assessment Test Data Evaluation")
    st.markdown(
        """
        This section evaluates the **10 raw assessment records** provided in the official Task 2 specification.
        - **Integrity**: Original values are displayed verbatim without silent alterations.
        - **Validation**: Each record is checked for email format, calendar date validity, future dates, and numeric metrics.
        - **Error Explanations**: For any invalid record, the exact reasons are clearly explained below.
        """
    )

    raw_records = get_assessment_records()
    validation_results = []
    valid_records_to_import = []

    for r in raw_records:
        is_valid, errors, cleaned = validator.validate_patient_record(r)
        status_badge = "🟢 VALID" if is_valid else "🔴 REJECTED"
        error_text = "; ".join(errors) if errors else "Passed all validation checks"
        
        validation_results.append({
            "Test #": r["test_id"],
            "Full Name": r["full_name"],
            "Date of Birth": r["date_of_birth"],
            "Email": r["email"],
            "Glucose": r["glucose"],
            "Haemoglobin": r["haemoglobin"],
            "Cholesterol": r["cholesterol"],
            "Validation Status": status_badge,
            "Validation Errors / Remarks": error_text,
        })
        
        if is_valid:
            valid_records_to_import.append((r["test_id"], cleaned))

    st.dataframe(validation_results, use_container_width=True, hide_index=True)

    # Explanation of detected errors for video and assessment demonstration
    st.markdown("### 🔍 Detailed Error Breakdown for Assessment Video Walkthrough")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.error("**Record #2: John Hunter**")
        st.write("• **Input Email**: `hunter@gmail`")
        st.write("• **Why it occurred**: Missing top-level domain suffix (e.g. `.com`).")
        st.write("• **Detection**: Rejected by RFC email regex pattern.")
    with col2:
        st.error("**Record #4: Peter Larry**")
        st.write("• **Input DOB**: `31.11.2001`")
        st.write("• **Why it occurred**: November only has 30 days. Day 31 does not exist.")
        st.write("• **Detection**: Detected via Python calendar parsing (`strptime`).")
    with col3:
        st.error("**Record #8: Kris Wu**")
        st.write("• **Input DOB**: `19.10.2030` (Future Date)")
        st.write("• **Input Email**: `Kris.wu.gmail.com` (Missing `@`)")
        st.write("• **Detection**: Date comparison against system today & missing `@` symbol.")

    st.markdown("---")
    st.subheader("📥 Assessment Records Import (Idempotent)")
    
    already_imported = db_manager.is_assessment_batch_imported()
    
    if already_imported:
        st.success(
            "✅ **Assessment Batch Already Imported**: The 7 valid assessment records are already present in the database. "
            "To prevent accidental duplicate entries, the import button is safely locked. "
            "If you wish to re-import, visit the **⚙️ Database & Demo Reset** section.",
            icon="🔒"
        )
    else:
        st.write(
            "Click below to import the **7 valid assessment records** (including the intentional duplicate **Robyn Pears #6** as a separate entry) "
            "and generate remarks for each. Re-running is strictly protected against accidental repeated sets."
        )

        if st.button("🚀 Process & Import Valid Records into SQLite", type="primary"):
            with st.spinner("Processing valid records and generating remarks..."):
                imported_count = 0
                for test_id, rec in valid_records_to_import:
                    remarks, source_type = ai_service.generate_health_remarks(
                        full_name=rec["full_name"],
                        date_of_birth=rec["date_of_birth"],
                        glucose=rec["glucose"],
                        haemoglobin=rec["haemoglobin"],
                        cholesterol=rec["cholesterol"],
                    )
                    db_manager.create_patient(
                        full_name=rec["full_name"],
                        date_of_birth=rec["date_of_birth"],
                        email=rec["email"],
                        glucose=rec["glucose"],
                        haemoglobin=rec["haemoglobin"],
                        cholesterol=rec["cholesterol"],
                        remarks=remarks,
                        source_type=source_type,
                        is_assessment_record=1,
                        assessment_test_id=test_id,
                    )
                    imported_count += 1
                
                # Mark batch as imported so reruns don't duplicate
                db_manager.mark_assessment_batch_imported(True)
                
                st.success(
                    f"Successfully saved exactly {imported_count} valid records into the SQLite database! "
                    "Notice that invalid records (#2, #4, #8) were strictly blocked from database entry.",
                    icon="🎉",
                )
                st.rerun()


# ------------------------------------------------------------------------------
# SECTION 2: All Saved Patient Records
# ------------------------------------------------------------------------------
elif menu_selection == "👥 All Saved Patient Records":
    st.header("👥 Saved Patient Records Directory")
    st.markdown("All persistent records currently stored in SQLite (`health_app.db`).")

    patients = db_manager.get_all_patients()

    if not patients:
        st.warning("No patient records found in the database. Add a new record or import valid assessment records.", icon="📂")
    else:
        st.write(f"Total Records: **{len(patients)}**")
        
        display_data = []
        for p in patients:
            record_tag = "Assessment Test" if p.get("is_assessment_record") else "Manual Entry"
            display_data.append({
                "ID": p["id"],
                "Full Name": p["full_name"],
                "Date of Birth": p["date_of_birth"],
                "Email Address": p["email"],
                "Glucose (mg/dL)": p["glucose"],
                "Haemoglobin (g/dL)": p["haemoglobin"],
                "Cholesterol (mg/dL)": p["cholesterol"],
                "Category": record_tag,
                "Source": p.get("source_type", "UNKNOWN"),
                "Remarks": p["remarks"],
            })
        
        st.dataframe(display_data, use_container_width=True, hide_index=True)

        st.markdown("### 📄 Detailed Patient Records & Remarks View")
        for p in patients:
            category_text = f"Assessment #{p['assessment_test_id']}" if p.get("is_assessment_record") else "Manual Entry"
            with st.expander(f"👤 Patient #{p['id']}: {p['full_name']} ({p['email']}) - [{category_text}]"):
                col1, col2, col3, col4 = st.columns(4)
                col1.write(f"**DOB**: {p['date_of_birth']}")
                col2.write(f"**Glucose**: {p['glucose']} mg/dL")
                col3.write(f"**Haemoglobin**: {p['haemoglobin']} g/dL")
                col4.write(f"**Cholesterol**: {p['cholesterol']} mg/dL")
                
                st.markdown("**Remarks generated:**")
                st.info(p["remarks"])
                
                # Resilient option: Regenerate AI remarks for this existing patient record
                if st.button(f"🔄 Regenerate AI Remarks for Patient #{p['id']}", key=f"retry_remarks_{p['id']}"):
                    with st.spinner("Calling Gemini API to refresh remarks..."):
                        new_remarks, new_source = ai_service.generate_health_remarks(
                            full_name=p["full_name"],
                            date_of_birth=p["date_of_birth"],
                            glucose=p["glucose"],
                            haemoglobin=p["haemoglobin"],
                            cholesterol=p["cholesterol"],
                        )
                        db_manager.update_patient(
                            patient_id=p["id"],
                            full_name=p["full_name"],
                            date_of_birth=p["date_of_birth"],
                            email=p["email"],
                            glucose=p["glucose"],
                            haemoglobin=p["haemoglobin"],
                            cholesterol=p["cholesterol"],
                            remarks=new_remarks,
                            source_type=new_source,
                        )
                    st.success(f"Remarks refreshed for Patient #{p['id']}! (Updated in-place with no duplicates)", icon="✨")
                    st.rerun()


# ------------------------------------------------------------------------------
# SECTION 3: Add New Patient
# ------------------------------------------------------------------------------
elif menu_selection == "➕ Add New Patient":
    st.header("➕ Add New Patient Record")
    st.markdown("Enter patient details and blood test measurements. Date format must be **DD/MM/YYYY**.")

    with st.form("add_patient_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Full Name *", placeholder="e.g. Robyn Pears")
            dob_input = st.text_input("Date of Birth (DD/MM/YYYY) *", placeholder="e.g. 28/01/1960")
            email = st.text_input("Email Address *", placeholder="e.g. robyn@gmail.com")
        with col2:
            glucose = st.text_input("Glucose (mg/dL) *", placeholder="e.g. 120 or 232")
            haemoglobin = st.text_input("Haemoglobin (g/dL) *", placeholder="e.g. 13.5")
            cholesterol = st.text_input("Cholesterol (mg/dL) *", placeholder="e.g. 180")

        submitted = st.form_submit_button("Save Patient & Generate Remarks", type="primary")

        if submitted:
            candidate_record = {
                "full_name": full_name,
                "date_of_birth": dob_input,
                "email": email,
                "glucose": glucose,
                "haemoglobin": haemoglobin,
                "cholesterol": cholesterol,
            }

            is_valid, errors, cleaned = validator.validate_patient_record(candidate_record)

            if not is_valid:
                st.error("Validation Failed. Please correct the following errors before submitting:")
                for err in errors:
                    st.write(f"• {err}")
            else:
                with st.spinner("Generating clinical observations and remarks..."):
                    remarks, source_type = ai_service.generate_health_remarks(
                        full_name=cleaned["full_name"],
                        date_of_birth=cleaned["date_of_birth"],
                        glucose=cleaned["glucose"],
                        haemoglobin=cleaned["haemoglobin"],
                        cholesterol=cleaned["cholesterol"],
                    )
                    new_id = db_manager.create_patient(
                        full_name=cleaned["full_name"],
                        date_of_birth=cleaned["date_of_birth"],
                        email=cleaned["email"],
                        glucose=cleaned["glucose"],
                        haemoglobin=cleaned["haemoglobin"],
                        cholesterol=cleaned["cholesterol"],
                        remarks=remarks,
                        source_type=source_type,
                        is_assessment_record=0,
                    )
                st.success(f"Patient record successfully created with ID #{new_id}!", icon="✅")
                st.info(f"**Remarks Added:**\n\n{remarks}")


# ------------------------------------------------------------------------------
# SECTION 4: Edit Patient Record
# ------------------------------------------------------------------------------
elif menu_selection == "✏️ Edit Patient Record":
    st.header("✏️ Edit Patient Record")
    st.markdown(
        "Official Assessment Operation: *'Choose any ONE Record and change their email Id to `gokul@infocare.com`'*"
    )

    patients = db_manager.get_all_patients()

    if not patients:
        st.warning("No records available to edit. Please add or import records first.")
    else:
        patient_options = {f"ID #{p['id']}: {p['full_name']} ({p['email']})": p["id"] for p in patients}
        selected_label = st.selectbox("Select Patient to Edit:", list(patient_options.keys()))
        selected_id = patient_options[selected_label]
        patient = db_manager.get_patient_by_id(selected_id)

        if patient:
            st.divider()
            # Shortcut button for assessment requirement
            if st.button("⚡ Quick Action: Set Email to gokul@infocare.com", type="secondary"):
                db_manager.update_patient(
                    patient_id=selected_id,
                    full_name=patient["full_name"],
                    date_of_birth=patient["date_of_birth"],
                    email="gokul@infocare.com",
                    glucose=patient["glucose"],
                    haemoglobin=patient["haemoglobin"],
                    cholesterol=patient["cholesterol"],
                )
                st.success(f"Email for Patient #{selected_id} updated to gokul@infocare.com!", icon="✅")
                st.rerun()

            with st.form("edit_patient_form"):
                col1, col2 = st.columns(2)
                with col1:
                    edit_name = st.text_input("Full Name", value=patient["full_name"])
                    edit_dob = st.text_input("Date of Birth (DD/MM/YYYY)", value=patient["date_of_birth"])
                    edit_email = st.text_input("Email Address", value=patient["email"])
                with col2:
                    edit_glucose = st.text_input("Glucose (mg/dL)", value=str(patient["glucose"]))
                    edit_hb = st.text_input("Haemoglobin (g/dL)", value=str(patient["haemoglobin"]))
                    edit_chol = st.text_input("Cholesterol (mg/dL)", value=str(patient["cholesterol"]))

                update_submitted = st.form_submit_button("Update Record", type="primary")

                if update_submitted:
                    update_candidate = {
                        "full_name": edit_name,
                        "date_of_birth": edit_dob,
                        "email": edit_email,
                        "glucose": edit_glucose,
                        "haemoglobin": edit_hb,
                        "cholesterol": edit_chol,
                    }
                    is_valid, errors, cleaned = validator.validate_patient_record(update_candidate)

                    if not is_valid:
                        st.error("Validation Failed. Cannot update record:")
                        for err in errors:
                            st.write(f"• {err}")
                    else:
                        db_manager.update_patient(
                            patient_id=selected_id,
                            full_name=cleaned["full_name"],
                            date_of_birth=cleaned["date_of_birth"],
                            email=cleaned["email"],
                            glucose=cleaned["glucose"],
                            haemoglobin=cleaned["haemoglobin"],
                            cholesterol=cleaned["cholesterol"],
                        )
                        st.success(f"Record #{selected_id} updated successfully!", icon="✅")
                        st.rerun()


# ------------------------------------------------------------------------------
# SECTION 5: Delete Patient Record
# ------------------------------------------------------------------------------
elif menu_selection == "🗑️ Delete Patient Record":
    st.header("🗑️ Delete Patient Record")
    st.markdown(
        "Official Assessment Operation: *'Choose any ONE record and delete the record. "
        "Once you have deleted the record, show again the list of all records you have.'*"
    )

    patients = db_manager.get_all_patients()

    if not patients:
        st.warning("No records available to delete.")
    else:
        patient_options = {f"ID #{p['id']}: {p['full_name']} ({p['email']})": p["id"] for p in patients}
        selected_label = st.selectbox("Select Record to Delete:", list(patient_options.keys()))
        selected_id = patient_options[selected_label]
        target_patient = db_manager.get_patient_by_id(selected_id)

        if target_patient:
            st.warning(
                f"Are you sure you want to delete **{target_patient['full_name']}** (ID #{target_patient['id']})?",
                icon="⚠️",
            )
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("Confirm Delete", type="primary"):
                    db_manager.delete_patient(selected_id)
                    st.success(f"Patient Record #{selected_id} has been permanently deleted.", icon="🗑️")
                    st.rerun()

        st.divider()
        st.subheader("Current Patient Records List")
        updated_patients = db_manager.get_all_patients()
        if updated_patients:
            st.dataframe(
                [
                    {
                        "ID": p["id"],
                        "Full Name": p["full_name"],
                        "DOB": p["date_of_birth"],
                        "Email": p["email"],
                        "Glucose": p["glucose"],
                        "Haemoglobin": p["haemoglobin"],
                        "Cholesterol": p["cholesterol"],
                    }
                    for p in updated_patients
                ],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("All records have been deleted.")


# ------------------------------------------------------------------------------
# SECTION 6: Database & Demo Reset
# ------------------------------------------------------------------------------
elif menu_selection == "⚙️ Database & Demo Reset":
    st.header("⚙️ Database & Demo Reset Controls")
    st.markdown(
        """
        Use these controls to prepare for your **video recording** or **HR demonstration**.
        - **Option 1**: Reset only the assessment records (preserves any manual patient records you added).
        - **Option 2**: Complete fresh database reset (wipes all records and resets ID counter to 1).
        """
    )

    st.subheader("1. Reset Assessment Batch Only")
    st.write("Removes only the 7 imported assessment records, allowing you to click the import button again in your demo video.")
    if st.button("🔄 Clear Assessment Records (Preserve Manual Data)", type="secondary"):
        deleted = db_manager.reset_assessment_records()
        st.success(f"Cleared {deleted} assessment records. Assessment import is now unlocked!", icon="🔓")
        st.rerun()

    st.divider()
    st.subheader("2. Complete Fresh Database Reset")
    st.warning("⚠️ **Warning**: This permanently removes ALL patient records from the database.", icon="⚠️")
    
    confirm_reset = st.checkbox("I understand that this will delete all saved patients.")
    if st.button("💥 Reset Entire Database (Fresh Demo State)", type="primary", disabled=not confirm_reset):
        db_manager.reset_entire_database()
        st.success("Database has been completely reset to fresh state (0 records, ID counter reset to 1).", icon="✨")
        st.rerun()
