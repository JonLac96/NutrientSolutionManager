# Nutrient Solution Manager

Der Nutrient Solution Manager pflegt Stammdaten von Pflanzen, Düngern und Tanks, erfasst Messwerte und führt Regelvorgänge für EC, Volumen und pH.

Die technische Festlegung steht in [`docs/pflichtenheft.md`](docs/pflichtenheft.md), die schrittweise Abarbeitung in [`docs/umsetzungsplan.md`](docs/umsetzungsplan.md).

Die Anwendung ist noch nicht angelegt. Die folgenden Befehle stammen aus Kapitel 14.1 des Pflichtenhefts und werden mit Schritt 1.8 lauffähig:

```powershell
uv sync
uv run alembic upgrade head
uv run python -m tools.seed        # optional, Beispieldaten
uv run fastapi dev app/main.py
```

Danach liegt die API-Dokumentation unter dem Pfad `/docs` der laufenden Anwendung und bleibt bis Meilenstein M6 die Bedienoberfläche.
