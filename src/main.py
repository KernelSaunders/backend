from fastapi import FastAPI

from .routers import products_router

app = FastAPI()

app.include_router(products_router)
