from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.api.routers.user import router as user_router
from app.models.base import Base 
from app.db.session import engine


# Lifespan
@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)

# Routers
app.include_router(user_router)

# CORS

