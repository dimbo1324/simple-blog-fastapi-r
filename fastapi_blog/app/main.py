from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from database import Base, engine
from exceptions import general_http_exception_handler, validation_exception_handler
from routers.api import users as api_users
from routers.api import posts as api_posts
from routers.views import posts as view_posts
from routers.views import users as view_users


@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")

# Routers
app.include_router(api_users.router)
app.include_router(api_posts.router)
app.include_router(view_posts.router)
app.include_router(view_users.router)

# Exception handlers
app.add_exception_handler(StarletteHTTPException, general_http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
