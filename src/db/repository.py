from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.models import Country, Regulation

class CountryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_names(self) -> list[str]:
        result = await self.session.exec(select(Country))
        return [c.name for c in result.all()]

class RegulationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_names(self) -> list[str]:
        result = await self.session.exec(select(Regulation))
        return [r.name for r in result.all()]
