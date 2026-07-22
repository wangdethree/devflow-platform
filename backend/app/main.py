from fastapi import FastAPI


app = FastAPI(
    title="DevFlow Platform",
    description="Enterprise Development Collaboration Platform",
    version="0.1.0",
)


@app.get("/")
async def root():
    return {
        "message": "DevFlow API is running"
    }