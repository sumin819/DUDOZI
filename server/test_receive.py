import requests

cycle_id = "2025_12_17_1936"
url = f"http://127.0.0.1:8000/agv/get_task_list?cycle_id={cycle_id}"

res = requests.get(url, timeout=10)
print(res.status_code)
print(res.json())
