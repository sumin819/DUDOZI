from dotenv import load_dotenv
load_dotenv()

from datetime import timedelta
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from firestore.client import get_db, init_firebase
import json

from firebase_admin import storage

from llm.client import call_gpt41_mini
from llm.prompt import SYSTEM_PROMPT
from llm.schemas import LLMResponse

app = FastAPI(title="AGV Observation API")  # 서버 생성

YoloLabel = Literal["normal", "abnormal", "unknown"]

class YoloIn(BaseModel):
    result: YoloLabel
    confidence: float = Field(ge=0.0, le=1.0)

class ObservationIn(BaseModel):
    node: str
    image_url: Optional[str] = ""   # public_url 저장
    yolo: YoloIn

class UploadObservationRequest(BaseModel):  # JSON 형식 검사 
    cycle_id: str
    agv_id: str
    timestamp: str        
    observations: List[ObservationIn]

@app.post("/agv/upload_observation")
async def upload_observation(
    payload: str = Form(...),             # JSON
    images: List[UploadFile] = File(...)  # 이미지
):
    try:
        init_firebase()

        payload_dict = json.loads(payload)
        req = UploadObservationRequest(**payload_dict)  # JSON 형식 검사

        if len(images) != len(req.observations):    # 이미지 개수와 observation 수가 같은지 확인
            raise HTTPException(
                status_code=400,
                detail=f"images({len(images)}) != observations({len(req.observations)})"
            )

        # storage 업로드
        bucket = storage.bucket()
        signed_url_map = {} # LLM용 signed_url

        for i, img in enumerate(images):
            node = req.observations[i].node
            filename = img.filename or f"{node}.jpg"

            # Storage 경로
            path = f"images/cycles/{req.cycle_id}/{filename}"

            blob = bucket.blob(path)
            blob.upload_from_file(img.file, content_type=img.content_type)

            # Firebase용 url
            req.observations[i].image_url = blob.public_url
            
            # LLM용 url -> 이거 있어야 권한 문제 해결
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

        # Firestore 정찰 결과 저장
        db = get_db()
        db.collection("cycles").document(req.cycle_id).set(
            {"agv": agv_doc},
            merge=True
        )

        # LLM 호출 및 검증
        llm_previews = []

        for obs in agv_doc["observations"]:
            payload_for_llm = {
                "cycle_id": req.cycle_id,
                "node": obs["node"],
                "image_url": obs["image_url"],
                "detection_result": obs["yolo"]["result"],
                "confidence": obs["yolo"]["confidence"],
                "prompt": "이 식물의 상태를 분석하고 필요한 조치를 추천해줘.",
                "metadata": {
                    "agv_id": req.agv_id,
                    "timestamp": req.timestamp,
                    "position": obs["node"],
                }
            }

            user_text = json.dumps(payload_for_llm, ensure_ascii=False)
            image_url = signed_url_map[obs["node"]]

            llm_text = call_gpt41_mini(
                SYSTEM_PROMPT,
                user_text,
                image_url
            )

            # JSON 올바른지 검증
            validated = LLMResponse(**json.loads(llm_text))

            llm_previews.append(validated.model_dump())

        
        return {
            "status": "ok",
            "cycle_id": req.cycle_id,
            "uploaded": [
                {"node": o.node, "image_url": o.image_url}
                for o in req.observations
            ],
            "llm_preview": llm_previews
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))