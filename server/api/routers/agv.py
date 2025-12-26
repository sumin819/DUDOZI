import json
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from services.agv_service import upload_and_analyze_observations, fetch_task_list, set_agv_run_state, get_agv_run_state, is_agv_running, get_image_signed_url, fetch_agv_observations, get_latest_cycle_id, save_task_result_to_firestore
from datetime import datetime
from .agv_cmd import mqtt_publish
router = APIRouter(prefix="/agv", tags=["AGV Management"])

# =================================
# 시스템 on off 
# =================================
@router.post("/run")
def set_run_state(agv_id: str, running: bool):
    """
    SYSTEM ON / OFF 제어 (카메라, 스트림)
    """
    # 1️⃣ 서버 내부 상태 저장
    result = set_agv_run_state(agv_id, running)

    # 2️⃣ MQTT publish
    topic = f"agv/{agv_id}/run"
    payload = {
        "agv_id": agv_id,
        "running": running
    }

    mqtt_publish(topic, payload, qos=1)

    return {
        "status": "sent",
        "agv_id": agv_id,
        "running": running,
        "topic": topic
    }


@router.get("/run")
def get_run_state(agv_id: str):
    return get_agv_run_state(agv_id)

# ===============================
# agv 움직익 하기 
# ===============================
@router.post("/manual_move")
def manual_move(cmd: dict):
    agv_id = cmd.get("agv_id")
    direction = cmd.get("direction")

    if not is_agv_running(agv_id):
        return {
            "status": "ignored",
            "reason": "AGV STOPPED"
        }

    # 🚧 지금은 MQTT 대신 로그만
    print(f"[MQTT MOCK] agv={agv_id}, MOVE={direction}")
    # mqtt.publish(f"agv/{agv_id}/cmd", {...})

    return {
        "status": "sent",
        "direction": direction
    }


# ===============================
# 요청 스키마 정의
# ===============================
class YoloIn(BaseModel):
    result: Literal["normal", "abnormal", "unknown"]
    confidence: float = Field(ge=0.0, le=1.0)

class ObservationIn(BaseModel):
    node: str
    image_url: Optional[str] = ""
    yolo: YoloIn

class UploadObservationRequest(BaseModel):
    cycle_id: str
    agv_id: str
    timestamp: str        
    observations: List[ObservationIn]

class ReportTaskResultIn(BaseModel):
    cycle_id: str
    result: Literal["success", "fail"]

@router.post("/upload_observation")
async def upload_observation(
    payload: str = Form(...),
    images: List[UploadFile] = File(...)
):
    try:
        payload_dict = json.loads(payload)
        req = UploadObservationRequest(**payload_dict)
        
        if len(images) != len(req.observations):
            raise HTTPException(status_code=400, detail="이미지 개수와 관찰 데이터 수가 일치하지 않습니다.")
            
        return await upload_and_analyze_observations(req, images)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get_task_list")
def get_task_list(cycle_id: str):
    return fetch_task_list(cycle_id)

@router.get("/latest_cycle")
def get_latest_cycle():
    """
    가장 최근에 정찰을 수행한 Cycle ID를 가져옵니다.
    """
    cycle_id = get_latest_cycle_id()
    if not cycle_id:
        raise HTTPException(status_code=404, detail="최근 정찰 기록이 없습니다.")
    return {"cycle_id": cycle_id}

@router.get("/get_image_url")
def get_image_url(cycle_id: str, node: str):
    """
    클라이언트에서 이미지 로드를 위해 호출하는 API
    """
    url = get_image_signed_url(cycle_id, node)
    if not url:
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다.")
    return {"image_url": url}


@router.get("/get_agv_data")
def get_agv_data(cycle_id: str = None):
    """
    최신 또는 특정 사이클의 AGV 관찰 데이터를 가져오는 API
    """
    # cycle_id가 인자로 오지 않으면 최신 ID를 자동으로 찾음
    target_id = cycle_id if cycle_id else get_latest_cycle_id()
    
    if not target_id:
        raise HTTPException(status_code=404, detail="최신 사이클 ID를 찾을 수 없습니다.")
        
    data = fetch_agv_observations(target_id)
    if not data:
        raise HTTPException(status_code=404, detail="해당 사이클의 AGV 데이터를 찾을 수 없습니다.")
        
    return data

@router.post("/report_task_result")
def report_task_result(body: ReportTaskResultIn):
    """
    AGV -> 서버 완료 작업 보고 수신
    """
    try:
        return save_task_result_to_firestore(body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===============================
# AGV 사이클 제어
# ===============================
class MissionRequest(BaseModel):
    cycle_id: str
    agv_id: str
    timestamp: str
    
@router.post("/start")
def start_agv(agv_id: str = "AGV1"):
    cycle_id = datetime.now().strftime("%Y_%m_%d_%H%M")

    topic = f"agv/{agv_id}/cmd"
    payload = {
        "type": "start",
        "cycle_id": cycle_id
    }

    mqtt_publish(topic, payload, qos=1)

    return {
        "status": "sent",
        "agv_id": agv_id,
        "cycle_id": cycle_id,
        "topic": topic
    }

@router.post("/pause")
def pause_mission(agv_id: str = "AGV1"):

    topic = f"agv/{agv_id}/cmd"
    payload = {
        "type": "pause"
    }

    mqtt_publish(topic, payload, qos=1)

    return {
        "status": "sent",
        "agv_id": agv_id,
        "topic": topic
    }
