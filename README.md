# Universal Data Analyzer

Universal Data Analyzer is a portfolio project that explores two different ways to build analytics tools:

- a rapid prototype version with Streamlit
- a more advanced full-stack version with Flask, JavaScript, authentication, saved reports, exports, anomaly detection, and forecasting

This repository is organized so each version is easy to run, demo, and explain.

## Highlights

- Upload CSV and Excel datasets
- Generate KPIs and business insights
- Visualize data with interactive charts
- Filter campaign data by user-selected fields
- Save reports and export analysis in the Flask version
- Demonstrate both fast prototyping and fuller product development workflows

## Project Structure

```text
social_media_tracker/
|-- streamlit_version/
|   |-- app.py
|   |-- campaign_data.xlsx
|   |-- requirements.txt
|   `-- README.md
|-- flask_version/
|   |-- backend/
|   |   |-- flask_app.py
|   |   `-- app.db
|   |-- frontend/
|   |   |-- app.js
|   |   |-- index.html
|   |   |-- package.json
|   |   `-- package-lock.json
|   |-- requirements.txt
|   `-- README.md
|-- .gitignore
`-- README.md
```

## Run The Streamlit Version

```powershell
cd C:\Users\user\OneDrive\Desktop\social_media_tracker
.venv\Scripts\Activate.ps1
pip install -r streamlit_version\requirements.txt
streamlit run streamlit_version\app.py
```

## Run The Flask Version

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

## Which Version To Use

- Choose `streamlit_version` for quick demos and lightweight analysis.
- Choose `flask_version` for the richer full-stack portfolio app.

## Live Demo

[Streamlit demo](https://universaldataanalyzer-gwfzsegpdzkqwav8bmo7zh.streamlit.app/)
