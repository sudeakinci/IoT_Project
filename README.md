# Hand Gesture Recognition & IoT Cloud Access Control

This project integrates an ESP32 board and a Python-based gesture recognition system (using MediaPipe and OpenCV) to detect predefined finger gesture sequences. When a valid user gesture is detected within proximity range, the system grants access by lighting up a corresponding LED and beeping a buzzer. The access data is also synchronized with the Arduino IoT Cloud.

---

##  Features

- ESP32 serves HTTP endpoints and connects to Arduino IoT Cloud.
- Real-time hand gesture recognition using Python + OpenCV + MediaPipe.
- Ultrasonic sensor for distance-based access control.
- Individual LED + buzzer feedback per user.
- Daily reset of access counters at midnight.
- Configurable gesture patterns per user.

---

##  Hardware Requirements

| Component         | ESP32 Pin |
|-------------------|-----------|
| Thumb LED         | 27        |
| Index LED         | 26        |
| Middle LED        | 25        |
| Buzzer            | 33        |
| Ultrasonic Trig   | 5         |
| Ultrasonic Echo   | 18        |
| 5V / GND          | Power     |

### Additional Items

- ESP32 Development Board  
- HC-SR04 Ultrasonic Distance Sensor  
- 3 LEDs + 220Ω Resistors  
- Buzzer  
- Jumper Wires  
- Breadboard  

---

##  Software Requirements

- Arduino IDE or PlatformIO  
- Python 3.9+  
- Arduino IoT Cloud Account  
- Required Python packages:
```cpp
pip install opencv-python mediapipe requests arduino_iot_cloud
```
  
---

# Arduino Setup

Create a new Thing on Arduino IoT Cloud.

Add variables (all READ_WRITE):

- `user1Access` (bool)  
- `user2Access` (bool)  
- `user3Access` (bool)  
- `user1EntryCount` (int)  
- `user2EntryCount` (int)  
- `user3EntryCount` (int)  
- `systemActive` (bool)  

Download the generated `thingProperties.h` file.

Create a file named `arduino_secrets.h`:

```cpp
#define SECRET_SSID "YourWiFiName"
#define SECRET_PASS "YourWiFiPassword"
```

#  Python Configuration
Update these constants in your Python script:

```cpp
ESP32_IP = "http://<your-esp32-ip>"
DEVICE_ID = "<your-arduino-iot-device-id>"
SECRET_KEY = "<your-device-secret-key>"
```

# Installation & Upload

1. **Arduino Sketch**  
Install required libraries in Arduino IDE:

- ESPAsyncWebServer  
- WiFi  
- ArduinoIoTCloud  

Upload the provided `.ino` sketch to your ESP32.

2. **Python Environment**  
Create and activate a virtual environment:

```cpp
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

Install dependencies:
```cpp
pip install opencv-python mediapipe requests arduino_iot_cloud
```

# Gesture Definitions

Each user is defined by a unique gesture sequence:

| User  | Gesture Sequence                      |
|-------|-------------------------------------|
| user1 | thumb → thumb_index → index_middle → reset |
| user2 | index → reset                       |
| user3 | index → index_middle → reset        |

A reset gesture (no fingers up) ends the sequence and triggers evaluation.


# API Endpoints on ESP32

| Endpoint          | Method | Description                |
|-------------------|--------|----------------------------|
| /distance         | GET    | Returns distance in cm      |
| /led/thumb/on     | GET    | Turn thumb LED ON           |
| /led/thumb/off    | GET    | Turn thumb LED OFF          |
| /led/index/on     | GET    | Turn index LED ON           |
| /led/index/off    | GET    | Turn index LED OFF          |
| /led/middle/on    | GET    | Turn middle LED ON          |
| /led/middle/off   | GET    | Turn middle LED OFF         |
| /buzzer/on        | GET    | Turn buzzer ON              |
| /buzzer/off       | GET    | Turn buzzer OFF             |

# Running the System

Start the ESP32 and confirm the IP address via Serial Monitor.

Run the Python script:

```cpp
python hand_access.py
```

The LED and buzzer will activate if access is granted.

Entry counters are synced to Arduino IoT Cloud.

# Example Commands

Test API endpoints via curl:
```cpp
curl http://<esp32_ip>/distance
curl http://<esp32_ip>/led/index/on
```

# Troubleshooting

-  **Camera not working?** Ensure no other process is using it.
-  **ESP32 not connecting?** Double-check Wi-Fi credentials.
-  **Distance always returns 999?** Ensure the hand is close and sensor is wired correctly.
-  **IoT Cloud sync failing?** Confirm device ID and secret key are correct.

# Scheduled Tasks

The system automatically resets the daily entry counters at midnight using a background thread in Python. You don’t need to configure cron or external schedulers.

---

Feel free to modify the gesture patterns, access rules, or logging behavior for your specific use case!
