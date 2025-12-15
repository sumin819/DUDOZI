from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from firestore.client import get_db, init_firebase
import json

from firebase_admin import storage

app = FastAPI(title="AGV Observation API")  # 서버 생성

YoloLabel = Literal["normal", "abnormal", "unknown"]

class YoloIn(BaseModel):
    result: YoloLabel
    confidence: float = Field(ge=0.0, le=1.0)

class ObservationIn(BaseModel):
    node: str
    image_url: Optional[str] = ""   # 서버가 업로드 후 채워넣을 예정
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

        for i, img in enumerate(images):
            node = req.observations[i].node
            filename = img.filename or f"{node}.jpg"

            # Storage 경로
            path = f"images/cycles/{req.cycle_id}/{filename}"

            blob = bucket.blob(path)
            blob.upload_from_file(img.file, content_type=img.content_type)

            # url 생성
            req.observations[i].image_url = blob.public_url

        agv_doc = {
            "cycle_id": req.cycle_id,
            "agv_id": req.agv_id,
            "timestamp": req.timestamp,
            "observations": [o.model_dump() for o in req.observations],
        }

        db = get_db()
        db.collection("cycles").document(req.cycle_id).set(
            {"agv": agv_doc},
            merge=True
        )

        return {
            "status": "ok",
            "cycle_id": req.cycle_id,
            "uploaded": [
                {"node": o.node, "image_url": o.image_url}
                for o in req.observations
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))