from fastapi import FastAPI

app = FastAPI(title="NeuroApp Backend", description="Importance Scoring Engine API")

@app.get("/health")
def health_check():
    return {"status": "ok"}
