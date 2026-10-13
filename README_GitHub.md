# Webcam-Controlled Arduino Servo

Control an Arduino-connected servo using **Go** and **Stop** gestures or objects recognized by a webcam. A Teachable Machine image-classification model runs in Python and sends serial commands to the Arduino.

## Table of Contents

- [How It Works](#how-it-works)
- [Hardware](#hardware)
- [Wiring](#wiring)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Setup](#setup)
- [Configure the Labels](#configure-the-labels)
- [Run the Project](#run-the-project)
- [Arduino Sketch](#arduino-sketch)
- [Troubleshooting](#troubleshooting)
- [Limitations and Safety](#limitations-and-safety)

## How It Works

1. Python reads frames from the webcam.
2. Each frame is prepared for the Teachable Machine model.
3. The model predicts a class and confidence score.
4. If confidence is at least **80%**, Python sends a command when the mapped command changes:
   - **Go** sends `on`.
   - **Stop** sends `off`.
5. The Arduino receives the command over USB serial:
   - `on` starts the servo sweeping between 0° and 180°.
   - `off` stops the sweep at the current commanded position.

## Hardware

- Arduino-compatible board
- SG90 servo
- USB cable
- Webcam
- Jumper wires
- Computer with Python installed

## Wiring

| Servo wire | Connect to |
| --- | --- |
| Signal (usually orange/yellow) | Arduino digital pin **9** |
| VCC (usually red) | Suitable **5 V** supply |
| GND (usually brown/black) | Arduino **GND** |

Use a suitable power supply for the servo. Connect the external supply's ground to Arduino GND. If the board resets or the servo behaves unpredictably, the servo may need a separate suitable 5 V supply.

## Project Structure

Keep these files in the same folder:

```text
project-folder/
├── main.py
├── keras_model.h5
├── labels.txt
└── README.md
```

- `main.py` — Python webcam, classification, and serial-control program.
- `keras_model.h5` — model exported from Teachable Machine.
- `labels.txt` — class names and numeric indices.
- `README.md` — project documentation.

The Python script loads `keras_model.h5` and `labels.txt` from the same directory as the script.

## Requirements

- Python
- OpenCV (`opencv-python`)
- NumPy (`numpy`)
- PySerial (`pyserial`)
- TensorFlow (`tensorflow`)
- Legacy Keras (`tf-keras`)

Install the Python packages:

```bash
python -m pip install opencv-python numpy pyserial tensorflow tf-keras
```

Use the same Python environment to install the packages and run the script.

## Setup

1. **Connect the hardware.** Connect the servo signal wire to pin 9, plus power and ground as described above.
2. **Upload the Arduino sketch.** Use the sketch in the [Arduino Sketch](#arduino-sketch) section.
3. **Set the serial port.** In `main.py`, update the port to match the Arduino IDE's **Tools → Port** menu:

   ```python
   SERIAL_PORT = "COM5"
   BAUD_RATE = 9600
   ```

   Replace `COM5` with your actual port. On macOS or Linux, it may look like `/dev/cu.usbmodem...` or `/dev/ttyACM0`.

4. **Check the model labels.** Confirm the class numbers in `labels.txt` match the Python mapping shown below.
5. **Close the Serial Monitor.** The Arduino IDE Serial Monitor and Python generally cannot use the same serial port at the same time.

## Configure the Labels

The numeric keys in `MESSAGE_FOR_LABEL` must match the class indices in `labels.txt`.

For example, if `labels.txt` contains:

```text
0 Background
1 Go
2 Stop
```

use this mapping in `main.py`:

```python
MESSAGE_FOR_LABEL = {
    1: "on",   # Go starts the servo sweep
    2: "off",  # Stop stops the servo sweep
}
```

To also stop the servo when the model recognizes Background, use:

```python
MESSAGE_FOR_LABEL = {
    0: "off",
    1: "on",
    2: "off",
}
```

The Python program sends a command only when the prediction confidence is at least `0.80` and the mapped command differs from the last command sent.

## Run the Project

1. Open a terminal in the project folder.
2. Make sure the Arduino is connected and the Serial Monitor is closed.
3. Run:

   ```bash
   python main.py
   ```

4. Show the webcam the trained **Go** or **Stop** class.
5. The terminal displays the predicted class and confidence score.
6. Click the webcam window and press **Esc** or **q** to quit.

## Arduino Sketch

This sketch is for a **standard SG90 positional servo**. It sweeps between 0° and 180° while `on` is active and stops updating the target position when `off` is received.

```cpp
#include <Servo.h>

Servo myservo;
String command = "";
int pos = 180;
int direction = -1;
bool isOn = false;

unsigned long lastMoveTime = 0;
const int moveDelay = 5;

void setup() {
  myservo.attach(9);
  Serial.begin(9600);
  Serial.setTimeout(50);
  myservo.write(pos);
}

void loop() {
  if (Serial.available() > 0) {
    command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "on") {
      isOn = true;
    } else if (command == "off") {
      isOn = false;
    }
  }

  if (isOn && millis() - lastMoveTime >= moveDelay) {
    lastMoveTime = millis();
    myservo.write(pos);

    pos += direction;

    if (pos <= 0) {
      pos = 0;
      direction = 1;
    } else if (pos >= 180) {
      pos = 180;
      direction = -1;
    }
  }
}
```

The `moveDelay` value controls how frequently the target angle changes. A smaller value does not guarantee faster physical movement; the servo's motor speed is the limiting factor.

## Troubleshooting

### `ModuleNotFoundError`

Install the missing package using the same Python interpreter used to run the script. For example:

```bash
python -m pip install opencv-python
python -m pip install pyserial
python -m pip install tensorflow tf-keras
```

### Cannot open the serial port

- Confirm the correct port in the Arduino IDE under **Tools → Port**.
- Update `SERIAL_PORT` in `main.py`.
- Close the Arduino Serial Monitor and any other program using the port.

### Webcam will not open

The script uses camera index `0`. If needed, change:

```python
camera = cv2.VideoCapture(0)
```

to:

```python
camera = cv2.VideoCapture(1)
```

Also check your operating system's camera permissions.

### Servo does not respond

- Confirm the signal wire is connected to pin 9.
- Confirm Python and Arduino both use a baud rate of `9600`.
- Confirm Python sends lowercase `on` and `off`.
- Confirm the class indices in `labels.txt` match `MESSAGE_FOR_LABEL`.
- Check the servo's power supply and shared ground.

### Predictions change too often

The confidence threshold is `0.80` (80%). You can increase `CONFIDENCE_THRESHOLD` in `main.py` to require more confident predictions, or improve the training images in Teachable Machine.

## Limitations and Safety

- A standard SG90 normally moves through approximately 180°; it does **not** spin continuously through 360°.
- The Arduino sketch above sweeps between 0° and 180°. A continuous-rotation servo requires different control behavior.
- The model must be trained with the classes you want to recognize, such as Go and Stop.
- Keep fingers, wires, and loose objects clear of moving parts.
