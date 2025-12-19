import requests

cycle_id = "2025_12_16_1350"
url = f"http://172.20.10.9:8000/agv/get_task_list?cycle_id={cycle_id}"

res = requests.get(url, timeout=10)
print(res.status_code)
print(res.json())
