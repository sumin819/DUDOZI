# mqtt_listener.py
import json
import threading
import paho.mqtt.client as mqtt

from camera_manager import system_on, system_off
from stream_server import run_stream_server
from mission import start_mission, stop_mission

AGV_ID = "AGV1"
MQTT_HOST = "172.20.10.6"
MQTT_PORT = 1883

RUN_TOPIC = f"agv/{AGV_ID}/run"   # ON / OFF
CMD_TOPIC = f"agv/{AGV_ID}/cmd"   # START / PAUSE

_stream_thread = None


def on_connect(client, userdata, flags, rc):
    print("MQTT connected:", rc)
    client.subscribe(RUN_TOPIC)
    client.subscribe(CMD_TOPIC)


def on_message(client, userdata, msg):
    global _stream_thread
    data = json.loads(msg.payload.decode())

    # ==========================
    # SYSTEM ON / OFF
    # ==========================
    if msg.topic == RUN_TOPIC:
        running = data.get("running")

        if running:
            print("[SYSTEM] ON")

            # ✅ 카메라 초기화
            system_on()

            # ✅ 스트림 서버 시작 (1회)
            if _stream_thread is None or not _stream_thread.is_alive():
                _stream_thread = threading.Thread(
                    target=run_stream_server,
                    daemon=True
                )
                _stream_thread.start()
                print("Stream server thread started")

        else:
            print("[SYSTEM] OFF")
            stop_mission()
            system_off()

    # ==========================
    # MISSION COMMAND
    # ==========================
    elif msg.topic == CMD_TOPIC:
        cmd_type = data.get("type")

        if cmd_type == "start":
            cycle_id = data.get("cycle_id")
            print(f"[MISSION] START ({cycle_id})")
            start_mission(cycle_id)

        elif cmd_type == "pause":
            print("[MISSION] PAUSE")
            stop_mission()
            # ❗ system_off() 절대 호출하지 않음


def start_mqtt_loop():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_forever()
