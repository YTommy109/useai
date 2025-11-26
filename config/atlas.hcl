data "external_schema" "sqlmodel" {
  program = [
    "sh",
    "-c",
    "export PYTHONPATH=$PYTHONPATH:. && uv run src/db/schema.py"
  ]
}

env "local" {
  src = data.external_schema.sqlmodel.url
  url = "sqlite://../data/app.db"
  dev = "sqlite://file?mode=memory"
}
