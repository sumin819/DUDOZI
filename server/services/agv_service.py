import json
from datetime import timedelta
from typing import List
from fastapi import UploadFile, HTTPException
from firebase_admin import storage
from firestore.client import get_db, init_firebase
from llm.client import call_gpt41_mini
from llm.prompt import SYSTEM_PROMPT
from llm.schemas import LLMResponse

async def upload_and_analyze_observations(req, images: List[UploadFile]):
    init_firebase()
    bucket = storage.bucket()
    signed_url_map = {}

    # 1. Storage 업로드 및 Signed URL 생성
    for i, img in enumerate(images):
        node = req.observations[i].node
        filename = img.filename or f"{node}.jpg"
        path = f"images/cycles/{req.cycle_id}/{filename}"

        blob = bucket.blob(path)
        blob.upload_from_file(img.file, content_type=img.content_type)
        
        req.observations[i].image_url = blob.public_url
        signed_url_map[node] = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=10),
            method="GET",
        )

    agv_doc = {
        "cycle_id": req.cycle_id,
        "agv_id": req.agv_id,
        "timestamp": req.timestamp,
        "observations": [o.model_dump() for o in req.observations],
    }

    # 2. Firestore 저장
    db = get_db()
    db.collection("cycles").document(req.cycle_id).set({"agv": agv_doc}, merge=True)

    # 3. LLM 분석 수행
    llm_previews = []
    for obs in agv_doc["observations"]:
        payload_for_llm = {
            "cycle_id": req.cycle_id,
            "node": obs["node"],
            "image_url": obs["image_url"],
            "detection_result": obs["yolo"]["result"],
            "confidence": obs["yolo"]["confidence"],
            "prompt": "이 식물의 상태를 분석하고 필요한 조치를 추천해줘.",
            "metadata": {"agv_id": req.agv_id, "timestamp": req.timestamp, "position": obs["node"]}
        }

        llm_text = call_gpt41_mini(SYSTEM_PROMPT, json.dumps(payload_for_llm, ensure_ascii=False), signed_url_map[obs["node"]])
        validated = LLMResponse(**json.loads(llm_text))
        llm_previews.append(validated.model_dump())

    # 4. 분석 결과(Task List) 요약 및 저장
    task_list = []
    summary_list = {}
    for one in llm_previews:
        task_list.extend(one["task_list"])
        node = one["task_list"][0]["node"]
        summary_list[node] = one["summary_report"]

    db.collection("cycles").document(req.cycle_id).set({"llm": {"task_list": task_list, "summary": summary_list}}, merge=True)
    
    return {
        "status": "ok",
        "cycle_id": req.cycle_id,
        "uploaded": [{"node": o.node, "image_url": o.image_url} for o in req.observations],
        "llm_preview": llm_previews
    }


def get_latest_cycle_id():
    """
    Firestore에서 가장 최근 생성된 cycle_id를 조회합니다.
    """
    init_firebase()
    db = get_db()
    
    # timestamp 필드를 기준으로 내림차순 정렬하여 가장 최근 문서 1개 조회
    docs = db.collection("cycles").order_by("agv.timestamp", direction="DESCENDING").limit(1).get()
    
    for doc in docs:
        return doc.id
    
    return None

def fetch_task_list(cycle_id: str):
    db = get_db()
    snap = db.collection("cycles").document(cycle_id).get()
    
    if not snap.exists:
        raise HTTPException(status_code=404, detail="cycle_id not found")
    
    data = snap.to_dict()
    llm_data = data.get("llm", {})
    
    if not llm_data or "task_list" not in llm_data:
        return {"cycle_id": cycle_id, "status": "pending", "task_list": [], "summary": {}}

    # === 데이터 정제 로직 추가 ===
    refined_tasks = []
    for task in llm_data.get("task_list", []):
        # 영문 액션을 한국어로 매핑
        action_map = {
            "supply_fertilizer": "일반 비료 공급 (영양 관리)",
            "spray": "치료제 살포 (병해충 관리)"
        }
        
        refined_tasks.append({
            "node": task.get("node"),
            "action": action_map.get(task.get("action"), "점검 필요"),
            "reason": task.get("reason"),
            "raw_action": task.get("action") # 로봇 제어용 원본 데이터도 유지
        })

    return {
        "cycle_id": cycle_id,
        "status": "ready",
        "task_list": refined_tasks,  # 정제된 한글 데이터
        "summary": llm_data.get("summary", {})
    }

def fetch_agv_observations(cycle_id: str):
    try:
        init_firebase()
        db = get_db()
        # 'cycles' 컬렉션에서 데이터 로드
        doc = db.collection("cycles").document(cycle_id).get()

        if not doc.exists: return None
        data = doc.to_dict().get("agv", {})
        observations = data.get("observations", [])

        # 🔥 핵심: 모든 관찰 데이터의 URL을 Signed URL로 교체합니다.
        for obs in observations:
            signed_link = get_image_signed_url(cycle_id, obs.get("node"))
            if signed_link:
                obs["image_url"] = signed_link 

        return {
            "agv_id": data.get("agv_id"),
            "cycle_id": data.get("cycle_id"),
            "timestamp": data.get("timestamp"),
            "observations": observations
        }
    except Exception as e:
        print(f"Error fetching observations: {e}")
        return None

def get_image_signed_url(cycle_id: str, node: str):
    """
    특정 cycle과 node에 해당하는 이미지의 10분간 유효한 Signed URL을 생성합니다.
    """
    try:
        init_firebase()
        bucket = storage.bucket()
        # 업로드 시 저장했던 경로 규칙과 일치해야 합니다: images/cycles/{cycle_id}/{node}.jpg
        blob = bucket.blob(f"images/cycles/{cycle_id}/{node}.jpg")
        
        if not blob.exists():
            return None

        # 클라이언트에서 접근 가능한 임시 URL 생성
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=10),
            method="GET",
        )
        return url
    except Exception as e:
        print(f"이미지 URL 생성 실패: {e}")
        return None

# =========================
# Mock AGV Power State
# =========================
_AGV_RUNTIME_STATE = {
    # "AGV-1": False  # False = STOP, True = START
}

def set_agv_run_state(agv_id: str, running: bool):
    _AGV_RUNTIME_STATE[agv_id] = running
    return {
        "agv_id": agv_id,
        "running": running
    }

def get_agv_run_state(agv_id: str):
    return {
        "agv_id": agv_id,
        "running": _AGV_RUNTIME_STATE.get(agv_id, False)
    }

# =========================
# agv 움직이게 하기
# =========================
_AGV_RUNTIME_STATE = {}

def is_agv_running(agv_id: str) -> bool:
    return _AGV_RUNTIME_STATE.get(agv_id, False)

def set_agv_run_state(agv_id: str, running: bool):
    _AGV_RUNTIME_STATE[agv_id] = running
    return {"agv_id": agv_id, "running": running}