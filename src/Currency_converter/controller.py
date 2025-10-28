from fastapi import APIRouter, status, Depends, Query, Response, HTTPException
from .models import CreateCountryRequest, CreateCountryResponse, CountrieStatus
from src.database.core import get_db
from sqlalchemy.orm import Session
from .services import get_all_country, get_country_by_name, delete_country_by_name, check_country_status, get_summary_image_path, bulk_refresh_countries
from typing import List, Optional
from datetime import datetime
from fastapi.responses import FileResponse

router = APIRouter(
    prefix="/countries",
    tags=["Currency Exchanger"]
)
    

@router.post("/refresh", status_code=status.HTTP_200_OK)
def refresh_all_countries(db: Session = Depends(get_db)):
    conreq = bulk_refresh_countries(db)
    return conreq

@router.get("/", response_model=List[CreateCountryResponse])
def get_all_country_exchanger_from_db(db: Session = Depends(get_db),
    region: Optional[str] = Query(None),
    currency: Optional[str] = Query(None),
    sort: Optional[str] = Query(None)):

    conreq = get_all_country(db, region=region, currency=currency, sort=sort)

    return conreq

@router.get("/image")
def get_summary_image():
    image_path = get_summary_image_path()
    
    if image_path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Summary image not found"}
        )
    
    return FileResponse(
        image_path,
        media_type="image/png",
        filename="summary.png"
    )

@router.get("/status", response_model=CountrieStatus)
def check_country_status_from_db(db: Session = Depends(get_db)):
    conreq = check_country_status(db=db)

    
    return conreq


@router.get("/{country_name}", response_model=CreateCountryResponse)
def get_country_name_from_db(country_name: str, db: Session = Depends(get_db)):
    conreq = get_country_by_name(country_name=country_name, db=db)

    return conreq

@router.delete("/{country_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_country_name_from_db(country_name: str, db: Session = Depends(get_db)):
    conreq = delete_country_by_name(country_name=country_name, db=db)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


