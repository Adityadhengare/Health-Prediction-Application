"""
Database Manager Module for Health Prediction Application
---------------------------------------------------------
Handles SQLite persistent storage using Python's built-in sqlite3 library.

CRUD Capabilities:
1. init_db(): Creates 'patients' table and 'import_batches' table if they don't exist.
2. create_patient(): Inserts a validated patient record with auto-increment ID.
3. get_all_patients(): Retrieves all stored records.
4. get_patient_by_id(): Retrieves a single record by primary key ID.
5. update_patient(): Updates fields (specifically tested for email update to gokul@infocare.com).
6. delete_patient(): Deletes a record by ID.
7. count_patients(): Returns total saved count.
8. Assessment Batch Idempotency:
   - has_imported_assessment_batch(): Checks if the assessment batch has already been imported.
   - mark_assessment_batch_imported(): Marks batch as imported.
   - reset_assessment_records(): Deletes only assessment-imported records (preserving manual additions).
   - reset_all_database(): Clear all records for a clean demonstration.
"""

import os
import sqlite3
from typing import Any, Dict, List, Optional

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "health_app.db"
)


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Initializes the database schema if not already present."""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        date_of_birth TEXT NOT NULL,
        email TEXT NOT NULL,
        glucose REAL NOT NULL,
        haemoglobin REAL NOT NULL,
        cholesterol REAL NOT NULL,
        remarks TEXT NOT NULL,
        source_type TEXT NOT NULL DEFAULT 'UNKNOWN',
        is_assessment_record INTEGER NOT NULL DEFAULT 0,
        assessment_test_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    create_batch_tracker_sql = """
    CREATE TABLE IF NOT EXISTS system_metadata (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(create_table_sql)
        cursor.execute(create_batch_tracker_sql)
        
        # Check if is_assessment_record column exists (migration helper if table existed)
        cursor.execute("PRAGMA table_info(patients);")
        columns = [row[1] for row in cursor.fetchall()]
        if "is_assessment_record" not in columns:
            cursor.execute("ALTER TABLE patients ADD COLUMN is_assessment_record INTEGER NOT NULL DEFAULT 0;")
        if "assessment_test_id" not in columns:
            cursor.execute("ALTER TABLE patients ADD COLUMN assessment_test_id INTEGER;")
            
        conn.commit()
    finally:
        conn.close()


def create_patient(
    full_name: str,
    date_of_birth: str,
    email: str,
    glucose: float,
    haemoglobin: float,
    cholesterol: float,
    remarks: str,
    source_type: str = "UNKNOWN",
    is_assessment_record: int = 0,
    assessment_test_id: Optional[int] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> int:
    """
    Inserts a new patient record into the SQLite database.
    Returns the auto-generated primary key ID.
    """
    insert_sql = """
    INSERT INTO patients (
        full_name, date_of_birth, email, glucose, haemoglobin, cholesterol,
        remarks, source_type, is_assessment_record, assessment_test_id
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            insert_sql,
            (
                full_name.strip(),
                date_of_birth.strip(),
                email.strip(),
                float(glucose),
                float(haemoglobin),
                float(cholesterol),
                remarks.strip(),
                source_type.strip(),
                int(is_assessment_record),
                assessment_test_id,
            ),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_all_patients(db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Retrieves all patient records ordered by ID ascending."""
    query_sql = """
    SELECT id, full_name, date_of_birth, email, glucose, haemoglobin, cholesterol,
           remarks, source_type, is_assessment_record, assessment_test_id, created_at, updated_at
    FROM patients
    ORDER BY id ASC;
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute(query_sql)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_patient_by_id(patient_id: int, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieves a single patient record by ID, or None if not found."""
    query_sql = """
    SELECT id, full_name, date_of_birth, email, glucose, haemoglobin, cholesterol,
           remarks, source_type, is_assessment_record, assessment_test_id, created_at, updated_at
    FROM patients
    WHERE id = ?;
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute(query_sql, (patient_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_patient(
    patient_id: int,
    full_name: str,
    date_of_birth: str,
    email: str,
    glucose: float,
    haemoglobin: float,
    cholesterol: float,
    remarks: Optional[str] = None,
    source_type: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> bool:
    """
    Updates an existing patient record.
    Returns True if a record was updated, False if ID not found.
    """
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        if remarks is not None and source_type is not None:
            update_sql = """
            UPDATE patients
            SET full_name = ?,
                date_of_birth = ?,
                email = ?,
                glucose = ?,
                haemoglobin = ?,
                cholesterol = ?,
                remarks = ?,
                source_type = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
            """
            params = (
                full_name.strip(),
                date_of_birth.strip(),
                email.strip(),
                float(glucose),
                float(haemoglobin),
                float(cholesterol),
                remarks.strip(),
                source_type.strip(),
                patient_id,
            )
        else:
            update_sql = """
            UPDATE patients
            SET full_name = ?,
                date_of_birth = ?,
                email = ?,
                glucose = ?,
                haemoglobin = ?,
                cholesterol = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
            """
            params = (
                full_name.strip(),
                date_of_birth.strip(),
                email.strip(),
                float(glucose),
                float(haemoglobin),
                float(cholesterol),
                patient_id,
            )
        cursor.execute(update_sql, params)
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_patient(patient_id: int, db_path: str = DEFAULT_DB_PATH) -> bool:
    """
    Deletes a patient record by ID.
    Returns True if record was deleted, False if ID not found.
    """
    delete_sql = "DELETE FROM patients WHERE id = ?;"
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(delete_sql, (patient_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def count_patients(db_path: str = DEFAULT_DB_PATH) -> int:
    """Returns total count of saved patient records."""
    count_sql = "SELECT COUNT(*) FROM patients;"
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(count_sql)
        return cursor.fetchone()[0]
    finally:
        conn.close()


# ------------------------------------------------------------------------------
# Assessment Batch Idempotency & Reset Management
# ------------------------------------------------------------------------------
def is_assessment_batch_imported(db_path: str = DEFAULT_DB_PATH) -> bool:
    """Checks whether the official assessment batch has already been imported."""
    check_sql = "SELECT value FROM system_metadata WHERE key = 'assessment_batch_imported';"
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(check_sql)
        row = cursor.fetchone()
        return row is not None and row[0] == "true"
    finally:
        conn.close()


def mark_assessment_batch_imported(imported: bool = True, db_path: str = DEFAULT_DB_PATH) -> None:
    """Marks assessment batch status in system_metadata table."""
    val = "true" if imported else "false"
    upsert_sql = """
    INSERT INTO system_metadata (key, value) VALUES ('assessment_batch_imported', ?)
    ON CONFLICT(key) DO UPDATE SET value = excluded.value, created_at = CURRENT_TIMESTAMP;
    """
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(upsert_sql, (val,))
        conn.commit()
    finally:
        conn.close()


def reset_assessment_records(db_path: str = DEFAULT_DB_PATH) -> int:
    """
    Removes ONLY records tagged as assessment records, preserving any manual additions.
    Resets the import flag so the assessment batch can be re-imported cleanly.
    Returns the number of deleted assessment records.
    """
    delete_sql = "DELETE FROM patients WHERE is_assessment_record = 1;"
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(delete_sql)
        deleted_count = cursor.rowcount
        cursor.execute("UPDATE system_metadata SET value = 'false' WHERE key = 'assessment_batch_imported';")
        conn.commit()
        return deleted_count
    finally:
        conn.close()


def reset_entire_database(db_path: str = DEFAULT_DB_PATH) -> None:
    """
    Completely purges all patient rows and metadata for a fresh demo run.
    Resets SQLite auto-increment counter to 1.
    """
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM patients;")
        cursor.execute("DELETE FROM system_metadata;")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='patients';")
        conn.commit()
    finally:
        conn.close()
