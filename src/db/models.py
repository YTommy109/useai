from sqlmodel import Field, SQLModel

class Country(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str

class Regulation(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
