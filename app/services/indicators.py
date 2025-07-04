import polars as pl
from datetime import datetime, timedelta
from fastapi import HTTPException, status

from app.core.settings import settings


class Indicators:
    def __init__(self, filename: str = ""):
        self.lazy_df = pl.scan_parquet(filename)

    def filter(self, start: str, end: str, symbol: str, tier: str) -> pl.LazyFrame:
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d")
        max_delta = timedelta(days=settings.TIER_CONFIG[tier]["max_months"] * 30)
        if end_dt - start_dt > max_delta:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Date range exceeds your tier limit ({settings.TIER_CONFIG[tier]['max_months']} months).")
        
        return self.lazy_df.filter(
            (pl.col("symbol") == symbol) &
            (pl.col("date") >= start_dt) &
            (pl.col("date") <= end_dt)
        )

    def compute_sma(self, df: pl.LazyFrame, window: int):
        return df.with_columns(
            pl.col("close").rolling_mean(window_size=window).alias(f"sma_{window}")
        ).sort("date").collect().to_dicts()

    def compute_ema(self, df: pl.LazyFrame, window: int):
        return df.with_columns(
            pl.col("close").ewm_mean(span=window).alias(f"ema_{window}")
        ).sort("date").collect().to_dicts()

    def compute_rsi(self, df: pl.LazyFrame, window: int):
        close = pl.col("close")
        delta = close.diff()

        gain = pl.when(delta > 0).then(delta).otherwise(0)
        loss = pl.when(delta < 0).then(-delta).otherwise(0)
    
        avg_gain = gain.ewm_mean(alpha=1/window, adjust=False)
        avg_loss = loss.ewm_mean(alpha=1/window, adjust=False)
    
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
    
        rsi = rsi.fill_nan(100)
        rsi = rsi.fill_null(100)    

        return df.with_columns(rsi.alias(f"rsi_{window}")).sort("date").collect().to_dicts()

    def compute_macd(self, df: pl.LazyFrame, fast_period: int, slow_period: int, signal_period: int):
        ema_fast = pl.col("close").ewm_mean(span=fast_period)
        ema_slow = pl.col("close").ewm_mean(span=slow_period)
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm_mean(span=signal_period)
        return df.with_columns([
            macd_line.alias("macd_line"),
            signal_line.alias("signal_line")
        ]).sort("date").collect().to_dicts()

    def compute_bollinger_bands(self, df: pl.LazyFrame, window: int, num_std: float = 2.0):
        sma = pl.col("close").rolling_mean(window_size=window)
        std = pl.col("close").rolling_std(window_size=window)
        upper = sma + num_std * std
        lower = sma - num_std * std
        return df.with_columns([
            upper.alias("upper_band"),
            lower.alias("lower_band")
        ]).sort("date").collect().to_dicts()
