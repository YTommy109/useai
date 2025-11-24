from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.engine import init_db, get_session
from src.db.repository import CountryRepository, RegulationRepository

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)

templates = Jinja2Templates(directory="src/templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(
    request: Request, session: AsyncSession = Depends(get_session)
):
    country_repo = CountryRepository(session)
    regulation_repo = RegulationRepository(session)

    countries = await country_repo.get_all_names()
    regulations = await regulation_repo.get_all_names()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"countries": countries, "regulations": regulations},
    )

@app.post("/selected", response_class=HTMLResponse)
async def selected_countries(request: Request, countries: list[str] = Form(default=[])):
    return templates.TemplateResponse(
        request=request,
        name="selected_items.html",
        context={"items": countries},
    )

@app.post("/selected_regulations", response_class=HTMLResponse)
async def selected_regulations(
    request: Request, regulations: list[str] = Form(default=[])
):
    return templates.TemplateResponse(
        request=request,
        name="selected_items.html",
        context={"items": regulations},
    )
