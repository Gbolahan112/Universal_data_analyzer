# Start Here

This project has two app versions:

- `streamlit_version` for the quick prototype
- `flask_version` for the full analytics web app

## One-Time Setup

Open PowerShell in:

```text
C:\Users\user\OneDrive\Desktop\social_media_tracker
```

Then run:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r streamlit_version\requirements.txt
python -m pip install -r flask_version\requirements.txt
```

## Run Flask Version

Option 1:

```powershell
.\run_flask.ps1
```

Option 2:

```powershell
.venv\Scripts\Activate.ps1
python flask_version\backend\flask_app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Run Streamlit Version

Option 1:

```powershell
.\run_streamlit.ps1
```

Option 2:

```powershell
.venv\Scripts\Activate.ps1
python -m streamlit run streamlit_version\app.py
```

## If PowerShell Blocks Script Activation

Run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

Then activate the environment again:

```powershell
.venv\Scripts\Activate.ps1
```

## Quick Reminder

- Flask app URL: `http://127.0.0.1:5000`
- Streamlit command uses `python -m streamlit`
- Use the project `.venv` whenever you run the app
