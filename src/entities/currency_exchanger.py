from src.database.core import Base
from sqlalchemy import Column, Integer, String, Float, TIMESTAMP
from sqlalchemy.sql.expression import text



class CurrencyExchanger(Base):
    __tablename__ = 'currency_exchanger'

    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    capital = Column(String, nullable=False)
    region = Column(String, nullable=False)
    population = Column(Integer, nullable=False)
    currency_code = Column(String, nullable=True)
    exchange_rate = Column(Float, nullable=True)
    estimated_gdp = Column(Float, nullable=False, default=0.0)
    flag_url = Column(String, nullable=True)
    last_refreshed_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False)