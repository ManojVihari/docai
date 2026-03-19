from fastapi import FastAPI
from app.api.routes import router
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="DocAI Server")

app.include_router(router)
templates = Jinja2Templates(directory="app/ui/templates")
app.mount("/static", StaticFiles(directory="app/ui/static"), name="static")