from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone
from typing import Optional


class CreateCountryResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        }
    )
     
    id: int
    name: str
    capital: str
    region: str
    population: int
    currency_code: Optional[str]
    exchange_rate: Optional[float]
    estimated_gdp: Optional[float]
    flag_url: str
    last_refreshed_at: datetime


class CountrieStatus(BaseModel):
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.astimezone(timezone.utc).isoformat().replace("+00:00", "Z") if v else None
        }
    )
    
    total_countries: int
    last_refreshed_at: Optional[datetime]