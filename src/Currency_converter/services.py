import requests
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from .models import CreateCountryRequest
from src.entities.currency_exchanger import CurrencyExchanger
from datetime import datetime, timezone
from random import randrange
from typing import Optional
from sqlalchemy import asc, desc, func
from dotenv import load_dotenv
import os
from pathlib import Path


load_dotenv()

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)
IMAGE_PATH = CACHE_DIR / "summary.png"


def create_country_exchanger(country_request: CreateCountryRequest, db: Session):
    
    if not country_request.currency_code or country_request.currency_code.strip() == "":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                             detail=f"Currency code is required")
    elif not country_request.name or country_request.name.strip() == "":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                             detail=f"Country name is required")
    elif country_request.population <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                             detail=f"Population is required")
    try:
        
        countries_response = requests.get(
            os.getenv("COUNTRIES_RESPONSE"),
            timeout=10
        )
        countries = countries_response.json()
        
        exchange_response = requests.get(
            os.getenv("EXCHANGE_RESPONSE"),
            timeout=10
        )
        exchange_data = exchange_response.json()
        exchange_rates = exchange_data['rates']
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching external data: {str(e)}"
        )
    
    matching_country = None
    for country in countries:
        if 'currencies' in country and country['currencies']:
            currency_code = country['currencies'][0]['code']
            
            if (currency_code == country_request.currency_code or 
                country['name'].lower() == country_request.name.lower()):
                matching_country = country
                break
    
    if not matching_country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Country with code '{country_request.currency_code}' or name '{country_request.name}' not found"
        )
    
    code = matching_country['currencies'][0]['code']
    existing = db.query(CurrencyExchanger).filter(
        CurrencyExchanger.currency_code == code
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Country with currency code '{currency_code}' already exists"
        )
    
   
    country_exchange_rate = exchange_rates.get(code, 1.0)
    
    
    population = matching_country.get('population', 0)
    estimated_gdp = (population * randrange(1000, 2000)) / country_exchange_rate if country_exchange_rate > 0 else 0
    
   
    new_country = CurrencyExchanger(
        name=matching_country['name'],
        capital=matching_country.get('capital', 'N/A'),
        region=matching_country.get('region', 'Unknown'),
        population=population,
        currency_code=currency_code,
        exchange_rate=country_exchange_rate,
        estimated_gdp=estimated_gdp,
        flag_url=matching_country.get('flag', ''),
        last_refreshed_at=datetime.now(timezone.utc),
    )
    
    db.add(new_country)
    db.commit()
    db.refresh(new_country)
    
    return new_country


def get_all_country(db: Session, region: Optional[str] = None,
    currency: Optional[str] = None,
    sort: Optional[str] = None):

    data = db.query(CurrencyExchanger)
    
    if region:
        query = data.filter(CurrencyExchanger.region.ilike(f"%{region}%"))
    
    if currency:
        query = data.filter(CurrencyExchanger.currency_code == currency.upper())
 
    if sort:
        sort_lower = sort.lower()
        
        if sort_lower == "gdp_desc":
            query = data.order_by(desc(CurrencyExchanger.estimated_gdp))
        elif sort_lower == "gdp_asc":
            query = data.order_by(asc(CurrencyExchanger.estimated_gdp))
        elif sort_lower == "population_desc":
            query = data.order_by(desc(CurrencyExchanger.population))
        elif sort_lower == "population_asc":
            query = data.order_by(asc(CurrencyExchanger.population))
        elif sort_lower == "name_asc":
            query = data.order_by(asc(CurrencyExchanger.name))
        elif sort_lower == "name_desc":
            query = data.order_by(desc(CurrencyExchanger.name))
        else:
            query = data.order_by(asc(CurrencyExchanger.name))
    else:
        query = data.order_by(asc(CurrencyExchanger.name))
 
    return query.all()


def get_country_by_name(country_name: str, db: Session):
    data = db.query(CurrencyExchanger).filter(func.lower(CurrencyExchanger.name) == country_name.lower()).first()

    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail=f"Country name {country_name} does not exist")
    return data


def delete_country_by_name(country_name: str, db: Session):
    data = db.query(CurrencyExchanger).filter(func.lower(CurrencyExchanger.name) == country_name.lower())

    data_query = data.first()
    if data_query == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail=f"Country name {country_name} does not exist")
    
    data.delete(synchronize_session=False)

    db.commit()

    return data_query


def check_country_status(db: Session):

    data = db.query(CurrencyExchanger).count()

    return data
    

def bulk_refresh_countries(db: Session):
        
    try:
        countries_response = requests.get(
            os.getenv("COUNTRIES_RESPONSE"),
            timeout=10
        )
        countries = countries_response.json()
        
        exchange_response = requests.get(
            os.getenv("EXCHANGE_RESPONSE"),
            timeout=10
        )
        exchange_data = exchange_response.json()
        exchange_rates = exchange_data['rates']
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching external data: {str(e)}"
        )
    
    created_countries = []
    updated_countries = []
    skipped_countries = []
    refresh_timestamp = datetime.now(timezone.utc)
    
    for country in countries:
        try:
            country_name = country.get('name', '')
            if not country_name:
                skipped_countries.append('Unknown')
                continue
            
            population = country.get('population', 0)
            if not population or population <= 0:
                skipped_countries.append(country_name)
                continue
            
            
            currency_code = None
            exchange_rate = None
            estimated_gdp = 0
            
            
            if not ('currencies' in country and country['currencies'] and len(country['currencies']) > 0):
                skipped_countries.append(f"{country_name} (no currency)")
                continue
            
            currency_code = country['currencies'][0].get('code', '')
            
            
            if not currency_code or currency_code.strip() == "":
                skipped_countries.append(f"{country_name} (no currency code)")
                continue 
            
            exchange_rate = exchange_rates.get(currency_code)            
           
            if exchange_rate is None:
                skipped_countries.append(f"{country_name} (currency {currency_code} not in exchange API)")
                continue
            
            if exchange_rate is None:
                estimated_gdp = None
            else:
                estimated_gdp = (population * randrange(1000, 2000)) / exchange_rate if exchange_rate > 0 else 0
            
            
                          
            new_country = CurrencyExchanger(
                name=country_name,
                capital=country.get('capital', 'N/A'),
                region=country.get('region', 'Unknown'),
                population=population,
                currency_code=currency_code,
                exchange_rate=exchange_rate,
                estimated_gdp=estimated_gdp,
                flag_url=country.get('flag', ''),
                last_refreshed_at=refresh_timestamp,
            )
            
            db.add(new_country)
            created_countries.append(country_name)
            
        except Exception as e:
            print(f"Error processing country {country.get('name', 'Unknown')}: {e}")
            skipped_countries.append(country.get('name', 'Unknown'))
            continue
    
    db.commit()
    

    try:
        generate_summary_image(db, refresh_timestamp)
        print("Summary image generated successfully")
    except Exception as e:
        print(f"Error generating image: {e}")
    
    return {
        "created": len(created_countries),
        "updated": len(updated_countries),
        "skipped": len(skipped_countries),
        "created_countries": created_countries[:10],
        "updated_countries": updated_countries[:10],
        "skipped_countries": skipped_countries,
        "message": f"Successfully created {len(created_countries)} and updated {len(updated_countries)} countries. Skipped {len(skipped_countries)} countries without currencies. Image generated."
    }


def generate_summary_image(db: Session, refresh_timestamp: datetime):
    
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("PIL/Pillow not installed. Run: pip install Pillow")
        return
    
    
    total_countries = db.query(CurrencyExchanger).count()
    
    
    top_5 = db.query(CurrencyExchanger).filter(
        CurrencyExchanger.estimated_gdp.isnot(None)
    ).order_by(desc(CurrencyExchanger.estimated_gdp)).limit(5).all()
    
    
    width = 800
    height = 500
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
   
    try:
        title_font = ImageFont.truetype("arial.ttf", 32)
        heading_font = ImageFont.truetype("arial.ttf", 24)
        text_font = ImageFont.truetype("arial.ttf", 18)
    except:
        title_font = ImageFont.load_default()
        heading_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
    
    
    draw.text((50, 30), "Country API Summary", fill='black', font=title_font)
    
    
    draw.text((50, 90), f"Total Countries In DB: {total_countries}", fill='blue', font=heading_font)
    
    
    draw.text((50, 140), "Top 5 Countries by Estimated GDP (USD):", fill='blue', font=heading_font)
    
    y_position = 180
    for idx, country in enumerate(top_5, 1):
        gdp_formatted = f"{country.estimated_gdp:,.0f}" if country.estimated_gdp else "N/A"
        text = f"{idx}. {country.name}: ${gdp_formatted}"
        draw.text((70, y_position), text, fill='black', font=text_font)
        y_position += 30
    
    
    timestamp_str = refresh_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')
    draw.text((50, height - 60), f"Last Refreshed: {timestamp_str}", fill='gray', font=text_font)
    
    
    img.save(IMAGE_PATH)
    print(f"Summary image saved to {IMAGE_PATH}")


def get_summary_image_path():
    if IMAGE_PATH.exists():
        return IMAGE_PATH
    return None
