# Health Prediction Application

AI Growth & Automation Associate - Task 2 Assessment Solution

## Overview
This is a beginner-friendly Python web application built using **Streamlit** for the frontend, **SQLite** for persistent local storage, and **Google Gemini API** (with a graceful, explicitly labeled local rule-based fallback engine) for generating health-risk remarks based on blood test results.

---

## Required Contact & Clinical Fields
1. **Full Name**
2. **Date of Birth** (Format: `DD/MM/YYYY`)
3. **Email Address**
4. **Glucose** (mg/dL)
5. **Haemoglobin** (g/dL)
6. **Cholesterol** (mg/dL)
7. **Remarks** (Generated from AI or explicit fallback)

---

## Features & Assessment Coverage

### 1. Assessment Test Data Runner
- Preserves all 10 official assessment records verbatim in `data/test_records.py`.
- Evaluates each record:
  - **7 Valid Records**: Processed and importable into SQLite (Record #6 duplicate is intentionally preserved as a distinct database row).
  - **3 Invalid Records**: Strictly blocked from entering the database with clear error explanations:
    - **Record #2 (John Hunter)**: Invalid email (`hunter@gmail` missing domain extension).
    - **Record #4 (Peter Larry)**: Impossible calendar date (`31.11.2001` - November has only 30 days).
    - **Record #8 (Kris Wu)**: Future date of birth (`19.10.2030`) and missing `@` symbol (`Kris.wu.gmail.com`).

### 2. Full CRUD Operations
- **Create**: Add new patient records with live input validation.
- **Read**: View all stored records in an interactive table with `DD/MM/YYYY` date formatting.
- **Update**: Select any record and modify its details. Includes a dedicated one-click action to change email to `gokul@infocare.com` as requested in the assessment.
- **Delete**: Select and delete any record with immediate UI table refresh.

### 3. AI & Safe Fallback Integration
- Generates cautious, informational health-risk observations.
- Explicitly labels remarks:
  - `[Source: External AI API (Google Gemini)]` when external API key is present.
  - `[Source: Local Rule-Based Engine (API unavailable/offline)]` when offline, missing key, or rate-limited. Local fallback is **never** falsely attributed to AI.
- Appends a prominent medical disclaimer to all remarks.

---

## Project Structure
```text
HealthPredictionApp/
├── .env.example              # Environment variables template
├── .gitignore                # Protects .env, health_app.db, and pycache from Git
├── requirements.txt          # Python dependencies (streamlit, google-genai, python-dotenv)
├── test_app.py               # Automated integration test suite
├── README.md                 # Complete documentation and setup guide
│
├── database/
│   ├── __init__.py
│   └── db_manager.py         # SQLite connection and CRUD functions
│
├── services/
│   ├── __init__.py
│   ├── validator.py          # Pure validation functions (RFC email, calendar date, numbers)
│   └── ai_service.py         # Gemini API client with explicit fallback engine
│
├── data/
│   ├── __init__.py
│   └── test_records.py       # Exact 10 assessment test records preserved verbatim
│
└── app.py                    # Streamlit web UI (CRUD, assessment runner, alerts)
```

---

## Setup & Running the Application

### 1. Clone the repository and enter the directory
```bash
cd HealthPredictionApp
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. (Optional) Configure Gemini API Key
To use Google Gemini API for remarks:
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   # Or on Windows PowerShell:
   Copy-Item .env.example .env
   ```
2. Open `.env` and add your free Google AI Studio key:
   ```env
   GEMINI_API_KEY=your_actual_key_here
   ```
*(Note: If you leave it empty, the application automatically runs in offline mode using the local clinical fallback engine with zero crashes).*

### 4. Run the Integration Tests
```bash
python test_app.py
```

### 5. Launch the Streamlit Web Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## Video Walkthrough Guide (For Assessment Submission)
When recording the requested demonstration video:
1. **Show Assessment Data Tab**: Point out the 10 records and explain why Records #2, #4, and #8 are rejected.
2. **Show Database Population**: Click the import button to load valid records.
3. **Show Read**: Navigate to *All Saved Patient Records* and show the table with `DD/MM/YYYY` formatting.
4. **Show Update**: Go to *Edit Patient Record*, choose a record, click the button to set email to `gokul@infocare.com`, and verify the update.
5. **Show Delete**: Go to *Delete Patient Record*, delete one entry, and show the updated list.
6. **Code Walkthrough**: Briefly walk through `services/validator.py`, `services/ai_service.py`, and `database/db_manager.py`.

---

## Candidate Submission Details (Task 2 Assessment Table)

Below is the candidate information table requested on Page 1 of the official assessment PDF for email submission to `jobs@gokulinfocare.com`:

| Field | Candidate Submission Value |
| :--- | :--- |
| **Candidate Number** | 115 |
| **Name** | Aditya Dhengare |
| **Mobile Number** | 9022738515 |
| **Email ID** | dhengareaditya5@gmail.com |
| **Education Qualifications** | B.Tech completed (CGPA: 7.79) |
| **Any Previous Experience?** | Yes - Data Scientist Intern in Delfine India Technology |
| **Notice Period Required** | Immediate |
| **Do you have an i5 or equivalent laptop/PC and internet speed of at least 40 Mbps?** | Yes |
| **What time you can start work (8 Hours work and 1-2 hours break)** | 6:00 AM (Monday–Saturday, 8 hours/day) |
| **GitHub Repository Link** | https://github.com/Adityadhengare/Health-Prediction-Application |
| **App Video Link** | https://drive.google.com/file/d/1_vkgQsJ5JWANzEFbQc-ZJjEbvK6eyPcR/view?usp=drive_link |

