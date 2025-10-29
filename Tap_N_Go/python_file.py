import pandas as pd
import paho.mqtt.client as mqtt
import json
import re
from datetime import datetime, timedelta
import os

# --- Load Registered Users File ---
EXCEL_FILE = 'rfid__data.xlsx'
df = pd.read_excel(EXCEL_FILE)
df['Card Number'] = df['Card Number'].str.strip()

# --- Attendance Log File ---
ATTENDANCE_FILE = 'attendance_log.xlsx'

# Create attendance log file if it does not exist
if not os.path.exists(ATTENDANCE_FILE):
    pd.DataFrame(columns=['Name', 'Card Number', 'Date', 'Punch In', 'Punch Out', 'Duration'])\
        .to_excel(ATTENDANCE_FILE, index=False)

# --- MQTT Setup ---
MQTT_BROKER = '192.168.41.145'
MQTT_PORT = 1883
REQUEST_TOPIC = 'rfid/request'
RESPONSE_TOPIC = 'rfid/response'

# --- MQTT Callback: Connected ---
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(REQUEST_TOPIC)

# --- Duration Formatter ---
def format_duration(seconds):
    return str(timedelta(seconds=round(seconds)))

# --- MQTT Callback: Message Received ---
def on_message(client, userdata, msg):
    print(f"\nMessage on topic: {msg.topic}")
    print(f"Raw payload (hex): {msg.payload.hex()}")

    if msg.topic != REQUEST_TOPIC:
        print(f"Ignoring message from topic {msg.topic}")
        return

    # Try decoding with UTF-8. If fails, ignore and log.
    try:
        card_number = msg.payload.decode('utf-8').strip()
    except UnicodeDecodeError as e:
        print(f"Warning: Cannot decode payload as UTF-8. Ignoring message. Error: {e}")
        return

    # Check card number format (example: MAC-like pattern)
    if not re.match(r'^([A-F0-9]{2}:){3,}[A-F0-9]{2}$', card_number, re.IGNORECASE):
        print(f"Invalid card number format received: {card_number}")
        return

    print(f"Decoded card number: {card_number}")

    # Lookup user in registered cards
    match = df[df['Card Number'] == card_number]
    if match.empty:
        response = {"status": "not ok", "name": "not found"}
        client.publish(RESPONSE_TOPIC, json.dumps(response))
        print(f"User not found. Sent response: {response}")
        return

    name = match.iloc[0]['Name'].strip()
    now = datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    full_time_str = now.strftime('%Y-%m-%d %H:%M:%S')

    # Load or create attendance log
    if os.path.exists(ATTENDANCE_FILE):
        log_df = pd.read_excel(ATTENDANCE_FILE)
    else:
        log_df = pd.DataFrame(columns=['Name', 'Card Number', 'Date', 'Punch In', 'Punch Out', 'Duration'])

    # Check if already punched in today
    today_entry = log_df[(log_df['Card Number'] == card_number) & (log_df['Date'] == date_str)]

    if today_entry.empty:
        # Punch In
        new_row = pd.DataFrame([{
            'Name': name,
            'Card Number': card_number,
            'Date': date_str,
            'Punch In': full_time_str,
            'Punch Out': '',
            'Duration': ''
        }])
        log_df = pd.concat([log_df, new_row], ignore_index=True)
        present_status = "punch in"
        print(f"{name} punched in at {full_time_str}")
    else:
        # Punch Out
        idx = today_entry.index[0]
        punch_in_str = today_entry.iloc[0]['Punch In']
        try:
            punch_in_time = datetime.strptime(punch_in_str, '%Y-%m-%d %H:%M:%S')
        except Exception as e:
            print(f"Error parsing Punch In time: {punch_in_str}. Error: {e}")
            return

        punch_out_time = now
        duration_seconds = (punch_out_time - punch_in_time).total_seconds()

        log_df.at[idx, 'Punch Out'] = full_time_str
        log_df.at[idx, 'Duration'] = format_duration(duration_seconds)
        present_status = "punch out"
        print(f"{name} punched out at {full_time_str}, duration: {format_duration(duration_seconds)}")

    # Save updated attendance log
    log_df.to_excel(ATTENDANCE_FILE, index=False)

    # Send response back
    response = {
        "status": "ok",
        "name": name,
        "present_Status": present_status
        # "timestamp": full_time_str
    }
    client.publish(RESPONSE_TOPIC, json.dumps(response))
    print(f"Sent response: {response}")

# --- Start MQTT Client ---
client = mqtt.Client(protocol=mqtt.MQTTv311)
client.on_connect = on_connect
client.on_message = on_message

print("Connecting to MQTT broker...")
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_forever()