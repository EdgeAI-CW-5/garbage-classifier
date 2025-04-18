# Connected Raspberry Pi with web server(local host)

import cv2
import os
import time
import numpy as np
import tensorflow as tf
import RPi.GPIO as GPIO
import requests  # Added for sending data
from tensorflow.keras.preprocessing.image import img_to_array

# === Load model ===
model = tf.keras.models.load_model("fine-tuning-garbage-classifier")

# === Labels ===
class_labels = ["Cardboard", "Metal", "Plastic"]

# === GPIO setup ===
GPIO.setmode(GPIO.BCM)

# === Servo setup ===
servo_pins = {
    "Plastic": 18,
    "Metal": 12,
    "Cardboard": 13
}

servos = {}
for label, pin in servo_pins.items():
    GPIO.setup(pin, GPIO.OUT)
    pwm = GPIO.PWM(pin, 50)
    pwm.start(0)
    servos[label] = pwm

def set_servo_angle(pwm, angle):
    duty = 2 + (angle / 18)
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)
    pwm.ChangeDutyCycle(0)

# === Ultrasonic sensor for Plastic only ===
ultrasonic_trig = 23
ultrasonic_echo = 24

GPIO.setup(ultrasonic_trig, GPIO.OUT)
GPIO.setup(ultrasonic_echo, GPIO.IN)

def get_bin_distance(trig, echo):
    GPIO.output(trig, False)
    time.sleep(0.05)

    GPIO.output(trig, True)
    time.sleep(0.00001)
    GPIO.output(trig, False)

    timeout = time.time() + 1
    while GPIO.input(echo) == 0:
        pulse_start = time.time()
        if pulse_start > timeout:
            return -1

    timeout = time.time() + 1
    while GPIO.input(echo) == 1:
        pulse_end = time.time()
        if pulse_end > timeout:
            return -1

    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150
    return round(distance, 2)

# === Create save directory ===
save_dir = "detected_images"
os.makedirs(save_dir, exist_ok=True)

# === Start webcam ===
cap = cv2.VideoCapture(0)
time.sleep(2)
if not cap.isOpened():
    print("? Error: Could not open webcam.")
    exit()

print("? Smart Bin System Ready!")

try:
    while True:
        countdown = 10
        start_time = time.time()

        print("\n??? Please place the garbage item in front of the camera...")
        print("?? Live video stream open. Image will be captured after countdown.")

        while True:
            ret, frame = cap.read()
            if not ret:
                print("?? Failed to grab frame.")
                break

            elapsed = int(time.time() - start_time)
            remaining = countdown - elapsed
            if remaining <= 0:
                break

            cv2.putText(frame, f"Capturing in {remaining}s", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.imshow("Live Feed - Adjust Object", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                raise KeyboardInterrupt

        print("?? Capturing image...")
        ret, captured_frame = cap.read()
        if not ret:
            print("?? Failed to capture image.")
            continue

        resized_frame = cv2.resize(captured_frame, (224, 224))
        img_array = img_to_array(resized_frame) / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        predictions = model.predict(img_array)
        predicted_class = np.argmax(predictions)
        label = class_labels[predicted_class]
        confidence = round(np.max(predictions) * 100, 2)

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"{label}_{timestamp}.jpg"
        filepath = os.path.join(save_dir, filename)
        cv2.imwrite(filepath, captured_frame)

        print(f"\n? Detected: {label.upper()} ({confidence}%)")
        print(f"??? Image saved as: {filename}")

        cv2.putText(captured_frame, f"{label} ({confidence}%)", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Prediction Result", captured_frame)
        cv2.waitKey(3000)
        cv2.destroyAllWindows()

        print(f"?? Opening {label.upper()} bin...")
        pwm = servos[label]
        set_servo_angle(pwm, 90)
        time.sleep(10)
        set_servo_angle(pwm, 0)
        print("?? Bin lid closed.")

        distance = None
        if label == "Plastic":
            distance = get_bin_distance(ultrasonic_trig, ultrasonic_echo)
            if distance == -1:
                print("?? PLASTIC bin distance measurement failed.")
            else:
                print(f"?? PLASTIC bin level: {distance} cm")
                if distance < 10:
                    print("?? PLASTIC bin is FULL!")
                    while True:
                        response = input("?? Please empty the bin and press 'y' to continue: ").strip().lower()
                        if response == 'y':
                            print("? Bin cleared. Resuming detection...")
                            break
                else:
                    print("? PLASTIC bin has space.")

        # === Send data to local Flask web app ===
        try:
            api_url = "http://192.168.8.123:5000/upload-data"  # Replace with your actual IP
            files = {
                'image': open(filepath, 'rb')
            }
            data = {
                'label': label,
                'confidence': confidence,
                'distance': distance if label == "Plastic" else None
            }

            response = requests.post(api_url, files=files, data=data)
            if response.status_code == 200:
                print("?? Data successfully sent to web application!")
            else:
                print(f"? Failed to send data. Status: {response.status_code}, Message: {response.text}")
        except Exception as e:
            print(f"?? Error sending data to server: {e}")

except KeyboardInterrupt:
    print("\n?? Exiting...")

finally:
    cap.release()
    cv2.destroyAllWindows()
    for pwm in servos.values():
        set_servo_angle(pwm, 0)
        pwm.stop()
    GPIO.cleanup()
