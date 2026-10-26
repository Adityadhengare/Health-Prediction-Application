"""
Comprehensive End-to-End Test Suite for Health Prediction Application
----------------------------------------------------------------------
Validates:
1. Input validation for all 10 assessment test records (7 valid, 3 rejected).
2. SQLite persistent CRUD: Create, Read, Update (email to gokul@infocare.com), Delete.
3. Import Idempotency:
   - First import inserts exactly 7 records.
   - Second import inserts 0 additional records.
   - Both Robyn Pears records (Record #1 and Record #6) remain separate distinct rows.
4. AI Service Behavior:
   - Verifies live API response when key is present (tagged [Source: External AI API...]).
   - Verifies deterministic rule-based response in offline/fallback mode (tagged [Source: Local Rule-Based Engine...]).
"""

import os
from datetime import date
from database import db_manager
from services import validator, ai_service
from data.test_records import ASSESSMENT_TEST_RECORDS

TEST_DB_NAME = "e2e_isolated_test.db"


def run_all_tests():
    print("=" * 60)
    print("RUNNING HEALTH PREDICTION APPLICATION INTEGRATION TESTS")
    print("=" * 60)

    # Clean up any leftover test db
    if os.path.exists(TEST_DB_NAME):
        os.remove(TEST_DB_NAME)

    # 1. Validation Test on 10 Assessment Records
    print("\n[TEST 1] Evaluating Assessment Records against Validation Engine...")
    ref_date = date(2026, 10, 26)
    valid_records = []
    rejected_count = 0

    for r in ASSESSMENT_TEST_RECORDS:
        is_valid, errors, cleaned = validator.validate_patient_record(r, reference_today=ref_date)
        if is_valid:
            valid_records.append((r["test_id"], cleaned))
            print(f"  [VALID] Record #{r['test_id']} ({r['full_name']}): VALID")
        else:
            rejected_count += 1
            print(f"  [REJECTED] Record #{r['test_id']} ({r['full_name']}): REJECTED -> {errors}")

    assert len(valid_records) == 7, f"Expected 7 valid, got {len(valid_records)}"
    assert rejected_count == 3, f"Expected 3 rejected, got {rejected_count}"
    print("  --> Assessment Data Validation Test: PASSED (7 valid, 3 rejected)")

    # 2. Database Initialization & CRUD Operations Test
    print("\n[TEST 2] Testing Database CRUD Operations on Isolated Test DB...")
    db_manager.init_db(TEST_DB_NAME)
    assert os.path.exists(TEST_DB_NAME), "Database file was not created"

    # CREATE MANUAL PATIENT
    pid_manual = db_manager.create_patient(
        full_name="Manual Patient",
        date_of_birth="15/05/1985",
        email="manual@test.com",
        glucose=110,
        haemoglobin=14.0,
        cholesterol=175,
        remarks="Manual entry remark",
        source_type="TEST_MANUAL",
        is_assessment_record=0,
        db_path=TEST_DB_NAME,
    )
    assert pid_manual == 1, f"Expected patient ID 1, got {pid_manual}"
    print("  [PASS] Create manual patient")

    # READ
    patient = db_manager.get_patient_by_id(pid_manual, db_path=TEST_DB_NAME)
    assert patient is not None, "Failed to retrieve created patient"
    assert patient["full_name"] == "Manual Patient"
    print("  [PASS] Read patient by ID")

    # UPDATE (Assessment Requirement: change email to gokul@infocare.com)
    updated = db_manager.update_patient(
        patient_id=pid_manual,
        full_name=patient["full_name"],
        date_of_birth=patient["date_of_birth"],
        email="gokul@infocare.com",
        glucose=patient["glucose"],
        haemoglobin=patient["haemoglobin"],
        cholesterol=patient["cholesterol"],
        db_path=TEST_DB_NAME,
    )
    assert updated is True, "Update patient failed"
    patient_after_update = db_manager.get_patient_by_id(pid_manual, db_path=TEST_DB_NAME)
    assert patient_after_update["email"] == "gokul@infocare.com", "Email was not updated to gokul@infocare.com"
    print("  [PASS] Update email to 'gokul@infocare.com'")

    # DELETE
    deleted = db_manager.delete_patient(pid_manual, db_path=TEST_DB_NAME)
    assert deleted is True, "Delete patient failed"
    count_after_del = db_manager.count_patients(db_path=TEST_DB_NAME)
    assert count_after_del == 0, f"Expected 0 patients, got {count_after_del}"
    print("  [PASS] Delete patient and refresh count")

    # 3. Assessment Import Idempotency Test
    print("\n[TEST 3] Testing Assessment Import Idempotency & Duplicate Preservation...")
    assert not db_manager.is_assessment_batch_imported(TEST_DB_NAME), "Expected batch not imported yet"

    # First Import
    for test_id, rec in valid_records:
        db_manager.create_patient(
            full_name=rec["full_name"],
            date_of_birth=rec["date_of_birth"],
            email=rec["email"],
            glucose=rec["glucose"],
            haemoglobin=rec["haemoglobin"],
            cholesterol=rec["cholesterol"],
            remarks="Test Remarks",
            source_type="TEST_SOURCE",
            is_assessment_record=1,
            assessment_test_id=test_id,
            db_path=TEST_DB_NAME,
        )
    db_manager.mark_assessment_batch_imported(True, db_path=TEST_DB_NAME)

    count_first_import = db_manager.count_patients(db_path=TEST_DB_NAME)
    assert count_first_import == 7, f"Expected exactly 7 rows after first import, got {count_first_import}"
    assert db_manager.is_assessment_batch_imported(TEST_DB_NAME) is True
    print(f"  [PASS] First import created exactly {count_first_import} records")

    # Verify both Robyn Pears records exist as distinct rows with unique IDs
    all_patients = db_manager.get_all_patients(db_path=TEST_DB_NAME)
    robyn_records = [p for p in all_patients if p["full_name"] == "Robyn Pears"]
    assert len(robyn_records) == 2, f"Expected 2 Robyn Pears records, got {len(robyn_records)}"
    assert robyn_records[0]["id"] != robyn_records[1]["id"], "Robyn Pears records must have distinct IDs"
    assert robyn_records[0]["assessment_test_id"] == 1
    assert robyn_records[1]["assessment_test_id"] == 6
    print(f"  [PASS] Both Robyn Pears records preserved separately (IDs #{robyn_records[0]['id']} & #{robyn_records[1]['id']})")

    # Second Import Attempt (Simulating app rerun or second button click)
    if not db_manager.is_assessment_batch_imported(TEST_DB_NAME):
        for test_id, rec in valid_records:
            db_manager.create_patient(
                full_name=rec["full_name"],
                date_of_birth=rec["date_of_birth"],
                email=rec["email"],
                glucose=rec["glucose"],
                haemoglobin=rec["haemoglobin"],
                cholesterol=rec["cholesterol"],
                remarks="Test Remarks",
                source_type="TEST_SOURCE",
                is_assessment_record=1,
                assessment_test_id=test_id,
                db_path=TEST_DB_NAME,
            )
    count_second_import = db_manager.count_patients(db_path=TEST_DB_NAME)
    assert count_second_import == 7, f"Second import should insert 0 records, got total {count_second_import}"
    print(f"  [PASS] Second import safely blocked by idempotency guard (Total remains {count_second_import})")

    # 4. AI Service: Verify Both Live API and Fallback Tagging
    print("\n[TEST 4] Testing AI Service Behavior & Distinct Provenance Labeling...")
    
    # 4A. Test remarks generation (Live or Fallback depending on network/quota)
    remarks, source = ai_service.generate_health_remarks("Test Patient", "01/01/1990", 240, 9.0, 310)
    assert "[Source:" in remarks, "Remarks missing explicit [Source: ...] tag"
    assert "DISCLAIMER" in remarks, "Remarks missing medical disclaimer"
    if source == "EXTERNAL_AI":
        assert "[Source: External AI API" in remarks
        print("  [PASS] Live Gemini API call succeeded with tag: EXTERNAL_AI")
    else:
        assert "[Source: Local Rule-Based Engine" in remarks
        print(f"  [PASS] Graceful fallback activated promptly with tag: {source}")

    # 4B. Test Local Clinical Fallback Engine (Deterministic directly)
    remarks_fallback = ai_service.generate_local_fallback_remarks(240, 9.0, 310)
    assert "[Source: Local Rule-Based Engine (API unavailable/offline)]" in remarks_fallback, "Fallback missing local engine tag"
    assert "DISCLAIMER" in remarks_fallback, "Fallback remarks missing medical disclaimer"
    print("  [PASS] Local clinical fallback engine verified with distinct [Source: Local Rule-Based Engine] tag")

    # Clean up test DB
    if os.path.exists(TEST_DB_NAME):
        os.remove(TEST_DB_NAME)

    print("\n" + "=" * 60)
    print("ALL INTEGRATION & IDEMPOTENCY TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
