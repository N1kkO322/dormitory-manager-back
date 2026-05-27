from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db
from .api import auth, news, machines, duties, users  

app = FastAPI(
    title="DorMan API",
    description="API для управления студенческим общежитием",
    version="1.0.0",
)

@app.on_event("startup")
async def startup_event():
    init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173",
    "http://localhost:3000",
    "https://x2zg0xzj-8000.euw.devtunnels.ms",
    "https://x2zg0xzj-5173.euw.devtunnels.ms" ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(news.router)
app.include_router(machines.router)
app.include_router(duties.router)
app.include_router(users.router) 

@app.get("/")
async def root():
    return {"message": "DorMan API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}