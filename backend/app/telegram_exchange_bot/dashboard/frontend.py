"""
Dashboard Frontend Server - Sprint 7C
FastAPI + Jinja2 para servir dashboard HTML.
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

# Router para frontend
frontend_router = APIRouter(prefix="/exchange", tags=["Exchange Frontend"])

# Templates
TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@frontend_router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """
    Página principal del dashboard.
    """
    return templates.TemplateResponse("dashboard.html", {"request": request})
