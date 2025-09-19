# backend/app/main.py


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.api import api_router


app = FastAPI(
    title="Hypertube API",
    description="API for the Hypertube project",
    version="0.1.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://imontero.ddns.net:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)


# Include the main router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Welcome to Hypertube API!"}

@app.get("/ping")
async def ping():
    return {"status": "ok", "message": "pong"}


# If this file is run directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
