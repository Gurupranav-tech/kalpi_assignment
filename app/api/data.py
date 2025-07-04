from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.core import auth
from app.core.cache import get_cached, set_cached
from app.core.limiter import limiter
from app.core.settings import settings
from app.db import db_session
from app.services import indicators
from . import router


@router.get(
    "/indicators/{symbol}",
    summary="Get indicators data for a symbol",
    description="""
    Fetches OHLC data for a given symbol within a specified date range and computes the requested technical indicator.
Supports SMA, EMA, RSI, MACD, and Bollinger Bands depending on your API tier.
Results are cached in Redis for fast repeated queries.
Fresh data can be fetched on each call by negating the cache parameter.
    """,
    tags=["indicators"]
)
async def get_indicators(
    symbol: str,
    indicator_name: str,
    start: str,
    end: str,
    window: int,
    request: Request,
    fast_period: Optional[int] = None,
    slow_period: Optional[int] = None,
    signal_period: Optional[int] = None,
    cache: Optional[bool] = True,
    indicators: indicators.Indicators = Depends(lambda : indicators.Indicators("./stocks_ohlc_data.parquet")),
    session: Session = Depends(db_session)
):
    """
    Get the user and subscription tier associated with the token from the database
    """
    user = await auth.get_user(request, session)
    tier = settings.TIER_CONFIG[user.tier]
    auth_header = request.headers.get("Authorization")

    if indicator_name not in tier["allowed_indicators"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your tier does not have access to the field")

    """
    Use cached data for performance. Cache is stored in redis.
    Cache is not used if the user wants freshly computed value everytime
    """
    cache_key = f"{symbol}:{start}:{end}:{tier}:{window}"
    cached_data = await get_cached(cache_key)
    if cache and cached_data:
        # Rate Limiter
        allowed, remaining = await limiter(auth_header, user.tier)
        if not allowed:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded. Upgrade your tier or try tomorrow.")

        cached_data["remaining_queries"] = remaining
        return cached_data

    if not tier:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Tier Configuration")

    """
    Filter the dataframe based on the start and end date only if allowed by the tier and then compute the indicator value
    """
    df = indicators.filter(start, end, symbol, user.tier)

    if indicator_name == "sma":
        df = indicators.compute_sma(df, window)
    elif indicator_name == "ema":
        df = indicators.compute_ema(df, window)
    elif indicator_name == "rsi":
        df = indicators.compute_rsi(df, window)
    elif indicator_name == "macd":
        if not fast_period or not slow_period or not signal_period:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Arguments missing")
        df = indicators.compute_macd(df, fast_period, slow_period, signal_period)
    elif indicator_name == "bollinger":
        df = indicators.compute_bollinger_bands(df, window)

    data = { "data": df  }
    for row in data["data"]:
        for key, value in row.items():
            if isinstance(value, datetime):
                row[key] = value.strftime("%Y-%m-%d")
    """
    Since python datetimes are not serializable to JSON we convert datetime to string before we cache it in redis.
    This is little inefficient from my point of view on a very large dataset.
    TODO: Maybe implement a custom JSON serializer or store dates in polars in such a way that it is JSON serializable
    """
    await set_cached(cache_key, data)
    # Rate Limiter
    allowed, remaining = await limiter(auth_header, user.tier)
    if not allowed:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded. Upgrade your tier or try tomorrow.")

    data["remaining_queries"] = remaining

    return data
