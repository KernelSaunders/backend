from fastapi import FastAPI

from src.routers import products_router

app = FastAPI()

app.include_router(products_router)
