# Pflichtenheft – Nutrient Solution Manager

Entwurf vom 2026-10-05. Grundlage für den Neuaufbau in einem frischen Repository.

Dieses Dokument beschreibt, **wie** das System umgesetzt wird. Es ergänzt das fachliche
Zielbild aus `projektkonzept.md` und ersetzt es dort, wo beide sich widersprechen. Die
Widersprüche sind in Kapitel 2.3 einzeln benannt.

---

# 1. Zweck und Abgrenzung

## 1.1 Zweck

Das Pflichtenheft legt die technische Lösung fest: Architektur, Datenmodell,
Berechnungsvorschriften, Schnittstellen, Konventionen, Teststrategie und
Umsetzungsreihenfolge. Es ist so konkret gehalten, dass daraus ohne weitere
Grundsatzentscheidungen implementiert werden kann.

## 1.2 Abgrenzung zum Lastenheft

| Dokument | Frage | Status |
|---|---|---|
| `projektkonzept.md` | Was soll das System fachlich leisten? | vorhanden, bleibt gültig |
| `pflichtenheft.md` | Wie wird es gebaut? | dieses Dokument |

## 1.3 Nicht Teil dieses Dokuments

- Der Lernpfad. Das neue Projekt wird nicht mehr als Lernprojekt mit Lerneinheiten geführt.
- Hardwareauswahl für Sensoren, Pumpen und Mikrocontroller.
- Mechanischer Aufbau der Tanks.

---

# 2. Ausgangslage und Ziele des Neuaufbaus

## 2.1 Was im bestehenden Projekt bereits funktioniert

Der bestehende Stand umfasst FastAPI mit SQLite, SQLAlchemy und Alembic, dazu CRUD für
`Fertilizer`, `Plant` und `GrowthStage` über alle Schichten hinweg sowie Tests auf drei
Ebenen. Die Schichtentrennung aus API, Service, Model und Schema hat sich bewährt und wird
übernommen.

## 2.2 Was beim Neuaufbau bewusst anders wird

Diese Punkte sind der Hauptgrund für den Neustart. Sie stammen aus der Durchsicht des
bestehenden Codes.

| Nr. | Befund im Altstand | Entscheidung für den Neuaufbau |
|---|---|---|
| N-1 | Tests laufen über `SessionLocal` gegen die Entwicklungsdatenbank `nsm.db`. API-Tests überschreiben die Session-Abhängigkeit nicht. | Eigene, pro Test frisch erzeugte Testdatenbank. `get_session` wird in API-Tests immer überschrieben. Siehe Kapitel 12. |
| N-2 | Testdaten hängen an fest verdrahteten Ids wie `plant_id=1`. | Factory-Fixtures erzeugen ihre Voraussetzungen selbst und geben echte Ids zurück. |
| N-3 | `PRAGMA foreign_keys` wird nicht gesetzt, SQLite prüft Fremdschlüssel daher nicht. | Pro Verbindung per Event-Listener aktiviert. Siehe Kapitel 10.1. |
| N-4 | Kein definiertes Löschverhalten bei abhängigen Datensätzen. | Löschregeln pro Beziehung festgelegt. Siehe Kapitel 6.3. |
| N-5 | Die Regel `ec_min <= ec_target <= ec_max` ist nirgends geprüft. | Als Schema-Validierung verbindlich. Siehe Kapitel 7. |
| N-6 | `ec_min` ist mit `Field(gt=0.0)` belegt, der fachlich sinnvolle Wert 0 ist dadurch verboten. | Grenzen fachlich begründet neu gesetzt. Siehe Kapitel 7.2. |
| N-7 | Jeder Endpunkt wiederholt denselben `try/except LookupError`. | Eigene Fehlerklassen plus globale Exception-Handler. Siehe Kapitel 11.4. |
| N-8 | `get_all` ist als `list[...]` annotiert, liefert aber eine `Sequence`. | Rückgabetypen entsprechen der Realität, mypy läuft im Strict-Modus. |
| N-9 | Keine Zeitstempel auf den Tabellen. | `created_at` und `updated_at` auf allen Tabellen. Siehe Kapitel 11.3. |
| N-10 | Kein Linter, kein Formatter, keine Typprüfung, keine CI, kein README. | Ab dem ersten Meilenstein Teil des Fundaments. Siehe Kapitel 13. |
| N-11 | `DemoRecord` ist eine Altlast aus der Einrichtungsphase. | Entfällt. |
| N-12 | Dateinamen weichen unabgesprochen von `projektkonzept.md` ab. | Namenskonvention verbindlich festgelegt. Siehe Kapitel 11.1. |

## 2.3 Bewusste Abweichungen vom bestehenden Projektkonzept

| Nr. | `projektkonzept.md` | Pflichtenheft | Begründung |
|---|---|---|---|
| A-1 | Regelzyklus als fester Ablauf von zwölf Schritten | Jobliste, in der Jobs Folgejobs erzeugen | Der Ablauf muss auf Eingaben und Wartezeiten pausieren können und wird später asynchron. Siehe Kapitel 5.3. |
| A-2 | `RegulationAction` als Protokoll ausgeführter Aktionen | Entfällt, die Jobliste ist das Protokoll | Zwei Tabellen für denselben Sachverhalt. |
| A-3 | `RegulationRun` | `RegulationCycle` als Klammer um die Jobs eines Prüfvorgangs | Klarere Benennung, gleiche Aufgabe. |
| A-4 | EC-Berechnung nur von Ist nach Ziel | Zusätzlich Mischungsrechnung für Auffüllen und Verdünnen | Dry Run und Simulation müssen den Wert vorhersagen, ohne zu messen. Siehe Kapitel 8.2. |
| A-5 | Kein Grund-EC des Füllwassers | `source_water_ec` pro Tank | Ohne diesen Wert ist die Mischungsrechnung nicht möglich. |
| A-6 | EC über Maximum nicht behandelt | Korrektur durch Verdünnen mit Wasser | Dünger kann einen zu hohen EC nicht senken. Siehe Kapitel 8.3. |
| A-7 | Keine Benutzeroberfläche erwähnt | Weboberfläche als Meilenstein M6 | Am 2026-10-05 entschieden. |
| A-8 | Projektstruktur mit `plant_service.py` | `app/services/plant.py` | Entspricht dem bewährten Altstand, Modulpfad nennt die Schicht bereits. |

## 2.4 Rollenverteilung

Am 2026-10-05 festgelegt: Der Agent implementiert und erklärt nur auf Nachfrage. Die
Mentorenrolle aus `AGENTS.md` gilt für das neue Repository nicht mehr. `AGENTS.md` muss beim
Anlegen des neuen Repositorys entsprechend ersetzt werden.

---

# 3. Systemkontext

## 3.1 Beteiligte

| Beteiligter | Rolle |
|---|---|
| Betreiber | Einzelner Nutzer. Pflegt Stammdaten, gibt Messwerte ein, bestätigt Dosierungen. |
| Messgerät | Zunächst Handmessgerät, Werte werden manuell eingegeben. |
| Sensorik, später | ESP32 liefert Messwerte über MQTT. |
| Aktorik, später | Dosierpumpen und Ventile, angesteuert über MQTT. |

## 3.2 Systemgrenze

```text
            ┌─────────────────────────────────────────┐
            │      Nutrient Solution Manager          │
 Betreiber ─┤  REST-API · Jobliste · Berechnungen     │
            │  SQLite-Datenbank                       │
            └────────────┬────────────────────────────┘
                         │ später
                         ▼
              MQTT-Broker ─► ESP32 ─► Sensoren, Pumpen
```

Innerhalb der Systemgrenze liegen Stammdatenverwaltung, Messwerterfassung,
Zielbereichsprüfung, Dosierberechnung, Jobsteuerung, Protokollierung und ab M6 die
Weboberfläche. Außerhalb liegen die physische Dosierung, der MQTT-Broker als Infrastruktur
und die Firmware des Mikrocontrollers.

## 3.3 Betriebsarten eines Regelvorgangs

| Modus | Bedeutung | ab |
|---|---|---|
| `advisory` | Das System berechnet und empfiehlt. Der Betreiber dosiert von Hand und bestätigt. | M3 |
| `simulation` | Messwerte und Dosierwirkung werden berechnet, keine Hardware beteiligt. | M5 |
| `automatic` | Das System steuert echte Aktoren an. | M9 |

Alle drei Modi verwenden dieselbe Berechnungslogik und dieselben Jobtypen. Sie
unterscheiden sich ausschließlich darin, wie ein Job seine Werte bezieht und ob er eine
Aktion tatsächlich ausführt.

---

# 4. Technologiestack

## 4.1 Festlegung

| Bereich | Technologie | Begründung |
|---|---|---|
| Sprache | Python, mindestens 3.13 | Moderne Typsyntax für optionale Werte ohne Zusatzimport |
| Paketverwaltung | uv mit `pyproject.toml` | Schnell, erzeugt reproduzierbare `uv.lock` |
| Web-Framework | FastAPI | Validierung über Pydantic, erzeugt API-Dokumentation selbst |
| Validierung | Pydantic v2 | Trennt API-Verträge von der Persistenz |
| ORM | SQLAlchemy 2.x mit `Mapped`-Syntax | Typisiert, vom Altstand bekannt |
| Datenbank | SQLite, Datei `nsm.db` | Kein Server nötig, am 2026-10-05 bestätigt |
| Migrationen | Alembic mit `render_as_batch=True` | SQLite kann Spalten nicht direkt ändern |
| Tests | pytest | Fixtures, Parametrisierung |
| Linter und Formatter | ruff | Ersetzt flake8, isort und black in einem Werkzeug |
| Typprüfung | mypy im Strict-Modus | Hätte N-8 verhindert |
| CI | GitHub Actions | Lint, Typprüfung und Tests bei jedem Push |
| Container | Docker, ab M8 | Nicht nötig, solange SQLite als Datei läuft |
| MQTT, ab M9 | `aiomqtt` | Asynchron, passt zur Lebenszyklusverwaltung von FastAPI. Baut auf `paho-mqtt` auf. |
| Broker, ab M9 | Mosquitto | Schlank genug für den Raspberry Pi |

## 4.2 Grenzen von SQLite und wann sie erreicht sind

SQLite erlaubt nur einen Schreibvorgang zur Zeit und kennt keinen Netzzugriff. Für einen
einzelnen Betreiber mit wenigen Tanks und Messungen im Minutenabstand ist das
unproblematisch. Ein Wechsel auf PostgreSQL wird nötig, sobald mehrere Schreibprozesse
parallel laufen, etwa ein Scheduler neben einem MQTT-Empfänger. Darauf wird vorbereitet,
indem ausschließlich SQLAlchemy verwendet wird, kein SQLite-spezifisches SQL geschrieben
wird und die Datenbank-URL aus der Konfiguration kommt.

---

# 5. Architektur

## 5.1 Schichten

```text
HTTP Request
     │
     ▼
app/api/routers/        Routing, Statuscodes, keine Fachlogik
     │
     ▼
app/schemas/            Pydantic, Validierung der Verträge
     │
     ▼
app/services/           Geschäftsprozesse, Transaktionen, Orchestrierung
     │
     ├──► app/calculations/   reine Funktionen, keine Infrastruktur
     ├──► app/jobs/           Jobtypen und Dispatcher
     └──► app/devices/        Messwertquellen und Aktoren, austauschbar
     │
     ▼
app/models/             SQLAlchemy, Persistenz
     │
     ▼
SQLite
```

## 5.2 Abhängigkeitsregeln

Diese Regeln werden in der CI geprüft, sobald M1 steht.

| Nr. | Regel |
|---|---|
| D-1 | `app/calculations/` importiert nichts aus `app/models/`, `app/api/`, `app/services/` oder SQLAlchemy. Nur Standardbibliothek und Dataclasses. |
| D-2 | `app/api/` importiert keine Models zur Fachlogik, sondern nur für Typannotationen von Rückgabewerten. |
| D-3 | `app/services/` kennt kein FastAPI. Keine `HTTPException` in Services. |
| D-4 | `app/models/` importiert keine Schemas. |
| D-5 | `app/devices/` definiert Protokolle. Services sprechen nur gegen diese Protokolle, nie gegen eine konkrete Implementierung. |

Der Zweck von D-1 ist, dass die Berechnungen ohne Datenbank und ohne HTTP testbar bleiben.
Der Zweck von D-5 ist, dass Handeingabe, Simulation und echte Sensoren ohne Änderung der
Fachlogik austauschbar sind.

## 5.3 Die Jobliste

Der Kern des Systems ist eine Liste von Jobs, die sequenziell abgearbeitet wird. Ein Job
kann weitere Jobs erzeugen. Dadurch entsteht der Regelablauf aus kleinen, einzeln
testbaren Schritten, ohne dass irgendwo ein fester Zwölf-Schritt-Ablauf hinterlegt ist.

```text
RegulationCycle (Tank 1, advisory)
│
├── 1  MeasureProbe(tank=1)          wartet auf Eingabe
│                                    → speichert Messung
├── 2  CompareProbe(tank=1)          liest neueste Messung
│                                    → Volumen im Bereich, EC zu niedrig
│                                    → erzeugt nur Job 3, ec_attempts = 1
├── 3  CompensationEC(tank=1)        berechnet Gesamtmenge und Verteilung
│                                    → erzeugt Jobs 4 bis 8
├── 4  DoseFertilizer(A, 55.4 ml)    wartet auf Bestätigung
├── 5  DoseFertilizer(B, 55.4 ml)    wartet auf Bestätigung
├── 6  DoseFertilizer(C, 73.8 ml)    wartet auf Bestätigung
├── 7  Mix(tank=1, 120 s)            wartet auf Bestätigung
├── 8  MeasureProbe(tank=1)          run_after = jetzt + 120 s
└── 9  CompareProbe(tank=1)          bewertet erneut
```

### Warum diese Form gewählt wurde

Ein Job, der auf eine Eingabe des Betreibers oder auf eine Stabilisierungszeit wartet, ist
hier einfach ein Job in einem Wartezustand. Ein fester Ablauf müsste dafür blockieren oder
seinen Zustand gesondert ablegen. Die Liste ist zugleich das vollständige Protokoll: Über
`parent_job_id` ist nachvollziehbar, welcher Job welchen Folgejob erzeugt hat und aus
welchem Grund. Und beim Umstieg auf echte Hardware ändert sich nur die Ausführung
einzelner Jobtypen, nicht der Ablauf.

### Reihenfolge und Fälligkeit

Jobs werden nach `run_after`, dann nach `id` abgearbeitet, immer nur der jeweils erste
fällige Job. `run_after` ist standardmäßig der Erstellzeitpunkt. Wartezeiten werden
dadurch ausgedrückt, dass ein Folgejob ein `run_after` in der Zukunft erhält. Ein eigener
Jobtyp `Wait` ist deshalb nicht nötig. `Mix` bleibt dagegen ein eigener Jobtyp, weil
Mischen eine echte Aktion ist, die später ein Rührwerk ansteuert.

### Nur eine Korrektur pro Bewertung

`CompareProbe` reiht höchstens **eine** Korrektur ein, auch wenn mehrere Größen außerhalb
ihres Bereichs liegen. Die Rangfolge ist Volumen, dann EC, dann pH. Nach der Korrektur
wird neu gemessen und neu bewertet; die nächste Abweichung wird dann im folgenden
Durchlauf behandelt.

Diese Regel ist nicht nur eine Vereinfachung, sondern notwendig. Würde `CompareProbe` alle
Korrekturen zugleich einreihen, entstünde folgender Ablauf:

```text
Job 2  CompareProbe        erzeugt Job 3 AdjustVolume
                                   Job 4 CompensationEC
                                   Job 5 CompensationPH
Job 3  AdjustVolume
Job 4  CompensationEC      erzeugt Job 6-8 DoseFertilizer
                                   Job 9  Mix
                                   Job 10 MeasureProbe (später fällig)
                                   Job 11 CompareProbe
Job 5  CompensationPH      ◄── läuft jetzt, weil sofort fällig und kleinere Id
```

Die pH-Korrektur würde also vor der ersten Düngerdosierung berechnet, auf Basis der alten
Messung. Genau das soll die Reihenfolge Volumen, EC, pH verhindern: Auffüllen verdünnt
beide Werte, Düngen verschiebt den pH. Eine Korrektur, die auf einem überholten Messwert
beruht, dosiert in die falsche Richtung.

### Zustände eines Jobs

```text
pending ──► running ──┬──► succeeded
   │           ▲      │
   │           │      ├──► failed         → Zyklus endet
   │           │      │
   │           │      ├──► waiting_input  → Eingabe   → running
   │           │      │
   │           │      ├──► waiting_device → Antwort   → running
   │           │      │                   → Frist ab  → failed
   │           │      │
   │           └──────┴──► blocked        → Freigabe  → running
   │
   └──► cancelled
```

| Zustand | Bedeutung | Zyklus läuft weiter |
|---|---|---|
| `pending` | Eingereiht, noch nicht fällig oder noch nicht an der Reihe | ja |
| `running` | Wird gerade ausgeführt | ja |
| `waiting_input` | Braucht eine Eingabe oder Bestätigung des Betreibers | ja |
| `waiting_device` | Befehl ist an ein Gerät abgesetzt, Antwort steht aus | ja |
| `blocked` | Ausführung verweigert, weil die Datenlage zweifelhaft ist. Wartet auf ausdrückliche Freigabe. | ja |
| `succeeded` | Erfolgreich beendet | ja |
| `failed` | Abgebrochen. Beendet den gesamten Zyklus. | nein |
| `cancelled` | Vom Betreiber oder durch Zyklusabbruch verworfen | nein |

Die drei Wartezustände unterscheiden sich darin, worauf gewartet wird und wie lange.
`waiting_input` wartet unbegrenzt, weil der Betreiber kommt, wenn er Zeit hat.
`waiting_device` hat eine Frist, weil ein stummes Gerät den Zyklus sonst dauerhaft
blockieren würde. `blocked` wartet auf eine Entscheidung, nicht auf eine Handlung.

Der Unterschied zwischen `blocked` und `failed` ist wesentlich. `failed` bedeutet, dass
weiteres Vorgehen unsicher wäre: eine überschrittene Sicherheitsgrenze, eine fehlende
Rezeptur, ein pH, der sich der Dosierung entgegen bewegt, eine abgelaufene Gerätefrist bei
einer Dosierung. Der Zyklus endet, alle offenen Jobs werden verworfen.

`blocked` bedeutet dagegen, dass nur die Datengrundlage zweifelhaft ist, etwa bei einem
unplausiblen Messsprung nach einem Wasserwechsel. Der Job hat nichts verändert, der Zyklus
bleibt offen, und nichts wird verworfen. Der Betreiber kann nach Sichtprüfung freigeben
oder abbrechen. Ohne diese Unterscheidung wäre das in Kapitel 9.3 beschriebene Fortsetzen
eines Zyklus nicht möglich, weil nach einem `failed` keine Jobs mehr übrig sind.

### Ausführung

Für M3 bis M6 wird der jeweils nächste fällige Job über einen API-Aufruf ausgeführt. Ein
dauerhaft laufender Hintergrundprozess ist bewusst zurückgestellt, weil im Modus
`advisory` ohnehin nach fast jedem Schritt auf den Betreiber gewartet wird. Der Scheduler
in M7 ruft dieselbe Dispatcher-Funktion auf, sodass dieser Wechsel keine Änderung an den
Jobtypen erfordert.

### Nebenläufigkeit

Es ist immer nur ein Job im Zustand `running`. Mehrere Jobs dürfen gleichzeitig auf einen
Knoten warten. Der Dispatcher setzt startbereite Gerätejobs nacheinander auf
`waiting_device`. Ihre Fertigmeldungen treffen in der Reihenfolge ein, in der die Knoten
fertig werden, nicht in der Startreihenfolge.

Pro Gerät ist höchstens ein Befehl offen. Ein zweiter Schritt an dasselbe Gerät bleibt
`pending`, bis der offene Befehl gemeldet hat. Schritte an verschiedene Geräte laufen
gleichzeitig.

Ein Anlagengerät, das ein Ablauf belegt, steht keinem zweiten Dosierjob zur Verfügung. Belegt
ist es, solange ein Gerätejob dieses Ablaufs `running` oder `waiting_device` ist, und bis
die Abschlussfolge beendet ist. Ein Messjob eines anderen Tanks darf daneben laufen.

Pro Tank darf höchstens ein Zyklus im Zustand `running` sein. Ein zweiter Startversuch wird
mit Statuscode 409 abgelehnt. Das verhindert, dass zwei Zyklen denselben Tank gegenläufig
regeln.

### Wiederaufsetzen nach einem Abbruch

Stirbt der Prozess während der Ausführung eines Jobs — Stromausfall, Neustart, Absturz —
bleibt dieser Job im Zustand `running`. Ohne Gegenmaßnahme steckt der Zyklus dauerhaft
fest, weil der Dispatcher immer nur den ersten fälligen Job nimmt und dieser nie fertig
wird. Bei einem Raspberry Pi ohne Notstromversorgung ist das kein Randfall.

Beim Start der Anwendung werden daher alle Jobs in `running` und `waiting_device` behandelt,
und zwar nach derselben Unterscheidung wie bei einer abgelaufenen Gerätefrist in 9.7:
Entscheidend ist, ob der Job etwas Physisches verändert haben könnte.

| Jobtyp | Behandlung beim Start |
|---|---|
| `MeasureProbe`, `CompareProbe` | zurück auf `pending`, auch aus `waiting_device`. Beide verändern nichts, eine Wiederholung ist gefahrlos. |
| `DoseFertilizer`, `DosePhAdjuster`, `AdjustVolume`, `Mix`, `DeviceCommand` | auf `failed`, Zyklus auf `failed`, manuelle Prüfung erforderlich. Laufende Schritte werden nicht fortgesetzt. Liegt für den Jobtyp ein Ablauf vor, wird seine Abschlussfolge veröffentlicht. |

Die Begründung für die Dosierjobs ist dieselbe wie dort: Nach einem Abbruch ist nicht
feststellbar, ob die Pumpe gelaufen ist. Weiterrechnen wäre in beide Richtungen falsch, und
ein automatischer zweiter Versuch könnte die doppelte Menge dosieren.

| Nr. | Regel |
|---|---|
| W-1 | Das Wiederaufsetzen läuft einmalig beim Start, bevor der erste Job ausgeführt oder ein Zeitplan aktiv wird. |
| W-2 | `failure_reason` nennt den Abbruch als Ursache und die ungewisse Menge. |
| W-3 | Jobs in `waiting_input`, `blocked` und `pending` bleiben unangetastet. Geändert am 2026-10-07: `waiting_device` übersteht einen Neustart nicht. Eine offene Aktorkette hat einen ungewissen physischen Zustand. |

Ein Job, der auf den Betreiber wartet, wartet nach dem Neustart weiter. Ein Job, der auf
einen Knoten wartet, tut das nicht. Die Abschlussfolge setzt die beteiligten Aktoren in den
sicheren Zustand. Kommt der Broker dabei nicht zustande, nennt `failure_reason` das, und
der Zyklus ist trotzdem `failed`. Die Dosierung wird nicht wiederholt.

---

# 6. Datenmodell

Alle Tabellen haben `id` als `INTEGER PRIMARY KEY` sowie `created_at` und `updated_at` als
UTC-Zeitstempel. Diese drei Spalten sind unten nicht wiederholt.

## 6.0 Aufzählungstypen

Felder mit festem Wertevorrat — `source`, `mode`, `trigger`, `status`, `type`, `direction` —
werden in der Datenbank als **`String(30)`** geführt, nicht als SQLAlchemy-`Enum`. Die
unten angegebenen Wertelisten sind trotzdem verbindlich; geprüft werden sie in Python über
`enum.StrEnum` und die Pydantic-Schemas.

Grund: SQLite kennt keinen Aufzählungstyp. SQLAlchemy bildet `Enum` dort als `VARCHAR` mit
einer Prüfbedingung ab, und jeder neue Wert verlangt eine Migration, die die Tabelle nach
Regel 10.3 neu aufbaut. In diesem Projekt kommt in fast jedem Meilenstein ein Jobtyp hinzu
— M4 allein bringt drei. Das wären drei Migrationen auf der Jobtabelle, die zu dem
Zeitpunkt bereits das vollständige Betriebsprotokoll enthält.

Der Preis ist, dass die Datenbank einen ungültigen Wert nicht abweist. Da ausschließlich
diese Anwendung schreibt und jeder Schreibweg über ein Pydantic-Schema führt, ist das
vertretbar. Die `StrEnum`-Klassen liegen in `app/enums/`.

## 6.1 Stammdaten

### `plants`

| Spalte | Typ | Bedingungen |
|---|---|---|
| `name` | `String(100)` | nicht leer, eindeutig |
| `description` | `String(500)` | optional |

### `growth_stages`

| Spalte | Typ | Bedingungen |
|---|---|---|
| `plant_id` | `ForeignKey("plants.id")` | Pflicht |
| `name` | `String(100)` | nicht leer |
| `sort_order` | `Integer` | größer oder gleich 0, eindeutig je `plant_id` |
| `ec_min` | `Float` | 0,0 bis 10,0 |
| `ec_target` | `Float` | 0,0 bis 10,0 |
| `ec_max` | `Float` | 0,0 bis 10,0 |
| `ph_min` | `Float` | 3,0 bis 9,0 |
| `ph_target` | `Float` | 3,0 bis 9,0 |
| `ph_max` | `Float` | 3,0 bis 9,0 |

### `fertilizers`

| Spalte | Typ | Bedingungen |
|---|---|---|
| `name` | `String(100)` | nicht leer, eindeutig |
| `description` | `String(500)` | optional |
| `ec_effect_per_ml_per_liter` | `Float` | größer 0 |

Die EC-Wirkung ist die EC-Erhöhung in mS/cm, die 1 ml dieses Düngers in 1 Liter Wasser
bewirkt.

### `recipes`

| Spalte | Typ | Bedingungen |
|---|---|---|
| `growth_stage_id` | `ForeignKey("growth_stages.id")` | eindeutig |
| `name` | `String(100)` | nicht leer |

`unique=True` auf `growth_stage_id` setzt die fachliche Regel um, dass eine Wachstumsphase
höchstens eine Rezeptur hat. Ohne diese Bedingung wäre es eine 1:n-Beziehung.

### `recipe_items`

| Spalte | Typ | Bedingungen |
|---|---|---|
| `recipe_id` | `ForeignKey("recipes.id")` | Pflicht |
| `fertilizer_id` | `ForeignKey("fertilizers.id")` | Pflicht, eindeutig je `recipe_id` |
| `percentage` | `Float` | größer 0, höchstens 100 |
| `dose_order` | `Integer` | größer oder gleich 0, eindeutig je `recipe_id` |

`dose_order` legt fest, in welcher Reihenfolge die Dünger dosiert werden. Das ist
vorgesehen, weil bei mehrteiligen Düngersystemen Calcium mit Sulfat und Phosphat ausfallen
kann, wenn die Konzentrate direkt zusammenkommen. Eine ausdrückliche Unverträglichkeit
zwischen zwei Düngern wird nicht modelliert; sie steht in Kapitel 17.

### `ph_adjusters`

| Spalte | Typ | Bedingungen |
|---|---|---|
| `name` | `String(100)` | nicht leer, eindeutig |
| `direction` | `String(30)` | Pflicht, `up` oder `down` |
| `initial_dose_ml_per_liter` | `Float` | größer 0 |

Für pH-Mittel wird keine berechenbare Wirkung hinterlegt, weil der Zusammenhang zwischen
Menge und pH-Änderung von der Pufferkapazität der Lösung abhängt und nicht linear ist.
Stattdessen wird iterativ in kleinen Schritten korrigiert. Siehe Kapitel 8.4.

### `tanks`

| Spalte | Typ | Bedingungen |
|---|---|---|
| `name` | `String(100)` | nicht leer, eindeutig |
| `target_volume_liters` | `Float` | größer 0 |
| `max_volume_liters` | `Float` | größer oder gleich `target_volume_liters` |
| `source_water_ec` | `Float` | 0,0 bis 10,0 |
| `plant_id` | `ForeignKey("plants.id")` | optional |
| `current_growth_stage_id` | `ForeignKey("growth_stages.id")` | optional |
| `stabilization_seconds` | `Integer` | größer oder gleich 0, Standard 120 |
| `max_water_per_cycle_liters` | `Float` | größer 0 |
| `max_fertilizer_per_cycle_ml` | `Float` | größer 0 |
| `max_ph_adjuster_per_cycle_ml` | `Float` | größer 0 |
| `max_correction_attempts` | `Integer` | 1 bis 10, Standard 3 |
| `max_cycle_duration_minutes` | `Integer` | größer 0, Standard 1440 |
| `water_change_interval_days` | `Integer` | optional |
| `last_water_change_at` | `DateTime` | optional |
| `retired_at` | `DateTime` | optional. Gesetzt heißt stillgelegt (O-3) |
| `measure_timeout_seconds` | `Integer` | größer 0, Standard 30 |
| `mix_timeout_margin_seconds` | `Integer` | größer oder gleich 0, Standard 30 |
| `dose_fertilizer_timeout_seconds` | `Integer` | größer 0, Standard 120 |
| `dose_ph_adjuster_timeout_seconds` | `Integer` | größer 0, Standard 120 |
| `adjust_volume_timeout_seconds` | `Integer` | größer 0, Standard 600 |

`source_water_ec` ist der Grund-EC des Füllwassers. Ohne diesen Wert lässt sich die
Verdünnung beim Auffüllen nicht berechnen. `max_volume_liters` ist die physische
Obergrenze und begrenzt, wie weit zum Senken des EC verdünnt werden darf.

Die Sicherheitsgrenzen stehen bewusst am Tank und nicht in einer globalen Konfiguration,
weil ein 30-Liter-Tank andere Grenzen braucht als ein 200-Liter-Tank. Dass sie als Spalten
in `tanks` liegen und nicht in einer eigenen Tabelle, ist eine bewusste Vereinfachung: Sie
sind nicht historisiert, eine Änderung gilt sofort für laufende Zyklen.

`retired_at` legt den Tank still, ohne Messverlauf oder Zyklen zu löschen. Ein stillgelegter
Tank nimmt keinen neuen Zyklus an. Das Löschen bleibt `RESTRICT`, solange Verlauf existiert.

Die fünf Fristspalten sind je Tank gesetzt (O-11). Die Zahlen sind die Standards aus
Kapitel 9.7. `Mix` läuft über seine Dauer plus `mix_timeout_margin_seconds`.

## 6.2 Betriebsdaten

### `measurements`

| Spalte | Typ | Bedingungen |
|---|---|---|
| `tank_id` | `ForeignKey("tanks.id")` | Pflicht |
| `measured_at` | `DateTime` | Pflicht, UTC |
| `ec` | `Float` | 0,0 bis 10,0 |
| `ph` | `Float` | 0,0 bis 14,0 |
| `temperature_c` | `Float` | optional, -5,0 bis 60,0 |
| `volume_liters` | `Float` | optional, größer oder gleich 0 |
| `source` | `String(30)` | Pflicht, `manual`, `simulated` oder `sensor` |
| `job_id` | `ForeignKey("jobs.id")` | optional |

Die Obergrenze von `volume_liters` ist `max_volume_liters` des zugehörigen Tanks. Diese
Prüfung kann nicht im Schema liegen, weil das Schema den Tank nicht kennt. Sie gehört damit
nach Regel 7.1 in den Service und ist als P-5 in 7.5 geführt.

Messungen werden als Verlauf gespeichert und nie überschrieben. „Aktuelle Probenwerte"
heißt immer: die Messung dieses Tanks mit dem größten `measured_at`. Daraus ergeben sich
die Verlaufsdiagramme für M6 ohne zusätzliche Datenhaltung, und es bleibt nachvollziehbar,
auf welcher Messung eine Dosierung beruhte.

`volume_liters` ist optional, weil der Füllstand nicht bei jeder Messung erfasst werden
muss. Für eine Dosierberechnung ist er allerdings Pflicht; fehlt er, schlägt der Job
`CompensationEC` mit einer entsprechenden Meldung fehl.

### `regulation_cycles`

| Spalte | Typ | Bedingungen |
|---|---|---|
| `tank_id` | `ForeignKey("tanks.id")` | Pflicht |
| `mode` | `String(30)` | Pflicht, `advisory`, `simulation` oder `automatic` |
| `trigger` | `String(30)` | Pflicht, `manual` oder `scheduled` |
| `status` | `String(30)` | Pflicht, `running`, `succeeded`, `failed` oder `cancelled` |
| `started_at` | `DateTime` | Pflicht |
| `finished_at` | `DateTime` | optional |
| `volume_attempts` | `Integer` | Standard 0 |
| `ec_attempts` | `Integer` | Standard 0 |
| `ph_attempts` | `Integer` | Standard 0 |
| `failure_reason` | `String(500)` | optional |

Die Korrekturversuche werden je Größe getrennt gezählt und jeweils einzeln gegen
`max_correction_attempts` des Tanks geprüft. Ein gemeinsamer Zähler wäre bei einem Standard
von 3 schon erschöpft, wenn EC und pH je einmal normal nachregeln, obwohl beide Größen für
sich völlig unauffällig wären. Getrennte Zähler begrenzen das, was wirklich begrenzt werden
soll: wiederholtes Nachdosieren derselben Größe ohne Annäherung an den Zielwert.

### `jobs`

| Spalte | Typ | Bedingungen |
|---|---|---|
| `cycle_id` | `ForeignKey("regulation_cycles.id")` | optional |
| `parent_job_id` | `ForeignKey("jobs.id")` | optional, selbstreferenziell |
| `type` | `String(30)` | Pflicht, Werte nach `JobType` in 9.4 |
| `status` | `String(30)` | Pflicht, Werte nach `JobStatus` in 5.3, Standard `pending` |
| `parameters` | `JSON` | Pflicht, Standard `{}` |
| `result` | `JSON` | optional |
| `run_after` | `DateTime` | Pflicht, Standard Erstellzeitpunkt |
| `started_at` | `DateTime` | optional |
| `finished_at` | `DateTime` | optional |
| `error_message` | `String(500)` | optional |
| `request_id` | `String(36)` | optional, eindeutig |
| `timeout_at` | `DateTime` | optional |

`request_id` und `timeout_at` werden erst gesetzt, wenn ein Job einen Befehl an ein Gerät
absetzt. Sie sind ab M9 nötig, stehen aber von Anfang an im Schema, damit dafür später
keine Migration eines dann schon gefüllten Protokolls nötig ist. Ihre Bedeutung steht in
Kapitel 9.7.

Die Jobparameter liegen als JSON und nicht als Spalten, weil jeder Jobtyp andere Parameter
braucht. Typsicher bleibt das dadurch, dass pro Jobtyp ein Pydantic-Schema existiert, das
die Parameter beim Einreihen und beim Ausführen validiert. Ein neuer Jobtyp braucht so
keine Migration. Der Preis ist, dass die Datenbank die Parameter selbst nicht prüft und
nicht sinnvoll darauf indiziert werden kann. Siehe Kapitel 9.4.

`cycle_id` ist optional, damit ein einzelner Job auch ohne Zyklus eingereiht werden kann,
etwa eine Messung zur Dokumentation ohne anschließende Regelung.

## 6.3 Beziehungen und Löschverhalten

```text
Plant 1 ──── n GrowthStage 1 ──── 0..1 Recipe 1 ──── n RecipeItem n ──── 1 Fertilizer

Tank n ──── 1 Plant
Tank n ──── 1 GrowthStage          (aktive Phase)
Tank 1 ──── n Measurement
Tank 1 ──── n RegulationCycle 1 ──── n Job
Job  1 ──── n Job                  (Folgejobs)
```

| Beziehung | Verhalten beim Löschen des übergeordneten Datensatzes |
|---|---|
| `Plant` → `GrowthStage` | `RESTRICT`. Eine Pflanze mit Phasen kann nicht gelöscht werden. |
| `GrowthStage` → `Recipe` | `CASCADE`. Die Rezeptur gehört zur Phase. |
| `Recipe` → `RecipeItem` | `CASCADE`. Die Bestandteile gehören zur Rezeptur. |
| `Fertilizer` → `RecipeItem` | `RESTRICT`. Ein verwendeter Dünger kann nicht gelöscht werden. |
| `Tank` → `Measurement` | `RESTRICT`. Messverlauf ist Dokumentation und darf nicht verschwinden. |
| `Tank` → `RegulationCycle` | `RESTRICT`. Gleiche Begründung. |
| `RegulationCycle` → `Job` | `CASCADE`. Jobs eines Zyklus gehören zum Zyklus. |
| `Job` → `Job` über `parent_job_id` | `SET NULL`. Sonst blockiert die Selbstreferenz das Löschen, weil SQLite die Zeilenreihenfolge nicht kennt. |
| `Job` → `Measurement` über `job_id` | `SET NULL`. Die Messung bleibt, auch wenn der Job mit dem Zyklus verschwindet. |
| `Plant` → `Tank` | `RESTRICT`. |
| `GrowthStage` → `Tank` | `RESTRICT`. |

`RESTRICT` ist bewusst häufiger als `CASCADE`. Protokoll- und Messdaten sollen nicht
dadurch verloren gehen, dass ein Stammdatensatz entfernt wird. Ein Tank mit Verlauf wird
stillgelegt, indem `retired_at` gesetzt wird (O-3, entschieden am 2026-10-07).

## 6.4 Indizes

| Tabelle | Index | Grund |
|---|---|---|
| `measurements` | `(tank_id, measured_at DESC)` | Jede Bewertung liest die neueste Messung eines Tanks. Jedes Verlaufsdiagramm liest einen Zeitraum eines Tanks. |
| `jobs` | `(status, run_after, id)` | Die zentrale Abfrage des Dispatchers: der erste fällige Job im Zustand `pending`. |
| `jobs` | `(cycle_id)` | Zyklusansicht mit allen Jobs |
| `recipe_items` | `(recipe_id, dose_order)` | Bestandteile in Dosierreihenfolge |
| `growth_stages` | `(plant_id, sort_order)` | Phasen einer Pflanze in Reihenfolge |

Bei den erwarteten Datenmengen ist das keine Frage der Geschwindigkeit, sondern eine der
Sorgfalt: Die Dispatcher-Abfrage läuft bei jedem einzelnen Jobwechsel, und der Index für
`measurements` wächst mit jeder Messung dauerhaft mit.

---

# 7. Fachliche Validierungsregeln

## 7.1 Wo validiert wird

| Art der Regel | Ort | Fehlerbild |
|---|---|---|
| Feldgrenzen eines einzelnen Werts | Pydantic-Schema, `Field` | 422 |
| Regel über mehrere Felder desselben Objekts | Pydantic, `model_validator` | 422 |
| Regel, die andere Datensätze braucht | Service | 409 oder 422 |
| Datenbankintegrität | `UNIQUE`, `ForeignKey`, `CheckConstraint` | 409 |

Eine Regel wird nur an einer Stelle durchgesetzt. Dass `ec_min` kleiner als `ec_max` ist,
prüft ausschließlich das Schema; der Service wiederholt das nicht.

## 7.2 Wertebereiche mit Begründung

| Nr. | Feld | Bereich | Begründung |
|---|---|---|---|
| V-1 | `ec_min`, `ec_target`, `ec_max` | 0,0 bis 10,0 mS/cm | 0 ist gültig und bedeutet reines Wasser. Der Altstand verbot das über `gt=0.0`, siehe N-6. Oberhalb von 10 liegt kein hydroponisch sinnvoller Wert. |
| V-2 | `ph_min`, `ph_target`, `ph_max` | 3,0 bis 9,0 | Die Skala reicht von 0 bis 14, aber Sollwerte außerhalb von 3 bis 9 sind in der Pflanzenernährung ein Eingabefehler. |
| V-3 | Gemessener `ph` | 0,0 bis 14,0 | Bei Messwerten gilt die physikalische Skala, damit eine Fehlmessung erfasst und als unplausibel erkannt werden kann, statt an der Eingabe zu scheitern. |
| V-4 | `temperature_c` | -5,0 bis 60,0 | Deckt Frost und aufgeheizte Gewächshäuser ab. |
| V-5 | `percentage` | größer 0 bis 100 | Ein Bestandteil mit 0 Prozent gehört nicht in die Rezeptur. |
| V-6 | `ec_effect_per_ml_per_liter` | größer 0 | Ein Dünger ohne EC-Wirkung würde in der Berechnung zur Division durch Null führen. |

## 7.3 Regeln über mehrere Felder

| Nr. | Regel | Ort |
|---|---|---|
| V-7 | `ec_min <= ec_target <= ec_max` | `GrowthStageCreate`, `GrowthStageUpdate` |
| V-8 | `ph_min <= ph_target <= ph_max` | dieselben Schemas |
| V-9 | `target_volume_liters <= max_volume_liters` | `TankCreate`, `TankUpdate` |

V-7 und V-8 schließen die Lücke N-5. Gleichheit ist erlaubt, damit ein exakter Zielwert
ohne Toleranz ausgedrückt werden kann.

Bei `Update`-Schemas mit lauter optionalen Feldern kann ein `model_validator` die Regel
nicht vollständig prüfen, weil die fehlenden Werte aus dem gespeicherten Datensatz
stammen. Deshalb gilt: Der Service führt die Teilaktualisierung auf dem geladenen Objekt
zusammen und validiert das Ergebnis gegen das vollständige Schema, bevor er speichert.

## 7.4 Regeln, die andere Datensätze brauchen

| Nr. | Regel | Verhalten bei Verstoß |
|---|---|---|
| V-10 | Die Summe aller `percentage` einer Rezeptur ergibt 100, mit Toleranz 0,01 | Eine Rezeptur, deren Summe abweicht, ist `incomplete`. Sie kann gespeichert werden, aber `CompensationEC` lehnt sie ab. |
| V-11 | `current_growth_stage_id` eines Tanks muss zu `plant_id` desselben Tanks gehören | 422 |
| V-12 | `dose_order` ist innerhalb einer Rezeptur lückenlos ab 0 | Der Service setzt die Werte beim Speichern selbst neu. |

Zu V-10: Die Summe strikt bei jedem Schreibvorgang zu erzwingen würde bedeuten, dass eine
Rezeptur nicht schrittweise aufgebaut werden kann, weil jeder Zwischenstand ungültig wäre.
Deshalb wird die Rezeptur als Ganzes auf Vollständigkeit geprüft und erst bei der
Verwendung abgelehnt. Die API liefert dazu ein Feld `is_complete` mit.

## 7.5 Plausibilitätsprüfung von Messwerten

Diese Prüfung ist von der Schema-Validierung getrennt. Sie entscheidet nicht, ob ein Wert
gespeichert werden darf, sondern ob auf ihm gerechnet werden darf.

| Nr. | Prüfung | Schwelle | Folge |
|---|---|---|---|
| P-1 | Absolutbereich EC | 0,0 bis 10,0 | Eingabe wird mit 422 abgelehnt |
| P-2 | Absolutbereich pH | 0,0 bis 14,0 | Eingabe wird mit 422 abgelehnt |
| P-3 | Sprung des EC gegenüber der letzten Messung | mehr als 1,0 mS/cm innerhalb von 10 Minuten | Messung wird gespeichert, `CompareProbe` geht auf `blocked` |
| P-4 | Sprung des pH gegenüber der letzten Messung | mehr als 1,5 innerhalb von 10 Minuten | ebenso |
| P-5 | Volumen über `max_volume_liters` des Tanks | — | ebenso |

P-3 und P-4 greifen absichtlich nicht bei der Eingabe, sondern erst bei der Auswertung.
Ein großer Sprung kann echt sein, etwa nach einem kompletten Wasserwechsel. Deshalb wird
der Wert erfasst, aber nicht automatisch zur Grundlage einer Dosierung gemacht.

Ein Plausibilitätsverstoß führt zu `blocked`, nicht zu `failed`. Der Zyklus bleibt offen,
es wird nichts verworfen, und der Betreiber kann nach Sichtprüfung über
`POST /cycles/{id}/continue` freigeben. Der freigegebene Job läuft dann einmalig ohne die
Prüfungen P-3 bis P-5. Begründung und Abgrenzung zu `failed` stehen in Kapitel 5.3.

---

# 8. Berechnungslogik

Alle Berechnungen liegen in `app/calculations/` als reine Funktionen auf Dataclasses. Sie
kennen weder Datenbank noch HTTP und sind damit ohne Infrastruktur testbar.

## 8.1 Zielbereichsprüfung

```text
wenn ec < ec_min        →  EC erhöhen, Ziel ist ec_target
wenn ec > ec_max        →  EC senken,  Ziel ist ec_target
sonst                   →  keine Aktion
```

Dieselbe Logik gilt für pH. Entscheidend ist, dass gegen die Grenzen geprüft, aber auf den
Zielwert hin korrigiert wird. Würde man gegen den Zielwert prüfen, dosierte das System bei
jeder minimalen Abweichung nach.

Modul: `app/calculations/target_range.py`

## 8.2 Wirkung einer Rezeptur und benötigte Düngermenge

Die Rezeptur wird als eine virtuelle Mischung behandelt. Für jeden Bestandteil ist
`share_i = percentage_i / 100`.

Wirkung der Mischung, in mS/cm pro ml pro Liter:

```text
ec_per_ml_per_liter = Σ ( share_i × ec_effect_i )
```

Benötigte Gesamtmenge der Mischung:

```text
ec_difference = ec_target - ec_current
total_ml      = ec_difference / ec_per_ml_per_liter × volume_liters
```

Verteilung auf die Einzeldünger:

```text
ml_i = total_ml × share_i
```

Beispiel mit 30 Litern, Ist-EC 1,2, Ziel-EC 2,0 und der Rezeptur 30 Prozent A, 30 Prozent
B, 40 Prozent C bei Wirkungen von 0,1, 0,2 und 0,1:

```text
ec_per_ml_per_liter = 0,3×0,1 + 0,3×0,2 + 0,4×0,1 = 0,13
total_ml            = 0,8 / 0,13 × 30            = 184,6 ml
A = 55,4 ml      B = 55,4 ml      C = 73,8 ml
```

Die Einzeldünger werden vollständig im berechneten Verhältnis dosiert. Zwischen den
Düngern wird **nicht** geprüft, ob der Ziel-EC bereits erreicht ist, weil ein vorzeitiger
Abbruch das Rezeptverhältnis verzerren würde. Erst nach der kompletten Dosierung folgen
Mischen, Stabilisieren und eine neue Messung.

Die Berechnung setzt voraus, dass sich EC-Wirkungen linear und additiv verhalten. Das ist
eine Vereinfachung; bei hohen Konzentrationen stimmt sie nicht genau. Praktisch wird der
Fehler dadurch aufgefangen, dass iterativ in mehreren Durchläufen nachgeregelt wird.

### Rundung

Gerechnet wird durchgehend mit voller Gleitkommagenauigkeit. Gerundet wird ausschließlich
bei der Ausgabe, auf eine Dezimalstelle in Millilitern. Zwischenergebnisse werden nicht
gerundet, weil sich der Fehler sonst über die Einzeldünger und über mehrere
Korrekturdurchläufe aufsummiert.

Das Beispiel steht im Projektkonzept mit 184,5 ml und einer Verteilung von 55,35, 55,35
und 73,8 ml. Diese Werte entstehen, wenn die Zwischengröße 6,1538 vorab auf 6,15 gerundet
wird. Mit durchgehender Genauigkeit ergibt sich 184,6 ml und eine Verteilung von 55,4,
55,4 und 73,8 ml. Für dieses Pflichtenheft gelten die Werte mit voller Genauigkeit.

Modul: `app/calculations/ec.py`

## 8.3 Mischungsrechnung für Auffüllen und Verdünnen

Diese Berechnungen fehlen im bestehenden Projektkonzept, siehe A-4 und A-6.

### Vorhergesagter EC nach dem Auffüllen

```text
ec_after = ( volume_old × ec_old + volume_added × source_water_ec )
           / ( volume_old + volume_added )
```

Beispiel: 25 Liter mit EC 2,0, aufgefüllt um 5 Liter Wasser mit EC 0,3, ergibt
rechnerisch `(25×2,0 + 5×0,3) / 30 = 1,72`.

Diese Formel wird im Modus `advisory` benötigt, damit die Empfehlung Auffüllen und
Nachdüngen in einem Schritt zusammen ausgeben kann, und in `simulation`, wo gar nicht
gemessen wird.

### Benötigte Wassermenge zum Senken eines zu hohen EC

```text
volume_needed = volume_old × ( ec_old - ec_target )
                / ( ec_target - source_water_ec )
```

Diese Korrektur ist nur möglich, wenn `source_water_ec < ec_target` gilt und wenn
`volume_old + volume_needed <= max_volume_liters`. Ist eine der beiden Bedingungen
verletzt, erzeugt das System keine Dosierung, sondern eine Warnung mit dem Hinweis, dass
ein Teil der Lösung abgelassen oder die Lösung erneuert werden muss. Dünger kann einen zu
hohen EC nicht senken, deshalb ist Verdünnen die einzige verfügbare Maßnahme.

### Auffüllen auf den Zielfüllstand

```text
water_to_add = min(
    target_volume_liters - volume_current,
    max_water_per_cycle_liters
)
```

Wird die Menge durch die Sicherheitsgrenze beschnitten, erscheint das im Ergebnis des Jobs
als ausdrücklicher Hinweis, damit nicht unbemerkt zu wenig aufgefüllt wird.

Modul: `app/calculations/volume.py`

## 8.4 pH-Korrektur

Die Wirkung von pH-Mitteln hängt von der Pufferkapazität der Lösung ab und lässt sich
nicht zuverlässig vorab berechnen. Deshalb wird nicht die nötige Menge bestimmt, sondern
iterativ in kleinen Schritten korrigiert:

```text
dose_ml = initial_dose_ml_per_liter × volume_liters
```

Danach Mischen, Stabilisieren, neu messen, neu bewerten. Liegt der pH nach dem Schritt
immer noch außerhalb des Bereichs, folgt der nächste Schritt, begrenzt durch
`max_correction_attempts` und `max_ph_adjuster_per_cycle_ml`.

Ein Schritt wird abgebrochen und als Fehler gemeldet, wenn der pH sich nach einer Dosierung
in die falsche Richtung bewegt hat. Das deutet auf ein verwechseltes Mittel oder eine
fehlerhafte Messung hin, und weiteres Dosieren würde den Zustand verschlechtern.

Die pH-Korrektur läuft nach der EC-Korrektur, weil das Zugeben von Dünger den pH
verschiebt. Die umgekehrte Reihenfolge würde eine gerade erreichte pH-Korrektur sofort
wieder entwerten.

Modul: `app/calculations/ph.py`

## 8.5 Temperatur

Die Temperatur wird erfasst und protokolliert, aber im ersten Ausbaustand **nicht** zur
Umrechnung des EC verwendet. Grund: Die meisten Messgeräte kompensieren bereits intern auf
25 Grad Celsius. Eine zweite Umrechnung würde den Wert verfälschen.

Vorbereitet wird das trotzdem: Sobald ein Sensor ohne eigene Kompensation angebunden wird,
kommt pro Messquelle ein Schalter hinzu, und die Umrechnung erfolgt nach

```text
ec_25 = ec_measured / ( 1 + 0,02 × ( temperature_c - 25 ) )
```

mit dem üblichen Koeffizienten von 2 Prozent pro Grad. Entschieden am 2026-10-07 (O-7):
der Schalter `ec_uncompensated` sitzt am Gerät, Standard `false`. Die Formel gilt nur,
wenn er `true` ist. Handmessungen bleiben unverändert, weil der Betreiber den abgelesenen
Wert einträgt.

## 8.6 Sicherheitsgrenzen

Die Grenzen werden vor jeder Dosierung geprüft, auf Summenbasis über den gesamten Zyklus.

| Nr. | Grenze | Prüfung |
|---|---|---|
| S-1 | `max_water_per_cycle_liters` | Summe aller Wasserzugaben im Zyklus |
| S-2 | `max_fertilizer_per_cycle_ml` | Summe aller Düngermengen im Zyklus |
| S-3 | `max_ph_adjuster_per_cycle_ml` | Summe aller pH-Mittel im Zyklus |
| S-4 | `max_correction_attempts` | Je Größe getrennt: `volume_attempts`, `ec_attempts`, `ph_attempts` |
| S-5 | Lösung passt nicht in den Tank | `volume_current + water_to_add <= max_volume_liters` |
| S-6 | `max_cycle_duration_minutes` | `utcnow() - started_at` des Zyklus, geprüft vor jedem Job |

S-6 begrenzt die Gesamtdauer eines Zyklus und löst zugleich ein betriebliches Problem: Ein
Job in `waiting_input`, auf den niemand antwortet, hält den Zyklus offen, und damit lehnt
`POST /tanks/{id}/cycles` jeden neuen Zyklus für diesen Tank dauerhaft mit 409 ab. Ohne
Obergrenze müsste man sich an einen vergessenen Zyklus erinnern, um ihn von Hand
abzubrechen. Der Standardwert von 1440 Minuten entspricht einem Tag und ist bewusst
großzügig, weil im Modus `advisory` zwischen zwei Handgriffen Stunden liegen können.

Bei Überschreitung gilt einheitlich:

```text
Job auf failed setzen
        ↓
alle noch offenen Jobs des Zyklus auf cancelled
        ↓
Zyklus auf failed, failure_reason füllen
        ↓
keine weitere Dosierung ohne Eingriff des Betreibers
```

Die Grenzen werden **vor** der Ausführung geprüft, nicht danach. Eine Dosierung, die eine
Grenze überschreiten würde, findet nicht statt; sie wird nicht teilweise ausgeführt.

Modul: `app/calculations/safety.py`

---

# 9. Schnittstellen

## 9.0 Betriebsendpunkte

```text
GET /health          200, prüft Erreichbarkeit der Datenbank
GET /version         200, Anwendungsversion und Schemastand
GET /docs            Interaktive API-Dokumentation, bis M6 die Bedienoberfläche
```

`GET /health` führt eine triviale Abfrage gegen die Datenbank aus. Ein Endpunkt, der nur
„läuft" meldet, ohne die Datenbank zu berühren, wäre für den Containerbetrieb ab M8
nutzlos.

`GET /version` liefert die Version aus `pyproject.toml`, die aktuelle Alembic-Revision und
die Systemzeit beim Start:

```json
{
  "version": "0.3.0",
  "alembic_revision": "5b10439fdc69",
  "started_at": "2026-10-06T16:30:12Z"
}
```

Nach einigen Auslieferungen ist sonst nicht mehr feststellbar, welcher Code und welcher
Schemastand auf dem Pi tatsächlich laufen. Die Startzeit ist zugleich die Umsetzung von
Regel B-2 aus 14.3: Eine Startzeit, die weit in der Vergangenheit liegt, verrät einen
Zeitsprung vor dem NTP-Abgleich.

## 9.1 Stammdaten-Endpunkte

Für `plants`, `growth-stages`, `fertilizers`, `recipes`, `recipe-items`, `ph-adjusters`
und `tanks` gilt dasselbe Muster:

```text
POST   /{resource}             201, Antwort ist das erzeugte Objekt
GET    /{resource}             200, Liste
GET    /{resource}/{id}        200 oder 404
PUT    /{resource}/{id}        200 oder 404, Teilaktualisierung
DELETE /{resource}/{id}        204, 404 oder 409 bei RESTRICT
```

Zusätzlich:

```text
GET /plants/{id}/growth-stages            Phasen einer Pflanze, nach sort_order
GET /growth-stages/{id}/recipe            Rezeptur der Phase oder 404
GET /recipes/{id}/items                   Bestandteile, nach dose_order
PUT /recipes/{id}/items                   Bestandteile vollständig ersetzen
```

`PUT /recipes/{id}/items` ersetzt die Liste als Ganzes, statt Bestandteile einzeln zu
pflegen. Das passt zur Regel V-10: Die Summe von 100 Prozent ist eine Eigenschaft der
Liste, nicht eines einzelnen Eintrags. Die Einzelendpunkte bleiben trotzdem erhalten.

### Seitenweise Abfrage

Stammdatenlisten bleiben klein und werden vollständig geliefert. Für die wachsenden Listen
— Messungen, Zyklen, Jobs — gilt:

| Parameter | Standard | Obergrenze |
|---|---|---|
| `limit` | 100 | 1000 |
| `offset` | 0 | — |

Die Antwort enthält zusätzlich die Gesamtzahl, damit die Oberfläche in M6 blättern kann.
Ohne feste Obergrenze würde `GET /jobs` nach einigen Monaten Betrieb zehntausende Zeilen
liefern — jeder Zyklus erzeugt rund zehn Jobs.

## 9.2 Messungen

```text
POST /tanks/{id}/measurements             Messwerte erfassen, 201
GET  /tanks/{id}/measurements             Verlauf, Filter: from, to, limit, offset
GET  /tanks/{id}/measurements/latest      Aktuelle Probenwerte, 200 oder 404
```

### Aufbewahrung

Messungen und Jobs werden nicht automatisch gelöscht. Beides wächst stetig, aber langsam:
Bei stündlicher Messung und mehreren Tanks sind es im Jahr einige zehntausend Zeilen, was
auf der SSD aus 14.3 keine Rolle spielt. Ein automatisches Löschen wäre hier riskanter als
nützlich, weil beides Protokoll ist und die Löschregeln aus 6.3 bewusst `RESTRICT`
verwenden.

Sollte es nötig werden, ist ein Verdichten alter Messungen auf Tagesmittelwerte der
richtige Weg, nicht ihr Löschen. Das steht in Kapitel 17.

## 9.3 Zyklen und Jobs

```text
POST /tanks/{id}/cycles                   Zyklus starten, 201 oder 409
GET  /tanks/{id}/cycles                   Zyklen eines Tanks, Filter: limit, offset
GET  /cycles/{id}                         Zyklus mit allen Jobs
POST /cycles/{id}/cancel                  Zyklus abbrechen, offene Jobs verwerfen
POST /cycles/{id}/continue                Blockierten Job freigeben, 200 oder 409

GET  /jobs                                Filter: status, type, cycle_id, limit, offset
GET  /jobs/next                           Nächster fälliger Job oder 404
POST /jobs/{id}/execute                   Diesen Job ausführen
POST /jobs/dispatch                       Nächsten fälligen Job ausführen
POST /jobs/{id}/input                     Eingabe für einen Job im Wartezustand
POST /jobs/{id}/cancel                    Einzelnen Job verwerfen
```

### Zyklusstart

`POST /tanks/{id}/cycles` erhält den Modus, reiht `MeasureProbe` und `CompareProbe` ein
**und führt den ersten Job unmittelbar aus**. Die Antwort enthält den Zyklus samt beider
Jobs; `MeasureProbe` steht darin im Modus `advisory` schon auf `waiting_input`.

Diese Festlegung ist bewusst getroffen, weil der erste Job eines Zyklus immer
`MeasureProbe` ist und dessen Ausführung nichts anderes tut, als in den Wartezustand zu
wechseln. Ohne die unmittelbare Ausführung bräuchte jeder Aufrufer zwei Anfragen, um
überhaupt zum Eingabeformular zu kommen, und das Zustandsdiagramm aus 5.3 wäre verletzt,
weil `waiting_input` nur über `running` erreichbar ist.

### Eingaben und Freigaben

`POST /jobs/{id}/input` ist der Weg, auf dem ein Job im Zustand `waiting_input`
weiterläuft. Bei `MeasureProbe` sind das die Messwerte, bei `DoseFertilizer`,
`DosePhAdjuster`, `AdjustVolume` und `Mix` die Bestätigung. Bei den Dosierjobs wird die
tatsächlich dosierte Menge mitgegeben, weil sie bei Handdosierung von der empfohlenen
abweicht und die nächste Berechnung auf dem echten Wert beruhen soll. Ein Aufruf auf einen
Job, der nicht wartet, wird mit 409 abgelehnt.

`POST /cycles/{id}/continue` gibt einen Job im Zustand `blocked` frei. Er wird erneut
ausgeführt, diesmal ohne die Plausibilitätsprüfungen P-3 bis P-5. Gibt es im Zyklus keinen
blockierten Job, antwortet der Endpunkt mit 409.

## 9.4 Jobtypen

Jeder Jobtyp hat ein Pydantic-Schema für seine Parameter, ein Schema für seine Eingabe,
sofern er eine braucht, und ein Schema für sein Ergebnis.

| Jobtyp | Parameter | Eingabe | Ergebnis | ab |
|---|---|---|---|---|
| `MeasureProbe` | `tank_id` | `ec`, `ph`, `temperature_c`, `volume_liters` | `measurement_id` | M3 |
| `CompareProbe` | `tank_id` | — | Bewertung je Größe, erzeugte Folgejobs | M3 |
| `CompensationEC` | `tank_id`, `measurement_id` | — | `total_ml`, Verteilung, Folgejobs | M3 |
| `DoseFertilizer` | `tank_id`, `fertilizer_id`, `amount_ml` | bestätigte Menge | `dosed_ml` | M3 |
| `Mix` | `tank_id`, `duration_seconds` | — | — | M3 |
| `AdjustVolume` | `tank_id`, `target_volume_liters` | bestätigte Menge | `added_liters`, `predicted_ec` | M4 |
| `CompensationPH` | `tank_id`, `measurement_id` | — | Richtung, Menge, Folgejobs | M4 |
| `DosePhAdjuster` | `tank_id`, `ph_adjuster_id`, `amount_ml` | bestätigte Menge | `dosed_ml` | M4 |
| `DeviceCommand` | `device_id`, `device_point_id`, `command`, optional `depends_on_job_id` | — | Meldung des Knotens, optional die gemessene Menge | M9 |

Der Tank ist bei **jedem** Jobtyp Parameter, auch bei `MeasureProbe`. In der ursprünglichen
Beschreibung hatte nur `CompareProbe` eine Tanknummer. Ohne Tankbezug an der Messung
hingen die aktuellen Probenwerte global in der Luft, und `CompareProbe` hätte Werte
auswerten können, die von einem anderen Tank stammen.

### Modusabhängige Bestätigung

Jobs, die eine physische Aktion auslösen — `DoseFertilizer`, `DosePhAdjuster`,
`AdjustVolume` und `Mix` — verhalten sich je Modus unterschiedlich:

| Modus | Verhalten |
|---|---|
| `advisory` | Job geht auf `waiting_input`. Der Betreiber führt die Aktion aus und bestätigt. |
| `simulation` | Job wird sofort ausgeführt, die Wirkung wird berechnet. |
| `automatic` | Der Job legt die Gerätejobs aus dem hinterlegten Ablauf an und wartet, bis dieser Ablauf einschließlich der Abschlussfolge fertig ist. |

Dass auch `Mix` im Modus `advisory` auf eine Bestätigung wartet, ist Absicht. Die
Stabilisierungszeit wird über `run_after` des nächsten Messjobs abgebildet, aber gerührt
hat dann noch niemand. Ohne Bestätigung würde das System nach Ablauf der Zeit eine Messung
anfordern, obwohl die Lösung womöglich ungemischt ist, und darauf eine Dosierung berechnen.

### Aufgabe von `CompareProbe`

`CompareProbe` ist der Entscheidungspunkt des Zyklus:

```text
neueste Messung des Tanks laden
        ↓
Plausibilität prüfen (P-3, P-4, P-5)   →  bei Verstoß: blocked
        ↓
aktive Wachstumsphase und deren Sollwerte laden
        ↓
erste Abweichung in dieser Rangfolge bestimmen:
        1. Volumen gegen target_volume_liters
        2. EC     gegen ec_min und ec_max
        3. pH     gegen ph_min und ph_max
        ↓
genau eine Korrektur einreihen:
        Volumen zu niedrig     →  AdjustVolume auf target_volume_liters
        EC unter ec_min        →  CompensationEC
        EC über ec_max         →  AdjustVolume mit der Verdünnungsmenge aus 8.3
        pH außerhalb           →  CompensationPH
        zugehörigen Zähler erhöhen
        ↓
keine Abweichung  →  Zyklus auf succeeded
```

Es wird immer nur die erste Abweichung dieser Rangfolge behandelt, aus den in 5.3
dargelegten Gründen. Das Ergebnis des Jobs enthält trotzdem die Bewertung **aller** drei
Größen, damit im Protokoll und in der Oberfläche sichtbar ist, was sonst noch offen ist.

Ein zu hoher EC wird **nicht** über `CompensationEC` behandelt. Dünger kann den EC nur
heben. Senken geht nur durch Verdünnen, und das ist derselbe Jobtyp wie das Auffüllen:
`AdjustVolume`. Der Parameter `target_volume_liters` ist dabei das Volumen **nach** der
Zugabe, nicht zwingend der konfigurierte Zielfüllstand des Tanks. Beim Auffüllen ist es
`target_volume_liters` des Tanks, beim Verdünnen `volume_current + volume_needed` aus 8.3,
begrenzt durch `max_volume_liters` und S-1.

Der Zähler wird erhöht, wenn die Korrektur eingereiht wird. Geprüft wird am Anfang von
`CompareProbe`, bevor etwas eingereiht wird: Steht der Zähler der betroffenen Größe bereits
auf `max_correction_attempts`, endet der Zyklus als `failed`, ohne einen weiteren
Korrekturjob. Die Korrektur, die den Zähler auf den Höchstwert gebracht hat, darf also zu
Ende laufen. Drei Versuche bei einem Standard von 3 bedeuten drei durchgeführte
Korrekturen.

### Einschränkung in M3

In M3 gibt es die Jobtypen `AdjustVolume` und `CompensationPH` noch nicht. Solange sie
fehlen, gilt:

- Eine Volumenabweichung erscheint in der Bewertung, erzeugt aber keinen Job.
- Eine pH-Abweichung erscheint in der Bewertung, erzeugt aber keinen Job.
- Ein EC unter `ec_min` führt zu `CompensationEC`.
- Ein EC über `ec_max` erscheint in der Bewertung, erzeugt aber keinen Job. Senken braucht
  `AdjustVolume`, und den gibt es erst ab M4.
- Liegt der EC im Bereich, endet der Zyklus als `succeeded`, auch wenn Volumen oder pH
  abweichen. Die Bewertung weist das ausdrücklich aus.

Das ist eine vorübergehende Einschränkung des Ausbaustands, keine fachliche Entscheidung.
Ab M4 greift die vollständige Rangfolge. Die Rangfolge selbst wird bereits in M3
implementiert, damit in M4 nur die beiden Jobtypen ergänzt werden müssen.

### Aufgabe von `CompensationEC`

```text
ec_current >= ec_min              →  failed, dieser Job hebt nur einen zu niedrigen EC
        ↓
Rezeptur der aktiven Phase laden  →  fehlt oder unvollständig: failed
        ↓
Düngermenge nach 8.2 berechnen, Ziel ist ec_target
        ↓
Sicherheitsgrenze S-2 prüfen
        ↓
je Bestandteil einen DoseFertilizer-Job in dose_order einreihen
        ↓
danach Mix, danach MeasureProbe mit run_after = jetzt + stabilization_seconds
        ↓
danach CompareProbe
```

Dass `CompensationEC` nicht selbst dosiert, sondern pro Dünger einen eigenen
`DoseFertilizer`-Job erzeugt, hat zwei Gründe. Die Dosierreihenfolge aus `dose_order` wird
dadurch im Protokoll sichtbar und einhaltbar. Und im Modus `advisory` entsteht für jeden
Dünger ein einzelner Bestätigungsschritt, was der Handdosierung entspricht.

### Momentaufnahme der Rechengrundlage

Das Ergebnis eines Berechnungsjobs schreibt **alle Eingangswerte mit**, nicht nur
Verweise auf sie:

| Job | Mitzuschreiben |
|---|---|
| `CompensationEC` | Ist-EC, Ziel-EC, Volumen, je Bestandteil `fertilizer_id`, Name, `percentage` und `ec_effect_per_ml_per_liter`, die errechnete Rezeptwirkung, `total_ml` |
| `CompensationPH` | Ist-pH, Sollbereich, Richtung, verwendetes Mittel, `initial_dose_ml_per_liter`, Volumen |
| `AdjustVolume` | Ist-Volumen, Zielvolumen, `source_water_ec`, vorhergesagter EC |

Begründung: Ändert man eine Rezeptur, nachdem damit gerechnet wurde, verweist das
Protokoll rückblickend auf eine Zusammensetzung, die zum Zeitpunkt der Dosierung anders
war. Ein Verweis allein macht das Protokoll also mit der Zeit unwahr. Dasselbe gilt für
die Sicherheitsgrenzen, die nach 6.1 bewusst nicht historisiert sind, und für die
EC-Wirkung eines Düngers, die man nach einer Produktumstellung korrigiert.

Da die Ergebnisse nach 6.2 als JSON liegen, kostet das keine Schemaänderung. Es ist der
Unterschied zwischen einem Protokoll, das zeigt, *was gerechnet wurde*, und einem, das
zeigt, *was heute gerechnet würde*.

## 9.5 Statuscodes

| Code | Verwendung |
|---|---|
| 200 | Erfolgreiches Lesen oder Aktualisieren |
| 201 | Erfolgreiches Erzeugen |
| 204 | Erfolgreiches Löschen |
| 404 | Datensatz existiert nicht |
| 409 | Konflikt: Eindeutigkeit verletzt, `RESTRICT` greift, Zyklus läuft bereits, Job ist im falschen Zustand |
| 422 | Validierung fehlgeschlagen |
| 500 | Unerwarteter Fehler |

## 9.6 Fehlerformat

Alle Fehlerantworten haben denselben Aufbau:

```json
{
  "error": {
    "code": "growth_stage_not_found",
    "message": "GrowthStage 42 existiert nicht.",
    "details": null
  }
}
```

`code` ist maschinenlesbar und stabil, `message` für Menschen, `details` trägt bei
Validierungsfehlern die Feldliste. Ein einheitliches Format ist Voraussetzung dafür, dass
die Weboberfläche in M6 Fehler sinnvoll anzeigen kann, ohne jeden Endpunkt einzeln zu
kennen.

## 9.7 Gerätekommunikation

Dieser Abschnitt beschreibt, wie ein Job eine Aufgabe an einen ESP32 übergibt und wie die
Antwort zurückfindet. Umgesetzt wird er in M9, festgelegt wird er hier, weil er den
Zustandsautomaten der Jobs betrifft und M5 sich daran ausrichten muss.

### Das Grundmuster

Ein Gerät ist fachlich dasselbe wie der Betreiber im Modus `advisory`: ein langsamer
Antwortgeber. Ein Job setzt einen Befehl ab, hält an, und irgendwann später trifft die
Antwort von außen ein. Nur der Kanal unterscheidet sich.

```text
Job wird ausgeführt
        ↓
Befehl veröffentlichen, request_id und timeout_at setzen
        ↓
Zustand waiting_device
        ↓
   ┌────┴─────────────────────────────┐
   ▼                                  ▼
Antwort trifft ein                 Frist läuft ab
   ↓                                  ↓
Ergebnis prüfen                    je Jobtyp: failed oder erneut
   ↓
succeeded, Folgejobs einreihen
```

Alle Antwortwege münden in dieselbe Funktion:

```text
HTTP   POST /jobs/{id}/input    ─┐
MQTT   Antwort vom ESP32         ├──►  complete_job(job_id, request_id, payload)
Simulation                      ─┘
```

Das ist der Grund, weshalb die Simulation später kaum Aufwand bedeutet: Ein simuliertes
Gerät ruft dieselbe Funktion wie ein echtes. `complete_job` prüft dabei immer, dass der
Job tatsächlich wartet und dass die `request_id` zur erwarteten passt. Eine Antwort auf
einen Job in einem anderen Zustand wird verworfen und protokolliert, nicht angewendet.

### Themenstruktur

```text
nsm/device/{device_id}/cmd/{action}  Pi  → ESP32
nsm/device/{device_id}/evt/{action}  ESP32 → Pi
nsm/device/{device_id}/status        ESP32 → Pi, Lebenszeichen
```

`device_id` ist die `identifier`-Spalte der Gerätetabelle, nicht die `tank_id`.
Die Tabellen entstehen in M9. Gepflegt werden sie wie Stammdaten, sie gehören nicht zu den
sieben Ressourcen aus M2.

Der Broker verlangt keine Anmeldedaten und kein TLS (O-10, entschieden am 2026-10-07).
Das gilt für das abgeschottete Heimnetz.

### Knoten, Punkte und Abläufe

Geändert am 2026-10-07 (O-9). Ein Dosierjob im Modus `automatic` ist kein einzelner Befehl
an ein Gerät. Er besteht aus Gerätejobs. Die Regelung entscheidet die Menge. Welche Knoten,
Sensoren und Aktoren dazu laufen und welcher Befehl auf welchen anderen wartet, steht in
den Stammdaten.

`advisory` und `simulation` legen keine Gerätejobs an. Dort bleibt es bei Bestätigung durch
den Betreiber beziehungsweise bei der berechneten Wirkung.

#### `devices`

| Spalte | Typ | Bedingungen |
|---|---|---|
| `name` | `String(100)` | nicht leer |
| `identifier` | `String(100)` | nicht leer, eindeutig, das ist die `device_id` im Thema |
| `tank_id` | `ForeignKey("tanks.id")` | optional. Leer: das Gerät gehört zur Anlage und darf von mehreren Tanks benutzt werden. Gesetzt: das Gerät gehört zu diesem Tank. |
| `ec_uncompensated` | `Boolean` | Standard `false` (O-7) |

#### `device_points`

| Spalte | Typ | Bedingungen |
|---|---|---|
| `device_id` | `ForeignKey("devices.id")` | Pflicht |
| `name` | `String(100)` | nicht leer, eindeutig je Gerät |
| `kind` | `String(30)` | `sensor` oder `actuator` |

Ein Punkt ist ein Sensor oder Aktor an einem Knoten, etwa Zähler, Pumpe, Ventil oder
Schlauchsensor.

#### `device_sequences`

| Spalte | Typ | Bedingungen |
|---|---|---|
| `job_type` | `String(30)` | `AdjustVolume`, `DoseFertilizer`, `DosePhAdjuster` oder `Mix` |
| `tank_id` | `ForeignKey("tanks.id")` | optional. Leer: Ablauf für alle Tanks dieses Jobtyps. Gesetzt: dieser Tank verwendet ihn statt des allgemeinen Ablaufs. |
| `name` | `String(100)` | nicht leer |

Je Jobtyp höchstens ein Ablauf ohne Tank und höchstens einer je Tank. Fehlt im Modus
`automatic` ein Ablauf, endet der Dosierjob als `failed` mit einer klaren Meldung.

#### `device_sequence_steps`

| Spalte | Typ | Bedingungen |
|---|---|---|
| `sequence_id` | `ForeignKey("device_sequences.id")` | Pflicht |
| `device_point_id` | `ForeignKey("device_points.id")` | Pflicht |
| `command` | `String(100)` | nicht leer, der Befehl an den Knoten |
| `parameter_key` | `String(100)` | optional. Nennt die Menge aus dem übergeordneten Job, etwa `amount_ml`. |
| `depends_on_step_id` | `ForeignKey("device_sequence_steps.id")` | optional |
| `phase` | `String(30)` | `run` oder `close` |
| `reports_amount` | `Boolean` | Standard `false`. Höchstens ein Schritt je Ablauf ist `true`. |
| `timeout_seconds` | `Integer` | optional, größer 0. Leer: die Frist des übergeordneten Jobtyps am Tank, gemessen ab Eintritt in `waiting_device`. |

Löschen: ein Gerät mit Punkten und ein Punkt, den ein Schritt verwendet, bleiben
`RESTRICT`. Ein Ablauf löscht seine Schritte per `CASCADE`. Ein Tank mit Geräten oder
Abläufen bleibt `RESTRICT`.

### Wie ein Ablauf läuft

Der Dosierjob legt für jeden Schritt einen `DeviceCommand` an. `parent_job_id` zeigt auf
den Dosierjob. Schritte der Phase `run` ohne Abhängigkeit sind sofort startbereit. Ein
Schritt mit Abhängigkeit wird startbereit, wenn der genannte Schritt `succeeded` ist.
Schritte der Phase `close` warten, bis die Phase `run` abgeschlossen ist.

Der Dosierjob geht auf `waiting_device`. Der Dispatcher bringt startbereite Gerätejobs
nacheinander dorthin: Befehl veröffentlichen, `request_id` und `timeout_at` setzen. Pro
Gerät bleibt es bei einem offenen Befehl. Die Fertigmeldung schließt nur diesen Gerätejob.
Der Dosierjob wird `succeeded`, wenn alle `run`-Schritte und danach alle `close`-Schritte
`succeeded` sind. Die Menge im Ergebnis liefert der Schritt mit `reports_amount`.

Schlägt ein `run`-Schritt fehl oder läuft seine Frist ab, wird kein weiterer `run`-Schritt
gestartet. Noch nicht gestartete `run`-Schritte werden `cancelled`. Die Abschlussfolge
startet, sobald an dem betroffenen Gerät kein Befehl mehr offen ist. An den übrigen Geräten
startet sie sofort. Danach enden Dosierjob und Zyklus als `failed`. Hat der Schritt mit
`reports_amount` nicht `succeeded`, nennt `failure_reason` die ungewisse Menge. Es gibt
keine zweite Dosierung.

Beispiel für `AdjustVolume`, als Ablauf hinterlegt und nicht im Code festgeschrieben:

```text
run
├── Zuführ-ESP, Zähler: auf die Menge scharf          reports_amount
├── Verteiler, Ventil 1: öffnen
├── Verteiler, Ventil 2: öffnen
└── Tank, Ventil 1: öffnen und Schlauchsensor melden
        └── Zuführ-ESP, Pumpe: ein
                wartet auf das Ventil und den Schlauchsensor

close
├── Zuführ-ESP, Pumpe: aus
└── Ventile zu
        warten auf Pumpe aus
```

Zähler und Ventile starten zusammen. Wer von ihnen zuerst fertig meldet, ist dem Knoten
überlassen. Die Pumpe wartet auf die Meldungen, von denen sie abhängt. Die Abschlussfolge
läuft nach Erfolg und nach Fehler.

Befehl, Beispiel für `nsm/device/esp-tank-1/cmd/dose_fertilizer`:

```json
{
  "request_id": "9f2c1b7e-5a44-4c91-9c0e-2f8d7a1b3e55",
  "job_id": 137,
  "fertilizer_id": 3,
  "amount_ml": 55.4,
  "issued_at": "2026-10-06T16:11:00Z"
}
```

Antwort auf `nsm/device/esp-tank-1/evt/dose_fertilizer`:

```json
{
  "request_id": "9f2c1b7e-5a44-4c91-9c0e-2f8d7a1b3e55",
  "job_id": 137,
  "status": "ok",
  "dosed_ml": 55.1,
  "finished_at": "2026-10-06T16:11:09Z"
}
```

Die `request_id` steht in beiden Richtungen und ist der Schlüssel für die Zuordnung. Die
`job_id` ist fachlich redundant, erleichtert aber das Lesen der Protokolle erheblich.

### Eine Dosierung darf nicht zweimal laufen

Das ist die sicherheitskritische Festlegung dieses Abschnitts. MQTT mit QoS 1 liefert
mindestens einmal, also unter Umständen zweimal. Bricht die Verbindung nach dem Absetzen
eines Dosierbefehls ab und wird der Befehl wiederholt, könnte der ESP32 ein zweites Mal
pumpen.

| Nr. | Regel |
|---|---|
| G-1 | Jeder Befehl trägt eine einmalige `request_id`. |
| G-2 | Der ESP32 führt eine Anforderung mit bereits gesehener `request_id` **nicht** erneut aus, sondern sendet nur die gespeicherte Antwort erneut. |
| G-3 | Der Pi verwirft eine Antwort, deren `request_id` nicht zur erwarteten des Jobs passt. |
| G-4 | Der Pi verwirft eine Antwort auf einen Job, der nicht im Zustand `waiting_device` ist. |
| G-5 | Dosierbefehle werden mit QoS 1 veröffentlicht, nie mit QoS 0. Ein verlorener Dosierbefehl ist schlimmer als ein doppelt empfangener, weil G-2 letzteren abfängt. |

G-2 verlangt eine kleine Liste zuletzt gesehener Anforderungen in der Firmware. Das ist
Teil der ESP32-Aufgabe und keine Eigenschaft dieses Systems, muss aber hier festgehalten
werden, weil die Sicherheit der Dosierung davon abhängt.

### Fristen und was bei Ablauf geschieht

| Jobtyp | Frist | Bei Ablauf |
|---|---|---|
| `MeasureProbe` | `measure_timeout_seconds`, Standard 30 s | `failed`. Wiederholung ist unkritisch, erfolgt aber nur durch einen neuen Zyklus. |
| `Mix` | Dauer plus `mix_timeout_margin_seconds`, Standard 30 s | `failed` |
| `DoseFertilizer` | `dose_fertilizer_timeout_seconds`, Standard 120 s | `failed`, ausdrücklich mit Hinweis auf manuelle Prüfung |
| `DosePhAdjuster` | `dose_ph_adjuster_timeout_seconds`, Standard 120 s | ebenso |
| `AdjustVolume` | `adjust_volume_timeout_seconds`, Standard 600 s | ebenso |
| `DeviceCommand` | `timeout_seconds` des Schritts, sonst die Frist des übergeordneten Jobtyps | Schritt `failed`, kein weiterer `run`-Schritt, Abschlussfolge, Dosierjob und Zyklus `failed` |

Die Fristen stehen am Tank (O-11, entschieden am 2026-10-07). Die Tabelle nennt die
Standards.

Entscheidend ist die Behandlung der Dosierjobs: Bei einer abgelaufenen Frist weiß der Pi
**nicht**, ob die Pumpe gelaufen ist. Weiterrechnen wäre in beide Richtungen falsch, und
ein automatischer zweiter Versuch könnte die doppelte Menge dosieren. Deshalb gilt für
`DoseFertilizer`, `DosePhAdjuster` und `AdjustVolume`:

```text
Frist abgelaufen
        ↓
Job auf failed, Zyklus auf failed
        ↓
failure_reason nennt die ungewisse Menge
        ↓
keine automatische Wiederholung
        ↓
manuelle Prüfung des Tanks erforderlich
```

Eine Messung darf dagegen gefahrlos erneut angefordert werden, weil sie nichts verändert.

Die Fristüberwachung läuft in derselben Dispatcher-Abfrage wie die Fälligkeitsprüfung: Vor
der Auswahl des nächsten Jobs werden Jobs im Zustand `waiting_device` mit abgelaufenem
`timeout_at` abgeschlossen. Ein eigener Zeitgeber ist dafür nicht nötig.

### Wo der MQTT-Client läuft

Als Hintergrundaufgabe im FastAPI-Prozess, gestartet und beendet über die
Lebenszyklusverwaltung der Anwendung. Ein zweiter, eigener Prozess wäre sauberer getrennt,
würde aber bedeuten, dass zwei Prozesse in dieselbe SQLite-Datei schreiben. Das verlangt
nach `busy_timeout` und einer Sperrstrategie und ist genau die Art von Komplexität, die
nach 4.2 den Wechsel auf PostgreSQL rechtfertigen würde. Solange es bei SQLite bleibt,
bleibt es bei einem Prozess.

### Unaufgeforderte Messwerte

Ein ESP32 kann Messwerte auch ohne Befehl senden, etwa stündlich zur Überwachung. Solche
Werte werden als Messung mit `source = "sensor"` und ohne `job_id` gespeichert und lösen
keinen Zyklus aus. Sie dienen dem Verlauf und der Überwachung. Ob daraus eine automatische
Regelung angestoßen wird, entscheidet der Zeitplan aus M7, nicht der Messwert selbst.

## 9.8 Simulation der Gerätekommunikation

Drei Stufen, die unterschiedliche Dinge prüfen. Alle drei werden vorgesehen.

| Stufe | Ort | MQTT | Prüft |
|---|---|---|---|
| 1 Sofort | im Prozess | nein | Fachlogik, Berechnungen, Zyklusablauf |
| 2 Zeitversetzt | im Prozess | nein | asynchronen Zustandsautomaten, Fristen, doppelte Antworten |
| 3 Gerätattrappe | eigener Prozess | ja | Themenstruktur, Nachrichtenformate, Verbindungsverhalten |

### Stufe 1 – sofortige Antwort

Das simulierte Gerät berechnet die Antwort und schließt den Job in derselben Transaktion
ab. Der Job sieht `waiting_device` nie. Deterministisch und schnell, deshalb die Grundlage
nahezu aller Tests und der Inhalt von M5.

### Stufe 2 – zeitversetzte Antwort

Das simulierte Gerät setzt den Job auf `waiting_device`, hinterlegt `request_id` und
`timeout_at` und legt die Antwort mit einer Verzögerung bereit. Damit werden genau die
Fälle prüfbar, die in Stufe 1 nicht auftreten können: Fristablauf, doppelt eintreffende
Antwort, Antwort mit falscher `request_id`, Antwort auf einen bereits abgeschlossenen Job.

In Tests wird dafür nicht gewartet, sondern die Uhr vorgestellt. Das ist der Grund, weshalb
die aktuelle Zeit nach Regel Z-3 ausschließlich aus `utcnow()` kommt: Eine einzige Stelle
lässt sich im Test ersetzen, über den Code verstreute `datetime.now()`-Aufrufe nicht.

### Stufe 3 – Gerätattrappe als eigener Prozess

Ein kleines Skript unter `tools/fake_esp.py`, das sich am Broker anmeldet, die
Befehlsthemen abonniert, eine Verarbeitungszeit abwartet und eine Antwort veröffentlicht.
Es führt dabei ein eigenes Tankmodell mit Volumen, EC und pH, damit aufeinanderfolgende
Messungen zusammenpassen und die Wirkung einer Dosierung sichtbar wird.

Der Code auf dem Pi ist dabei vollständig identisch zum Echtbetrieb. Das ist der Zweck
dieser Stufe: Sie prüft, was Stufe 1 und 2 grundsätzlich nicht prüfen können, weil dort
kein Broker beteiligt ist. Die Attrappe kann zusätzlich Fehlerfälle erzeugen, die mit
echter Hardware schwer herzustellen sind — gar keine Antwort, verzögerte Antwort, doppelte
Antwort, Antwort mit abweichender Menge.

Die Attrappe ist Werkzeug, nicht Teil der Anwendung. Sie liegt deshalb unter `tools/` und
nicht unter `app/`, und die Abhängigkeitsregeln aus 5.2 gelten für sie nicht.

---

# 10. Persistenz

## 10.1 Engine und Verbindungen

```python
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()
```

`foreign_keys=ON` schließt die Lücke N-3. SQLite prüft Fremdschlüssel ohne dieses Pragma
nicht, selbst wenn sie im Schema stehen: Eine Wachstumsphase mit einer `plant_id`, die es
nicht gibt, würde ohne Fehler gespeichert. Das Pragma gilt pro Verbindung und muss daher
per Event-Listener gesetzt werden.

`journal_mode=WAL` erlaubt Lesen während eines Schreibvorgangs. `check_same_thread=False`
ist nötig, weil FastAPI Anfragen in verschiedenen Threads bearbeitet.

## 10.2 Sessions

| Kontext | Herkunft der Session |
|---|---|
| HTTP-Anfrage | FastAPI-Dependency `get_session`, eine Session pro Anfrage |
| Jobausführung | Eine Session pro Job, vom Dispatcher geöffnet |
| Tests | Fixture mit eigener Datenbank, siehe 12.2 |

Ein Service bekommt eine Session übergeben und öffnet selbst keine. Ein Job wird komplett
in einer Transaktion ausgeführt: Erzeugt er Folgejobs und schlägt dann fehl, entstehen
auch die Folgejobs nicht. Der Statuswechsel auf `failed` samt `error_message` wird danach
in einer eigenen Transaktion geschrieben, damit die Fehlerinformation den Rollback
überlebt.

## 10.3 Migrationen

Alembic mit `render_as_batch=True`, weil SQLite `ALTER COLUMN` nicht beherrscht und
Alembic die Tabelle dafür neu aufbauen muss. Autogenerate erkennt ein Model nur, wenn es
in `app/models/__init__.py` importiert ist.

Verbindliche Regeln:

| Nr. | Regel |
|---|---|
| M-1 | Jede Schemaänderung bekommt eine eigene Revision. Kein Bearbeiten bereits angewandter Revisionen. |
| M-2 | Autogenerierte Revisionen werden vor dem Festschreiben gelesen und korrigiert. |
| M-3 | Revisionen haben eine aussagekräftige `message`, nicht nur den Hash. |
| M-4 | Jede Revision hat ein funktionierendes `downgrade`. |
| M-5 | Ein Test prüft, dass `alembic upgrade head` ein Schema erzeugt, das zu den Models passt. |

M-5 ist nötig, weil die Tests aus Geschwindigkeitsgründen über `Base.metadata.create_all`
arbeiten und ein Auseinanderlaufen von Models und Migrationen sonst unentdeckt bliebe.

### Migrationen beim Start

Die Anwendung führt `alembic upgrade head` beim Start selbst aus, vor dem Wiederaufsetzen
nach W-1. Schlägt das fehl, startet sie nicht.

Entschieden am 2026-10-06 für den automatischen Weg. Das System läuft als einzelne Instanz
auf einem Gerät, es gibt also keine zwei Prozesse, die gleichzeitig migrieren könnten —
das übliche Gegenargument entfällt damit. Dafür kann eine Auslieferung auf dem Pi nicht
mehr dadurch misslingen, dass ein Schritt von Hand vergessen wurde; der Fehler
„no such table" aus dem Altprojekt kann so nicht wieder auftreten.

Sollte später doch mehr als eine Instanz laufen, ist diese Festlegung zurückzunehmen.

## 10.4 Konfiguration

Über `pydantic-settings` aus Umgebungsvariablen und `.env`, mit `.env.example` im
Repository.

| Variable | Standard | Bedeutung |
|---|---|---|
| `NSM_DATABASE_URL` | `sqlite:///./nsm.db` | Datenbank |
| `NSM_LOG_LEVEL` | `INFO` | Protokollierungsstufe |
| `NSM_DEFAULT_STABILIZATION_SECONDS` | `120` | Vorbelegung neuer Tanks |
| `NSM_DEFAULT_MAX_CORRECTION_ATTEMPTS` | `3` | Vorbelegung neuer Tanks |
| `NSM_DEFAULT_MAX_CYCLE_DURATION_MINUTES` | `1440` | Vorbelegung neuer Tanks, siehe S-6 |

Die Datenbankdatei und `.env` gehören nicht ins Repository.

---

# 11. Konventionen

## 11.1 Projektstruktur und Benennung

```text
nutrient-solution-manager/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── dependencies.py
│   │   ├── errors.py              Exception-Handler
│   │   └── routers/               Plural: plants.py, growth_stages.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── exceptions.py          Fehlerklassen der Fachschicht
│   ├── models/                    Singular: plant.py, growth_stage.py
│   ├── schemas/                   Singular
│   ├── services/                  Singular
│   ├── calculations/              ec.py, ph.py, volume.py, target_range.py, safety.py
│   ├── jobs/
│   │   ├── base.py                Protokoll eines Jobtyps
│   │   ├── dispatcher.py
│   │   ├── registry.py
│   │   └── types/                 measure_probe.py, compare_probe.py, ...
│   ├── devices/
│   │   ├── protocols.py           MeasurementSource, Actuator
│   │   ├── manual.py
│   │   ├── simulated.py           Stufe 1 und 2 aus 9.8
│   │   └── mqtt.py                ab M9
│   └── enums/
├── tests/
│   ├── conftest.py
│   ├── factories/
│   ├── unit/
│   ├── integration/
│   └── api/
├── tools/
│   ├── seed.py                    Beispieldaten, siehe 14.1
│   └── fake_esp.py                Gerätattrappe, Stufe 3 aus 9.8
├── alembic/
├── docs/
│   ├── pflichtenheft.md
│   └── projektkonzept.md
├── .github/
│   └── workflows/ci.yml           zwei Aufträge, siehe 13.3
├── .env.example
├── .gitattributes                 Zeilenenden, siehe 13.3
├── pyproject.toml
├── uv.lock
└── README.md
```

| Gegenstand | Konvention | Beispiel |
|---|---|---|
| Model-Modul | Singular | `app/models/growth_stage.py` |
| Model-Klasse | Singular, PascalCase | `GrowthStage` |
| Tabelle | Plural, snake_case | `growth_stages` |
| Schema-Modul | Singular | `app/schemas/growth_stage.py` |
| Schema-Klassen | Objekt plus Zweck | `GrowthStageCreate`, `GrowthStageUpdate`, `GrowthStageResponse` |
| Service-Modul | Singular, ohne Suffix | `app/services/growth_stage.py` |
| Service-Klasse | Objekt plus `Service` | `GrowthStageService` |
| Router-Modul | Plural | `app/api/routers/growth_stages.py` |
| URL-Pfad | Plural, Bindestriche | `/growth-stages` |
| Fremdschlüssel | Objekt im Singular plus `_id` | `plant_id` |
| Zeitstempel | Partizip plus `_at` | `measured_at`, `finished_at` |
| Mengen mit Einheit | Einheit im Namen | `amount_ml`, `volume_liters`, `temperature_c` |

Die Einheit im Feldnamen ist bewusst gewählt. Bei einem System, das Flüssigkeiten dosiert,
ist eine Verwechslung von Milliliter und Liter ein realer Schaden.

Der Router-Import erfolgt ausdrücklich über den Router, nicht über das Modul:

```python
from app.api.routers.growth_stages import router as growth_stages_router

app.include_router(growth_stages_router)
```

## 11.2 Aufbau eines Service

```python
class GrowthStageService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, data: GrowthStageCreate) -> GrowthStage: ...
    def get(self, growth_stage_id: int) -> GrowthStage: ...
    def list(self) -> Sequence[GrowthStage]: ...
    def update(self, growth_stage_id: int, data: GrowthStageUpdate) -> GrowthStage: ...
    def delete(self, growth_stage_id: int) -> None: ...
```

| Nr. | Regel |
|---|---|
| C-1 | `get` liefert nie `None`, sondern wirft `NotFoundError`. |
| C-2 | `list` gibt `Sequence[...]` zurück, weil `.all()` genau das liefert. Behebt N-8. |
| C-3 | Objekte entstehen über `Model(**data.model_dump())`, nicht durch Aufzählen aller Felder. |
| C-4 | `update` verwendet `model_dump(exclude_unset=True)`, damit nicht gesetzte Felder unberührt bleiben. |
| C-5 | `update` und `delete` laden über das eigene `get` und erben so die Prüfung aus C-1. |
| C-6 | Der Service schreibt `commit`. Router und Jobs committen nicht selbst. |
| C-7 | Nach `commit` folgt `refresh`, wenn der Aufrufer datenbankseitige Werte braucht. |
| C-8 | Kein Service importiert FastAPI. |

Zu C-3: Im Altstand zählt `GrowthStageService.create` alle neun Felder einzeln auf. Jedes
neue Feld muss dort nachgetragen werden, und ein vergessenes Feld fällt nur durch einen
Test auf.

## 11.3 Zeitstempel

### Das Problem

SQLite kennt keinen Datums- und Zeittyp. Werte werden als Text abgelegt, und
`DateTime(timezone=True)` liefert dort beim Lesen **naive** `datetime`-Objekte zurück, auch
wenn zeitzonenbehaftete Werte geschrieben wurden. Python verweigert anschließend den
Vergleich zwischen naivem und zeitzonenbehaftetem `datetime` mit einem `TypeError`.

Das trifft nicht irgendeine Nebenstelle, sondern die zentrale Abfrage des Systems: Der
Dispatcher vergleicht `run_after` gegen die aktuelle Zeit. Eine unklare Festlegung an
dieser Stelle führt zu einem Fehler, der erst zur Laufzeit und nur bei bestimmten Daten
auftritt.

### Die Festlegung

Alle Zeitstempel werden über einen eigenen Spaltentyp abgewickelt:

```python
class UtcDateTime(TypeDecorator[datetime]):
    """Speichert naiv in UTC, liefert zeitzonenbehaftet in UTC zurück."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("Naives datetime ist nicht erlaubt.")
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc)
```

| Nr. | Regel |
|---|---|
| Z-1 | Jede Zeitspalte verwendet `UtcDateTime`, nie `DateTime` direkt. |
| Z-2 | Im Python-Code sind alle `datetime`-Werte zeitzonenbehaftet und in UTC. |
| Z-3 | Die aktuelle Zeit kommt ausschließlich aus einer Hilfsfunktion `utcnow()`. `datetime.now()` ohne Zeitzone ist verboten und wird per Linter-Regel unterbunden. |
| Z-4 | Umrechnung in Ortszeit geschieht erst in der Anzeige, nie in der Datenbank. |

Die Alternative wäre, durchgehend naiv in UTC zu arbeiten. Das wäre weniger Code, aber jede
Vergleichsstelle müsste sich darauf verlassen, dass wirklich überall UTC gemeint ist, und
ein Wechsel auf PostgreSQL nach 4.2 würde das Verhalten still verändern. Der Spaltentyp
kostet fünfzehn Zeilen und macht die Annahme unverletzbar.

`created_at` und `updated_at` stehen auf jeder Tabelle und werden über eine gemeinsame
Basisklasse gesetzt, nicht pro Model wiederholt.

## 11.4 Fehlerbehandlung

In `app/core/exceptions.py`:

```text
NsmError
├── NotFoundError          → 404
├── ConflictError          → 409
├── ValidationError        → 422
├── SafetyLimitExceeded    → 409
└── JobStateError          → 409
```

Diese Klassen werden in `app/api/errors.py` einmal zentral auf HTTP-Antworten abgebildet:

```python
@app.exception_handler(NotFoundError)
async def handle_not_found(request: Request, exc: NotFoundError) -> JSONResponse: ...
```

Damit entfällt der wiederholte `try/except` in jedem einzelnen Endpunkt, der im Altstand
in jeder Router-Funktion steht, siehe N-7. Ein Endpunkt sieht dann so aus:

```python
@router.get("/{growth_stage_id}", response_model=GrowthStageResponse)
def get_growth_stage(
    growth_stage_id: int,
    session: Session = Depends(get_session),
) -> GrowthStage:
    return GrowthStageService(session).get(growth_stage_id)
```

`LookupError` aus dem Altstand wird durch `NotFoundError` ersetzt. Eigene Klassen können
einen Fehlercode und den betroffenen Datensatz tragen, eingebaute Ausnahmen nicht.

## 11.5 Typannotationen

Vollständige Annotationen an allen öffentlichen Funktionen, `-> None` wird ausgeschrieben.
Moderne Syntax `X | None` statt `Optional[X]`, `list[X]` statt `List[X]`. mypy läuft im
Strict-Modus. Für Forward-Referenzen in SQLAlchemy-Beziehungen wird
`if TYPE_CHECKING:`-Import verwendet, damit der Typprüfer die Gegenseite kennt.

---

# 12. Teststrategie

## 12.1 Ebenen

| Ebene | Gegenstand | Datenbank | HTTP |
|---|---|---|---|
| Unit | Berechnungen, Schema-Validierung | nein | nein |
| Integration | Services, Beziehungen, Löschregeln, Jobausführung | ja | nein |
| API | Endpunkte, Statuscodes, Fehlerformat | ja | `TestClient` |

## 12.2 Testdatenbank

Das ist die wichtigste Korrektur gegenüber dem Altstand, siehe N-1.

| Nr. | Regel |
|---|---|
| T-1 | Tests benutzen niemals `app.core.database.SessionLocal` und niemals `nsm.db`. |
| T-2 | Jeder Test erhält eine eigene SQLite-Datenbank im Arbeitsspeicher, erzeugt per `create_all`, verworfen am Testende. |
| T-3 | Die In-Memory-Engine wird mit `StaticPool` und `check_same_thread=False` gebaut, damit alle Verbindungen dieselbe Datenbank sehen. |
| T-4 | API-Tests ersetzen `get_session` über `app.dependency_overrides` und räumen die Überschreibung danach auf. |
| T-5 | `PRAGMA foreign_keys=ON` gilt auch für die Testdatenbank, sonst werden die Löschregeln aus 6.3 nicht geprüft. |
| T-6 | Kein Test verlässt sich auf eine bestimmte Id. Behebt N-2. |
| T-7 | Kein Test hängt davon ab, ob ein anderer Test vorher gelaufen ist. |

Begründung zu T-2: Eine Datenbank pro Test ist bei SQLite im Arbeitsspeicher schnell
genug und schlägt die Alternative, nach jedem Test die Tabellen zu leeren, an
Verlässlichkeit. Ein Rückrollen der Transaktion am Testende funktioniert hier nicht, weil
die Services nach Regel C-6 selbst committen.

## 12.3 Testdaten

Testdaten entstehen über Factory-Fixtures in `tests/factories/`. Eine Factory erzeugt ihre
Voraussetzungen selbst und gibt das erzeugte Objekt zurück:

```python
def test_growth_stage_belongs_to_plant(session, make_growth_stage):
    stage = make_growth_stage(session)
    assert stage.plant_id is not None
```

Die Factory legt also die Pflanze selbst an, statt ein vorhandenes `plant_id=1`
vorauszusetzen. Überschreiben einzelner Felder geschieht über Schlüsselwortargumente, nicht
durch Verändern eines gemeinsamen Fixture-Objekts.

## 12.4 Pflichttests pro Baustein

| Gegenstand | Mindestens zu prüfen |
|---|---|
| Jedes Schema | ein gültiger Fall, je ein Fall pro Grenzverletzung |
| `GrowthStage`-Schema | V-7 und V-8 verletzt, Gleichheit erlaubt |
| Jeder Service | `create`, `get`, `list`, `update` mit Teilmenge, `delete`, `get` nach `delete` wirft `NotFoundError` |
| Löschregeln | je Beziehung aus 6.3 ein Test |
| Jeder Endpunkt | Erfolgsfall, 404 bei unbekannter Id, 422 bei ungültiger Eingabe |
| EC-Berechnung | das Beispiel aus 8.2, Division durch Null, negative Differenz |
| Mischungsrechnung | das Beispiel aus 8.3, `source_water_ec >= ec_target`, Tank zu klein |
| Zielbereichsprüfung | unter Minimum, über Maximum, innerhalb, genau auf der Grenze |
| Sicherheitsgrenzen | je Grenze S-1 bis S-6 ein Test |
| Plausibilität | je Prüfung P-1 bis P-5 ein Test |
| Jeder Jobtyp | Erfolgsfall, erzeugte Folgejobs, Fehlerfall, Zustandsübergänge |
| `CompareProbe` | je Rangfolgestufe ein Test, zusätzlich mehrere gleichzeitige Abweichungen mit genau einem erzeugten Job |
| Dispatcher | Reihenfolge nach `run_after`, Überspringen nicht fälliger Jobs, Verhalten bei leerer Liste, Abwechseln zwischen zwei Tanks |
| Zyklus | vollständiger Durchlauf bis `succeeded`, Abbruch bei `max_correction_attempts` je Größe, `blocked` und anschließende Freigabe, Abbruch durch den Betreiber, Abbruch durch S-6 |
| Wiederaufsetzen | je Jobtyp aus 5.3 die Behandlung nach W-1 bis W-3, Dosierjob nach Abbruch nicht erneut ausgeführt |
| Momentaufnahme | `CompensationEC` schreibt verwendete Anteile und EC-Wirkungen; nach Änderung der Rezeptur bleibt das Jobergebnis unverändert |
| Listen | Standard-`limit` 100, Werte über 1000 werden auf 1000 gekürzt, Antwort enthält die Gesamtzahl |
| Zeitstempel | Schreiben und Lesen über `UtcDateTime`, Ablehnung naiver Werte, Vergleich mit `utcnow()` |
| Sommerzeit | eine nicht existierende und eine doppelte Ortszeitstunde, siehe M7 |
| Gerätekommunikation | je Regel G-3 und G-4 ein Test, Fristablauf je Jobtyp, doppelte Antwort, Antwort mit falscher `request_id` |
| Migrationen | M-5, plus ein Start mit fehlender Tabelle, nach dem die Tabelle existiert |

Grenzfälle werden mit `pytest.mark.parametrize` zusammengefasst. Im Altprojekt war das
zurückgestellt; hier ist es von Anfang an vorgesehen, weil die Tabelle oben sonst in sehr
viele fast gleiche Testfunktionen zerfällt.

Gleitkommawerte werden mit `pytest.approx` verglichen, nie auf Gleichheit. Alle Mengen und
Messwerte sind `float`, und eine Rezeptwirkung von `0,3×0,1 + 0,3×0,2 + 0,4×0,1` ergibt
nicht exakt `0,13`. Ein Test, der darauf besteht, schlägt scheinbar grundlos fehl.

## 12.5 Abdeckung

`app/calculations/` muss vollständig abgedeckt sein, weil dort die Dosiermengen entstehen.
Für `app/services/` und `app/jobs/` gilt eine Zweiglabdeckung von mindestens 90 Prozent,
für das Gesamtprojekt mindestens 80 Prozent. Die CI bricht bei Unterschreitung ab.

---

# 13. Qualitätssicherung

## 13.1 Werkzeuge

| Werkzeug | Aufruf | Zweck |
|---|---|---|
| ruff | `uv run ruff check .` | Linter |
| ruff | `uv run ruff format .` | Formatierung |
| mypy | `uv run mypy app` | Typprüfung, Strict-Modus |
| pytest | `uv run pytest` | Tests mit Abdeckung |

## 13.2 Entwicklungs- und Testumgebung

Entwickelt wird auf Windows, betrieben wird auf einem Raspberry Pi mit ARM64-Linux. Dieser
Abschnitt legt fest, wo welche Prüfung läuft und warum.

### Was überhaupt plattformabhängig ist

Diese Unterscheidung trägt die ganze Festlegung. Der weit überwiegende Teil der Testsuite
aus Kapitel 12 — Berechnungen, Schema-Validierung, Services, Beziehungen, Jobzustände,
Endpunkte — verhält sich auf Windows, x86-Linux und ARM-Linux gleich. Diese Tests auf der
Zielhardware auszuführen liefert keine zusätzliche Erkenntnis, nur längere Laufzeit.

| Gegenstand | Wird nur erkannt auf |
|---|---|
| Groß- und Kleinschreibung in Import- und Dateinamen | Linux, gleich welcher Architektur |
| Pfadtrennzeichen, absolute Pfade | Linux |
| Zeilenenden in Skripten, ab M8 im Container | Linux |
| Fehlende vorgefertigte Pakete für `aarch64` | ARM64 |
| SQLite-Version aus Raspberry Pi OS | Pi |
| systemd-Einheit, Regeln B-1 und B-2 aus 14.3 | Pi |
| Verhalten echter Hardware, ab M9 | Pi mit ESP32 |

Die Groß- und Kleinschreibung ist dabei die häufigste Falle: Windows unterscheidet
`app/Models/plant.py` nicht von `app/models/plant.py`, Linux schon. Ein Import, der lokal
läuft, lässt die Anwendung auf dem Pi beim Start abstürzen. Ohne eine Linux-Prüfung fällt
das nie auf.

### Drei Stufen

| Stufe | Wo | Umfang | Wann |
|---|---|---|---|
| 1 | Windows, nativ | vollständige Testsuite, ruff, mypy | laufend während der Entwicklung |
| 2 | CI, Linux x64 und ARM64 | vollständige Prüfkette | bei jedem Push und Pull Request |
| 3 | Raspberry Pi, von Hand | Auslieferungstest, einmal die Testsuite als Stichprobe | je Meilenstein |

**Stufe 1** läuft ohne Container. uv arbeitet auf Windows einwandfrei, und jede zusätzliche
Schicht verlangsamt eine Schleife, die am Tag dutzende Male durchlaufen wird.

**Stufe 2** ist das Tor. Der x64-Auftrag fängt alles, was Linux von Windows unterscheidet,
der ARM64-Auftrag zusätzlich die fehlenden Pakete für die Zielarchitektur. Damit ersetzt die
CI den Pi als Testumgebung nahezu vollständig, weil sie dieselbe Architektur verwendet.

**Stufe 3** prüft, was keine gemietete Maschine prüfen kann: Migrationen auf der echten
Datei, Dienststart, Zeitabgleich, ab M9 die Hardware. Nicht bei jedem Commit, sondern am
Ende eines Meilensteins. Die vollständige Testsuite dort einmal mitlaufen zu lassen kostet
wenige Minuten und ist als Stichprobe sinnvoll, aber kein Tor.

### Wofür Docker verwendet wird und wofür nicht

| Zweck | Docker? |
|---|---|
| Ausliefern ab M8 | ja, das ist der Zweck |
| Nachstellen eines Fehlers, den die CI meldet und Windows nicht zeigt | ja, als Werkzeug |
| Tägliche Entwicklungs- und Testschleife | nein |

Unter Windows läuft Docker in einer virtuellen Maschine, und Dateizugriffe aus dem
Container auf das Projektverzeichnis gehen über eine Freigabe. Bei einer Testsuite, die
vielfach pro Stunde startet, ist das deutlich spürbar. Dazu kommt, dass im Fehlerfall der
Container zum Gegenstand der Fehlersuche wird und nicht der Code.

Wer lokal eine Linux-Umgebung braucht, ohne auf die CI zu warten, nimmt **WSL2** mit dem
Projektverzeichnis im Linux-Dateisystem. Das ist optional und ersetzt Stufe 2 nicht.

### Kein selbstbetriebener CI-Läufer auf dem Pi

Am 2026-10-06 geprüft und **verworfen**. Technisch möglich, aber aus vier Gründen
abgelehnt:

| Nr. | Grund |
|---|---|
| L-1 | Der Pi ist ab M7 die Produktionsmaschine. Ein CI-Lauf konkurriert mit dem regelnden Dienst um CPU und Festspeicher, während womöglich ein Dosierjob fällig wird. |
| L-2 | Jeder Lauf erzeugt erhebliche Schreiblast durch `uv sync`, virtuelle Umgebungen und Zwischenspeicher. Genau diese Last soll nach 14.3 vom Speichermedium fernbleiben. |
| L-3 | Ein Läufer hat Schreibrechte auf der ganzen Maschine. Eine Verletzung der Regeln T-1 und T-2 träfe dort die Betriebsdatenbank statt einer Wegwerfdatei. |
| L-4 | Bei einem öffentlichen Projekt kann ein Beitragsvorschlag aus einer Abspaltung beliebigen Code auf dem Läufer ausführen — also im Heimnetz, auf dem Gerät, das die Pumpen steuert. GitHub rät davon ausdrücklich ab. |

Hinzu kommt, dass der zusätzliche Nutzen gering ist: Die kostenlosen ARM64-Läufer haben
dieselbe Architektur wie der Pi und fangen damit den einzigen Punkt, den die x64-Prüfung
nicht abdeckt.

Diese Entscheidung ist **ab M9 neu zu bewerten**. Tests mit echter Hardware in der Schleife
— eine Pumpe, die wirklich läuft — kann keine gemietete Maschine ausführen. Dann wäre ein
selbstbetriebener Läufer das richtige Werkzeug, aber auf einem **zweiten**, eigens dafür
bestimmten Pi und nicht auf dem Betriebsgerät. Bis dahin deckt die Attrappe aus 9.8 den
Weg über den Broker ab.

## 13.3 CI

GitHub Actions bei jedem Push und jedem Pull Request, in zwei Aufträgen:

| Auftrag | Läufer | Architektur |
|---|---|---|
| `test-x64` | `ubuntu-latest` | x86-64 |
| `test-arm64` | `ubuntu-24.04-arm` | ARM64, entspricht dem Pi |

Beide führen dieselbe Kette aus:

```text
uv sync
        ↓
ruff format --check
        ↓
ruff check
        ↓
mypy app
        ↓
pytest mit Abdeckungsschwelle
        ↓
Abhängigkeitsregeln D-1 bis D-5 prüfen
```

Die ARM64-Läufer sind für öffentliche Projekte kostenlos und unbegrenzt. Bleibt das
Projekt privat, verbrauchen sie Minuten; dann läuft `test-arm64` nur auf `main`, während
`test-x64` bei jedem Push läuft.

Die Prüfung der Abhängigkeitsregeln erfolgt über `ruff`-Regel `TID251` für verbotene
Importe. Damit wird die Architektur aus Kapitel 5 maschinell durchgesetzt und nicht nur
dokumentiert.

### Zeilenenden

Eine `.gitattributes` im Projektwurzelverzeichnis legt `* text=auto eol=lf` fest, für
`*.ps1` ausdrücklich `eol=crlf`. Ohne das wandern unter Windows erzeugte Zeilenenden in
Skripte, die ab M8 im Container ausgeführt werden, und scheitern dort.

## 13.4 Protokollierung

Strukturierte Protokollierung über das `logging`-Modul der Standardbibliothek, Stufe aus
der Konfiguration. Jeder Jobwechsel wird mit Jobtyp, Jobnummer, Zyklusnummer und
Statuswechsel protokolliert. Jede berechnete Dosiermenge wird mit allen Eingangswerten
protokolliert, damit im Nachhinein nachvollziehbar ist, worauf eine Dosierung beruhte.

Keine Protokollierung über `print`. Keine Messwerte oder Dosiermengen nur im Protokoll —
alles Fachliche steht in der Datenbank.

---

# 14. Betrieb

## 14.1 Entwicklung

```powershell
uv sync
uv run alembic upgrade head
uv run python -m tools.seed        # optional, Beispieldaten
uv run fastapi dev app/main.py
```

Die API-Dokumentation liegt unter `/docs` und ist bis M6 die Bedienoberfläche.

### Startdaten

`tools/seed.py` legt einen vollständigen, lauffähigen Beispielbestand an: eine Pflanze mit
zwei Wachstumsphasen samt Sollwerten, drei Dünger mit EC-Wirkung, eine Rezeptur mit den
Anteilen 30, 30 und 40 Prozent, und einen Tank mit Sicherheitsgrenzen und `source_water_ec`.

Das ist nicht nur Bequemlichkeit. Nach dem ersten Start ist das System unbenutzbar, bis
sechs zusammenhängende Datensätze angelegt sind — ohne Rezeptur lehnt `CompensationEC` nach
9.4 jede Berechnung ab. Zugleich ist das Skript die beste Prüfung, ob die Stammdaten aus M2
tatsächlich zusammenpassen, und es liefert die Zahlen des Beispiels aus 8.2, sodass eine
Berechnung von Hand nachvollziehbar bleibt.

Das Skript ist bewusst wiederholbar aufgerufen unschädlich: Es prüft auf vorhandene Namen
und legt nichts doppelt an. Es liegt unter `tools/` und ist nicht Teil der Anwendung.

## 14.2 Zielbetrieb

Zielplattform ist ein Raspberry Pi im Heimnetz, festgelegt in 14.3. Dort laufen API,
SQLite-Datei und ab M6 auch die Weboberfläche auf demselben Gerät. Ab M9 kommt der
MQTT-Broker dazu, entweder auf demselben Pi oder im Netz daneben.

Bis M7 wird die Anwendung bei Bedarf gestartet. Ab M7 läuft sie dauerhaft, weil der
Scheduler Zyklen zeitgesteuert anstößt, und wird daher als Dienst eingerichtet. Ab M8
geschieht das in einem Container. Die Datenbankdatei liegt dann in einem Volume, damit sie
den Neubau des Containers überlebt.

Dass alles auf einem Gerät läuft, ist der eigentliche Grund für mehrere Festlegungen
dieses Dokuments: SQLite statt eines Datenbankservers, ein Prozess statt mehrerer nach
9.7, und der MQTT-Client als Hintergrundaufgabe in der Anwendung. Ein Pi verträgt das
ohne Weiteres, solange nicht mehrere Prozesse um dieselbe Datenbankdatei konkurrieren.

## 14.3 Zielplattform

| Gegenstand | Festlegung |
|---|---|
| Gerät | Raspberry Pi 4 |
| Betriebssystem | Raspberry Pi OS Lite, 64-bit, Debian 13 Trixie |
| Python | 3.13 aus der Distribution |
| Startmedium | USB-SSD, nicht SD-Karte |
| Zeitzone des Systems | `Europe/Berlin` |
| Zeitabgleich | NTP, Dienststart erst nach erfolgtem Abgleich |
| Dienstverwaltung | systemd, ab M7 |

### Begründung der Auswahl

**Debian 13 Trixie** liefert Python 3.13 als Systemversion und deckt damit
`requires-python = ">=3.13"` aus 4.1 unmittelbar ab. Auf Debian 12 Bookworm wäre es Python
3.11, und uv müsste eine eigene Laufzeitumgebung nachladen — eine zusätzliche bewegliche
Komponente ohne Gegenwert.

**Lite statt Desktop**, weil der Pi headless betrieben wird. Die Weboberfläche aus M6 wird
von einem anderen Gerät im Netz aufgerufen; auf dem Pi muss kein Browser laufen. Das
Abbild ist etwa ein Drittel so groß, und ein nie genutzter Grafikstapel muss nicht
mitgepflegt werden.

**64-bit statt armhf** ist bei diesem Projekt keine Nebensache. Pydantic v2 hat seinen Kern
in Rust. Für `aarch64` existieren vorgefertigte Pakete, für 32-bit-`armhf` in der Regel
nicht — dort würde der Pi beim Installieren eine Rust-Bibliothek übersetzen müssen. Für
weitere Abhängigkeiten gilt dasselbe.

### Startmedium

Die Anwendung läuft ab M7 dauerhaft, und SQLite schreibt im WAL-Modus fortlaufend.
SD-Karten verschleißen daran, und sie versagen nicht sauber, sondern mit stillen
Lesefehlern — bei einer Datenbankdatei im schlechtesten Fall mit einer beschädigten Datei.
Der Pi 4 kann unmittelbar von USB starten; eine kleine SSD an einem USB-3-Anschluss ist
daher die festgelegte Grundlage. Wird ausnahmsweise doch von SD-Karte betrieben, dann mit
einer Karte der Kennzeichnung A2 und zusätzlich `log2ram`, damit die Systemprotokolle nicht
dauernd schreiben.

### Zeitabgleich als Startbedingung

Der Pi 4 hat keine Echtzeituhr. Nach einem Stromausfall startet er mit einer falschen Zeit
und korrigiert sie erst, wenn Netz und NTP verfügbar sind.

Das betrifft dieses System unmittelbar: Die gesamte Jobsteuerung hängt an `run_after`, und
ab M9 kommen die Gerätefristen aus 9.7 hinzu. Ein Job, dessen Fälligkeit vor dem
Zeitabgleich berechnet wurde, liegt nach dem Sprung möglicherweise Stunden in Vergangenheit
oder Zukunft. Im schlimmsten Fall wird eine Dosierung sofort fällig, deren
Stabilisierungszeit noch nicht abgelaufen ist.

| Nr. | Regel |
|---|---|
| B-1 | Die systemd-Einheit der Anwendung hängt von `time-sync.target` ab und startet nicht davor. |
| B-2 | Beim Start wird die Systemzeit protokolliert, damit ein Zeitsprung im Nachhinein erkennbar ist. |

B-1 ist eine Zeile in der Dienstdatei und erspart eine Fehlersuche, deren Ursache aus den
Daten allein kaum zu erkennen wäre.

Die Zeitzone des Systems betrifft nur Protokolle und Anzeige. Die Anwendung speichert nach
Z-1 bis Z-4 ausschließlich UTC, unabhängig von der Systemeinstellung.

### Verworfene Alternativen

| Alternative | Grund der Ablehnung |
|---|---|
| Raspberry Pi OS Desktop | Pflegeaufwand ohne Nutzen im headless Betrieb |
| Ubuntu Server für Raspberry Pi | Tragfähig und länger unterstützt, aber die Pi-spezifische Hardwareunterstützung ist bei Raspberry Pi OS besser erprobt, und ein Vorteil für dieses Projekt besteht nicht |
| DietPi und ähnliche schlanke Ableitungen | Sparen einige hundert Megabyte, kosten Vertrautheit und Dokumentation. Kein guter Tausch bei reichlich freiem Speicher |
| 32-bit-System | Fehlende vorgefertigte Pakete für Pydantic und andere Abhängigkeiten |

## 14.4 Sicherung

Die Datenbank ist eine einzelne Datei und wird durch Kopieren gesichert. Ab M8 ist das ein
Dateikopierauftrag im Container-Host. Ein eigener Sicherungsmechanismus ist nicht
vorgesehen.

Eine Kopie im laufenden Betrieb muss die WAL-Datei einbeziehen oder über den
Sicherungsmechanismus von SQLite erfolgen. Ein einfaches Kopieren der Hauptdatei während
eines Schreibvorgangs ergibt eine unvollständige Sicherung.

---

# 15. Umsetzungsreihenfolge

## M1 – Fundament

Repository, `pyproject.toml` mit uv, FastAPI mit den Betriebsendpunkten aus 9.0,
SQLite-Engine mit den Pragmas aus 10.1, der Spaltentyp `UtcDateTime` und `utcnow()` aus
11.3, Alembic mit Migration beim Start nach 10.3, pytest mit der Testdatenbank aus 12.2,
ruff, mypy, CI, README, `.env.example`, `.gitattributes`, Fehlerklassen und
Exception-Handler aus 11.4.

Begründung für die Vorziehung: Testdatenbank, Fehlerbehandlung und CI sind genau die
Punkte, die im Altprojekt fehlten und sich später nur mühsam nachziehen lassen. Es
entsteht in M1 noch keine Fachtabelle.

## M2 – Stammdaten

`Plant`, `GrowthStage`, `Fertilizer`, `Recipe`, `RecipeItem`, `PhAdjuster`, `Tank` mit
Models, Migrationen, Schemas, Services, Endpunkten und Tests. Validierungsregeln V-1 bis
V-12, die Löschregeln aus 6.3, Aufzählungstypen nach 6.0 und `tools/seed.py` aus 14.1.

Diese Stammdaten sind Voraussetzung für die Jobliste: `CompareProbe` braucht die Sollwerte
der Wachstumsphase, `CompensationEC` braucht Rezeptur und Dünger.

## M3 – Jobliste und EC-Regelung im Modus `advisory`

Der erste fachlich nutzbare Stand und der Meilenstein, der am 2026-10-05 als Ziel benannt
wurde.

Inhalt: `Measurement` mit Verlauf, `RegulationCycle`, `Job` mit allen Zuständen aus 5.3 und
Dispatcher, die Jobtypen `MeasureProbe`, `CompareProbe`, `CompensationEC`,
`DoseFertilizer` und `Mix`, die Berechnungen aus 8.1 und 8.2, die Plausibilitätsprüfung aus
7.5, die Endpunkte aus 9.2 und 9.3, die Indizes aus 6.4, das Wiederaufsetzen aus 5.3, die
Momentaufnahme aus 9.4, S-6, die Seitenweise Abfrage aus 9.1.

Die Rangfolge Volumen, EC, pH aus 9.4 wird bereits vollständig implementiert, auch wenn in
M3 nur die EC-Korrektur einen Jobtyp hat. Die Einschränkung ist in 9.4 beschrieben.

Danach ist dieser Ablauf vollständig möglich: Zyklus starten, Messwerte eingeben,
Auswertung erhalten, Dosierempfehlung je Dünger bekommen, Dosierung bestätigen, mischen und
bestätigen, nach der Stabilisierungszeit erneut messen, bis der EC im Zielbereich liegt.

## M4 – Volumen und pH

`AdjustVolume` mit der Mischungsrechnung aus 8.3, `CompensationPH` und `DosePhAdjuster`
mit der Logik aus 8.4, die Sicherheitsgrenzen S-1 bis S-5 aus 8.6, Zyklusabbruch und
Fehlerbehandlung. S-6 entsteht bereits in M3.

## M5 – Simulation

`app/devices/` mit den Protokollen, simulierte Messwertquelle und simulierte Aktoren,
Modus `simulation`. Ein Zyklus läuft damit ohne jede Eingabe durch, was die
Korrekturschleife über viele Durchläufe prüfbar macht.

**Wichtig:** M5 setzt die Simulationsstufen 1 **und** 2 aus 9.8 um, nicht nur Stufe 1. Das
heißt, der Zustand `waiting_device`, die Fristüberwachung und die gemeinsame
Abschlussfunktion `complete_job` entstehen bereits hier. Würde M5 nur den sofortigen Fall
kennen, müsste in M9 der Zustandsautomat der Jobs nachträglich umgebaut werden — und zwar
an einem Punkt, an dem schon echte Pumpen angeschlossen sind. Genau diese Art von
Nacharbeit soll der Neuaufbau vermeiden.

## M6 – Weboberfläche

Übersicht aller Tanks mit aktuellen Werten und Bewertung, Messwerteingabe, Jobliste mit
Bestätigungsschaltflächen, Verlaufsdiagramme, Stammdatenpflege. Technologie, entschieden
am 2026-10-07 (O-5): Jinja2 und HTMX im selben FastAPI-Prozess.

## M7 – Scheduler

Zeitgesteuertes Anstoßen von Zyklen je Tank, Erinnerung an den Wasserwechsel nach
`water_change_interval_days`.

Zeitpläne werden als Ortszeit mit Zeitzonennamen hinterlegt, nicht als UTC-Uhrzeit.
Nach Z-1 bis Z-4 speichert die Datenbank alles in UTC — ein Plan „täglich 08:00" meint
aber die Ortszeit des Betreibers, und die liegt im Sommer auf einem anderen UTC-Zeitpunkt
als im Winter. Rechnet man die Uhrzeit einmalig in UTC um, verschiebt sich der Zyklus bei
der Zeitumstellung um eine Stunde. Der nächste Fälligkeitszeitpunkt wird daher bei jeder
Berechnung aus Ortszeit und `zoneinfo` neu bestimmt und erst dann als UTC in `run_after`
geschrieben. Die beiden Grenzfälle der Umstellungsnacht — eine nicht existierende und eine
doppelte Stunde — gehören in die Pflichttests aus 12.4.

## M8 – Container

Dockerfile und Compose-Datei, Datenbank im Volume.

## M9 – Hardware

MQTT-Anbindung nach 9.7, `app/devices/mqtt.py`, Gerätattrappe `tools/fake_esp.py` als
Stufe 3 aus 9.8, Pumpensteuerung, Modus `automatic`, Temperaturkompensation nach 8.5.

Die Gerätattrappe entsteht **vor** der ersten echten Pumpe. Der gesamte Weg über den
Broker wird gegen sie geprüft, einschließlich der Fälle ohne Antwort, mit verzögerter
Antwort und mit doppelter Antwort. Erst danach wird Hardware angeschlossen.

---

# 16. Abnahmekriterien

## M1

| Nr. | Kriterium |
|---|---|
| AK-1.1 | `uv sync` und `uv run pytest` laufen auf Windows, auf Linux-x64 und auf Linux-ARM64 fehlerfrei, jeweils aus einem frisch geklonten Projekt. |
| AK-1.1b | Entfällt, entschieden am 2026-10-07. Die ARM64-CI ersetzt diese einmalige Stichprobe auf dem Pi. |
| AK-1.2 | `GET /health` antwortet mit 200. |
| AK-1.3 | Ein Test belegt, dass ein verletzter Fremdschlüssel einen Datenbankfehler auslöst. Das beweist, dass `PRAGMA foreign_keys` wirkt. |
| AK-1.4 | Ein Test belegt, dass die Testdatenbank nach dem Testlauf keine Spuren in `nsm.db` hinterlässt. |
| AK-1.5 | `ruff check`, `ruff format --check` und `mypy app` melden nichts. |
| AK-1.6 | Die CI läuft bei einem Push durch und schlägt bei einem absichtlich eingebauten Typfehler fehl. |
| AK-1.7 | Ein Endpunkt, der `NotFoundError` wirft, liefert 404 im Format aus 9.6, ohne eigenes `try/except`. |
| AK-1.8 | Ein zeitzonenbehafteter Wert, der über `UtcDateTime` geschrieben und wieder gelesen wird, kommt zeitzonenbehaftet in UTC zurück und ist mit `utcnow()` vergleichbar. Ein naiver Schreibversuch wird abgelehnt. |
| AK-1.9 | `GET /health` schlägt fehl, wenn die Datenbank nicht erreichbar ist. |
| AK-1.10 | `GET /version` liefert die Version aus `pyproject.toml` und die Startzeit als zeitzonenbehaftetes UTC. |
| AK-1.11 | Ein Start gegen eine Datenbank ohne Tabellen erzeugt die Tabellen selbst und antwortet danach mit 200 auf `GET /health`. |

## M2

| Nr. | Kriterium |
|---|---|
| AK-2.1 | Alle sieben Stammdatenressourcen beherrschen das CRUD-Muster aus 9.1. |
| AK-2.2 | `ec_min = 2,0`, `ec_target = 1,0`, `ec_max = 3,0` wird mit 422 abgelehnt. |
| AK-2.3 | `ec_min = 0,0` wird angenommen. |
| AK-2.4 | Eine zweite Rezeptur für dieselbe Wachstumsphase wird mit 409 abgelehnt. |
| AK-2.5 | Das Löschen einer Pflanze mit Wachstumsphasen wird mit 409 abgelehnt. |
| AK-2.6 | Das Löschen einer Wachstumsphase entfernt ihre Rezeptur samt Bestandteilen. |
| AK-2.7 | Eine Rezeptur mit Anteilen von 30, 30 und 40 wird als `is_complete = true` gemeldet, eine mit 30 und 30 als `false`. |
| AK-2.8 | Eine Wachstumsphase, die nicht zur Pflanze des Tanks gehört, wird als aktive Phase mit 422 abgelehnt. |
| AK-2.9 | `alembic upgrade head` auf einer leeren Datenbank erzeugt alle Tabellen, `downgrade base` entfernt sie wieder. |
| AK-2.10 | `uv run python -m tools.seed` legt den Beispielbestand aus 14.1 an und ist beim zweiten Aufruf unschädlich. |

## M3

| Nr. | Kriterium |
|---|---|
| AK-3.1 | `POST /tanks/1/cycles` erzeugt einen Zyklus und zwei Jobs und führt den ersten sofort aus. `MeasureProbe` steht danach auf `waiting_input`, `CompareProbe` auf `pending`. |
| AK-3.2 | Ein zweiter Zyklus für denselben Tank wird mit 409 abgelehnt. |
| AK-3.3 | Die Eingabe von EC, pH, Temperatur und Volumen beendet `MeasureProbe` als `succeeded` und erzeugt genau eine Messung mit korrektem `tank_id`. |
| AK-3.4 | `GET /tanks/1/measurements/latest` liefert die Messung mit dem größten `measured_at`, auch wenn eine ältere später erfasst wurde. |
| AK-3.5 | `CompareProbe` bei Werten im Zielbereich erzeugt keinen Folgejob und setzt den Zyklus auf `succeeded`. |
| AK-3.6 | `CompareProbe` bei einem EC unter `ec_min` erzeugt genau einen `CompensationEC`-Job mit korrektem `parent_job_id` und erhöht `ec_attempts` auf 1. |
| AK-3.7 | `CompareProbe` bei gleichzeitiger Abweichung von EC und pH erzeugt in M3 nur den `CompensationEC`-Job. Die Bewertung im Ergebnis weist die pH-Abweichung trotzdem aus. |
| AK-3.8 | `CompareProbe` bei abweichendem pH und EC im Zielbereich erzeugt in M3 keinen Job und setzt den Zyklus auf `succeeded`, mit ausgewiesener pH-Abweichung. Ein EC über `ec_max` erzeugt in M3 ebenfalls keinen Job und keinen Düngerauftrag. |
| AK-3.9 | Das Beispiel aus 8.2 ergibt 184,6 ml gesamt und 55,4, 55,4 und 73,8 ml je Dünger, auf eine Dezimalstelle gerundet. |
| AK-3.10 | `CompensationEC` erzeugt je Rezepturbestandteil einen `DoseFertilizer`-Job in der Reihenfolge von `dose_order`. |
| AK-3.11 | Nach dem letzten `DoseFertilizer` folgen `Mix`, dann `MeasureProbe` mit einem `run_after`, das um `stabilization_seconds` in der Zukunft liegt. |
| AK-3.12 | Im Modus `advisory` wartet auch `Mix` auf eine Bestätigung. |
| AK-3.13 | `GET /jobs/next` liefert einen noch nicht fälligen Job nicht. |
| AK-3.14 | `POST /jobs/dispatch` arbeitet bei zwei Tanks mit offenen Zyklen den Job mit dem kleinsten `run_after` ab, nicht den mit der kleinsten Id. |
| AK-3.15 | `CompensationEC` ohne Rezeptur an der aktiven Phase endet als `failed`, bricht den Zyklus ab und erzeugt keine Dosierjobs. |
| AK-3.16 | Ein EC-Sprung von 1,2 auf 8,0 innerhalb von zwei Minuten setzt `CompareProbe` auf `blocked`. Die Messung bleibt gespeichert, der Zyklus bleibt `running`, kein Job wird verworfen. |
| AK-3.17 | `POST /cycles/{id}/continue` führt den blockierten Job erneut aus, diesmal ohne die Prüfungen P-3 bis P-5. Ohne blockierten Job antwortet der Endpunkt mit 409. |
| AK-3.18 | Eine Messung ohne Volumen lässt `CompensationEC` mit verständlicher Meldung fehlschlagen. |
| AK-3.19 | Ein Zyklus, der dreimal den EC nachkorrigiert, endet bei `ec_attempts = max_correction_attempts` als `failed`, und alle offenen Jobs stehen auf `cancelled`. |
| AK-3.20 | Ein `run_after`, das aus der Datenbank gelesen wurde, lässt sich ohne `TypeError` mit `utcnow()` vergleichen. Beide Werte sind zeitzonenbehaftet und in UTC. |
| AK-3.21 | `GET /cycles/{id}` liefert alle Jobs mit Typ, Zustand, Parametern, Ergebnis und `parent_job_id`, sodass der Ablauf vollständig nachvollziehbar ist. |
| AK-3.22 | Das Ergebnis von `CompensationEC` enthält Ist-EC, Ziel-EC, Volumen und je Bestandteil Name, Anteil und EC-Wirkung. Nach einer Änderung der Rezeptur bleibt dieses Ergebnis unverändert. |
| AK-3.23 | Ein Job `DoseFertilizer` im Zustand `running` oder `waiting_device` wird beim Start nach W-1 auf `failed` gesetzt, der Zyklus endet, und der Job wird nicht erneut ausgeführt. Ein `CompareProbe` im Zustand `running` oder `waiting_device` geht auf `pending`. |
| AK-3.24 | Ein Zyklus, dessen `started_at` länger als `max_cycle_duration_minutes` zurückliegt, endet vor der nächsten Jobausführung als `failed`, offene Jobs stehen auf `cancelled`. |
| AK-3.25 | `GET /jobs` ohne Parameter liefert höchstens 100 Einträge und die Gesamtzahl. `limit=5000` wird auf 1000 gekürzt. |

## M4

| Nr. | Kriterium |
|---|---|
| AK-4.1 | Das Beispiel aus 8.3 ergibt einen vorhergesagten EC von 1,72. |
| AK-4.2 | Ein EC über `ec_max` erzeugt einen `AdjustVolume`-Job mit der Menge aus 8.3, keinen `CompensationEC` und keinen `DoseFertilizer`. |
| AK-4.3 | Ein `source_water_ec`, der nicht unter `ec_target` liegt, erzeugt eine Warnung statt einer Verdünnungsempfehlung. |
| AK-4.4 | Eine Verdünnung, die `max_volume_liters` überschreiten würde, wird abgelehnt. |
| AK-4.5 | Weichen Volumen, EC und pH gleichzeitig ab, erzeugt `CompareProbe` genau einen Job, und zwar `AdjustVolume`. Erst der folgende Durchlauf behandelt den EC, der darauf folgende den pH. |
| AK-4.6 | Ein Zyklus, der den EC dreimal und den pH einmal korrigiert, läuft weiter. Ein gemeinsamer Zähler hätte hier abgebrochen. |
| AK-4.7 | Jede Grenze S-1 bis S-5 bricht den Zyklus ab, bevor dosiert wird. |
| AK-4.8 | Ein pH, der sich nach einer Dosierung in die falsche Richtung bewegt, bricht die pH-Korrektur ab. |

---

# 17. Bewusst zurückgestellt

| Gegenstand | Begründung |
|---|---|
| Nährstoffbilanz für N, P, K, Ca und Mg | Deutlich größeres Datenmodell. EC und pH reichen für die Regelung. Die Drift der Zusammensetzung wird stattdessen durch den Hinweis auf einen Wasserwechsel abgefangen. |
| Unverträglichkeit zwischen zwei Düngern | `dose_order` und `Mix` zwischen den Dosierungen genügen praktisch. Eine Verträglichkeitsmatrix lohnt erst bei vielen Düngern. |
| Vorratsverwaltung der Dünger | Nützlich, aber nicht Teil der Regelung. Nachrüstbar als Tabelle mit Füllstand plus Abzug in `DoseFertilizer`. |
| Mehrbenutzerbetrieb, Anmeldung, Rechte | Ein einzelner Betreiber im Heimnetz. Nachrüstbar, bevor das System aus dem Netz erreichbar wird. |
| Benachrichtigung per E-Mail oder Push | Erst sinnvoll, wenn das System dauerhaft läuft, also ab M7. |
| Eigener Prozess für Jobliste oder MQTT | Im Modus `advisory` wird ohnehin auf den Betreiber gewartet. Ab M7 und M9 laufen Zeitplan und MQTT-Client als Hintergrundaufgaben **im** FastAPI-Prozess, nicht daneben, damit nur ein Prozess in die SQLite-Datei schreibt. Siehe 9.7 und 14.2. |
| PostgreSQL | Am 2026-10-05 bewusst gegen SQLite entschieden. Bedingungen für einen Wechsel in 4.2. |
| Temperaturkompensation des EC | Messgeräte kompensieren meist selbst. Formel und Bedingung in 8.5 vorbereitet. |
| Historisierung der Sicherheitsgrenzen | Eine Änderung gilt sofort. Bewusste Vereinfachung, in 6.1 vermerkt. |
| Mehrere parallele Rezepturen pro Phase | Entspricht der fachlichen Festlegung im Projektkonzept. |
| Versionierung der API unter `/api/v1/` | Oberfläche und API werden zusammen ausgeliefert, es gibt keinen fremden Aufrufer, der an eine alte Fassung gebunden wäre. Bewusst weggelassen, kein Versäumnis. |
| Automatisches Löschen alter Messungen und Jobs | Nach 9.2 nicht nötig. Falls doch, ist ein Verdichten auf Tagesmittelwerte der richtige Weg, nicht Löschen. |
| Rundung der Dosiermengen auf die Auflösung einer Pumpe | Erst mit echter Hardware in M9 bestimmbar. Bis dahin volle Genauigkeit nach 8.2. |

---

# 18. Offene Entscheidungen

| Nr. | Frage | Bis wann nötig |
|---|---|---|
| O-1 | ~~Welches Düngersystem wird konkret verwendet, und ist eine Dosierreihenfolge erforderlich?~~ Entschieden am 2026-10-07: kein konkretes System. Der Seed legt A, B und C mit `dose_order` 0, 1 und 2 an. | erledigt |
| O-2 | ~~Konkrete Werte für die Sicherheitsgrenzen je Tank.~~ Entschieden am 2026-10-07: Platzhalter, bis ein echter Tank andere Werte trägt. Ziel 30 l, Maximum 40 l, `source_water_ec` 0,3, Stabilisierung 120 s, Wasser 20 l, Dünger 500 ml, pH-Mittel 50 ml, 3 Versuche, Zyklusdauer 1440 min. | erledigt |
| O-3 | ~~Soll ein Tank stillgelegt werden können, statt ihn zu löschen?~~ Entschieden am 2026-10-07: Ja. `retired_at` am Tank. Löschen bleibt `RESTRICT`. Ein stillgelegter Tank nimmt keinen neuen Zyklus an. | erledigt |
| O-4 | ~~Soll bei Handdosierung die tatsächliche Menge erzwungen abgefragt werden?~~ Entschieden am 2026-10-06: Ja, Pflichtfeld, vorbelegt mit der empfohlenen Menge. Eine stillschweigend übernommene Empfehlung würde die nächste Berechnung auf einen Wert stützen, der nie dosiert wurde. | erledigt |
| O-5 | ~~Technologie der Weboberfläche: serverseitige Vorlagen mit HTMX oder eine getrennte Anwendung mit eigenem Build.~~ Entschieden am 2026-10-07: Jinja2 und HTMX im selben FastAPI-Prozess. | erledigt |
| O-6 | ~~Soll die Erinnerung an den Wasserwechsel einen Zyklus blockieren oder nur hinweisen?~~ Entschieden am 2026-10-07: nur Hinweis. Der Zyklus startet trotzdem. | erledigt |
| O-7 | ~~Wie werden Messgeräte mit eigener Temperaturkompensation von solchen ohne unterschieden?~~ Entschieden am 2026-10-07: `ec_uncompensated` am Gerät, Standard `false`. Die Formel aus 8.5 gilt nur bei `true`. | erledigt |
| O-8 | Soll `projektkonzept.md` auf die rein fachlichen Kapitel gekürzt werden, nachdem die technischen Festlegungen hier stehen? Die Datei liegt in diesem Repository nicht. | liegen geblieben |
| O-9 | ~~Braucht es eine Geräteverwaltung, die festhält, welcher ESP32 welchen Tank bedient?~~ Entschieden am 2026-10-07, geändert am selben Tag: Ja. Knoten tragen Sensoren und Aktoren. Ein Knoten gehört zu einem Tank oder zur Anlage. Ein Dosierjob im Modus `automatic` führt den Ablauf aus, der als Stammdaten hinterlegt ist. Schritte ohne Abhängigkeit laufen gleichzeitig, ein Schritt mit Abhängigkeit startet nach der Meldung seines Vorgängers. Die Abschlussfolge läuft nach Erfolg, Fehler, Frist und beim Neustart. | erledigt |
| O-10 | ~~Soll der MQTT-Broker Anmeldedaten und TLS verlangen?~~ Entschieden am 2026-10-07: ohne Anmeldedaten und ohne TLS, nur im abgeschotteten Heimnetz. | erledigt |
| O-11 | ~~Sollen die Fristen aus 9.7 je Tank konfigurierbar sein oder global bleiben?~~ Entschieden am 2026-10-07: je Tank, mit den Werten aus 9.7 als Standard. | erledigt |

---

# 19. Erste Schritte im neuen Repository

```text
1  Repository anlegen, README und Lizenz
2  AGENTS.md ersetzen: Agent implementiert, erklärt auf Nachfrage (siehe 2.4)
3  pflichtenheft.md und projektkonzept.md nach docs/ übernehmen
4  lernpfad.md und kistart.md nicht übernehmen
5  M1 umsetzen und gegen AK-1.1 bis AK-1.11 prüfen
6  M2 umsetzen und gegen AK-2.1 bis AK-2.10 prüfen
7  M3 umsetzen und gegen AK-3.1 bis AK-3.25 prüfen
```

Vom Altprojekt wird kein Code übernommen. Die Models und Services sind in M2 schnell neu
geschrieben, und ein Übernehmen würde die in 2.2 aufgeführten Befunde mitbringen.
