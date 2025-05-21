import cv2
import mediapipe as mp
import requests
import re
import time
import logging
import threading
from datetime import datetime
import sys

sys.path.append("lib")
from arduino_iot_cloud import ArduinoCloudClient


ESP32_IP = "http://192.168.1.193"
DEVICE_ID = "1fdd7445-1d49-4ef2-9107-c04d5724ffbc"
SECRET_KEY = "g0V!G9ruxuPZkjiA8kRyt#g2!"

KNOWN_USERS = {
    # "user1": ["thumb", "thumb_index", "index_middle", "reset"],
    # "user2": ["thumb", "thumb_pinky", "index", "reset"],
    # "user3": ["index", "index_middle", "reset"],
    "user1": ["thumb","reset"],
    "user2": ["index", "reset"],
    "user3": ["index", "index_middle", "reset"],

}

USER_LEDS = {
    "user1": "thumb",
    "user2": "index",
    "user3": "middle"
}

def logging_func():
    logging.basicConfig(
        datefmt="%H:%M:%S",
        format="%(asctime)s.%(msecs)03d %(message)s",
        level=logging.INFO,
    )  
    
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_drawing = mp.solutions.drawing_utils

leds_off_due_to_proximity = False
current_gesture_sequence = []
last_gesture_time = time.time()
GESTURE_TIMEOUT = 3  # saniye

def control_led(endpoint):
    url = f"{ESP32_IP}/led/{endpoint}"
    try:
        response = requests.get(url)
        print(f"Sent command: {endpoint}, Response: {response.text}")
    except Exception as e:
        print(f"Error sending command: {endpoint}, {e}")

def set_all_leds_off():
    for led in ["thumb", "index", "middle"]:
        control_led(f"{led}/off")

def is_hand_near(threshold_cm=10):
    try:
        response = requests.get(f"{ESP32_IP}/distance")
        match = re.search(r'\d+', response.text)
        if match:
            distance = int(match.group(0))

            return distance < threshold_cm
        else:
            print("No valid number in response")
            return False
    except Exception as e:
        print(f"Distance read error: {e}")
        return False

def get_finger_state(hand_landmarks, handedness_label):
    is_right = handedness_label == "Right"
    thumb = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].x < \
            hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_IP].x if is_right else \
            hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].x > \
            hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_IP].x

    index = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y < \
            hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_PIP].y
    middle = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y < \
             hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_PIP].y
    ring = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP].y < \
           hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_PIP].y
    pinky = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP].y < \
            hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_PIP].y

    return {
        "thumb": thumb,
        "index": index,
        "middle": middle,
        "ring": ring,
        "pinky": pinky
    }

def detect_combination(finger_states):
    finger_order = ["thumb", "index", "middle", "ring", "pinky"]
    active = [f for f in finger_order if finger_states[f]]
    if not active:
        return "reset"
    return "_".join(active)


def count_fingers_and_track(hand_landmarks, handedness_label):
    global leds_off_due_to_proximity, current_gesture_sequence, last_gesture_time

    finger_states = get_finger_state(hand_landmarks, handedness_label)

    now = time.time()
    if now - last_gesture_time > GESTURE_TIMEOUT:
        current_gesture_sequence.clear()

    gesture = detect_combination(finger_states)

    if not current_gesture_sequence or gesture != current_gesture_sequence[-1]:
        current_gesture_sequence.append(gesture)
        print(f"Current gesture sequence: {current_gesture_sequence}")

    last_gesture_time = now

    if gesture == "reset":
        print("Gesture sequence complete. Checking user...")
        matched_user = None
        for user, sequence in KNOWN_USERS.items():
            if sequence == current_gesture_sequence:
                matched_user = user
                break

        if matched_user:
            print(f"User gesture matched: {matched_user}. Checking distance...")
            if is_hand_near():
                print(f"Distance check passed. Access Granted for {matched_user}")
                threading.Thread(target=send_to_arduino_cloud, args=(matched_user,), daemon=True).start()
            else:
                print("Access Denied: Hand is too far.")
        else:
            print("No matching gesture sequence found.")

        current_gesture_sequence.clear()


def light_user_led(username):
    set_all_leds_off()
    led_name = USER_LEDS.get(username)
    if led_name:
        control_led(f"{led_name}/on")
        print(f"{username} için {led_name} LED'i yakıldı.")
        beep_buzzer()
        # 3 saniye sonra LED'leri kapat
        threading.Timer(3, set_all_leds_off).start()

def beep_buzzer():
    try:
        response_on = requests.get(f"{ESP32_IP}/buzzer/on")
        print(f"Buzzer ON: {response_on.text}")

        threading.Timer(1.0, lambda: requests.get(f"{ESP32_IP}/buzzer/off")).start()

    except Exception as e:
        print(f"Buzzer error: {e}")

def is_within_working_hours():
    now = datetime.now().time()
    start_time = datetime.strptime("09:00", "%H:%M").time()
    end_time = datetime.strptime("17:00", "%H:%M").time()
    return start_time <= now <= end_time

def reset_daily_counters():
    try:
        client = ArduinoCloudClient(device_id=DEVICE_ID, username=DEVICE_ID, password=SECRET_KEY, sync_mode=True)
        client.register("user1EntryCount")
        client.register("user2EntryCount")
        client.register("user3EntryCount")
        client.update()

        client["user1EntryCount"] = 0
        client["user2EntryCount"] = 0
        client["user3EntryCount"] = 0

        client.update()
        print("Sayaçlar başarıyla sıfırlandı.")
    except Exception as e:
        print(f"Günlük sayaç sıfırlama hatası: {e}")

def send_to_arduino_cloud(username):
    try:
        print("Arduino Cloud bağlantısı başlatılıyor...")
        client = ArduinoCloudClient(device_id=DEVICE_ID, username=DEVICE_ID, password=SECRET_KEY, sync_mode=True)  # sync_mode=True!

        print("Arduino Cloud istemcisi oluşturuldu.")
        client.register("user1Access")
        client.register("user2Access")
        client.register("user3Access")
        client.register("user1EntryCount")
        client.register("user2EntryCount")
        client.register("user3EntryCount")
        client.register("systemActive")


        client.update()  
        
        # is systemActive and current time check
        system_status = client.get("systemActive", False)
        current_time_status = is_within_working_hours()

        print(f"systemActive (manuel): {system_status}")
        print(f"Saat aralığı kontrolü: {current_time_status}")

        if not system_status and not current_time_status:
            print("Sistem devre dışı ve çalışma saati dışında. İşlem yapılmayacak.")
            return
        
        client["user1Access"] = (username == "user1")
        client["user2Access"] = (username == "user2")
        client["user3Access"] = (username == "user3")

        # increment entry count
        if username == "user1":
            current = client.get("user1EntryCount", 0) or 0
            updated = int(current) + 1
            client["user1EntryCount"] = updated
            print(f"user1EntryCount: {current} -> {updated}")
        elif username == "user2":
            current = client.get("user2EntryCount", 0) or 0
            updated = int(current) + 1
            client["user2EntryCount"] = updated
            print(f"user2EntryCount: {current} -> {updated}")
        elif username == "user3":
            current = client.get("user3EntryCount", 0) or 0
            updated = int(current) + 1
            client["user3EntryCount"] = updated
            print(f"user3EntryCount: {current} -> {updated}")

        client.update()  # update cloud

        client.start()
        
        light_user_led(username)
        print("Client başlatıldı, bağlantı bekleniyor...")

        timeout = time.time() + 10
        while not client.connected:
            print("Bağlanmaya çalışılıyor...")
            if time.time() > timeout:
                print("Bağlantı zaman aşımına uğradı.")
                return
            time.sleep(0.5)

        print("Arduino Cloud'a başarıyla bağlandı.")

        start = time.time()
        while time.time() - start < 5:
            client.update()
            time.sleep(0.2)

        print(f"Access granted for {username} ve Arduino Cloud'a veri gönderildi.")

    except Exception as e:
        import traceback
        print("HATA: Arduino Cloud bağlantısı sırasında istisna oluştu:")
        traceback.print_exc()
        
def schedule_daily_reset():
    def reset_loop():
        while True:
            now = datetime.now()
            midnight = datetime.combine(now.date(), datetime.min.time())
            next_midnight = midnight.replace(day=now.day + 1, hour=0, minute=0, second=0)
            wait_seconds = (next_midnight - now).total_seconds()
            print(f"Günlük sıfırlama {wait_seconds / 3600:.2f} saat sonra gerçekleşecek.")
            time.sleep(wait_seconds)
            reset_daily_counters()

    threading.Thread(target=reset_loop, daemon=True).start()

schedule_daily_reset()

cap = cv2.VideoCapture(0)
while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks and results.multi_handedness:
        for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            label = handedness.classification[0].label
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            count_fingers_and_track(hand_landmarks, label)

    cv2.imshow("Hand Detection", frame)
    if cv2.waitKey(5) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
