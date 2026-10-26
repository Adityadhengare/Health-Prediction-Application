"""
Assessment Test Records Module
------------------------------
This module contains the exact 10 patient test records provided in the official
Task 2 Assessment PDF ("AI Growth & Automation Associate - WFH").

CRITICAL DESIGN NOTE:
- These records are preserved VERBATIM.
- Do NOT correct, normalize, or discard invalid values here.
- Validation, error detection, and persistent insertion happen downstream in
  the application's validation and service layers.
- Test #6 is intentionally an exact duplicate of Test #1 as specified in the PDF.
- Invalid entries (e.g. impossible calendar date 31.11.2001, missing email domain
  hunter@gmail, future date 19.10.2030, and missing '@' Kris.wu.gmail.com) are
  intentionally kept to evaluate the application's input validation routines.
"""

ASSESSMENT_TEST_RECORDS = [
    {
        "test_id": 1,
        "full_name": "Robyn Pears",
        "date_of_birth": "28.01.1960",
        "email": "robyn@gmail.com",
        "glucose": 232,
        "haemoglobin": 13.5,
        "cholesterol": 180,
    },
    {
        "test_id": 2,
        "full_name": "John Hunter",
        "date_of_birth": "10.12.1990",
        "email": "hunter@gmail",
        "glucose": 94,
        "haemoglobin": 15,
        "cholesterol": 200,
    },
    {
        "test_id": 3,
        "full_name": "Darryl Tim",
        "date_of_birth": "12.11.1993",
        "email": "timd@smh.com.au",
        "glucose": 240,
        "haemoglobin": 18.6,
        "cholesterol": 326,
    },
    {
        "test_id": 4,
        "full_name": "Peter Larry",
        "date_of_birth": "31.11.2001",
        "email": "Larry@hotmail.com",
        "glucose": 88,
        "haemoglobin": 11.5,
        "cholesterol": 165,
    },
    {
        "test_id": 5,
        "full_name": "Sam Kerr",
        "date_of_birth": "09.12.2006",
        "email": "sam@news.com.au",
        "glucose": 198,
        "haemoglobin": 8.9,
        "cholesterol": 192,
    },
    {
        "test_id": 6,
        "full_name": "Robyn Pears",
        "date_of_birth": "28.01.1960",
        "email": "robyn@gmail.com",
        "glucose": 232,
        "haemoglobin": 13.5,
        "cholesterol": 180,
    },
    {
        "test_id": 7,
        "full_name": "Madison XI",
        "date_of_birth": "12.09.1998",
        "email": "madison@hotmail.com",
        "glucose": 85,
        "haemoglobin": 7.6,
        "cholesterol": 163,
    },
    {
        "test_id": 8,
        "full_name": "Kris Wu",
        "date_of_birth": "19.10.2030",
        "email": "Kris.wu.gmail.com",
        "glucose": 79,
        "haemoglobin": 16.5,
        "cholesterol": 197,
    },
    {
        "test_id": 9,
        "full_name": "Tenille Singh",
        "date_of_birth": "30.11.1991",
        "email": "Tenille@yahoo.com",
        "glucose": 101,
        "haemoglobin": 15,
        "cholesterol": 310,
    },
    {
        "test_id": 10,
        "full_name": "Prem Kumar",
        "date_of_birth": "28.04.1990",
        "email": "prem@telstra.com",
        "glucose": 155,
        "haemoglobin": 12.5,
        "cholesterol": 265,
    },
]


def get_assessment_records():
    """
    Returns a fresh deep copy of the 10 raw assessment records.
    This prevents downstream functions from inadvertently mutating the source data.
    """
    return [record.copy() for record in ASSESSMENT_TEST_RECORDS]
