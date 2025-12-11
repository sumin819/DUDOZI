from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "DU-DO-ZI FastAPI Server Running!"}
