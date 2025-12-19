# api/history.py
import requests

SERVER_URL = "http://127.0.0.1:8000"

def fetch_agv_history(cycle_id: str = None):
    """
    서버의 /agv/get_agv_data API 호출
    """
    try:
        res = requests.get(
            f"{SERVER_URL}/agv/get_agv_data",
            params={"cycle_id": cycle_id} if cycle_id else {},
            timeout=5
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("fetch_agv_history failed:", e)
        return None
