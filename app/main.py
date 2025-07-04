from fastapi import FastAPI
from app.api import router
from app.db.user import Base
from app.db import engine


app = FastAPI(
    title="Stock Analysis Data - Kalpi Assignment",
    description="API for fast tier based stock analysis data using polars and redis caching",
    version="1.0.0"
)
Base.metadata.create_all(bind=engine)
app.include_router(router, prefix="/api")

@app.get("/")
def home():
    return "Kalpi Assignment"
