from flask import Flask, request, jsonify, send_from_directory, session, send_file
import pandas as pd
import numpy as np
import sqlite3
import json
import io
import hashlib
from datetime import datetime
from functools import wraps
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__, static_folder="../frontend", static_url_path="/frontend")
app.secret_key = "change-this-secret-key"
DB_PATH = "app.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            report_name TEXT NOT NULL,
            filters_json TEXT,
            results_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Please log in first."}), 401
        return fn(*args, **kwargs)
    return wrapper


def safe_float(value):
    if pd.isna(value):
        return 0.0
    return float(value)


def safe_int(value):
    if pd.isna(value):
        return 0
    return int(value)


def load_dataset(file):
    if file.filename.endswith(".csv"):
        return pd.read_csv(file)
    if file.filename.endswith(".xlsx"):
        return pd.read_excel(file)
    raise ValueError("Only CSV and XLSX supported for now")


def apply_filters(df, gender=None, age=None, campaign_id=None):
    filtered = df.copy()
    if gender and gender != "All" and "gender" in filtered.columns:
        filtered = filtered[filtered["gender"].astype(str) == str(gender)]
    if age and age != "All" and "age" in filtered.columns:
        filtered = filtered[filtered["age"].astype(str) == str(age)]
    if campaign_id and campaign_id != "All" and "campaign_id" in filtered.columns:
        filtered = filtered[filtered["campaign_id"].astype(str) == str(campaign_id)]
    return filtered


def build_analysis(df):
    df = df.replace([np.inf, -np.inf], np.nan)

    if "reporting_start" in df.columns:
        df["reporting_start"] = pd.to_datetime(df["reporting_start"], errors="coerce")

    rows = int(df.shape[0])
    columns = int(df.shape[1])

    total_impressions = safe_float(df["impressions"].sum()) if "impressions" in df.columns else 0
    total_clicks = safe_float(df["clicks"].sum()) if "clicks" in df.columns else 0
    total_spent = safe_float(df["spent"].sum()) if "spent" in df.columns else 0
    total_approved = safe_float(df["approved_conversion"].sum()) if "approved_conversion" in df.columns else 0
    avg_ctr = safe_float(df["Click_Through_Rate"].mean()) if "Click_Through_Rate" in df.columns else 0
    avg_conversion = safe_float(df["Conversion_Rate"].mean()) if "Conversion_Rate" in df.columns else 0
    avg_roi = safe_float(df["Return_On_Investment"].mean()) if "Return_On_Investment" in df.columns else 0

    preview = df.head(10).fillna("").astype(str).to_dict(orient="records")
    missing_values = {col: int(val) for col, val in df.isnull().sum().to_dict().items()}

    spend_by_gender = []
    if "gender" in df.columns and "spent" in df.columns:
        spend_by_gender = df.groupby("gender", dropna=False)["spent"].sum().reset_index().fillna("").to_dict(orient="records")

    clicks_by_age = []
    if "age" in df.columns and "clicks" in df.columns:
        clicks_by_age = df.groupby("age", dropna=False)["clicks"].sum().reset_index().fillna("").to_dict(orient="records")

    trend_data = []
    if "reporting_start" in df.columns:
        trend_source = df.dropna(subset=["reporting_start"]).copy()
        if not trend_source.empty:
            trend_source["date"] = trend_source["reporting_start"].dt.date.astype(str)
            agg = {"impressions": "sum", "clicks": "sum", "spent": "sum"}
            valid_agg = {k: v for k, v in agg.items() if k in trend_source.columns}
            trend_data = trend_source.groupby("date").agg(valid_agg).reset_index().to_dict(orient="records")

    top_ads_by_clicks = []
    if "ad_id" in df.columns and "clicks" in df.columns:
        cols = [c for c in ["ad_id", "clicks", "spent", "approved_conversion"] if c in df.columns]
        top_ads_by_clicks = df[cols].sort_values(by="clicks", ascending=False).head(10).fillna("").to_dict(orient="records")

    top_ads_by_roi = []
    if "ad_id" in df.columns and "Return_On_Investment" in df.columns:
        cols = [c for c in ["ad_id", "Return_On_Investment", "spent", "approved_conversion"] if c in df.columns]
        top_ads_by_roi = df[cols].sort_values(by="Return_On_Investment", ascending=False).head(10).fillna("").to_dict(orient="records")

    top_campaigns = []
    if "campaign_id" in df.columns:
        agg = {}
        for col in ["impressions", "clicks", "spent", "approved_conversion"]:
            if col in df.columns:
                agg[col] = "sum"
        if agg:
            top_campaigns = df.groupby("campaign_id", dropna=False).agg(agg).reset_index()
            sort_col = "spent" if "spent" in top_campaigns.columns else list(agg.keys())[0]
            top_campaigns = top_campaigns.sort_values(by=sort_col, ascending=False).head(10).fillna("").to_dict(orient="records")

    best_age_group = None
    if "age" in df.columns and "Return_On_Investment" in df.columns:
        age_roi = df.groupby("age", dropna=False)["Return_On_Investment"].mean().reset_index().sort_values(by="Return_On_Investment", ascending=False)
        if not age_roi.empty:
            best_age_group = {
                "age": str(age_roi.iloc[0]["age"]),
                "average_roi": safe_float(age_roi.iloc[0]["Return_On_Investment"])
            }

    best_gender = None
    if "gender" in df.columns and "approved_conversion" in df.columns:
        gender_conv = df.groupby("gender", dropna=False)["approved_conversion"].sum().reset_index().sort_values(by="approved_conversion", ascending=False)
        if not gender_conv.empty:
            best_gender = {
                "gender": str(gender_conv.iloc[0]["gender"]),
                "approved_conversions": safe_int(gender_conv.iloc[0]["approved_conversion"])
            }

    anomaly_results = []
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) >= 2 and len(df) >= 10:
        numeric_df = df[numeric_cols].fillna(0)
        model = IsolationForest(contamination=0.05, random_state=42)
        preds = model.fit_predict(numeric_df)
        scores = model.decision_function(numeric_df)
        temp = df.copy()
        temp["anomaly_flag"] = preds
        temp["anomaly_score"] = scores
        anomaly_rows = temp[temp["anomaly_flag"] == -1].head(10)
        display_cols = [c for c in ["ad_id", "campaign_id", "spent", "clicks", "impressions", "anomaly_score"] if c in anomaly_rows.columns]
        anomaly_results = anomaly_rows[display_cols].fillna("").astype(str).to_dict(orient="records")

    predictions = []
    if "reporting_start" in df.columns and "clicks" in df.columns:
        pred_df = df.dropna(subset=["reporting_start"]).copy()
        if not pred_df.empty:
            pred_df["date"] = pd.to_datetime(pred_df["reporting_start"]).dt.date
            daily = pred_df.groupby("date")["clicks"].sum().reset_index()
            if len(daily) >= 3:
                daily["day_index"] = range(len(daily))
                model = LinearRegression()
                model.fit(daily[["day_index"]], daily["clicks"])
                future_idx = np.array([len(daily), len(daily) + 1, len(daily) + 2]).reshape(-1, 1)
                future_preds = model.predict(future_idx)
                last_date = pd.to_datetime(daily["date"].iloc[-1])
                predictions = [
                    {
                        "date": str((last_date + pd.Timedelta(days=i + 1)).date()),
                        "predicted_clicks": round(float(pred), 2)
                    }
                    for i, pred in enumerate(future_preds)
                ]

    insights = [
        f"Filtered dataset contains {rows:,} rows and {columns} columns.",
        f"Total impressions: {int(total_impressions):,}.",
        f"Total clicks: {int(total_clicks):,}.",
        f"Total spend: ${total_spent:,.2f}.",
        f"Approved conversions: {int(total_approved):,}.",
        f"Average CTR: {avg_ctr:.4f}.",
        f"Average conversion rate: {avg_conversion:.4f}.",
        f"Average ROI: {avg_roi:.4f}.",
    ]
    if best_age_group:
        insights.append(f"Best age group by ROI is {best_age_group['age']} with ROI {best_age_group['average_roi']:.4f}.")
    if best_gender:
        insights.append(f"Best gender by approved conversions is {best_gender['gender']} with {best_gender['approved_conversions']} conversions.")
    if anomaly_results:
        insights.append(f"Detected {len(anomaly_results)} high-risk anomaly rows in the sample view.")
    if predictions:
        insights.append("Generated a short-term clicks forecast for the next 3 periods.")

    return {
        "rows": rows,
        "columns": columns,
        "preview": preview,
        "missing_values": missing_values,
        "kpis": {
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "total_spent": total_spent,
            "total_approved_conversions": total_approved,
            "average_ctr": avg_ctr,
            "average_conversion_rate": avg_conversion,
            "average_roi": avg_roi,
        },
        "insights": insights,
        "best_age_group": best_age_group,
        "best_gender": best_gender,
        "charts": {
            "spend_by_gender": spend_by_gender,
            "clicks_by_age": clicks_by_age,
            "trend_data": trend_data,
        },
        "top_campaigns": top_campaigns,
        "top_ads_by_clicks": top_ads_by_clicks,
        "top_ads_by_roi": top_ads_by_roi,
        "anomalies": anomaly_results,
        "predictions": predictions,
    }


@app.route("/")
def index():
    return send_from_directory("../frontend", "index.html")


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400

    conn = get_db()
    try:
        conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hash_password(password)))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Username already exists."}), 400

    user = conn.execute("SELECT id, username FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    return jsonify({"message": "Registered successfully.", "username": user["username"]})


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ? AND password_hash = ?",
        (username, hash_password(password))
    ).fetchone()
    conn.close()

    if not user:
        return jsonify({"error": "Invalid login details."}), 401

    session["user_id"] = user["id"]
    session["username"] = user["username"]
    return jsonify({"message": "Logged in successfully.", "username": user["username"]})


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out."})


@app.route("/me")
def me():
    return jsonify({
        "logged_in": "user_id" in session,
        "username": session.get("username")
    })


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    try:
        df = load_dataset(file)
        df = df.replace([np.inf, -np.inf], np.nan)
        if "reporting_start" in df.columns:
            df["reporting_start"] = pd.to_datetime(df["reporting_start"], errors="coerce")

        result = {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "column_names": df.columns.tolist(),
            "missing_values": {col: int(val) for col, val in df.isnull().sum().to_dict().items()},
            "preview": df.head(10).fillna("").astype(str).to_dict(orient="records"),
            "filters": {
                "gender": sorted(df["gender"].dropna().astype(str).unique().tolist()) if "gender" in df.columns else [],
                "age": sorted(df["age"].dropna().astype(str).unique().tolist()) if "age" in df.columns else [],
                "campaign_id": sorted(df["campaign_id"].dropna().astype(str).unique().tolist()) if "campaign_id" in df.columns else []
            }
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/analyze", methods=["POST"])
@login_required
def analyze():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    gender = request.form.get("gender", "All")
    age = request.form.get("age", "All")
    campaign_id = request.form.get("campaign_id", "All")

    try:
        df = load_dataset(file)
        filtered = apply_filters(df, gender, age, campaign_id)

        if filtered.empty:
            return jsonify({"error": "No data matched the selected filters."}), 400

        results = build_analysis(filtered)

        conn = get_db()
        conn.execute(
            "INSERT INTO reports (user_id, report_name, filters_json, results_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (
                session["user_id"],
                f"Analysis {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                json.dumps({"gender": gender, "age": age, "campaign_id": campaign_id}),
                json.dumps(results),
                datetime.now().isoformat()
            )
        )
        conn.commit()
        report_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()

        results["report_id"] = report_id
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/reports", methods=["GET"])
@login_required
def reports():
    conn = get_db()
    rows = conn.execute(
        "SELECT id, report_name, filters_json, created_at FROM reports WHERE user_id = ? ORDER BY id DESC",
        (session["user_id"],)
    ).fetchall()
    conn.close()

    data = []
    for row in rows:
        data.append({
            "id": row["id"],
            "report_name": row["report_name"],
            "filters": json.loads(row["filters_json"]) if row["filters_json"] else {},
            "created_at": row["created_at"]
        })
    return jsonify(data)


@app.route("/reports/<int:report_id>", methods=["GET"])
@login_required
def report_detail(report_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM reports WHERE id = ? AND user_id = ?",
        (report_id, session["user_id"])
    ).fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Report not found."}), 404

    return jsonify({
        "id": row["id"],
        "report_name": row["report_name"],
        "filters": json.loads(row["filters_json"]) if row["filters_json"] else {},
        "results": json.loads(row["results_json"]),
        "created_at": row["created_at"]
    })


@app.route("/reports/<int:report_id>/pdf", methods=["GET"])
@login_required
def export_pdf(report_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM reports WHERE id = ? AND user_id = ?",
        (report_id, session["user_id"])
    ).fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Report not found."}), 404

    results = json.loads(row["results_json"])
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    y = 760
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, y, row["report_name"])
    y -= 30
    pdf.setFont("Helvetica", 10)

    lines = [
        f"Rows: {results['rows']}",
        f"Columns: {results['columns']}",
        f"Impressions: {results['kpis']['total_impressions']}",
        f"Clicks: {results['kpis']['total_clicks']}",
        f"Spend: ${results['kpis']['total_spent']:.2f}",
        f"Approved Conversions: {results['kpis']['total_approved_conversions']}",
        f"Avg CTR: {results['kpis']['average_ctr']:.4f}",
        f"Avg Conversion Rate: {results['kpis']['average_conversion_rate']:.4f}",
        f"Avg ROI: {results['kpis']['average_roi']:.4f}",
        ""
    ] + results["insights"]

    for line in lines:
        if y < 50:
            pdf.showPage()
            y = 760
            pdf.setFont("Helvetica", 10)
        pdf.drawString(50, y, str(line)[:110])
        y -= 18

    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"report_{report_id}.pdf", mimetype="application/pdf")


@app.route("/reports/<int:report_id>/xlsx", methods=["GET"])
@login_required
def export_xlsx(report_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM reports WHERE id = ? AND user_id = ?",
        (report_id, session["user_id"])
    ).fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Report not found."}), 404

    results = json.loads(row["results_json"])
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame([results["kpis"]]).to_excel(writer, index=False, sheet_name="KPIs")
        pd.DataFrame(results["preview"]).to_excel(writer, index=False, sheet_name="Preview")
        pd.DataFrame(results["top_campaigns"]).to_excel(writer, index=False, sheet_name="Top Campaigns")
        pd.DataFrame(results["top_ads_by_clicks"]).to_excel(writer, index=False, sheet_name="Top Ads Clicks")
        pd.DataFrame(results["top_ads_by_roi"]).to_excel(writer, index=False, sheet_name="Top Ads ROI")
        pd.DataFrame(results["anomalies"]).to_excel(writer, index=False, sheet_name="Anomalies")
        pd.DataFrame(results["predictions"]).to_excel(writer, index=False, sheet_name="Predictions")
        pd.DataFrame({"insights": results["insights"]}).to_excel(writer, index=False, sheet_name="Insights")

    output.seek(0)
    return send_file(output, as_attachment=True, download_name=f"report_{report_id}.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
