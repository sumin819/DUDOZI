# api/analysis.py
import requests

SERVER_URL = "http://127.0.0.1:8000"

def get_latest_cycle_id():
    """서버에서 가장 최근의 cycle_id를 가져옴"""
    try:
        url = f"{SERVER_URL}/agv/latest_cycle"
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        return res.json().get("cycle_id")
    except Exception as e:
        print(f"최신 Cycle ID 조회 실패: {e}")
        return None

def fetch_task_list(cycle_id: str):
    """서버에서 LLM task_list 및 summary 조회"""
    url = f"{SERVER_URL}/agv/get_task_list?cycle_id={cycle_id}"
    res = requests.get(url, timeout=10)
    res.raise_for_status()
    return res.json()
