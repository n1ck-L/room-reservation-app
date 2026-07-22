from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routers.room import router as room_router
from app.api.routers.user import router as user_router
from app.api.routers.reservation import router as reservation_router
from app.api.routers.auth import router as auth_router
from app.db.session import SessionLocal, engine
from app.models.base import Base
from app.services.user import UserService


# Lifespan
@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        UserService(db).ensure_default_admin()
    finally:
        db.close()

    yield


app = FastAPI(lifespan=lifespan)

# Routers
app.include_router(user_router)
app.include_router(room_router)
app.include_router(reservation_router)
app.include_router(auth_router)
