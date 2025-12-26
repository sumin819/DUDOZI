import requests

# SERVER_URL = "http://127.0.0.1:8000"
SERVER_URL = "http://172.20.10.6:8888"

AGV_ID = "AGV1"

def on_toggle_system(self):
    will_run = self.ui.toggleSystem.isChecked()

    try:
        res = requests.post(
            f"{SERVER_URL}/agv/run",
            params={
                "agv_id": AGV_ID,
                "running": will_run
            },
            timeout=2
        )

        running = res.json().get("running", False)

        if running:
            self.enter_running_state()
        else:
            self.enter_stopped_state()

    except Exception as e:
        print("Server error:", e)
        self.ui.toggleSystem.setChecked(not will_run)


def send_agv_start(agv_id):
    try:
        res = requests.post(
            f"{SERVER_URL}/agv/start",
            params={"agv_id": agv_id},
            timeout=3
        )
        return res.status_code == 200
    except Exception:
        print("[ERROR] Failed to send START")
        return False


def send_agv_pause(agv_id):
    try:
        res = requests.post(
            f"{SERVER_URL}/agv/pause",
            params={"agv_id": agv_id},
            timeout=3
        )
        return res.status_code == 200
    except Exception:
        print("[ERROR] Pause request failed")
        return False
