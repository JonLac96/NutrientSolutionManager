# Umsetzungsplan – Nutrient Solution Manager

Stand: 2026-10-06. Grundlage ist [`pflichtenheft.md`](pflichtenheft.md) (Entwurf vom 2026-10-05, Kapitel 1 bis 19). Beide Dokumente liegen in `docs/`.
Das Paketgerüst aus Schritt 1.1 steht. Vom Altprojekt wird kein Code übernommen.

Dieser Plan zerlegt die Meilensteine M1 bis M9 in Schritte, die nacheinander abgearbeitet werden.
Ein Schritt ist fertig, wenn seine eigenen Tests grün sind und die Werkzeugkette nichts meldet.
Erst dann beginnt der nächste Schritt.

**Nächster Schritt: 1.2**

---

## So wird dieser Plan abgearbeitet

1. Oben den nächsten offenen Schritt nehmen. Die Statuszeile des Schritts auf `in Arbeit` setzen.
2. Nur diesen Schritt umsetzen. Dateien und Verhalten stehen im Schritt, die fachlichen Details im verwiesenen Kapitel des Pflichtenhefts.
3. Am Ende jedes Schritts ausführen:
   `uv run ruff format --check .`
   `uv run ruff check .`
   `uv run mypy app`
   `uv run pytest`
4. Die genannten Abnahmekriterien gegen das Pflichtenheft Kapitel 16 prüfen.
5. Die Statuszeile auf `erledigt` setzen und oben den nächsten Schritt eintragen.

Ein Schritt ist ein sinnvoller Commit, sobald ein Commit gewünscht ist. Bis dahin bleibt die Änderung im Arbeitsbaum.

`projektkonzept.md` liegt in diesem Repository nicht. M1 hängt nicht daran. O-8 (Konzept kürzen) bleibt liegen, bis die Datei vorhanden ist.

---

## Leitlinien, die bei jedem Schritt gelten

Diese Punkte stehen im Pflichtenheft, gehen aber leicht unter, wenn ein Schritt nur seine eigene Tabelle im Blick hat.

- Schichten aus Kapitel 5.1 einhalten. Berechnungen sind reine Funktionen auf Dataclasses. Services werfen Fachfehler und kennen kein FastAPI. Router enthalten keine Fachlogik.
- Jeder Schreibweg läuft durch ein Pydantic-Schema. Aufzählungen sind `StrEnum` in `app/enums/` und in der Datenbank `String(30)`, nie SQLAlchemy-`Enum`.
- Zeitstempel laufen über `UtcDateTime`. Die aktuelle Zeit kommt nur aus `utcnow()`.
- Services für HTTP-CRUD schreiben `commit` selbst (C-6). Ein Job läuft in genau einer Transaktion des Dispatchers. Schlägt er fehl, entstehen auch seine Folgejobs nicht. Der Status `failed` wird danach in einer zweiten Transaktion geschrieben (Kapitel 10.2). Job-Handler rufen deshalb keine Service-Methoden auf, die selbst committen. Gemeinsame Prüfungen liegen in Funktionen, die nur die Session benutzen und nichts festschreiben.
- Teilaktualisierungen: der Service legt die gesendeten Felder auf das geladene Objekt und prüft das Ergebnis am vollständigen Schema (Kapitel 7.3).
- `IntegrityError` aus Eindeutigkeit und `RESTRICT` wird an einer Stelle auf `ConflictError` (409) abgebildet, mit benannten Constraints.
- Gleitkomma in Berechnungen nicht zwischendurch runden. Gerundet wird bei der Ausgabe auf eine Dezimalstelle in Millilitern. Tests vergleichen mit `pytest.approx`.
- Testdatenbanken sind SQLite im Arbeitsspeicher, eine pro Test, mit `StaticPool`, `foreign_keys=ON` und überschriebenem `get_session`. Kein Test verwendet `nsm.db` oder fest verdrahtete Ids.
- Kein SQLite-SQL außer den beiden Pragmas im Connect-Listener. Die Datenbank-URL kommt aus der Konfiguration.
- Im gesamten System läuft höchstens ein Job gleichzeitig. Pro Tank höchstens ein Zyklus im Zustand `running`.

---

## Entscheidungen, die das Pflichtenheft der Umsetzung überlässt

| Thema | Festlegung für die Umsetzung |
|---|---|
| Anwendungsfabrik | `create_app()` in `app/main.py`, dazu `app = create_app()` für `fastapi dev`. Tests bauen die App selbst und hängen die Abhängigkeiten dort um. |
| Uhr | `utcnow()` liest eine austauschbare Uhr in `app/core/time.py`. Tests stellen die Uhr vor, statt `datetime.now()` zu streuen. Das ist die Voraussetzung für Simulationsstufe 2. |
| Leere Datenbank in M1 | Die erste Alembic-Revision hat noch keine Fachtabelle. Der Starttest prüft, dass `upgrade head` durchläuft, die Revisionszeile steht und `GET /health` danach 200 liefert. |
| Nachweis für `NotFoundError` in M1 | Der Test hängt eine Route nur für diesen Test an die App. In der Anwendung gibt es dafür keinen Platzhalter-Endpunkt. |
| pH-Mittel auswählen | `CompensationPH` sucht Mittel nach Richtung. Genau eines wird verwendet. Keines oder mehrere: der Job endet als `failed` mit einer klaren Meldung. Eine Geräte- oder Tankzuordnung kommt erst, wenn O-9 das verlangt. |
| Volumen über dem Ziel | Die Bewertung weist es aus. Einen Job gibt es dafür nicht. Ablassen ist nicht modelliert. Handlungsbedarf besteht bei Volumen unter dem Ziel. |
| Eingabe beendet den Job | `POST /jobs/{id}/input` schließt den wartenden Job ab und reiht nichts zusätzlich ein. Der nächste Job startet über `POST /jobs/dispatch`. Einzige Ausnahme ist der Zyklusstart: der legt `MeasureProbe` und `CompareProbe` an und führt `MeasureProbe` sofort aus. |
| Weboberfläche (O-5) | Annahme bis zur ausdrücklichen anderen Entscheidung: serverseitige Vorlagen mit Jinja2 und HTMX, ausgeliefert vom selben FastAPI-Prozess. Diagramme über eine kleine Bibliothek ohne eigenen Build. Begründung: ein Betreiber, eine Auslieferung, ein Prozess auf SQLite. Vor Schritt 6.1 kurz bestätigen. |
| Wasserwechsel (O-6) | Annahme: nur Hinweis, kein Blockieren des Zyklus. Vor Schritt 7.4 kurz bestätigen. |
| Sicherheitsgrenzen im Seed (O-2) | Platzhalter, keine Empfehlung für einen echten Tank: Ziel 30 l, Maximum 40 l, `source_water_ec` 0,3, Stabilisierung 120 s, Wasser 20 l, Dünger 500 ml, pH-Mittel 50 ml, 3 Versuche, Zyklusdauer 1440 min. |
| Dosierreihenfolge (O-1) | Der Seed legt A, B, C mit `dose_order` 0, 1, 2 an. Eine chemische Reihenfolge ist damit nicht entschieden. |
| Lizenz | Keine Lizenzdatei anlegen, solange keine genannt ist. |
| CI auf ARM64 | Öffentliches Repository: `test-arm64` bei jedem Push. Privates Repository: `test-arm64` nur auf `main`, `test-x64` bei jedem Push. |
| Startmedium am Pi | Bis M7 die SD-Karte im Pi. USB-SSD erst zum Dauerbetrieb. Einkauf und Preisgrenze stehen in [`hardware.md`](hardware.md). |

Offen bleiben und den Start nicht aufhalten: O-3 (Stilllegen statt Löschen, vor M4 entscheiden), O-7, O-9, O-10, O-11 (alle vor M9). O-4 ist entschieden: die tatsächlich dosierte Menge ist Pflicht und mit der Empfehlung vorbelegt.

---

## Phasenüberblick

| Phase | Meilenstein | Schritte | Ergebnis |
|---|---|---|---|
| 0 | Vorbereitung | 0.1 | Repository entspricht Kapitel 19, noch ohne Fachcode |
| 1 | M1 Fundament | 1.1–1.8 | Laufende App, Tests, Lint, Typprüfung, CI |
| 2 | M2 Stammdaten | 2.1–2.9 | Sieben Ressourcen, Seed, Löschregeln |
| 3 | M3 Jobliste und EC | 3.1–3.12 | Advisory-Zyklus bis der EC im Bereich liegt |
| 4 | M4 Volumen und pH | 4.1–4.6 | Vollständige Rangfolge und Grenzen S-1 bis S-5 |
| 5 | M5 Simulation | 5.1–5.5 | Modus `simulation`, Zustände und Fristen aus 9.7 |
| 6 | M6 Weboberfläche | 6.1–6.5 | Bedienung ohne `/docs` |
| 7 | M7 Scheduler | 7.1–7.4 | Zeitpläne in Ortszeit, Dienstbetrieb |
| 8 | M8 Container | 8.1–8.2 | Image, Volume, Start auf dem Pi vorbereitet |
| 9 | M9 Hardware | 9.1–9.5 | MQTT, Attrappe, danach erst echte Pumpen |

Kapitel 17 wird nicht eingeplant.

---

## Phase 0 – Repository vorbereiten

### Schritt 0.1 – Grundlagen laut Kapitel 19

Status: erledigt

Ziel: ein sauberer Ausgangspunkt, bevor Fachcode entsteht.

Umsetzen:

- `README.md` mit Zweck in wenigen Sätzen und den Befehlen aus Kapitel 14.1. Die Befehle dürfen noch als „ab Schritt 1.8 lauffähig“ gekennzeichnet sein, bis M1 steht; am Ende von Schritt 1.8 den Hinweis entfernen.
- `AGENTS.md` ersetzen beziehungsweise anlegen: der Agent implementiert und erklärt nur auf Nachfrage (Kapitel 2.4). Keine Mentorenrolle, kein Lernpfad.
- `.gitignore` für `.env`, `.venv`, `nsm.db`, `nsm.db-wal`, `nsm.db-shm`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, Coverage-Dateien.
- `.gitattributes` mit `* text=auto eol=lf` und `*.ps1 text eol=crlf`.
- `.env.example` mit den fünf Variablen aus Kapitel 10.4.
- `pflichtenheft.md` nach `docs/pflichtenheft.md` verschieben. Diesen Plan nach `docs/umsetzungsplan.md` verschieben. Verweise in beiden Dateien auf den neuen Ort prüfen.

Fertig, wenn die Dateien am beschriebenen Ort liegen und kein Fachpaket existiert.

Bezug: Kapitel 19, 13.3, 10.4.

---

## Phase 1 – M1 Fundament

Reihenfolge innerhalb der Phase ist verbindlich: Uhr und Datenbank vor der App, Test-Fixture bevor Endpunkte getestet werden, Alembic bevor der Start die Datenbank selbst migriert.

### Schritt 1.1 – Werkzeugkette und Paketgerüst

Status: erledigt

Ziel: `uv sync` erzeugt eine Umgebung, in der die späteren Prüfbefehle überhaupt starten.

Umsetzen:

- `pyproject.toml`, Paketname passend zum Repository, `requires-python = ">=3.13"`.
- Laufzeit: FastAPI, Uvicorn, SQLAlchemy 2, Alembic, Pydantic v2, pydantic-settings.
- Entwicklung: pytest, pytest-cov, httpx, ruff, mypy.
- Ruff: Formatierung, Linten, Regel `DTZ` (verbotenes naives `datetime.now()`), später `TID251`. Zunächst die DTZ-Regel aktivieren.
- mypy im Strict-Modus für `app`.
- pytest mit `testpaths = ["tests"]` und Coverage-Schwelle 80 Prozent für das Gesamtprojekt. Schwellen für `app/calculations` (100 Prozent) sowie `app/services` und `app/jobs` (90 Prozent Zweigabdeckung) erst aktivieren, wenn diese Pakete existieren, sonst schlägt die Konfiguration fehl, bevor es etwas zu messen gibt. In diesem Schritt die Gesamt-Schwelle so setzen, dass sie mit dem jeweils vorhandenen, getesteten Code besteht; ab Schritt 1.8 gilt die Gesamt-Schwelle verbindlich.
- Verzeichnisse aus Kapitel 11.1 anlegen, jeweils mit `__init__.py`, noch ohne Fachmodule: `app/api/routers`, `app/core`, `app/models`, `app/schemas`, `app/services`, `app/calculations`, `app/jobs/types`, `app/devices`, `app/enums`, `tests/unit`, `tests/integration`, `tests/api`, `tests/factories`, `tools`, `alembic`.
- `uv lock` erzeugen.

Fertig, wenn `uv sync` durchläuft und `uv run ruff check .`, `uv run mypy app` sowie `uv run pytest` ohne Fehlermeldung enden.

Bezug: Kapitel 4.1, 11.1, 13.1.

### Schritt 1.2 – Konfiguration

Status: offen

Ziel: alle Umgebungswerte an einer Stelle, mit den Standards aus Kapitel 10.4.

Umsetzen:

- `app/core/config.py` mit pydantic-settings, Präfix `NSM_`.
- Felder: `database_url`, `log_level`, `default_stabilization_seconds`, `default_max_correction_attempts`, `default_max_cycle_duration_minutes`.
- Eine Funktion `get_settings()`, die Tests überschreiben können.

Fertig, wenn ein Test die Standards und das Überschreiben über Umgebungsvariablen belegt.

Bezug: Kapitel 10.4.

### Schritt 1.3 – Uhr und Zeitstempel

Status: offen

Ziel: jeder gespeicherte Zeitpunkt kommt zeitzonenbehaftet in UTC zurück und ist mit `utcnow()` vergleichbar.

Umsetzen:

- `app/core/time.py`: `utcnow()` über eine austauschbare Uhr. Hilfsfunktion, mit der Tests die Uhr festsetzen und wieder lösen.
- `app/core/types.py`: `UtcDateTime` genau nach Kapitel 11.3. Naive Werte beim Schreiben ablehnen.
- `app/models/base.py`: gemeinsame Basisklasse mit `id`, `created_at`, `updated_at`. Defaults und `onupdate` rufen `utcnow()` auf, nicht die Datenbankuhr.

Fertig, wenn die Tests zu AK-1.8 grün sind: Schreiben und Lesen, Ablehnung eines naiven Werts, Vergleich mit `utcnow()`.

Bezug: Kapitel 11.3, AK-1.8. Der Test darf dafür eine nur im Test existierende Tabelle auf der Test-Engine anlegen. Das ist noch keine Fachtabelle der Anwendung.

### Schritt 1.4 – Engine, Pragmas, Session

Status: offen

Ziel: jede Verbindung prüft Fremdschlüssel und schreibt im WAL-Modus.

Umsetzen:

- `app/core/database.py`: Engine aus `settings.database_url`, `check_same_thread=False`, Connect-Listener mit `foreign_keys=ON` und `journal_mode=WAL`.
- `get_session()` als FastAPI-Dependency, eine Session pro Anfrage, geschlossen im `finally`.
- Die Anwendung öffnet neben dieser Dependency keine eigenen Sessions, außer später der Dispatcher und der Startvorgang.

Fertig, wenn ein Test zwei Tabellen mit Fremdschlüssel anlegt, eine fehlende Elternzeile einfügt und einen Integritätsfehler erhält (AK-1.3). Derselbe Listener wird in der Test-Engine verwendet.

Bezug: Kapitel 10.1, 10.2, AK-1.3.

### Schritt 1.5 – Testinfrastruktur

Status: offen

Ziel: die Regeln T-1 bis T-7 sind ab hier der einzige Weg, die Datenbank in Tests zu benutzen.

Umsetzen:

- `tests/conftest.py`: pro Test eine In-Memory-SQLite-Engine mit `StaticPool` und `check_same_thread=False`, `create_all`, am Ende verworfen.
- Fixture `session`.
- Fixture `client`: `TestClient`, `get_session` über `dependency_overrides` auf die Testsession, Override danach entfernt.
- Die Test-Engine setzt dieselben Pragmas wie die Anwendung.
- Factory-Paket `tests/factories/` vorerst leer, mit einem Modul-Docstring, der die Regel festhält: eine Factory legt ihre Voraussetzungen selbst an und gibt das Objekt zurück.

Fertig, wenn ein Test zeigt, dass nach dem Lauf die Datei `nsm.db` unverändert ist beziehungsweise nicht neu entsteht (AK-1.4), und dass zwei Tests nicht dieselbe Datenbank sehen.

Bezug: Kapitel 12.2, 12.3, AK-1.4.

### Schritt 1.6 – Fehlerklassen und einheitliches Fehlerformat

Status: offen

Ziel: Fachfehler werden an einer Stelle zu HTTP, Router brauchen kein `try/except`.

Umsetzen:

- `app/core/exceptions.py` mit `NsmError`, `NotFoundError` (404), `ConflictError` (409), `ValidationError` (422), `SafetyLimitExceeded` (409), `JobStateError` (409). Jede Klasse trägt `code`, `message` und optionale `details`.
- `app/api/errors.py` registriert die Handler. Aufbau der Antwort exakt nach Kapitel 9.6.
- Unbehandelte Ausnahmen bleiben 500 und verwenden dasselbe Format, ohne interne Details nach außen zu geben.
- Validierungsfehler von Request-Schemas (FastAPI/Pydantic, Status 422) auf dasselbe Format abbilden, `details` enthält die Feldliste.

Fertig, wenn ein Test eine nur im Test registrierte Route `NotFoundError` werfen lässt und 404 im Format aus 9.6 erhält, ohne dass die Route selbst fängt (AK-1.7). Ein zweiter Test prüft einen Pydantic-422 auf dasselbe Format, sobald die App existiert; wenn die App erst in 1.7 steht, diesen zweiten Test dort ergänzen.

Bezug: Kapitel 11.4, 9.5, 9.6, AK-1.7.

### Schritt 1.7 – Anwendung, Health, Version, Startreihenfolge

Status: offen

Ziel: die App startet, prüft die Datenbank und nennt Version und Startzeit.

Umsetzen:

- `app/main.py`: `create_app()`, Logging über `logging` mit Stufe aus der Konfiguration, keine `print`-Aufrufe.
- Lebenszyklus, in dieser Reihenfolge: Einstellungen laden, Startzeit merken, `alembic upgrade head` (der Aufruf wird in 1.8 real, hier die Stelle dafür vorsehen), danach `recover_interrupted_jobs()` als noch leere Funktion in `app/jobs/recovery.py`, danach Anfragen annehmen. Schlägt die Migration fehl, startet die App nicht.
- `GET /health`: führt `SELECT 1` aus. Datenbank nicht erreichbar: keine 200 (AK-1.9).
- `GET /version`: Version aus dem installierten Paket (`pyproject.toml`), aktuelle Alembic-Revision, `started_at` als UTC mit Zeitzone (AK-1.10).
- Strukturierte Protokollierung des Starts inklusive der Systemzeit (B-2). Die systemd-Abhängigkeit B-1 ist erst Schritt 7.4.

Fertig, wenn AK-1.2, AK-1.9 und AK-1.10 grün sind. AK-1.11 wird in 1.8 geschlossen, sobald die Migration wirklich läuft.

Bezug: Kapitel 9.0, 10.3, 13.4, AK-1.2, AK-1.9, AK-1.10.

### Schritt 1.8 – Alembic, Architekturregeln, CI, Abnahme M1

Status: offen

Ziel: M1 ist gegen AK-1.1 bis AK-1.11 geprüft, soweit die Prüfung nicht den Raspberry Pi oder ein einmaliges CI-Experiment braucht.

Umsetzen:

- Alembic mit `render_as_batch=True`. `env.py` importiert `app.models`, damit Autogenerate später alle Models sieht. `target_metadata` ist die Basisklasse.
- Erste Revision mit aussagekräftiger Meldung und funktionierendem `downgrade`, auch wenn sie noch keine Fachtabelle anlegt.
- Beim Start ruft die App die Alembic-API auf, nicht eine Shell.
- Test M-5 vorbereiten: Vergleich von Models und Migrationsstand. Solange es keine Fachtabelle gibt, prüft der Test, dass `upgrade head` und `downgrade base` auf einer Datei-Datenbank durchlaufen. Ab M2 vergleicht derselbe Test das erzeugte Schema mit den Models.
- Test AK-1.11: Start gegen eine Datenbank ohne Tabellen, danach `GET /health` mit 200.
- Ruff `TID251` für die harten Kanten:
  - `app/calculations` importiert weder `app.models`, `app.api`, `app.services` noch SQLAlchemy.
  - `app/services` importiert weder FastAPI noch Starlette.
  - `app/models` importiert weder `app.schemas` noch FastAPI.
  - `app/devices` wird von Services nicht konkret importiert; erlaubt ist `app.devices.protocols`. Die konkrete Regel wird scharf geschaltet, sobald `app/devices` mehr als ein leeres Paket ist (Schritt 5.1). Bis dahin die Verbote für calculations, services und models aktivieren.
- D-2 (API importiert Models nur als Rückgabetypen) im README-Abschnitt zur Architektur in einem Satz festhalten und in den Routern so umsetzen: Models dürfen in Annotationen stehen, Fachentscheidungen bleiben im Service.
- `.github/workflows/ci.yml` mit `test-x64` auf `ubuntu-latest` und `test-arm64` auf `ubuntu-24.04-arm`, Kette aus Kapitel 13.3. Sichtbarkeit des Repositorys prüfen und die ARM64-Regel aus der Entscheidungstabelle anwenden.
- `README.md` auf den tatsächlichen Stand bringen: Voraussetzungen (Python 3.13, uv), Einrichtung, Start, Tests, Hinweis dass `/docs` bis M6 die Oberfläche ist.
- Coverage-Schwelle 80 Prozent für das Gesamtprojekt aktiv lassen. Die Paket-Schwellen aus Kapitel 12.5 einschalten, sobald das jeweilige Paket echten Code enthält.

Fertig, wenn auf Windows `uv sync`, `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .` und `uv run mypy app` fehlerfrei sind.

Manuell und nicht Teil dieses Schritts:

- AK-1.1 auf Linux-x64 und Linux-ARM64 leistet die CI beim ersten Push.
- AK-1.1b einmal auf dem Raspberry Pi mit der Plattform aus Kapitel 14.3, am Ende von M1, nicht bei jedem Commit.
- AK-1.6 einmal auf einem Wegwerf-Branch einen Typfehler einbauen, sehen dass die CI rot wird, den Branch verwerfen. Erst möglich, wenn ein Remote existiert.

Bezug: Kapitel 10.3, 12.4, 13.2, 13.3, 14.1, AK-1.1 bis AK-1.11.

---

## Phase 2 – M2 Stammdaten

Jeder Ressourcen-Schritt ist ein vertikaler Schnitt: Model, eine Alembic-Revision, Schema, Service, Router, Factory, Tests. Die nächste Ressource beginnt erst, wenn dieser Schnitt grün ist.

Für alle sieben Ressourcen gilt das Muster aus Kapitel 9.1 und 11.2:

- `POST` 201, `GET` Liste, `GET` einzeln, `PUT` Teilaktualisierung, `DELETE` 204.
- `get` wirft `NotFoundError`. `list` liefert `Sequence`. Anlegen über `Model(**data.model_dump())`. Update über `exclude_unset=True`, danach Validierung am vollständigen Schema.
- Nach `commit` ein `refresh`, wenn die Antwort datenbankseitige Felder braucht.
- Router importiert den Service und gibt das Model zurück, `response_model` ist das Response-Schema. Kein eigenes `try/except`.
- Schema-Tests: ein gültiger Fall und je ein Fall pro Grenzverletzung, per `parametrize`.
- Service-Tests: create, get, list, Teil-Update, delete, get nach delete.
- API-Tests: Erfolg, 404, 422.

Listen der Stammdaten bleiben vollständig, ohne `limit`/`offset`. Das kommt in Phase 3.

### Schritt 2.1 – Gemeinsame Persistenzhilfen und Pflanze

Status: offen

Ziel: das CRUD-Muster existiert einmal in echter Form, an `Plant`, und Integritätsfehler werden zu 409.

Umsetzen:

- Eine kleine Hilfe, die `IntegrityError` anhand des Constraint-Namens in `ConflictError` übersetzt. Jeder Unique- und Fremdschlüssel-Constraint bekommt einen festen Namen.
- `Plant`: `name` nicht leer und eindeutig, `description` optional. Model, Revision, Schemas `PlantCreate`, `PlantUpdate`, `PlantResponse`, `PlantService`, Router `/plants`.
- Factory `make_plant`.

Fertig, wenn der Pflanzenschnitt die Pflichttests aus Kapitel 12.4 erfüllt und ein doppelter Name 409 liefert.

Bezug: Kapitel 6.1, 9.1, 11.2, 11.4.

### Schritt 2.2 – Wachstumsphase

Status: offen

Ziel: Sollwerte sind nur speicherbar, wenn Minimum, Ziel und Maximum in der richtigen Ordnung liegen, einschließlich der Gleichheit und einschließlich EC 0.

Umsetzen:

- Model `GrowthStage` mit `plant_id`, `name`, `sort_order`, den sechs Sollwerten. Eindeutigkeit von `sort_order` je Pflanze.
- `ondelete="RESTRICT"` von Pflanze zu Phase.
- Schema-Validatoren V-7 und V-8. Wertebereiche V-1 und V-2. `ec_min = 0` ist gültig.
- `GET /plants/{id}/growth-stages`, sortiert nach `sort_order`.
- Update-Pfad prüft die Drei-Felder-Regeln am zusammengeführten Objekt.
- Factory `make_growth_stage` legt die Pflanze selbst an.

Fertig, wenn AK-2.2 und AK-2.3 grün sind und eine Phase ohne passende Pflanze an der Datenbank scheitert.

Bezug: Kapitel 6.1, 7.2, 7.3, AK-2.2, AK-2.3.

### Schritt 2.3 – Dünger

Status: offen

Ziel: Dünger mit einer EC-Wirkung größer 0, Name eindeutig.

Umsetzen:

- Model, Revision, Schemas, Service, Router `/fertilizers`, Factory.
- `ec_effect_per_ml_per_liter` größer 0 (V-6). Wirkung 0 und negativ werden mit 422 abgelehnt.

Fertig, wenn der Pflichtschnitt für Schema, Service und API grün ist.

Bezug: Kapitel 6.1, V-6.

### Schritt 2.4 – Rezeptur

Status: offen

Ziel: eine Wachstumsphase hat höchstens eine Rezeptur, und die API sagt, ob die Anteile 100 ergeben.

Umsetzen:

- Model `Recipe` mit eindeutigem `growth_stage_id` und `name`. Löschen der Phase löscht die Rezeptur (`CASCADE`).
- `GET /growth-stages/{id}/recipe`, 404 wenn keine existiert.
- Response enthält `is_complete`. Ohne Bestandteile ist die Summe 0, also `is_complete = false`. Die Summenprüfung selbst kommt mit den Bestandteilen in 2.5; das Feld existiert ab hier und wird dort gespeist.
- Zweiter Versuch, eine Rezeptur für dieselbe Phase anzulegen: 409 (AK-2.4).

Fertig, wenn AK-2.4 grün ist.

Bezug: Kapitel 6.1, 7.4 V-10, 9.1, AK-2.4.

### Schritt 2.5 – Rezepturbestandteile

Status: offen

Ziel: Bestandteile lassen sich schrittweise speichern, die Vollständigkeit gilt für die Liste, und die Dosierreihenfolge ist lückenlos.

Umsetzen:

- Model `RecipeItem`: `recipe_id`, `fertilizer_id` eindeutig je Rezeptur, `percentage` größer 0 bis 100, `dose_order` eindeutig je Rezeptur.
- Löschen der Rezeptur löscht die Bestandteile. Löschen eines verwendeten Düngers ist `RESTRICT`.
- Einzelendpunkte unter `/recipe-items`.
- `GET /recipes/{id}/items` nach `dose_order`.
- `PUT /recipes/{id}/items` ersetzt die Liste vollständig. Der Service vergibt `dose_order` lückenlos ab 0 neu (V-12).
- `is_complete` ist wahr, wenn die Summe der Anteile 100 beträgt, Toleranz 0,01. Eine unvollständige Rezeptur bleibt speicherbar.
- Factory legt Rezeptur, Phase, Pflanze und Dünger selbst an.

Fertig, wenn AK-2.6 (soweit die Phase ihre Rezeptur und Bestandteile entfernt) und AK-2.7 grün sind.

Bezug: Kapitel 6.1, 6.3, 7.4, 9.1, AK-2.6, AK-2.7.

### Schritt 2.6 – pH-Mittel

Status: offen

Ziel: pH-Mittel mit Richtung und Anfangsdosis, ohne eine vorgegebene Wirkungskurve.

Umsetzen:

- `app/enums/ph_direction.py` mit `up` und `down`.
- Model `PhAdjuster`, Spalte `direction` als `String(30)`, geprüft über das Schema.
- `initial_dose_ml_per_liter` größer 0. Name eindeutig.
- Router `/ph-adjusters`, Factory.

Fertig, wenn eine andere Richtung als `up` oder `down` mit 422 abgelehnt wird und der Pflichtschnitt grün ist.

Bezug: Kapitel 6.0, 6.1, 8.4.

### Schritt 2.7 – Tank

Status: offen

Ziel: der Tank trägt Zuordnung, Füllwasser-EC und alle Sicherheitsgrenzen.

Umsetzen:

- Model `Tank` mit allen Spalten aus Kapitel 6.1. Standards für Stabilisierung, Korrekturversuche und Zyklusdauer kommen aus der Konfiguration, wenn der Client sie weglässt.
- `target_volume_liters <= max_volume_liters` (V-9) im Schema und nach dem Zusammenführen im Update.
- `current_growth_stage_id` muss zur `plant_id` desselben Tanks gehören (V-11), geprüft im Service, Verstoß 422.
- Pflanze und Phase löschen, solange ein Tank darauf zeigt: `RESTRICT`.
- Router `/tanks`, Factory. Die Factory legt auf Wunsch Pflanze und Phase an und setzt eine passende aktive Phase.

Fertig, wenn AK-2.8 grün ist und V-9 bei Create und bei einem Teil-Update greift, das nur eines der beiden Volumenfelder sendet.

Bezug: Kapitel 6.1, 7.3, 7.4, AK-2.8.

### Schritt 2.8 – Löschregeln, Migrationen, Seed

Status: offen

Ziel: die Stammdaten aus M2 hängen fachlich zusammen und lassen sich aus einer leeren Datenbank auf- und wieder abbauen.

Umsetzen:

- Je einen Integrationstest für jede Beziehung aus Kapitel 6.3, die nach M2 existiert. Beziehungen zu `Measurement`, `RegulationCycle` und `Job` folgen in Phase 3, sobald diese Tabellen existieren; der Testmodul-Name lässt die Lücke als noch offene Fälle erkennbar.
- Erwartung: Pflanze mit Phase löschen ergibt 409 (AK-2.5). Phase löschen entfernt Rezeptur und Bestandteile (AK-2.6). Verwendeten Dünger löschen ergibt 409. Tank blockiert das Löschen von Pflanze und Phase.
- Alle Revisionen lesen: eigene Meldung, kein Bearbeiten alter Revisionen, `downgrade` funktioniert. Ein Test fährt `upgrade head` und `downgrade base` auf einer leeren Datei-Datenbank (AK-2.9) und prüft, dass der Stand zu den Models passt (M-5).
- `tools/seed.py`: eine Pflanze, zwei Phasen mit Sollwerten, drei Dünger mit EC-Wirkung 0,1, 0,2 und 0,1, eine vollständige Rezeptur 30/30/40, ein Tank mit den Platzhalter-Grenzen und `source_water_ec` 0,3. Vorhandene Namen werden nicht doppelt angelegt. Das Skript liegt unter `tools/` und importiert die Services oder eine schmale Anlegefunktion, sodass dieselben Validierungen gelten wie über die API.

Fertig, wenn AK-2.5, AK-2.6, AK-2.9 und AK-2.10 grün sind. Zweimaliges Ausführen des Seeds in einem Test ändert die Anzahl der Zeilen nicht.

Bezug: Kapitel 6.3, 10.3, 14.1, AK-2.5, AK-2.6, AK-2.9, AK-2.10.

### Schritt 2.9 – Abnahme M2

Status: offen

Ziel: der Meilenstein ist als Ganzes geprüft, nicht nur seine einzelnen Schnitte.

Prüfen: AK-2.1 bis AK-2.10. Zusätzlich die Werkzeugkette und die Coverage-Schwelle für `app/services` (90 Prozent Zweige), sobald sie eingeschaltet wird.

Fertig, wenn diese Prüfung ohne offene Abweichung endet. Abweichungen werden im Schritt behoben, nicht in die nächste Phase verschoben.

---

## Phase 3 – M3 Jobliste und EC-Regelung

Danach ist dieser Ablauf möglich: Zyklus starten, Messwerte eingeben, auswerten, je Dünger eine Empfehlung bekommen, Mengen bestätigen, Mischen bestätigen, nach der Stabilisierungszeit erneut messen, bis der EC im Bereich liegt.

In M3 erzeugt nur ein zu niedriger EC einen Korrekturjob. Volumen, pH und ein zu hoher EC erscheinen in der Bewertung und erzeugen noch keinen Job. Die Rangfolge Volumen, EC, pH ist trotzdem schon die Entscheidungslogik, damit Phase 4 nur die fehlenden Jobtypen einhängt.

### Schritt 3.1 – Zielbereich und EC-Berechnung

Status: offen

Ziel: die Rechenkerne aus 8.1 und 8.2 stehen, bevor irgendein Job sie aufruft.

Umsetzen:

- `app/calculations/target_range.py`: Grenze verletzt heißt korrigieren auf den Zielwert, innerhalb des Bereichs heißt keine Aktion. Dieselbe Funktion für EC und pH. Fälle: unter Minimum, über Maximum, innerhalb, genau auf der Grenze.
- `app/calculations/ec.py`: Rezeptwirkung, Gesamtmenge, Verteilung. Eingabe als Dataclasses. Ausgabe enthält die exakten Werte und die auf eine Dezimalstelle gerundeten Milliliter.
- Das Beispiel aus 8.2: exakt gerechnet 184,615… ml, gerundet 184,6 sowie 55,4, 55,4 und 73,8. Negative Differenz und Wirkung 0 sind Fehler der Funktion, keine stillen Nullen.
- Coverage-Schwelle 100 Prozent für `app/calculations` ab diesem Schritt einschalten.
- TID251 für `app/calculations` prüfen: keine Models, kein SQLAlchemy, kein HTTP.

Fertig, wenn AK-3.9 auf der Funktionsebene grün ist und die Grenztests aus Kapitel 12.4 für Zielbereich und EC grün sind.

Bezug: Kapitel 8.1, 8.2, 5.2 D-1, AK-3.9.

### Schritt 3.2 – Messung

Status: offen

Ziel: Messungen sind ein unveränderlicher Verlauf. „Aktuell“ ist die Zeile mit dem größten `measured_at`.

Umsetzen:

- Enum `MeasurementSource`: `manual`, `simulated`, `sensor`.
- Model `Measurement` mit allen Spalten aus Kapitel 6.2, Index `(tank_id, measured_at)`. `job_id` bleibt vorerst ohne Fremdschlüssel-Ziel, bis die Jobtabelle in 3.3 existiert; die Revision in 3.3 ergänzt den Fremdschlüssel, nicht eine nachträgliche Änderung an dieser Revision, falls 3.2 schon angewendet wurde. Praktisch: 3.2 und 3.3 können denselben Entwicklungsstand teilen, aber die Measurement-Revision enthält `job_id` erst, wenn `jobs` existiert. Deshalb in diesem Schritt `job_id` noch weglassen und sie in 3.3 in einer eigenen Revision nachziehen. Das ist eine echte Schemaänderung und bekommt eine eigene Revision (M-1).
- Wertebereiche: EC 0 bis 10, pH 0 bis 14, Temperatur optional −5 bis 60, Volumen optional und mindestens 0. Obergrenze des Volumens gegen den Tank gehört nicht ins Schema (P-5).
- `POST /tanks/{id}/measurements`, `GET /tanks/{id}/measurements` mit `from`, `to`, `limit`, `offset`, `GET /tanks/{id}/measurements/latest`.
- Seitenweise Abfrage ab hier über eine gemeinsame Hilfe: Standard `limit` 100, Obergrenze 1000, Antwort enthält `items` und `total`. Dieselbe Hilfe nutzen später Zyklen und Jobs.
- Messungen werden nicht überschrieben und nicht gelöscht. Tank löschen, solange Messungen existieren: `RESTRICT`.
- Factory `make_measurement`.

Fertig, wenn AK-3.4 grün ist: eine später erfasste, aber zeitlich ältere Messung verliert gegen `latest`. P-1 und P-2 lehnen die Eingabe mit 422 ab.

Bezug: Kapitel 6.2, 6.4, 7.5, 9.1, 9.2, AK-3.4.

### Schritt 3.3 – Zyklus, Job und Aufzählungen

Status: offen

Ziel: das Protokoll hat alle Spalten, die spätere Meilensteine brauchen, inklusive der Gerätefelder, die in M3 noch leer bleiben.

Umsetzen:

- Enums: `CycleMode` (`advisory`, `simulation`, `automatic`), `CycleTrigger` (`manual`, `scheduled`), `CycleStatus` (`running`, `succeeded`, `failed`, `cancelled`), `JobStatus` (alle acht Zustände aus Kapitel 5.3), `JobType` zunächst mit `MeasureProbe`, `CompareProbe`, `CompensationEC`, `DoseFertilizer`, `Mix`. `AdjustVolume`, `CompensationPH` und `DosePhAdjuster` kommen in Phase 4 als Enum-Erweiterung ohne Migration hinzu.
- Model `RegulationCycle` und `Job` nach Kapitel 6.2. `parameters` JSON mit Standard `{}`. `request_id` eindeutig und optional, `timeout_at` optional, beide von Anfang an vorhanden.
- `cycle_id` am Job optional. `parent_job_id` mit `ON DELETE SET NULL`. Jobs eines Zyklus `CASCADE`. Messung erhält `job_id` mit `ON DELETE SET NULL`.
- Indizes `(status, run_after, id)`, `(cycle_id)` und der Messindex aus 3.2.
- `created_at`/`updated_at` über die Basisklasse. `run_after` standardmäßig `utcnow()` zum Zeitpunkt des Einreihens.
- Noch keine Ausführung. Ein Integrationstest schreibt einen Job mit `run_after`, liest ihn und vergleicht mit `utcnow()` ohne `TypeError` (AK-3.20).

Fertig, wenn die Tabellen per Migration entstehen, der Zeitvergleich grün ist und die Löschregeln für Zyklus, Job und Messung aus Kapitel 6.3 eigene Tests haben.

Bezug: Kapitel 5.3, 6.0, 6.2, 6.3, 6.4, AK-3.20.

### Schritt 3.4 – Dispatcher, Registry, Seiten und Protokoll

Status: offen

Ziel: es gibt genau eine Funktion, die den nächsten fälligen Job auswählt und ausführt. Die Jobtypen registrieren sich, ohne dass der Dispatcher ihre Fachlogik kennt.

Umsetzen:

- `app/jobs/base.py`: Protokoll eines Jobtyps mit Parameter-Schema, optionalem Eingabe-Schema, Ergebnis-Schema und `execute`.
- `app/jobs/registry.py`: Abbildung `JobType` auf Handler.
- `app/jobs/dispatcher.py`:
  - höchstens ein Job im Zustand `running`
  - Auswahl: `pending`, `run_after <= utcnow()`, Sortierung `run_after`, dann `id`
  - vor der Auswahl: Zyklen prüfen, deren Dauer S-6 überschreitet (die konkrete Behandlung kann in 3.10 vervollständigt werden; die Stelle im Dispatcher steht hier)
  - vor der Auswahl: `waiting_device` mit abgelaufenem `timeout_at` (die Behandlung bleibt bis Phase 5 eine leere, getestete Abfrage, damit M9 den Dispatcher nicht umbaut)
  - Erfolg: eine Transaktion, commit durch den Dispatcher
  - Fehler: Rollback, danach Status `failed` und `error_message` in einer neuen Transaktion; offene Jobs des Zyklus `cancelled`, Zyklus `failed`
- `GET /jobs/next`, `POST /jobs/dispatch`, `GET /jobs` mit Filtern `status`, `type`, `cycle_id` und Seitenparametern.
- Jeder Zustandswechsel wird protokolliert: Typ, Id, Zyklus-Id, alter und neuer Status.
- Berechnete Mengen werden später in den Jobtypen mit allen Eingangswerten protokolliert. Die Logger-Stelle liegt in der gemeinsamen Job-Hilfe.

Fertig, wenn AK-3.13, AK-3.14 und AK-3.25 grün sind. Für AK-3.14 genügen zwei Tanks mit je einem pending Job und unterschiedlichen `run_after`, noch ohne fachliche Handler: der Dispatcher führt den früher fälligen aus. Dafür einen minimalen Test-Handler nur im Test registrieren oder den ersten echten Handler aus 3.5 schon so bauen, dass er hier verwendbar ist. Liegt 3.5 noch nicht, einen internen No-Op-Jobtyp vermeiden und AK-3.14 zusammen mit 3.5 abschließen. Die Abfrage-Sortierung selbst hat in diesem Schritt einen eigenen Test.

Bezug: Kapitel 5.3, 9.1, 9.3, 13.4, AK-3.13, AK-3.14, AK-3.25.

### Schritt 3.5 – Wiederaufsetzen beim Start

Status: offen

Ziel: ein Prozessabbruch hinterlässt keinen Job dauerhaft in `running`.

Umsetzen:

- `recover_interrupted_jobs()` wird im Lebenszyklus nach der Migration und vor der ersten Anfrage aufgerufen.
- `MeasureProbe` und `CompareProbe` von `running` zurück auf `pending`.
- `DoseFertilizer`, und sobald sie existieren `DosePhAdjuster` und `AdjustVolume`, auf `failed`, Zyklus auf `failed`, `failure_reason` nennt den Abbruch und die ungewisse Menge. Der Job wird nicht erneut ausgeführt.
- `Mix` auf `failed` mit derselben Zyklusfolge.
- `waiting_input`, `waiting_device`, `blocked` und `pending` bleiben unverändert.
- Die Regel hängt am Jobtyp, nicht an verstreuten Sonderfällen, damit Phase 4 die neuen Dosierjobs nur in diese Tabelle einträgt.

Fertig, wenn AK-3.23 grün ist.

Bezug: Kapitel 5.3, Regeln W-1 bis W-3, AK-3.23.

### Schritt 3.6 – Zyklusstart und MeasureProbe

Status: offen

Ziel: ein Zyklus beginnt mit einer Messung, die im Modus `advisory` sofort auf eine Eingabe wartet.

Umsetzen:

- `POST /tanks/{id}/cycles` mit Modus und Auslöser. In M3 ist der fachlich unterstützte Modus `advisory`. `simulation` und `automatic` werden mit 422 abgelehnt, bis Phase 5 beziehungsweise Phase 9 sie können. Den Enum-Wert trotzdem schon speichern zu können, bleibt erlaubt; der Start-Endpunkt lehnt die noch nicht umgesetzten Modi ab.
- Zweiter laufender Zyklus desselben Tanks: 409.
- Anlegen von `MeasureProbe` und `CompareProbe`, `parent_job_id` des Compare-Jobs zeigt auf die Messung. Erster Job wird in derselben Einheit sofort ausgeführt.
- `MeasureProbe` im Modus `advisory`: Zustand `waiting_input`, noch keine Messung.
- Parameter beider Jobs enthalten `tank_id`.
- `GET /cycles/{id}` liefert den Zyklus und alle Jobs mit Typ, Zustand, Parametern, Ergebnis und `parent_job_id`.
- `GET /tanks/{id}/cycles` seitenweise.

Fertig, wenn AK-3.1, AK-3.2 und AK-3.21 grün sind.

Bezug: Kapitel 9.3, 9.4, AK-3.1, AK-3.2, AK-3.21.

### Schritt 3.7 – Eingabe für wartende Jobs

Status: offen

Ziel: der Betreiber kann eine Messung abgeben. Dieselbe Route nimmt später Bestätigungen von Dosierung und Mischen an.

Umsetzen:

- `POST /jobs/{id}/input`. Der Job muss `waiting_input` sein, sonst 409 (`JobStateError`).
- Für `MeasureProbe`: Eingabe `ec`, `ph`, optionale Temperatur, optionales Volumen. Der Handler legt genau eine Messung an mit `source=manual`, `tank_id` aus den Parametern und `job_id`, setzt den Job auf `succeeded` und schreibt `measurement_id` ins Ergebnis.
- Ein Aufruf führt nicht den nächsten Job aus.
- Bestätigungsschema für Dosierjobs schon als Form vorsehen: `dosed_ml` beziehungsweise `added_liters` ist Pflicht. Die Handler dafür folgen in 3.9.

Fertig, wenn AK-3.3 grün ist.

Bezug: Kapitel 9.3, 9.4, O-4, AK-3.3.

### Schritt 3.8 – CompareProbe, Plausibilität, Freigabe

Status: offen

Ziel: die Bewertung entscheidet höchstens eine Korrektur, und unplausible Messungen blockieren den Zyklus, ohne ihn zu zerstören.

Umsetzen:

- Neueste Messung des Tanks laden. Aktive Phase und Sollwerte laden. Fehlt die Phase oder die Sollwerte: Job `failed`, Zyklus `failed`.
- Plausibilität P-3, P-4, P-5 gegen die vorherige Messung desselben Tanks. Schwellen: EC-Sprung größer 1,0 innerhalb von 10 Minuten, pH-Sprung größer 1,5 innerhalb von 10 Minuten, Volumen über `max_volume_liters`. Verstoß: Job `blocked`, Messung bleibt, Zyklus bleibt `running`, nichts wird verworfen.
- Erste Abweichung in der Rangfolge Volumen, EC, pH bestimmen. Das Ergebnis enthält die Bewertung aller drei Größen.
- In M3 einen Job erzeugen nur für EC unter `ec_min`: genau ein `CompensationEC`, `parent_job_id` gesetzt, `ec_attempts` um 1 erhöht. Volumenabweichung, pH-Abweichung und EC über `ec_max` werden ausgewiesen und erzeugen keinen Job. Liegt der EC im Bereich, endet der Zyklus als `succeeded`, auch wenn Volumen oder pH abweichen.
- Steht `ec_attempts` vor dem Einreihen bereits auf `max_correction_attempts`, endet der Zyklus als `failed`, ohne weiteren Korrekturjob. Offene Jobs `cancelled`.
- `POST /cycles/{id}/continue`: gibt es einen `blocked`-Job, wird er erneut ausgeführt, einmalig ohne P-3 bis P-5. Sonst 409.
- Die spätere Erweiterung in Phase 4 ist eine Ergänzung der „erzeuge Job“-Fälle, nicht ein Umbau der Bewertung.

Fertig, wenn AK-3.5, AK-3.6, AK-3.7, AK-3.8, AK-3.16, AK-3.17 und AK-3.19 grün sind.

Bezug: Kapitel 7.5, 9.3, 9.4, AK-3.5 bis AK-3.8, AK-3.16, AK-3.17, AK-3.19.

### Schritt 3.9 – CompensationEC, DoseFertilizer, Mix

Status: offen

Ziel: ein zu niedriger EC wird in einzelne, bestätigte Dosierschritte und einen anschließenden Messpunkt übersetzt.

Umsetzen:

- `CompensationEC` liest die in den Parametern genannte Messung. EC bereits mindestens `ec_min`: `failed`. Kein Volumen an der Messung: `failed` mit verständlicher Meldung (AK-3.18). Keine Rezeptur oder `is_complete` falsch: `failed`, Zyklus `failed`, keine Dosierjobs (AK-3.15).
- Menge nach `app/calculations/ec.py`, Ziel ist `ec_target`.
- Je Bestandteil ein `DoseFertilizer` in `dose_order`, danach ein `Mix` mit `duration_seconds` aus `stabilization_seconds` des Tanks, danach ein `MeasureProbe` mit `run_after = utcnow() + stabilization_seconds`, danach ein `CompareProbe`. Alle mit `parent_job_id` auf den Berechnungsjob.
- Ergebnis enthält die Momentaufnahme aus Kapitel 9.4: Ist-EC, Ziel-EC, Volumen, je Bestandteil Id, Name, Anteil, EC-Wirkung, Rezeptwirkung, `total_ml`, gerundete Einzelmengen. Ein Test ändert danach die Rezeptur und liest das Jobergebnis erneut (AK-3.22).
- Sicherheitsgrenze S-2 wird hier noch nicht erzwungen; der Job bekommt in Phase 4 die Prüfung, bevor die Dosierjobs entstehen. Im Code eine deutlich benannte Stelle lassen, an der Schritt 4.3 die Prüfung einhängt, damit sie nicht nach dem Erzeugen der Jobs landet.
- `DoseFertilizer` im Modus `advisory`: beim Ausführen nach `waiting_input`. Die Eingabe liefert `dosed_ml`. Ergebnis `dosed_ml`. Die empfohlene Menge bleibt in den Parametern.
- `Mix` im Modus `advisory`: ebenfalls `waiting_input`. Die Eingabe ist die Bestätigung ohne Menge. Erst danach ist der folgende Messjob an der Reihe, und nur wenn `run_after` erreicht ist.
- Jede berechnete Menge wird mit den Eingangswerten protokolliert.

Fertig, wenn AK-3.10, AK-3.11, AK-3.12, AK-3.15, AK-3.18 und AK-3.22 grün sind.

Bezug: Kapitel 8.2, 9.4, AK-3.10 bis AK-3.12, AK-3.15, AK-3.18, AK-3.22.

### Schritt 3.10 – Zyklusabbruch, Dauergrenze, Abbruch eines einzelnen Jobs

Status: offen

Ziel: ein Zyklus lässt sich beenden, und ein vergessener Zyklus endet nach der Höchstdauer von selbst.

Umsetzen:

- `POST /cycles/{id}/cancel`: offene Jobs `cancelled`, Zyklus `cancelled`, `finished_at` gesetzt.
- `POST /jobs/{id}/cancel`: dieser Job `cancelled`. Läuft der Zyklus dadurch in eine Sackgasse, bleibt das vorerst so; der Betreiber bricht den Zyklus über den Zyklus-Endpunkt ab. Nicht still weitere Jobs erfunden.
- S-6 im Dispatcher, vor jeder Ausführung: `utcnow() - started_at` größer als `max_cycle_duration_minutes` des Tanks. Dann der nächste Job `failed`, offene Jobs `cancelled`, Zyklus `failed`, `failure_reason` gesetzt. Es wird nichts dosiert.
- `SafetyLimitExceeded` ist der Fachfehler für diese Grenze. Die Abbildung auf den Zykluszustand macht der Dispatcher, nicht der Router.

Fertig, wenn AK-3.24 grün ist und ein Abbruch durch den Betreiber die offenen Jobs verwirft.

Bezug: Kapitel 8.6 S-6, 9.3, AK-3.24.

### Schritt 3.11 – Durchlauf über die API

Status: offen

Ziel: der in der Phasenbeschreibung genannte Ablauf läuft als API-Test von Anfang bis `succeeded`, nicht nur in Einzeltests der Jobtypen.

Umsetzen:

- Ein API-Test mit den Seed-Zahlen: Tank 30 l, Ist-EC so gewählt, dass eine Korrektur nötig ist und die zweite Messung im Bereich liegt. Die zweite Messung gibt der Test ein, sie wird nicht aus der Dosierung berechnet (das kann die Simulation erst in Phase 5).
- Der Test geht den Weg über die öffentlichen Endpunkte: Zyklus starten, Eingabe, dispatch, Eingaben für die drei Dünger, Mix bestätigen, Uhr vorstellen, nächste Messung im Zielbereich, Compare, Zyklus `succeeded`.
- Ein zweiter Fall: dreimal EC nachkorrigieren, dann `failed` (deckt AK-3.19 noch einmal auf der API-Ebene, falls 3.8 das nur als Integrationstest hat).

Fertig, wenn dieser Durchlauf grün ist und dabei kein Endpunkt an der Datenbank vorbeischreibt.

Bezug: Kapitel 15 M3, AK-3.19.

### Schritt 3.12 – Abnahme M3

Status: offen

Ziel: AK-3.1 bis AK-3.25 sind erfüllt. Coverage für `app/jobs` mindestens 90 Prozent Zweige, `app/calculations` vollständig, Gesamtprojekt mindestens 80 Prozent.

Fertig, wenn die Prüfliste ohne offene Abweichung ist. Die Einschränkung „EC über Maximum erzeugt noch keinen Job“ ist in M3 korrekt und wird in Phase 4 aufgehoben, nicht hier vorweggenommen.

---

## Phase 4 – M4 Volumen und pH

### Schritt 4.1 – Mischungsrechnung

Status: offen

Ziel: Auffüllen und Verdünnen sind vorhersagbar, ohne zu messen.

Umsetzen:

- `app/calculations/volume.py`.
- EC nach Zugabe: Beispiel 25 l bei EC 2,0 plus 5 l bei EC 0,3 ergibt 1,72 (AK-4.1).
- Wassermenge zum Senken: Formel aus 8.3. Nicht berechenbar, wenn `source_water_ec >= ec_target`. Nicht ausführbar, wenn das Ergebnis nicht in `max_volume_liters` passt. Beides sind Ergebnisse der Funktion, keine Exceptions mit HTTP-Wissen: ein Dataclass mit entweder einer Menge oder einem Warnhinweis.
- Auffüllen auf den Zielfüllstand, beschnitten durch `max_water_per_cycle_liters`, mit einem Feld, das die Beschneidung ausweist.

Fertig, wenn AK-4.1, und die beiden Ablehnungsfälle der Funktion, als Unit-Tests grün sind.

Bezug: Kapitel 8.3, AK-4.1, AK-4.3, AK-4.4.

### Schritt 4.2 – pH-Schritt

Status: offen

Ziel: die pH-Korrektur berechnet eine kleine Dosis und erkennt die falsche Richtung.

Umsetzen:

- `app/calculations/ph.py`: `dose_ml = initial_dose_ml_per_liter * volume_liters`.
- Eine zweite Funktion bewertet die neue Messung gegen die vorherige: Bewegung entgegen der Dosierichtung ist ein Abbruchgrund. Keine Kurve, keine geschätzte Zielmenge.

Fertig, wenn Dosis und falsche Richtung als Unit-Tests grün sind.

Bezug: Kapitel 8.4.

### Schritt 4.3 – Sicherheitsgrenzen S-1 bis S-5

Status: offen

Ziel: eine Dosierung, die eine Grenze überschreiten würde, wird nicht angelegt.

Umsetzen:

- `app/calculations/safety.py` prüft Summen über den bisherigen Zyklus plus die beabsichtigte Menge. Eingaben sind Zahlen, keine Models.
- S-1 Wasser, S-2 Dünger, S-3 pH-Mittel, S-4 Versuche je Größe, S-5 Volumen passt in den Tank. S-6 bleibt im Dispatcher.
- `CompensationEC` ruft S-2 auf, bevor Dosierjobs entstehen. Überschreitung: `SafetyLimitExceeded`, Zyklus `failed`, keine Teil-Dosierung.
- Dieselbe Prüfung nutzen `AdjustVolume` (S-1 und S-5) und `CompensationPH` (S-3), sobald diese Jobs existieren.

Fertig, wenn je Grenze ein Unit-Test existiert und ein Integrationstest zeigt, dass bei Überschreitung keine Dosierjobs in der Datenbank stehen (AK-4.7, zunächst für S-2; die übrigen Jobtypen ergänzen denselben Test in 4.4 und 4.5).

Bezug: Kapitel 8.6, AK-4.7.

### Schritt 4.4 – AdjustVolume und die Rangfolge fürs Volumen

Status: offen

Ziel: zu wenig Volumen wird aufgefüllt, ein zu hoher EC wird verdünnt, beides über denselben Jobtyp.

Umsetzen:

- Enum-Wert `AdjustVolume`. Parameter `tank_id` und `target_volume_liters` (Volumen nach der Zugabe).
- Beim Auffüllen ist das Ziel das `target_volume_liters` des Tanks, beschnitten nach 8.3. Beim Verdünnen ist es `volume_current + volume_needed`, begrenzt durch `max_volume_liters` und S-1.
- `CompareProbe` erzeugt bei zu niedrigem Volumen genau einen `AdjustVolume` und erhöht `volume_attempts`. Bei EC über `ec_max` ebenfalls `AdjustVolume`, keinen `CompensationEC` und keinen `DoseFertilizer`. Ist Verdünnen unmöglich, enthält das Ergebnis die Warnung, der Job endet als `failed`, der Zyklus endet, weil ohne diese Korrektur nicht sicher weitergerechnet werden kann.
- Im Modus `advisory` wartet der Job auf `added_liters`. Ergebnis: `added_liters` und `predicted_ec` aus der tatsächlich bestätigten Menge, plus die Momentaufnahme Ist-Volumen, Zielvolumen, `source_water_ec`.
- Wiederaufsetzen: `AdjustVolume` im Zustand `running` wird wie die anderen Dosierjobs behandelt.
- Nach der bestätigten Zugabe folgen `Mix`, `MeasureProbe` mit Stabilisierungszeit und `CompareProbe`, analog zur EC-Korrektur. Das Auffüllen verändert EC und pH, deshalb wird neu gemessen, bevor die nächste Größe drankommt.

Fertig, wenn AK-4.2, AK-4.3 und AK-4.4 grün sind.

Bezug: Kapitel 8.3, 9.4, AK-4.2, AK-4.3, AK-4.4.

### Schritt 4.5 – CompensationPH und DosePhAdjuster

Status: offen

Ziel: pH wird nach dem EC in kleinen Schritten korrigiert.

Umsetzen:

- Enum-Werte `CompensationPH` und `DosePhAdjuster`.
- `CompareProbe` erzeugt bei pH außerhalb des Bereichs, wenn Volumen und EC im Bereich sind, genau einen `CompensationPH` und erhöht `ph_attempts`.
- Der Job wählt das Mittel nach der Entscheidungstabelle (genau eines je Richtung). Menge aus `ph.py`. S-3 vor dem Erzeugen des Dosierjobs.
- Folgejobs: `DosePhAdjuster`, `Mix`, `MeasureProbe`, `CompareProbe`.
- Momentaufnahme: Ist-pH, Sollbereich, Richtung, Mittel, `initial_dose_ml_per_liter`, Volumen.
- `DosePhAdjuster` im Modus `advisory` wartet auf `dosed_ml`.
- Bewegt sich der pH nach der folgenden Messung in die falsche Richtung, endet die Korrektur als `failed` (AK-4.8). Die Richtung steht im Ergebnis des Berechnungsjobs, der nächste `CompareProbe` führt den Vergleich aus.
- Wiederaufsetzen behandelt `DosePhAdjuster` wie `DoseFertilizer`.

Fertig, wenn AK-4.8 grün ist und ein pH-Schritt die vier Folgejobs in der richtigen Reihenfolge erzeugt.

Bezug: Kapitel 8.4, 9.4, AK-4.8.

### Schritt 4.6 – Zusammenspiel und Abnahme M4

Status: offen

Ziel: bei mehreren Abweichungen läuft genau eine Korrektur, und die Zähler sind je Größe getrennt.

Umsetzen:

- API-Durchlauf: Volumen, EC und pH gleichzeitig außerhalb. Erster Compare erzeugt nur `AdjustVolume`. Nach der nächsten Messung nur die EC-Korrektur. Danach nur die pH-Korrektur (AK-4.5).
- Ein Zyklus mit drei EC-Korrekturen und einer pH-Korrektur läuft weiter (AK-4.6).
- AK-4.7 für S-1, S-3, S-4 und S-5 auf Jobebene, ergänzend zum S-2-Test aus 4.3.
- Vor diesem Schritt O-3 klären. Bis zur Entscheidung kein Stilllege-Feld anlegen.

Fertig, wenn AK-4.1 bis AK-4.8 grün sind.

Bezug: Kapitel 9.4, 16 M4.

---

## Phase 5 – M5 Simulation

M5 baut den Zustandsautomaten so, wie ihn M9 mit echten Geräten benutzt. Ein simuliertes Gerät und später der ESP32 rufen dieselbe Abschlussfunktion auf.

### Schritt 5.1 – Protokolle und die zwei Ausführungswege

Status: offen

Ziel: Services und Jobs sprechen gegen Protokolle. Handeingabe und Simulation sind austauschbar.

Umsetzen:

- `app/devices/protocols.py`: `MeasurementSource` und `Actuator`.
- `app/devices/manual.py`: der bisherige Advisory-Weg. Jobs, die eine physische Aktion auslösen, gehen auf `waiting_input`.
- Der Dispatcher wählt die Implementierung nach `CycleMode`. Jobs enthalten keine Verzweigung auf konkrete Klassen.
- TID251: Services importieren keine konkreten Geräteklassen.

Fertig, wenn die Advisory-Durchläufe aus Phase 3 und 4 unverändert grün sind und die Importregel scharf ist.

Bezug: Kapitel 5.2 D-5, 9.4 Modusverhalten.

### Schritt 5.2 – Sofortige Simulation

Status: offen

Ziel: ein Zyklus im Modus `simulation` läuft ohne Eingabe bis zum Ende.

Umsetzen:

- `app/devices/simulated.py`, Stufe 1: Wirkung berechnen und den Job in derselben Transaktion abschließen. `waiting_device` wird in dieser Stufe nicht sichtbar.
- EC nach Düngerzugabe über die Rezeptwirkung aus 8.2 fortschreiben. EC nach Wasserzugabe über 8.3. pH nach einer pH-Dosis um einen kleinen, im Gerät hinterlegten Schritt in die gewünschte Richtung verschieben, damit die Schleife ein Ende findet. Der Schritt ist eine Eigenschaft der Attrappe, nicht der Fachberechnung.
- Volumen, EC und pH liegen im Simulationszustand des Tanks für die Dauer des Zyklus, gespeist aus der letzten Messung beziehungsweise dem Tankvolumen beim Start.
- `POST /tanks/{id}/cycles` mit `mode=simulation` ist erlaubt.
- Ein Test startet einen Zyklus außerhalb des Zielbereichs und dispatcht, bis der Zyklus `succeeded` ist, ohne `POST /jobs/{id}/input`.

Fertig, wenn dieser Durchlauf grün ist, inklusive mehrerer Korrekturrunden.

Bezug: Kapitel 9.8 Stufe 1, Kapitel 15 M5.

### Schritt 5.3 – Abschlussfunktion, Wartezustand, Fristen

Status: offen

Ziel: Antworten von außen haben einen einzigen Eingang, und eine Dosierung kann nicht durch eine verspätete oder falsche Antwort abgeschlossen werden.

Umsetzen:

- `complete_job(job_id, request_id, payload)` prüft: Job ist `waiting_device`, `request_id` stimmt. Sonst wird die Antwort protokolliert und verworfen (G-3, G-4).
- Stufe 2 setzt den Job auf `waiting_device`, vergibt `request_id` und `timeout_at` und legt die Antwort zeitversetzt bereit. Tests stellen die Uhr vor.
- Fristen aus Kapitel 9.7: Messung 30 s, Mix Dauer plus 30 s, Dünger und pH-Mittel 120 s, Volumen 600 s. Ablauf der Dosierjobs: Job und Zyklus `failed`, Grund nennt die ungewisse Menge, keine Wiederholung. Messung und Mix: `failed`.
- Die Überwachung läuft in der Dispatcher-Abfrage, die in Schritt 3.4 vorbereitet wurde.
- Doppelte Antwort und falsche `request_id` ändern den gespeicherten Job nicht.

Fertig, wenn je ein Test für G-3, G-4, Fristablauf je Jobtyp, doppelte Antwort und falsche `request_id` grün ist.

Bezug: Kapitel 9.7, 9.8 Stufe 2, Kapitel 12.4.

### Schritt 5.4 – Gemeinsamer Eingang für HTTP und Simulation

Status: offen

Ziel: die Handeingabe und die simulierte Geräteantwort laufen in dieselbe Abschlussfunktion, soweit der Zustand das hergibt.

Umsetzen:

- Advisory bleibt bei `waiting_input` und `POST /jobs/{id}/input`, weil der Betreiber kein Gerät mit `request_id` ist.
- Simulation Stufe 2 und später MQTT verwenden `complete_job`.
- Ein dünner Adapter macht die Nutzlast beider Wege zu dem Ergebnis-Schema des Jobtyps, damit die Folgejobs an einer Stelle erzeugt werden.

Fertig, wenn ein Dosierjob über Stufe 2 und ein Dosierjob über die Handeingabe dasselbe Ergebnis-Schema schreiben und dieselben Folgejobs erzeugen.

Bezug: Kapitel 9.7, der gemeinsame Trichter vor den drei Eingängen.

### Schritt 5.5 – Abnahme M5

Status: offen

Ziel: ein langer Simulationslauf deckt die Korrekturschleife ab, und die Advisory-Tests sind nicht regressiert.

Prüfen: ein Zyklus mit Volumen-, EC- und pH-Abweichung im Modus `simulation` endet als `succeeded`. Frist- und Antworttests aus 5.3 bleiben grün. Werkzeugkette und Coverage bleiben innerhalb der Schwellen.

---

## Phase 6 – M6 Weboberfläche

Vor Schritt 6.1 die Annahme zu O-5 bestätigen: Jinja2 und HTMX im selben Prozess. Eine andere Entscheidung ändert diese Phase und lässt die API unverändert.

### Schritt 6.1 – Gerüst der Oberfläche

Status: offen

Ziel: Seiten liegen unter demselben Server wie die API und nutzen dieselben Services.

Umsetzen:

- Vorlagenverzeichnis, Basis-Layout, Einbindung von HTMX.
- Fehlerformat aus 9.6 wird in den Formularen an den Feldern gezeigt.
- Kein zweites Datenmodell und kein zweiter Schreibweg an den Services vorbei.

Fertig, wenn eine Startseite vom laufenden Server ausgeliefert wird und ein fachlicher 422 im Formular sichtbar ist.

### Schritt 6.2 – Stammdatenpflege

Status: offen

Ziel: Pflanze, Phase, Dünger, Rezeptur, pH-Mittel und Tank lassen sich ohne `/docs` pflegen.

Umsetzen:

- Listen und Formulare für die sieben Ressourcen, einschließlich Rezeptur-Vollständigkeit und dem Ersetzen der Bestandteilliste.
- Tankformular zeigt die Sicherheitsgrenzen und `source_water_ec`.

Fertig, wenn der Seed-Bestand über die Oberfläche nachvollziehbar ist und Anlegen, Ändern und ein abgewiesenes Löschen (Pflanze mit Phase) im Browser funktionieren.

### Schritt 6.3 – Tanks, Messung, Jobliste

Status: offen

Ziel: der Advisory-Ablauf aus M3 und M4 ist über Schaltflächen bedienbar.

Umsetzen:

- Übersicht aller Tanks mit letzter Messung und letzter Bewertung.
- Messwerteingabe für einen Job in `waiting_input`, Mengenfelder mit der empfohlenen Menge vorbelegt und als Pflicht sendbar.
- Jobliste eines Zyklus mit Typ, Zustand, Parametern, Ergebnis und Elternjob. Bestätigen, Freigeben (`continue`), Abbrechen.
- `dispatch` als eigene Aktion, damit die Oberfläche denselben Takt hat wie die API.

Fertig, wenn der API-Durchlauf aus Schritt 3.11 und der Rangfolgen-Durchlauf aus Schritt 4.6 im Browser klickbar sind: eingeben, bestätigen, abwarten beziehungsweise die Uhr im Test vorstellen, bis der Zyklus einen Endzustand hat.

### Schritt 6.4 – Verläufe

Status: offen

Ziel: EC, pH und Volumen eines Tanks sind über die gespeicherten Messungen sichtbar.

Umsetzen:

- Diagramm aus `GET /tanks/{id}/measurements` für einen wählbaren Zeitraum. Keine zusätzliche Tabelle.

Fertig, wenn ein Tank mit mehreren Messungen die zeitliche Reihenfolge zeigt, einschließlich einer Messung, die später erfasst wurde, aber ein früheres `measured_at` hat.

### Schritt 6.5 – Abnahme M6

Status: offen

Ziel: die Oberfläche ist für den einzelnen Betreiber der normale Zugang. `/docs` bleibt für die API erhalten.

Prüfen im Browser, nicht nur per Screenshot: Stammdaten anlegen, Zyklus im Modus `advisory` bis zum Ende führen, einen blockierten Job freigeben, einen Zyklus abbrechen, einen Verlauf öffnen. Dieselben Aktionen danach über die API lesen und prüfen, dass die Zustände zusammenpassen.

---

## Phase 7 – M7 Scheduler

### Schritt 7.1 – Zeitplan je Tank

Status: offen

Ziel: „täglich um 08:00 Ortszeit“ bleibt bei der Zeitumstellung um 08:00 Ortszeit.

Umsetzen:

- Eigene Tabelle für den Plan: Tank, Ortszeit, `zoneinfo`-Name, aktiv. Gespeicherte Fälligkeit, die der Scheduler in `run_after` beziehungsweise in den nächsten Start schreibt, ist UTC.
- Nächster Zeitpunkt wird bei jeder Berechnung aus Ortszeit und Zone neu bestimmt.
- Tests mit einer nicht existierenden und einer doppelten Stunde in `Europe/Berlin`.

Fertig, wenn die beiden Umstellungsfälle grün sind und ein normaler Tag den erwarteten UTC-Zeitpunkt trifft.

Bezug: Kapitel 15 M7, Kapitel 12.4 Sommerzeit.

### Schritt 7.2 – Hintergrundlauf

Status: offen

Ziel: der Scheduler ruft denselben Dispatcher auf wie `POST /jobs/dispatch`.

Umsetzen:

- Lebenszyklus startet eine Hintergrundaufgabe im FastAPI-Prozess und beendet sie beim Herunterfahren. Kein zweiter Prozess.
- Fällige Pläne starten einen Zyklus mit `trigger=scheduled`. Läuft für den Tank schon ein Zyklus, wird der Start ausgelassen und protokolliert, nicht mit 409 nach außen geworfen.
- Der Dispatcher bleibt die einzige Stelle, die Jobs ausführt.

Fertig, wenn ein Test die Uhr auf den Planzeitpunkt stellt und genau einen Zyklus mit Auslöser `scheduled` sieht.

Bezug: Kapitel 5.3, 14.2.

### Schritt 7.3 – Wasserwechsel-Hinweis

Status: offen

Ziel: ein fälliger Wasserwechsel ist sichtbar.

Umsetzen, nachdem O-6 bestätigt ist. Annahme dieses Plans: Hinweis, kein Blockieren.

- Vergleich von `last_water_change_at` und `water_change_interval_days`.
- Der Hinweis erscheint in der Tankübersicht und im Protokoll beim Zyklusstart. Der Zyklus startet trotzdem.
- `last_water_change_at` lässt sich über die Tank-Aktualisierung setzen, wenn der Betreiber den Wechsel durchgeführt hat.

Fertig, wenn ein überfälliger Tank den Hinweis zeigt und ein Zyklus dafür trotzdem `running` wird.

### Schritt 7.4 – Dienst und Abnahme M7

Status: offen

Ziel: auf dem Pi startet die Anwendung erst nach dem Zeitabgleich und läuft dauerhaft.

Umsetzen:

- systemd-Einheit mit Abhängigkeit von `time-sync.target` (B-1). Sie liegt im Repository als Vorlage, die Installation auf dem Pi ist der manuelle Schritt aus Kapitel 13.2 Stufe 3.
- Startprotokoll enthält die Systemzeit (B-2), das ist seit Schritt 1.7 vorhanden und wird hier nur noch gegen die Einheit geprüft.
- Abnahme: ein zeitgesteuerter Zyklus im Modus `advisory` oder `simulation` entsteht ohne manuellen POST. Die Umstellungstests bleiben grün.

Fertig, wenn die Einheitenvorlage im Repository liegt und die automatischen Tests grün sind. Die echte Installation auf dem Pi wird einmal ausgeführt und im README beschrieben, nicht von der CI.

Bezug: Kapitel 14.2, 14.3, B-1, B-2. Das Startmedium für diesen Dauerbetrieb ist in [`hardware.md`](hardware.md) festgehalten.

---

## Phase 8 – M8 Container

### Schritt 8.1 – Image und Compose

Status: offen

Ziel: die Anwendung läuft im Container, die Datenbank überlebt den Neubau des Images.

Umsetzen:

- Dockerfile für die Laufzeit aus Kapitel 4.1, Abhängigkeiten über uv, Startbefehl führt die App aus. Migration und Wiederaufsetzen bleiben im Anwendungsstart, nicht als vergessbarer Eintrittsbefehl davor.
- Compose-Datei mit einem Volume für die SQLite-Datei. `.env` wird nicht ins Image gebacken.
- Zeilenenden sind seit Schritt 0.1 auf LF festgelegt; ein im Image liegendes Shell-Skript wird daraufhin einmal geprüft.

Fertig, wenn `docker compose up` eine leere Volume-Datenbank migriert, `GET /health` 200 liefert und nach einem Image-Neubau dieselben Zeilen noch da sind.

Bezug: Kapitel 14.2, 15 M8.

### Schritt 8.2 – Abnahme M8 und Sicherungshinweis

Status: offen

Ziel: der Betriebsweg ist im README beschrieben.

Umsetzen:

- README: Start mit Compose, Lage der Datenbankdatei, Hinweis dass eine Kopie im laufenden Betrieb die WAL-Datei einbeziehen oder die SQLite-Sicherungsschnittstelle nutzen muss (Kapitel 14.4). Keinen eigenen Sicherungsdienst bauen.
- Einmal auf dem Pi starten (Stufe 3 aus Kapitel 13.2) und das Ergebnis im Abnahmevermerk dieses Schritts festhalten.

Fertig, wenn Health und Version im Container stimmen und ein Neustart einen zuvor angelegten Tank noch liefert.

---

## Phase 9 – M9 Hardware

Die Attrappe kommt vor der ersten echten Pumpe. O-7, O-9, O-10 und O-11 werden vor Schritt 9.1 entschieden. Bis dahin gilt: ein Gerät je Tank, Themen aus `tank_id`, Fristen global wie in Kapitel 9.7, Broker ohne TLS nur im abgeschotteten Netz, Temperaturkompensation ausgeschaltet, solange die Quelle nicht ausdrücklich unkorrigierte Werte liefert.

### Schritt 9.1 – MQTT-Client im Anwendungsprozess

Status: offen

Ziel: der Client lebt und stirbt mit der App, ein zweiter Schreibprozess entsteht nicht.

Umsetzen:

- `app/devices/mqtt.py` mit `aiomqtt`, Start und Ende über den Lebenszyklus.
- Themen aus Kapitel 9.7. Veröffentlichen von Dosierbefehlen mit QoS 1.
- Eingehende Antworten rufen `complete_job` auf. Unaufgeforderte Messwerte werden mit `source=sensor` und ohne `job_id` gespeichert und starten keinen Zyklus.
- Modus `automatic` ist am Zyklusstart erlaubt und benutzt diese Implementierung.

Fertig, wenn ein Test mit einem lokalen Broker oder einer eingesetzten Client-Attrappe einen Befehl sieht und eine passende Antwort den Job abschließt. Die CI muss dafür keinen dauerhaften Broker verlangen; der Test kann den Client an der Protokollgrenze ersetzen, der echte Broker-Test liegt in Schritt 9.2.

Bezug: Kapitel 9.7, 4.1.

### Schritt 9.2 – Gerätattrappe

Status: offen

Ziel: der Weg über den Broker ist geprüft, bevor eine Pumpe Strom bekommt.

Umsetzen:

- `tools/fake_esp.py`: abonniert die Befehlsthemen, wartet eine Verarbeitungszeit, veröffentlicht die Antwort, führt ein eigenes Tankmodell. Gesehene `request_id` werden nicht ein zweites Mal ausgeführt, die gespeicherte Antwort wird erneut gesendet (G-2, hier in der Attrappe, weil die Firmware später dasselbe tun muss).
- Die Attrappe kann keine Antwort, eine verspätete Antwort, eine doppelte Antwort und eine abweichende Menge erzeugen.
- Sie liegt unter `tools/` und unterliegt nicht den Importregeln von `app/`.

Fertig, wenn gegen einen Mosquitto die Fälle ohne Antwort, verzögerte Antwort und doppelte Antwort den Zyklus so beenden, wie Kapitel 9.7 es für den Pi beschreibt.

Bezug: Kapitel 9.8 Stufe 3, Regeln G-1 bis G-5.

### Schritt 9.3 – Modus automatic und Temperatur

Status: offen

Ziel: echte Aktoren werden nur über den bereits getesteten Weg angesteuert.

Umsetzen:

- Dosierjobs im Modus `automatic` veröffentlichen den Befehl, setzen `request_id` und `timeout_at` und gehen auf `waiting_device`.
- Temperaturkompensation nach 8.5 nur, wenn die Messquelle als unkompensiert gekennzeichnet ist (O-7). Standard ist aus. Die Formel `ec_25 = ec_measured / (1 + 0.02 * (temperature_c - 25))` liegt in `app/calculations` und hat Unit-Tests, auch solange der Schalter aus ist.
- Rundung auf die Auflösung einer konkreten Pumpe bleibt liegen, bis die Pumpe feststeht (Kapitel 17). Bis dahin gilt die eine Dezimalstelle aus Kapitel 8.2.

Fertig, wenn ein automatic-Zyklus gegen die Attrappe durchläuft und ein kompensierter Sensor denselben EC-Wert behält, den er gesendet hat.

### Schritt 9.4 – Abnahme M9

Status: offen

Ziel: Hardware wird erst nach der Attrappe angeschlossen.

Prüfen:

- Die Fälle aus 9.2 sind dokumentiert grün.
- Erst danach eine echte Dosierung, mit den Grenzen des betroffenen Tanks auf kleine Mengen gestellt, und mit einem Beobachter am Tank.
- Ein Prozessabbruch während `DoseFertilizer` im Zustand `running` führt beim nächsten Start zu `failed` und dosiert nicht nach.

Die Entscheidung aus Kapitel 13.2, keinen CI-Läufer auf dem Betriebs-Pi zu betreiben, wird jetzt neu bewertet. Ein Läufer, falls nötig, kommt auf ein zweites Gerät.

### Schritt 9.5 – Betriebshinweise

Status: offen

Ziel: der Zielbetrieb aus Kapitel 14 ist im README in der Reihenfolge beschrieben, in der ein neuer Pi aufgesetzt wird.

Inhalt: Plattform aus 14.3, SSD, Zeitzone, NTP, systemd, Container, Volume, Broker, Attrappe, dann Hardware. Keine Wiederholung des Pflichtenhefts, nur der Arbeitsweg.

---

## Was bewusst nicht in diesem Plan steht

Nährstoffbilanz, Düngerverträglichkeit, Vorratsverwaltung, Anmeldung, Benachrichtigungen, ein zweiter Prozess, PostgreSQL, Historisierung der Sicherheitsgrenzen, mehrere Rezepturen pro Phase, ein URL-Präfix `/api/v1/`, automatisches Löschen von Messungen, Rundung auf Pumpenauflösung. Begründung jeweils in Kapitel 17.

Stilllegen eines Tanks (O-3) wird nicht nebenbei als Spalte mitgebaut. Dafür gibt es vor Phase 4 eine kurze Entscheidung.
