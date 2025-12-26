import json
import os
from fastapi import APIRouter, HTTPException
import paho.mqtt.client as mqtt

from services.agv_service import fetch_task_list, is_agv_running

router = APIRouter(prefix="/agv", tags=["AGV Command (MQTT)"])

MQTT_HOST = os.getenv("MQTT_HOST", "172.20.10.6")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

def mqtt_publish(topic: str, payload: dict, qos: int = 1):
    """
    MQTT PUB
    """
    try:
        client = mqtt.Client()
        client.connect(MQTT_HOST, MQTT_PORT)
        client.publish(topic, json.dumps(payload, ensure_ascii=False), qos=qos)
        client.disconnect()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MQTT publish failed: {e}")


@router.post("/publish_zone_actions")
def publish_zone_actions(agv_id: str, cycle_id: str):
    # STOP 상태면 publish X -> 무조건 START 해주고 하기!!
    if not is_agv_running(agv_id):
        return {"status": "ignored", "reason": "AGV STOPPED", "agv_id": agv_id}

    data = fetch_task_list(cycle_id)
    if data.get("status") != "ready":   # task_list가 아직 없다면
        return {
            "status": "pending",
            "cycle_id": cycle_id,
            "task_list": [],
            "topic": f"agv/{agv_id}/zone_action"
        }

    task_list = data.get("task_list", [])
    if not task_list:
        raise HTTPException(status_code=404, detail="task_list is empty")

    commands = []
    for t in task_list:
        zone = t.get("node")
        action = t.get("raw_action") or t.get("action")

        if not zone or not action:
            continue

        commands.append({"zone": zone, "action": action})

    if not commands:
        raise HTTPException(status_code=400, detail="no valid commands")

    topic = f"agv/{agv_id}/zone_action"
    payload = {"commands": commands}  # 명령 commands 배열 안에 넣어주기

    mqtt_publish(topic, payload, qos=1)

    return {"status": "sent", "topic": topic, "sent": len(commands), "payload": payload}