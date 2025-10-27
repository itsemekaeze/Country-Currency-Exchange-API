from fastapi import FastAPI
from src.entities import currency_exchanger
from src.database.core import engine
from src.Currency_converter.controller import router as country_router

currency_exchanger.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Welcome to FastAPI"}


app.include_router(country_router)
