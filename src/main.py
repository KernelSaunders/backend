from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import get_client
from .routers import missions_router, products_router, users_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_client()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products_router)
app.include_router(missions_router)
app.include_router(users_router)
