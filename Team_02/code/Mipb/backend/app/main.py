
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db.init_db import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Init DB
    try:
        init_db()
    except Exception as e:
        print(f"DB Init failed (might be expected if DB not ready): {e}")
    yield

from app.routers import process, auth
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="MPP Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(process.router, prefix="/api/process", tags=["process"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])

@app.get("/")
def read_root():
    return {"message": "MPP Backend is online"}
