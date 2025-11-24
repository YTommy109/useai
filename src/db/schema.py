from sqlalchemy import create_mock_engine
from sqlmodel import SQLModel
from src.db.models import Country, Regulation  # Import all models here

def dump_ddl(url):
    def dump(sql, *multiparams, **params):
        print(str(sql.compile(dialect=engine.dialect)).replace("\t", "").replace("\n", ""), end=";\n")

    engine = create_mock_engine(url, dump)
    SQLModel.metadata.create_all(engine, checkfirst=False)

if __name__ == "__main__":
    dump_ddl("sqlite://")
