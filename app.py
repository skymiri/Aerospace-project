"""
Example of integrating notification system into Flask app
This file shows how to add notification features to app.py.
When actually using, integrate this code into app.py.
"""

from flask import Flask, request, render_template, redirect, url_for, flash
import os
import time
import import_cleaned_data
import convert_anemometer
import Clean_and_Timestamp

# Import notification modules
from notifier import send_priority_notification
from monitor_system import handle_server_error

UPLOAD_DIR = "/app/uploads"
DATA_DIR = "/data"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = "supersecret"


# =====================================================
# HOME PAGE
# =====================================================
@app.route("/")
def index():
    return render_template("upload.html")


# =====================================================
# FILE UPLOAD HANDLER (Notification Integration Example)
# =====================================================
@app.route("/upload", methods=["POST"])
def upload():
    drone_file = request.files.get("drone")
    anemo_file = request.files.get("anemo")

    if not (drone_file or anemo_file):
        flash("Please upload at least one file.")
        return redirect(url_for("index"))

    start_time = time.time()
    processed_files = []

    # ----------------------------
    # DRONE FILE PROCESSING
    # ----------------------------
    if drone_file:
        drone_path = os.path.join(UPLOAD_DIR, drone_file.filename)
        drone_file.save(drone_path)
        try:
            Clean_and_Timestamp.main(drone_path)
            processing_time = time.time() - start_time
            flash(f"✅ Processed drone data: {drone_file.filename}")
            processed_files.append(f"Drone: {drone_file.filename}")

            # Send success notification
            send_priority_notification(
                message=f"Drone data file processing completed\n"
                f"Filename: {drone_file.filename}\n"
                f"Processing time: {processing_time:.2f}s",
                title="✅ File Processing Complete",
                priority="default",
                tags=["success", "file", "drone"],
            )
        except Exception as e:
            flash(f"❌ Error processing drone file: {e}")

            # Send error notification
            send_priority_notification(
                message=f"Drone file processing failed\n"
                f"Filename: {drone_file.filename}\n"
                f"Error: {str(e)}",
                title="❌ File Processing Failed",
                priority="high",
                tags=["warning", "skull", "file"],
            )
            return redirect(url_for("index"))

    # ----------------------------
    # ANEMOMETER FILE PROCESSING
    # ----------------------------
    if anemo_file:
        anemo_path = os.path.join(UPLOAD_DIR, anemo_file.filename)
        anemo_file.save(anemo_path)
        try:
            out_path = convert_anemometer.convert_file(
                anemo_path, None, "America/Vancouver"
            )
            processing_time = time.time() - start_time
            flash(f"✅ Converted anemometer log to {os.path.basename(out_path)}")
            processed_files.append(f"Anemometer: {anemo_file.filename}")

            # Send success notification
            send_priority_notification(
                message=f"Anemometer data file conversion completed\n"
                f"Filename: {anemo_file.filename}\n"
                f"Output file: {os.path.basename(out_path)}\n"
                f"Processing time: {processing_time:.2f}s",
                title="✅ File Conversion Complete",
                priority="default",
                tags=["success", "file", "anemometer"],
            )
        except Exception as e:
            flash(f"❌ Error converting anemometer log: {e}")

            # Send error notification
            send_priority_notification(
                message=f"Anemometer file conversion failed\n"
                f"Filename: {anemo_file.filename}\n"
                f"Error: {str(e)}",
                title="❌ File Conversion Failed",
                priority="high",
                tags=["warning", "skull", "file"],
            )
            return redirect(url_for("index"))

    # ----------------------------
    # DATABASE INGESTION
    # ----------------------------
    try:
        import_start = time.time()
        drone_records = import_cleaned_data.ingest_drone()
        anemo_records = import_cleaned_data.ingest_anemometer()
        import_time = time.time() - import_start

        flash("✅ Data successfully imported into PostgreSQL.")

        # Send database import success notification
        send_priority_notification(
            message=f"Database import completed\n"
            f"Processed files: {', '.join(processed_files)}\n"
            f"Drone records: {drone_records if drone_records else 'N/A'} records\n"
            f"Anemometer records: {anemo_records if anemo_records else 'N/A'} records\n"
            f"Import time: {import_time:.2f}s",
            title="✅ Database Import Complete",
            priority="default",
            tags=["success", "database"],
        )
    except Exception as e:
        flash(f"⚠️ Data import warning: {e}")

        # Send database import warning notification
        send_priority_notification(
            message=f"Database import warning\n"
            f"Error: {str(e)}\n"
            f"Processed files: {', '.join(processed_files) if processed_files else 'None'}",
            title="⚠️ Database Import Warning",
            priority="high",
            tags=["warning", "database"],
        )

    return redirect(url_for("index"))


# =====================================================
# ANALYTICS PAGE (Notification Integration Example)
# =====================================================
@app.route("/analytics")
def analytics():
    try:
        import compare

        start_time = time.time()
        used_file = compare.generate_plots()
        processing_time = time.time() - start_time

        flash(f"📊 Analytics generated successfully from {os.path.basename(used_file)}")

        # Send analysis completion notification
        send_priority_notification(
            message=f"Data analysis completed\n"
            f"File used: {os.path.basename(used_file)}\n"
            f"Processing time: {processing_time:.2f}s",
            title="📊 Analysis Complete",
            priority="default",
            tags=["success", "chart"],
        )

        return render_template("analytics.html")
    except Exception as e:
        flash(f"Error generating analytics: {e}")

        # Send analysis failure notification
        handle_server_error(e, context="Data Analysis")

        return redirect(url_for("index"))


# =====================================================
# ERROR HANDLERS (Notification Integration Example)
# =====================================================
@app.errorhandler(500)
def internal_error(error):
    """Sends notification when 500 error occurs"""
    handle_server_error(error, context="Internal Server Error")
    flash("A server error occurred. Please contact the administrator.")
    return redirect(url_for("index"))


@app.errorhandler(404)
def not_found(error):
    """404 errors are handled without notification (common error)"""
    flash("Page not found.")
    return redirect(url_for("index"))


# =====================================================
# APP ENTRYPOINT
# =====================================================
if __name__ == "__main__":
    # Send app startup notification
    send_priority_notification(
        message="BCIT Aerospace web application has started.",
        title="🚀 Application Started",
        priority="default",
        tags=["info", "rocket"],
    )

    app.run(host="0.0.0.0", port=8080, debug=True)
