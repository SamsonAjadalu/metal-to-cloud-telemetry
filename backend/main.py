from fastapi import FastAPI

app = FastAPI(title="Fleet Telemetry API")

@app.get("/")
def read_root():
    return {"status": "Backend is running and ready for WebSockets."}