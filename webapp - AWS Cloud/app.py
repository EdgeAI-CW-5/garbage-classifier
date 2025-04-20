########################################################################
# AWS #
########################################################################

from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv  # ✅ Add this line
import mysql.connector
from datetime import datetime
import boto3
from botocore.exceptions import NoCredentialsError

load_dotenv()  # ✅ Load .env variables

app = Flask(__name__)

# Load secrets from environment
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
S3_BUCKET = os.getenv('S3_BUCKET')

# S3 client
s3 = boto3.client('s3',
                  aws_access_key_id=AWS_ACCESS_KEY,
                  aws_secret_access_key=AWS_SECRET_KEY)

# Connect to RDS
db = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)
cursor = db.cursor()


# Home page - Dashboard
@app.route('/')
def dashboard():
    bins = ['Plastic', 'Metal', 'Cardboard']
    bin_status = []

    for b in bins:
        cursor.execute("""
            SELECT distance_cm, bin_status 
            FROM smartbin_data 
            WHERE label=%s 
            ORDER BY timestamp DESC LIMIT 1
        """, (b,))
        record = cursor.fetchone()

        if record:
            distance, status = record
            if b == "Plastic":
                if distance is not None:
                    fill = max(0, min(100, int((30 - distance) / 30 * 100)))
                else:
                    fill = "N/A"
            else:
                fill = "N/A"
        else:
            fill = "N/A"
            status = "N/A"

        bin_status.append({"fill": fill, "status": status})

    return render_template("dashboard.html", bin_status=bin_status)


# === Model Predictions Table ===
@app.route('/predictions')
def predictions():
    cursor.execute("SELECT label, confidence, image_path, timestamp FROM smartbin_data ORDER BY timestamp DESC")
    records = cursor.fetchall()
    return render_template("predictions.html", records=records)


# === Bin Insight Page ===
@app.route('/insight/<int:bin_id>')
def insight(bin_id):
    bins = ['Plastic', 'Metal', 'Cardboard']
    label = bins[bin_id - 1]

    cursor.execute("SELECT timestamp, distance_cm, confidence FROM smartbin_data WHERE label=%s ORDER BY timestamp", (label,))
    data = cursor.fetchall()

    timestamps = [row[0].strftime("%Y-%m-%d %H:%M") for row in data]
    distances = [float(row[1]) if row[1] is not None else None for row in data]
    confidences = [float(row[2]) for row in data]

    return render_template("insight.html", bin_label=label, bin_id=bin_id,
                           timestamps=timestamps, distances=distances, confidences=confidences)


@app.route('/upload-data', methods=['POST'])
def upload_data():
    label = request.form.get('label')
    confidence = request.form.get('confidence')
    distance = request.form.get('distance')
    bin_status = request.form.get('bin_status')
    image = request.files.get('image')

    # ✅ Convert values
    confidence = float(confidence) if confidence else None
    distance = float(distance) if distance not in (None, '', 'null') else None


    if image:
        filename = secure_filename(image.filename)
        try:
            s3.upload_fileobj(image, S3_BUCKET, filename,
                            ExtraArgs={'ACL': 'public-read', 'ContentType': image.content_type})

            s3_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{filename}"
            timestamp = datetime.now()

            query = """
                INSERT INTO smartbin_data (label, confidence, distance_cm, bin_status, image_path, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            values = (label, confidence, distance, bin_status, s3_url, timestamp)
            cursor.execute(query, values)
            db.commit()

            return jsonify({"status": "success", "message": "Data saved to S3"}), 200
        except NoCredentialsError:
            return jsonify({"status": "error", "message": "S3 credentials not valid"}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
