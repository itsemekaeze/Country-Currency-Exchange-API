import requests
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
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


def get_all_country(db: Session, region: Optional[str] = None,
    currency: Optional[str] = None,
    sort: Optional[str] = None):
    """Get all countries with optional filtering and sorting"""
    
    query = db.query(CurrencyExchanger)
    
    if region:
        query = query.filter(CurrencyExchanger.region.ilike(f"%{region}%"))
    
    if currency:
        query = query.filter(CurrencyExchanger.currency_code == currency.upper())
 
    if sort:
        sort_lower = sort.lower()
        
        if sort_lower == "gdp_desc":
            query = query.order_by(desc(CurrencyExchanger.estimated_gdp))
        elif sort_lower == "gdp_asc":
            query = query.order_by(asc(CurrencyExchanger.estimated_gdp))
        elif sort_lower == "population_desc":
            query = query.order_by(desc(CurrencyExchanger.population))
        elif sort_lower == "population_asc":
            query = query.order_by(asc(CurrencyExchanger.population))
        elif sort_lower == "name_asc":
            query = query.order_by(asc(CurrencyExchanger.name))
        elif sort_lower == "name_desc":
            query = query.order_by(desc(CurrencyExchanger.name))
        else:
            query = query.order_by(asc(CurrencyExchanger.name))
    else:
        query = query.order_by(asc(CurrencyExchanger.name))
 
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

    total_countries = db.query(CurrencyExchanger).count()
    
    last_refresh = db.query(func.max(CurrencyExchanger.last_refreshed_at)).scalar()
    
    return {
        "total_countries": total_countries,
        "last_refreshed_at": last_refresh
    }
    

def bulk_refresh_countries(db: Session):
    
    try:
        countries_response = requests.get(
            os.getenv("COUNTRIES_RESPONSE"),
            timeout=10
        )
        countries_response.raise_for_status()
        countries = countries_response.json()
        
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "External data source unavailable",
                "details": "Could not fetch data from restcountries.com - request timed out"
            }
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "External data source unavailable",
                "details": f"Could not fetch data from restcountries.com - {str(e)}"
            }
        )
    
    try:
        exchange_response = requests.get(
            os.getenv("EXCHANGE_RESPONSE"),
            timeout=10
        )
        exchange_response.raise_for_status()
        exchange_data = exchange_response.json()
        exchange_rates = exchange_data['rates']
        
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "External data source unavailable",
                "details": "Could not fetch data from open.er-api.com - request timed out"
            }
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "External data source unavailable",
                "details": f"Could not fetch data from open.er-api.com - {str(e)}"
            }
        )
    
    created_countries = []
    updated_countries = []
    skipped_countries = []
    refresh_timestamp = datetime.now(timezone.utc)
    
    for country in countries:
        try:
            country_name = country.get('name', '')
            if not country_name:
                skipped_countries.append('Unknown - no name')
                continue
            
            population = country.get('population', 0)
            if not population or population <= 0:
                skipped_countries.append(f"{country_name} - invalid population")
                continue
            
            
            currency_code = None
            exchange_rate = None
            estimated_gdp = 0.0
            
            
            if 'currencies' in country and country['currencies'] and len(country['currencies']) > 0:
                currency_code = country['currencies'][0].get('code', '').strip()
                
                if currency_code:
                    
                    exchange_rate = exchange_rates.get(currency_code)
                    
                    
                    if exchange_rate and exchange_rate > 0:
                        estimated_gdp = (population * randrange(1000, 2001)) / exchange_rate
                    else:
                        
                        exchange_rate = None
                        estimated_gdp = 0.0
            
            
            if not currency_code:
                currency_code = None
                exchange_rate = None
                estimated_gdp = 0.0
            
            
            existing = db.query(CurrencyExchanger).filter(
                func.lower(CurrencyExchanger.name) == country_name.lower()
            ).first()
            
            if existing:
                
                existing.capital = country.get('capital', 'N/A')
                existing.region = country.get('region', 'Unknown')
                existing.population = population
                existing.currency_code = currency_code
                existing.exchange_rate = exchange_rate
                existing.estimated_gdp = estimated_gdp
                existing.flag_url = country.get('flag', '')
                existing.last_refreshed_at = refresh_timestamp
                
                updated_countries.append(country_name)
            else:
                
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
            skipped_countries.append(f"{country.get('name', 'Unknown')} - processing error")
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
        "created_countries": created_countries[:10] if len(created_countries) <= 10 else created_countries[:10],
        "updated_countries": updated_countries[:10] if len(updated_countries) <= 10 else updated_countries[:10],
        "skipped_countries": skipped_countries[:10] if len(skipped_countries) <= 10 else skipped_countries[:10],
        "message": f"Successfully created {len(created_countries)} and updated {len(updated_countries)} countries. Skipped {len(skipped_countries)} countries."
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
    
    # Create image
    width = 800
    height = 500
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    try:
        title_font = ImageFont.truetype("arial.ttf", 32)
        heading_font = ImageFont.truetype("arial.ttf", 24)
        text_font = ImageFont.truetype("arial.ttf", 18)
    except:
        title_font = ImageFont.load_default()
        heading_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
    
    # Draw title
    draw.text((50, 30), "Country API Summary", fill='black', font=title_font)
    
    # Draw total countries
    draw.text((50, 90), f"Total Countries: {total_countries}", fill='blue', font=heading_font)
    
    # Draw top 5 header
    draw.text((50, 140), "Top 5 Countries by Estimated GDP:", fill='blue', font=heading_font)
    
    # Draw top 5 countries
    y_position = 180
    for idx, country in enumerate(top_5, 1):
        gdp_formatted = f"{country.estimated_gdp:,.0f}" if country.estimated_gdp else "N/A"
        text = f"{idx}. {country.name}: ${gdp_formatted}"
        draw.text((70, y_position), text, fill='black', font=text_font)
        y_position += 30
    
    # Draw timestamp
    timestamp_str = refresh_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')
    draw.text((50, height - 60), f"Last Refreshed: {timestamp_str}", fill='gray', font=text_font)
    
    # Save image
    img.save(IMAGE_PATH)
    print(f"Summary image saved to {IMAGE_PATH}")


def get_summary_image_path():

    if IMAGE_PATH.exists():
        return IMAGE_PATH
    return None