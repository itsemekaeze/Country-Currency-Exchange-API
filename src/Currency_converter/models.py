from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone


class CreateCountryRequest(BaseModel):
    name: str
    population: int
    currency_code: str


class CreateCountryResponse(CreateCountryRequest):
    model_config = ConfigDict(
       
        json_encoders={
            datetime: lambda v: v.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        }
    )
     
    id: int
    capital: str
    region: str
    exchange_rate: float
    estimated_gdp: float
    flag_url: str
    last_refreshed_at:datetime =  Field(default_factory=lambda: datetime.now(timezone.utc))


class CountrieStatus(BaseModel):
    model_config = ConfigDict(
       
        json_encoders={
            datetime: lambda v: v.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        }
    )
    
    total_countries: int
    last_refreshed_at: datetime =  Field(default_factory=lambda: datetime.now(timezone.utc))
