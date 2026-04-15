# Universal Data Analyzer

This repository contains two separate versions of the project:

- `streamlit_version/` for the quick prototype dashboard
- `flask_version/` for the full frontend/backend analytics app

## Project Structure

```text
social_media_tracker/
|-- streamlit_version/
|   |-- streamlit_app.py
|   |-- campaign_data.xlsx
|   `-- requirements.txt
|-- flask_version/
|   |-- backend/
|   |   |-- flask_app.py
|   |   |-- analysis.py
|   |   `-- app.db
|   |-- frontend/
|   |   |-- app.js
|   |   |-- index.html
|   |   |-- package.json
|   |   `-- package-lock.json
|   `-- requirements.txt
|-- .gitignore
`-- README.md
```

## Streamlit Version

Use this version for quick demos and simple exploratory analysis.

### Features

- Upload CSV or Excel files
- Map columns dynamically
- Calculate CTR, CPC, and ROI
- Show KPIs, charts, and recommendations
- Filter by categorical values in the dataset

### Run It

```powershell
cd C:\Users\user\OneDrive\Desktop\social_media_tracker
.venv\Scripts\Activate.ps1
pip install -r streamlit_version\requirements.txt
streamlit run streamlit_version\streamlit_app.py
```

## Flask Version

Use this version for the fuller portfolio app with login, saved reports, exports, anomaly detection, and forecasting.

### Features

- Register and login users
- Upload CSV or Excel files
- Run advanced campaign analysis
- Save reports in SQLite
- Export PDF and Excel reports
- Detect anomalies and generate simple forecasts

### Run It

```powershell
cd C:\Users\user\OneDrive\Desktop\social_media_tracker
.venv\Scripts\Activate.ps1
pip install -r flask_version\requirements.txt
cd flask_version\backend
python flask_app.py
```

Then open:

```text
http://127.0.0.1:5000
```

## Which One To Use

- Choose `streamlit_version` if you want the faster and simpler demo.
- Choose `flask_version` if you want the more polished full-stack application.

## Live Demo

[Streamlit demo](https://universaldataanalyzer-gwfzsegpdzkqwav8bmo7zh.streamlit.app/)
