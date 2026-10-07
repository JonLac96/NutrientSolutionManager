# Nutrient Solution Manager

Der Nutrient Solution Manager pflegt Stammdaten von Pflanzen, Düngern und Tanks, erfasst Messwerte und führt Regelvorgänge für EC, Volumen und pH.

Die technische Festlegung steht in [`docs/pflichtenheft.md`](docs/pflichtenheft.md), die schrittweise Abarbeitung in [`docs/umsetzungsplan.md`](docs/umsetzungsplan.md).

## Voraussetzungen

- Python 3.13
- [uv](https://docs.astral.sh/uv/)

## Einrichtung und Start

```powershell
uv sync
uv run alembic upgrade head
uv run fastapi dev app/main.py
```

Die API-Dokumentation liegt unter `/docs` und ist bis Meilenstein M6 die Bedienoberfläche.

## Tests und Prüfung

```powershell
uv run ruff format --check .
uv run ruff check .
uv run mypy app
uv run pytest
```

## Architektur

Die API importiert Models nur als Typannotationen von Rückgabewerten. Fachentscheidungen bleiben im Service.
