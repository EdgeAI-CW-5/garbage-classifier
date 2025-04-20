from flask import Flask, render_template, Response
import random
import os
from flask import Flask, jsonify


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
@app.route('/api/bin_levels')
def get_bin_levels():
    bins = [
        {"id": 1, "fill": random.randint(0, 100)},
        {"id": 2, "fill": random.randint(0, 100)},
        {"id": 3, "fill": random.randint(0, 100)}
    ]
    return jsonify({"bins": bins})

@app.route('/api/bin_status')
def bin_status():
    # Example of bin data with random fill levels and statuses
    bins = [
        {'id': 1, 'name': 'Cardboard', 'is_open': random.choice([True, False])},
        {'id': 2, 'name': 'Metal', 'is_open': random.choice([True, False])},
        {'id': 3, 'name': 'Plastic', 'is_open': random.choice([True, False])}
    ]
    return jsonify({'bins': bins})

@app.route('/api/detection')
def detection():
    # Example detection data
    detected_class = random.choice(['Cardboard', 'Metal', 'Plastic', None])
    bin_open_type = None

    # If a class is detected, get the corresponding bin
    if detected_class:
        bin_open_type = detected_class

    return jsonify({
        'detected_class': detected_class,
        'bin_open_status': bin_open_type
    })

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='video/mp4')  # Directly serve video as 'video/mp4'

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/insight/<int:bin_id>')
def insight(bin_id):
    return render_template('insight.html', bin_id=bin_id)

if __name__ == '__main__':
    app.run(debug=True)
