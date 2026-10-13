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

  myservo.write(180);
}

void loop() {
  // Read commands from Python
  if (Serial.available() > 0) {
    command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "on") {
      isOn = true;
    }
    else if (command == "off") {
      isOn = false;
    }
  }

  // Sweep between 180 and 0 while ON
  if (isOn && millis() - lastMoveTime >= moveDelay) {
    lastMoveTime = millis();

    myservo.write(pos);

    pos += direction;

    if (pos <= 0) {
      pos = 0;
      direction = 1;
    }
    else if (pos >= 180) {
      pos = 180;
      direction = -1;
    }
  }
}
