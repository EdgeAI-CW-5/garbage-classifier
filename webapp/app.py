from flask import Flask, render_template, Response
import random
import os

app = Flask(__name__)

# Path to your sample video
video_path = "static/sample.mp4"

# Generator function to stream video frames
def generate_frames():
    # Instead of using external libraries, just serve the video directly.
    # Open the file and stream the content.
    with open(video_path, "rb") as f:
        while True:
            video_chunk = f.read(1024 * 1024)  # Read 1MB at a time
            if not video_chunk:
                break
            yield video_chunk

# Generate bin levels once at app start
@app.route('/')
def home():
    # Replace this with actual logic from your ML model and sensors
    detected_class = "Plastic"
    bin_open_status = {
        "Cardboard": False,
        "Metal": False,
        "Plastic": True
    }

    return render_template("home.html",
                           detected_class=detected_class,
                           bin_open_status=bin_open_status)


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='video/mp4')  # Directly serve video as 'video/mp4'

@app.route("/dashboard")
def dashboard():
    bin_names = ['Cardboard', 'Metal', 'Plastic']
    bins = []

    for name in bin_names:
        fill_level = random.randint(0, 100)
        bins.append({
            'name': name,
            'fill': fill_level
        })

    return render_template('dashboard.html', bins=bins)


@app.route('/insight/<int:bin_id>')
def insight(bin_id):
    # Logic for handling insights for the specific bin
    return render_template("insight.html", bin_id=bin_id)


if __name__ == '__main__':
    app.run(debug=True)
