from fastapi import FastAPI
from api.routers import agv
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Smart Farm AGV Observation API")

# 라우터 등록
app.include_router(agv.router)

@app.get("/")
def read_root():
    return {"message": "AGV API Server is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)