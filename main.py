import os
import sys
import time

# Force TensorFlow to use the legacy Keras 2 engine.
# This must be set before TensorFlow is imported.
os.environ["TF_USE_LEGACY_KERAS"] = "1"

# Workaround for environments where importing pyarrow can interfere with TensorFlow.
# This project does not use pyarrow.
sys.modules["pyarrow"] = None

import cv2
import numpy as np
import serial
from tf_keras.models import load_model

# Find the model and labels next to this script, whatever folder you run it from.
HERE = os.path.dirname(os.path.abspath(__file__))

# ----------------------------------------------------------------------
# Serial settings
# ----------------------------------------------------------------------

# Update these label indices to match labels.txt.
# Example: 0 Background, 1 Go, 2 Stop.
# Go -> "on"; Stop -> "off".
MESSAGE_FOR_LABEL = {
    1: "on",
    2: "off",
}

# Must match Serial.begin() in the Arduino sketch.
BAUD_RATE = 9600

# Only act on predictions the model is confident about.
CONFIDENCE_THRESHOLD = 0.80

# Change this to the port shown in the Arduino IDE under Tools > Port.
# Windows example: "COM5"; macOS example: "/dev/cu.usbmodem14101".
SERIAL_PORT = "COM5"

# Open the serial port. The program can still test the camera/model if
# the Arduino port cannot be opened.
board = None
try:
    board = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    # Opening the port resets most Arduino boards; wait for it to restart.
    time.sleep(2)
    print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud.")
except serial.SerialException as error:
    print(f"Could not open {SERIAL_PORT}: {error}")
    print("Check Tools > Port in the Arduino IDE and close the Serial Monitor.")


def send(message):
    """Send one newline-terminated command to the Arduino."""
    if board is None:
        return
    board.write((message + "\n").encode("utf-8"))
    print(f"Sent: {message}")


# ----------------------------------------------------------------------
# Model, labels, and camera
# ----------------------------------------------------------------------

model = load_model(os.path.join(HERE, "keras_model.h5"), compile=False)

# Each labels.txt line should look like "0 Background".
with open(os.path.join(HERE, "labels.txt"), "r", encoding="utf-8") as label_file:
    class_names = [
        line.strip().split(" ", 1)[1]
        for line in label_file
        if line.strip() and " " in line.strip()
    ]

camera = cv2.VideoCapture(0)
if not camera.isOpened():
    if board is not None:
        board.close()
    sys.exit(
        "Could not open the camera. Try VideoCapture(1), or check your "
        "operating system's camera permissions."
    )

print("Click the webcam window, then press Esc or q to quit.")

# Remember the last command so it is only sent when it changes.
last_message = None

try:
    while True:
        ret, frame = camera.read()
        if not ret:
            print("Could not read a frame from the camera.")
            break

        # Center-crop to a square so the image is not stretched.
        height, width = frame.shape[:2]
        size = min(height, width)
        top = (height - size) // 2
        left = (width - size) // 2
        frame = frame[top:top + size, left:left + size]

        # Teachable Machine image models expect a 224 x 224 image.
        frame = cv2.resize(frame, (224, 224), interpolation=cv2.INTER_AREA)
        cv2.imshow("Webcam Image", frame)

        # Convert OpenCV's BGR image to RGB.
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = np.asarray(image, dtype=np.float32).reshape(1, 224, 224, 3)
        image = (image / 127.5) - 1

        prediction = model.predict(image, verbose=0)
        index = int(np.argmax(prediction[0]))

        if index >= len(class_names):
            print(f"Prediction index {index} has no matching entry in labels.txt.")
            continue

        class_name = class_names[index]
        confidence_score = float(prediction[0][index])
        print(
            f"Class: {class_name}   "
            f"Confidence Score: {confidence_score * 100:.0f} %"
        )

        message = None
        if confidence_score >= CONFIDENCE_THRESHOLD:
            message = MESSAGE_FOR_LABEL.get(index)

        if message is not None and message != last_message:
            send(message)
            last_message = message

        key = cv2.waitKey(1) & 0xFF
        if key == 27 or key == ord("q"):
            break
finally:
    camera.release()
    cv2.destroyAllWindows()
    if board is not None:
        # Send stop when exiting, then close the connection.
        try:
            send("off")
        finally:
            board.close()
