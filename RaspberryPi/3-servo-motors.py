# Connection between the classification model & 3 Servo Motors (For predicting Plastic, Metal, Cardboard)

import cv2
import os
import time
import numpy as np
import tensorflow as tf
import RPi.GPIO as GPIO
from tensorflow.keras.preprocessing.image import img_to_array

# === Load model ===
model = tf.keras.models.load_model("fine-tuning-garbage-classifier")

# === Labels ===
class_labels = ["Cardboard", "Metal", "Plastic"]

# === Servo setup using RPi.GPIO ===
GPIO.setmode(GPIO.BCM)

servo_pins = {
    "Plastic": 18,    # GPIO18 ? Pin 12
    "Metal": 12,      # GPIO12 ? Pin 32
    "Cardboard": 13   # GPIO13 ? Pin 33
}

servos = {}
for label, pin in servo_pins.items():
    GPIO.setup(pin, GPIO.OUT)
    pwm = GPIO.PWM(pin, 50)  # 50Hz PWM
    pwm.start(0)  # Start with 0% duty cycle
    servos[label] = pwm

def set_servo_angle(pwm, angle):
    duty = 2 + (angle / 18)
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)
    pwm.ChangeDutyCycle(0)

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
        countdown = 10  # seconds
        start_time = time.time()

        print("\n?? Please place the garbage item in front of the camera...")
        print("? Live video stream open. Image will be captured after countdown.")

        # === Live feed with countdown overlay ===
        while True:
            ret, frame = cap.read()
            if not ret:
                print("? Failed to grab frame.")
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

        # === Capture one frame for prediction ===
        print("?? Capturing image...")
        ret, captured_frame = cap.read()
        if not ret:
            print("? Failed to capture image.")
            continue

        # === Preprocess and predict ===
        resized_frame = cv2.resize(captured_frame, (224, 224))
        img_array = img_to_array(resized_frame) / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        predictions = model.predict(img_array)
        predicted_class = np.argmax(predictions)
        label = class_labels[predicted_class]
        confidence = round(np.max(predictions) * 100, 2)

        # === Save image ===
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"{label}_{timestamp}.jpg"
        filepath = os.path.join(save_dir, filename)
        cv2.imwrite(filepath, captured_frame)

        # === Display result ===
        print(f"\n? Detected: {label.upper()} ({confidence}%)")
        print(f"?? Image saved as: {filename}")

        cv2.putText(captured_frame, f"{label} ({confidence}%)", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Prediction Result", captured_frame)
        cv2.waitKey(3000)
        cv2.destroyAllWindows()

        # === Open bin lid ===
        print(f"?? Opening {label.upper()} bin...")
        pwm = servos[label]
        set_servo_angle(pwm, 90)  # Open
        time.sleep(10)
        set_servo_angle(pwm, 0)   # Close
        print("? Bin lid closed.")

except KeyboardInterrupt:
    print("\n?? Exiting...")

finally:
    cap.release()
    cv2.destroyAllWindows()
    for pwm in servos.values():
        set_servo_angle(pwm, 0)  # Ensure bin is closed
        pwm.stop()
    GPIO.cleanup()
