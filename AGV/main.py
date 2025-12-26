# main.py
import threading
import time
from mqtt_listener import start_mqtt_loop

def main():
    print("AGV BOOTING...")

    mqtt_thread = threading.Thread(
        target=start_mqtt_loop,
        daemon=True
    )
    mqtt_thread.start()

    print("MQTT listener running")

    # 프로세스 유지용 루프
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("AGV SHUTDOWN")

if __name__ == "__main__":
    main()
