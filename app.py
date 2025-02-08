import os
import pdfplumber
import pandas as pd
from flask import Flask, request, render_template, jsonify, send_from_directory

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf"}

def allowed_file(filename):
    """Check if the uploaded file has a PDF extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file part"})

    files = request.files.getlist("file")  # Get multiple files
    if not files or files[0].filename == "":
        return jsonify({"success": False, "error": "No selected file"})

    download_links = []

    for file in files:
        if not allowed_file(file.filename):
            return jsonify({"success": False, "error": f"Invalid file type: {file.filename}. Only PDFs allowed."})

        # Save the uploaded PDF
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        # Extract tables
        tables = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                extracted_table = page.extract_table()
                if extracted_table:
                    tables.append(extracted_table)

        if not tables:
            return jsonify({"success": False, "error": f"No tables found in {file.filename}."})

        # Convert to DataFrame and save as CSV
        df = pd.DataFrame(sum(tables, []))  # Flatten list of tables
        output_filename = file.filename.replace(".pdf", ".csv")
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        df.to_csv(output_path, index=False)

        download_links.append(f"/download/{output_filename}")

    return jsonify({"success": True, "download_urls": download_links})

@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)