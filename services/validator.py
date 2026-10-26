"""
Data Validation Engine for Health Prediction Application
--------------------------------------------------------
This module provides beginner-friendly, pure Python validation functions for patient records.

Responsibilities:
1. Email Validation:
   - Must contain '@' and a valid domain name with a conventional top-level domain (TLD).
   - Rejects 'hunter@gmail' (no TLD) and 'Kris.wu.gmail.com' (missing '@').
   - Accepts complex valid emails such as 'timd@smh.com.au'.

2. Date of Birth Validation:
   - Rejects impossible calendar dates (e.g. 31.11.2001, since November only has 30 days).
   - Rejects future dates (e.g. 19.10.2030) relative to today's date.
   - Accepts both 'DD/MM/YYYY' (UI standard) and 'DD.MM.YYYY' (raw assessment test data format).
   - Rejects incorrect delimiters or malformed formats.

3. Blood-Test Value Validation:
   - Ensures Glucose, Haemoglobin, and Cholesterol are valid numbers.
   - Rejects NaN, Infinity, non-numeric strings, and missing values.
   - Does NOT invent arbitrary clinical range limits or reject unusual clinical readings.

4. Full-Name Validation:
   - Rejects empty strings or whitespace-only inputs.
   - Accepts valid characters and multi-word names (e.g. 'Madison XI').

All functions return a tuple: (is_valid: bool, error_message: str or list[str]).
This module is strictly decoupled from UI, database operations, and external APIs.
"""

import math
import re
from datetime import date, datetime
from typing import Any, Dict, List, Tuple


# Regex for email validation:
# - Local part: alphanumeric characters plus . _ % + -
# - Separator: exactly one '@'
# - Domain name: alphanumeric characters plus hyphens, followed by '.'
# - Domain suffix (TLD): at least 2 alphabetic characters (e.g. .com, .org, .com.au)
EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9_.%+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,}$"
)


def validate_full_name(name: Any) -> Tuple[bool, str]:
    """
    Validates patient full name.
    
    Accepts: Non-empty strings, names with spaces or Roman numerals (e.g. 'Madison XI').
    Rejects: None, empty string, or whitespace-only strings.
    """
    if name is None:
        return False, "Full Name is required and cannot be empty."
    
    if not isinstance(name, str):
        return False, "Full Name must be a text value."
    
    cleaned = name.strip()
    if not cleaned:
        return False, "Full Name cannot be empty or blank spaces only."
    
    if len(cleaned) < 2:
        return False, "Full Name must be at least 2 characters long."
    
    return True, ""


def validate_email(email: Any) -> Tuple[bool, str]:
    """
    Validates patient email address.
    
    Accepts: Standard email formats including multi-part domains like 'timd@smh.com.au'.
    Rejects:
      - 'hunter@gmail' -> Missing top-level domain extension (e.g. .com).
      - 'Kris.wu.gmail.com' -> Missing '@' symbol.
      - Blank, None, or malformed strings.
    """
    if email is None:
        return False, "Email address is required."
    
    if not isinstance(email, str):
        return False, "Email address must be a string."
    
    cleaned = email.strip()
    if not cleaned:
        return False, "Email address cannot be empty or blank."
    
    # Specific diagnostics to help the user/candidate explain the exact failure in the video
    if "@" not in cleaned:
        return False, f"Invalid email '{cleaned}': Missing '@' symbol."
    
    # Check if the domain part after '@' has a valid dot and extension
    domain_part = cleaned.split("@", 1)[1]
    if "." not in domain_part:
        return (
            False,
            f"Invalid email '{cleaned}': Domain '{domain_part}' lacks a valid extension (e.g. .com).",
        )
    
    # Final check against standard regex
    if not EMAIL_REGEX.match(cleaned):
        return (
            False,
            f"Invalid email format '{cleaned}': Must follow standard 'user@domain.com' format.",
        )
    
    return True, ""


def validate_dob(dob_input: Any, reference_today: date = None) -> Tuple[bool, str, str]:
    """
    Validates Date of Birth.
    
    Rules:
    1. Format: Accepts 'DD/MM/YYYY' (Streamlit UI format) and 'DD.MM.YYYY' (Assessment PDF format).
    2. Real Calendar Date: Rejects impossible dates (e.g. 31.11.2001 because November has 30 days).
    3. Not in the Future: Rejects dates greater than today (e.g. 19.10.2030).
    
    Returns:
      (is_valid: bool, error_message: str, standardized_dob_str: str)
      If valid, standardized_dob_str is formatted as 'DD/MM/YYYY'.
    """
    if dob_input is None:
        return False, "Date of Birth is required.", ""
    
    if not isinstance(dob_input, str):
        return False, "Date of Birth must be a string in DD/MM/YYYY or DD.MM.YYYY format.", ""
    
    cleaned = dob_input.strip()
    if not cleaned:
        return False, "Date of Birth cannot be empty or blank.", ""
    
    # Identify delimiter: support both assessment PDF ('.') and application UI ('/')
    delimiter = None
    if "/" in cleaned:
        delimiter = "/"
    elif "." in cleaned:
        delimiter = "."
    else:
        return (
            False,
            f"Invalid date format '{cleaned}': Please use DD/MM/YYYY or DD.MM.YYYY.",
            "",
        )
    
    parts = cleaned.split(delimiter)
    if len(parts) != 3:
        return (
            False,
            f"Invalid date format '{cleaned}': Expected day, month, and 4-digit year.",
            "",
        )
    
    day_str, month_str, year_str = parts[0].strip(), parts[1].strip(), parts[2].strip()
    
    # Check if parts are numbers and year has 4 digits
    if not (day_str.isdigit() and month_str.isdigit() and year_str.isdigit()):
        return (
            False,
            f"Invalid date '{cleaned}': Day, month, and year must be numeric numbers.",
            "",
        )
    
    if len(year_str) != 4:
        return (
            False,
            f"Invalid year '{year_str}' in date '{cleaned}': Year must be 4 digits (e.g. 1990).",
            "",
        )
    
    # Parse into actual calendar date using Python's datetime.strptime
    # strptime strictly checks calendar validity (e.g. leap years, month day counts)
    parse_format = f"%d{delimiter}%m{delimiter}%Y"
    try:
        parsed_date = datetime.strptime(cleaned, parse_format).date()
    except ValueError as e:
        # e.g., 'day is out of range for month'
        return (
            False,
            f"Impossible calendar date '{cleaned}': Date does not exist on the calendar (e.g. day out of range for month).",
            "",
        )
    
    # Check for future dates
    today = reference_today if reference_today is not None else date.today()
    if parsed_date > today:
        return (
            False,
            f"Future date rejected '{cleaned}': Date of birth cannot be in the future (today is {today.strftime('%d/%m/%Y')}).",
            "",
        )
    
    # Format to standardized user-facing DD/MM/YYYY representation
    standardized = parsed_date.strftime("%d/%m/%Y")
    return True, "", standardized


def validate_numeric_metric(metric_name: str, value: Any) -> Tuple[bool, str, float]:
    """
    Validates that a single blood test metric (Glucose, Haemoglobin, Cholesterol) is numeric.
    
    Rejects: None, non-numeric strings, NaN, Infinity, negative values.
    Accepts: ints, floats, or numeric strings (e.g. '13.5' or 180).
    
    Returns:
      (is_valid: bool, error_message: str, parsed_float_value: float)
    """
    if value is None:
        return False, f"{metric_name} is required and cannot be empty.", 0.0
    
    # If passed as string, strip whitespace
    if isinstance(value, str):
        cleaned_str = value.strip()
        if not cleaned_str:
            return False, f"{metric_name} cannot be empty or blank.", 0.0
        try:
            num_val = float(cleaned_str)
        except ValueError:
            return (
                False,
                f"{metric_name} must be a valid number. Got non-numeric text: '{value}'.",
                0.0,
            )
    elif isinstance(value, (int, float)):
        num_val = float(value)
    else:
        return (
            False,
            f"{metric_name} must be numeric. Received unsupported type: {type(value).__name__}.",
            0.0,
        )
    
    # Reject NaN and Infinity
    if math.isnan(num_val) or math.isinf(num_val):
        return (
            False,
            f"{metric_name} must be a finite number. Got invalid floating-point value: '{num_val}'.",
            0.0,
        )
    
    # Non-negative validation
    if num_val < 0:
        return (
            False,
            f"{metric_name} cannot be negative. Got: {num_val}.",
            0.0,
        )
    
    return True, "", num_val


def validate_blood_values(
    glucose: Any, haemoglobin: Any, cholesterol: Any
) -> Tuple[bool, List[str], Dict[str, float]]:
    """
    Validates all three blood test values together.
    
    Returns:
      (is_valid: bool, list_of_errors: list[str], parsed_metrics: dict)
    """
    errors: List[str] = []
    parsed: Dict[str, float] = {}
    
    g_valid, g_err, g_val = validate_numeric_metric("Glucose", glucose)
    if not g_valid:
        errors.append(g_err)
    else:
        parsed["glucose"] = g_val
        
    h_valid, h_err, h_val = validate_numeric_metric("Haemoglobin", haemoglobin)
    if not h_valid:
        errors.append(h_err)
    else:
        parsed["haemoglobin"] = h_val
        
    c_valid, c_err, c_val = validate_numeric_metric("Cholesterol", cholesterol)
    if not c_valid:
        errors.append(c_err)
    else:
        parsed["cholesterol"] = c_val
        
    return len(errors) == 0, errors, parsed


def validate_patient_record(
    record: Dict[str, Any], reference_today: date = None
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Validates a complete patient record dictionary.
    
    Takes raw inputs:
      - full_name
      - date_of_birth
      - email
      - glucose
      - haemoglobin
      - cholesterol
      
    Returns:
      (is_valid: bool, error_messages: list[str], validated_cleaned_data: dict)
      
    Note: If validation fails, error_messages contains all reasons for failure,
    allowing the UI and test runner to display the exact issues clearly.
    """
    errors: List[str] = []
    cleaned_data: Dict[str, Any] = {}
    
    # 1. Full Name
    fn_valid, fn_err = validate_full_name(record.get("full_name"))
    if not fn_valid:
        errors.append(fn_err)
    else:
        cleaned_data["full_name"] = str(record.get("full_name")).strip()
        
    # 2. Date of Birth
    dob_valid, dob_err, std_dob = validate_dob(
        record.get("date_of_birth"), reference_today=reference_today
    )
    if not dob_valid:
        errors.append(dob_err)
    else:
        cleaned_data["date_of_birth"] = std_dob
        
    # 3. Email Address
    em_valid, em_err = validate_email(record.get("email"))
    if not em_valid:
        errors.append(em_err)
    else:
        cleaned_data["email"] = str(record.get("email")).strip()
        
    # 4. Blood Metrics
    bm_valid, bm_errors, parsed_bm = validate_blood_values(
        record.get("glucose"),
        record.get("haemoglobin"),
        record.get("cholesterol"),
    )
    if not bm_valid:
        errors.extend(bm_errors)
    else:
        cleaned_data.update(parsed_bm)
        
    return len(errors) == 0, errors, cleaned_data


# ------------------------------------------------------------------------------
# Self-contained Unit Tests
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    print("Running self-contained unit tests for services/validator.py...\n")
    
    # 1. Test Email Validation
    email_cases = [
        ("robyn@gmail.com", True, "Standard valid email"),
        ("timd@smh.com.au", True, "Multi-part Australian domain"),
        ("hunter@gmail", False, "Missing top-level domain"),
        ("Kris.wu.gmail.com", False, "Missing @ symbol"),
        ("", False, "Empty email"),
    ]
    for email, expected, desc in email_cases:
        res, msg = validate_email(email)
        assert res == expected, f"Failed on {desc}: {email}. Got {res}, expected {expected}."
        print(f"  [EMAIL] '{email}' -> Valid: {res} | {msg if not res else 'OK'}")
        
    # 2. Test DOB Validation
    # Use fixed reference date 2026-10-26 to match current time
    ref_date = date(2026, 10, 26)
    dob_cases = [
        ("28.01.1960", True, "Standard valid date (dot format)"),
        ("28/01/1960", True, "Standard valid date (slash format)"),
        ("31.11.2001", False, "Impossible date (Nov has 30 days)"),
        ("19.10.2030", False, "Future date"),
        ("29.02.2024", True, "Valid leap day"),
        ("29.02.2023", False, "Invalid leap day (non-leap year)"),
    ]
    for dob, expected, desc in dob_cases:
        res, msg, std = validate_dob(dob, reference_today=ref_date)
        assert res == expected, f"Failed on {desc}: {dob}. Got {res}, expected {expected}."
        print(f"  [DOB] '{dob}' -> Valid: {res} | {msg if not res else 'Standardized: ' + std}")
        
    # 3. Test Numeric Metrics
    metric_cases = [
        (232, 13.5, 180, True, "Standard numeric metrics"),
        ("94", "15.0", "200", True, "Numeric strings"),
        ("abc", 15, 200, False, "Non-numeric glucose string"),
        (float("nan"), 15, 200, False, "NaN value"),
        (-10, 15, 200, False, "Negative value"),
    ]
    for g, h, c, expected, desc in metric_cases:
        res, errors, parsed = validate_blood_values(g, h, c)
        assert res == expected, f"Failed on {desc}. Got {res}, expected {expected}."
        print(f"  [METRICS] (G:{g}, H:{h}, C:{c}) -> Valid: {res} | Errors: {errors}")
        
    # 4. Test Against the 10 Assessment Records
    print("\nEvaluating the 10 Official Assessment Records:")
    from data.test_records import ASSESSMENT_TEST_RECORDS
    
    passed_count = 0
    rejected_count = 0
    
    for rec in ASSESSMENT_TEST_RECORDS:
        valid, errs, clean = validate_patient_record(rec, reference_today=ref_date)
        status = "PASSED" if valid else "REJECTED"
        if valid:
            passed_count += 1
            print(f"  Record #{rec['test_id']}: [{rec['full_name']}] -> {status}")
        else:
            rejected_count += 1
            print(f"  Record #{rec['test_id']}: [{rec['full_name']}] -> {status} | Errors: {errs}")
            
    print(f"\nSummary: {passed_count} Passed, {rejected_count} Rejected (Expected: 7 Passed, 3 Rejected).")
    assert passed_count == 7, f"Expected 7 valid records, got {passed_count}"
    assert rejected_count == 3, f"Expected 3 invalid records, got {rejected_count}"
    print("\nAll unit tests passed successfully!")
