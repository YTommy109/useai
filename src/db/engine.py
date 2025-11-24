from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker

from src.db.models import Country, Regulation

DATABASE_URL = "sqlite+aiosqlite:///./db/app.db"

engine = create_async_engine(DATABASE_URL, echo=True)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

import csv
from pathlib import Path

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with async_session() as session:
        # Check if countries exist
        result = await session.exec(select(Country))
        countries = result.all()
        if not countries:
            csv_path = Path("config/countries.csv")
            if csv_path.exists():
                with open(csv_path, mode="r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        session.add(Country(name=row["name"]))
        
        # Check if regulations exist
        result = await session.exec(select(Regulation))
        regulations = result.all()
        if not regulations:
            csv_path = Path("config/regulations.csv")
            if csv_path.exists():
                with open(csv_path, mode="r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        session.add(Regulation(name=row["name"]))
        
        await session.commit()

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
