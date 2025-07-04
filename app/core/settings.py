import os
from pydantic import BaseModel 


class Settings(BaseModel):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "qwerty")
    ALGORITHM: str = "HS256"
    JWT_EXPIRY: int = 60 * 24
    TIER_CONFIG: dict = {
        "free": {
            "allowed_indicators": ["sma", "ema"],
            "max_months": 3,
            "limit": 50,
        },
        "pro": {
            "allowed_indicators": ["sma", "ema", "rsi", "macd"],
            "max_months": 12,
            "limit": 500,
        },
        "premium": {
            "allowed_indicators": ["sma", "ema", "rsi", "macd", "bollinger"],
            "max_months": 36,
            "limit": float("inf"),
        },
    }

settings = Settings()
