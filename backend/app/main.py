from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def home():
    return {"message": "5G AI Smart Campus backend is running!"}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "5G AI Smart Campus backend"
    }