## AI Ready Check (Streamlit)

This repository contains a Streamlit wizard that walks business users through ten slider questions to estimate their AI readiness, adoption level, and the expected working-hours reduction.

### Features
- One-question-per-page wizard with progress indicator and back/next controls
- Industry selection upfront (single-choice dropdown with optional free text)
- Live calculation of AI Ready score, adoption (Q4), reduction percentage, and a next-step suggestion
- Review step before submission, with the option to edit answers
- Google Sheets logging with retry logic and timestamping (default Asia/Tokyo)

### Prerequisites
- Python 3.10+
- Streamlit Cloud (or local Streamlit) runtime
- Google Cloud service account with Sheets API access

Install dependencies:
```bash
pip install -r requirements.txt
```

### Streamlit Secrets
Configure the following secrets (e.g. in Streamlit Cloud):
- `GOOGLE_SHEETS_CREDS`: JSON string for the service account credentials
- `SHEET_NAME`: Target spreadsheet name (default `AI_Ready_Responses`)
- `WORKSHEET_NAME`: Worksheet tab (default `responses`)
- `TZ`: IANA timezone name (default `Asia/Tokyo`)

### Running locally
```bash
streamlit run app.py
```

Without the Google Sheets secrets the app still works in preview mode, but the submission button is disabled.

### Google Sheets columns
Expect a header order like:
`timestamp,q1..q10,ready_score,adoption_q4,reduction_pct,industry,client_id,user_agent,referrer,notes`
