# Hardware-Notizen zum Startmedium

Stand: 2026-10-07. Gespräch über das Laufwerk des Raspberry Pi 4.
Die technische Festlegung bleibt Kapitel 14.3 im Pflichtenheft. Diese Datei hält die
Einkaufsüberlegung fest, damit sie nicht verloren geht.

## Was das Pflichtenheft festlegt

Die Hauptanwendung läuft auf einem Raspberry Pi 4 mit Raspberry Pi OS Lite, 64-bit.
Das Startmedium ist eine USB-SSD, keine SD-Karte. Der Pi 4 hat keinen PCIe-Anschluss,
eine NVMe-Platine hängt dort nur über USB.

Grund: Ab M7 läuft die Anwendung dauerhaft, und SQLite schreibt im WAL-Modus fortlaufend.
SD-Karten verschleißen daran und fallen oft ohne klare Fehlermeldung aus. Wird doch von
SD-Karte betrieben, dann mit einer Karte der Kennzeichnung A2 und zusätzlich `log2ram`.

## Entscheidung für die Entwicklung

Bis 80 Euro gab es keine Kombination aus seriöser SSD und Gehäuse, die sich gelohnt hätte.
Die Entwicklung und der erste Test laufen deshalb auf der SD-Karte, die bereits im Pi steckt.

Das reicht, solange die Anwendung nur zum Ausprobieren gestartet wird. Die Schreiblast ist
dann zu klein, als dass die Karte daran verschleißt. Eine USB-SSD wird erst fällig, wenn
der Pi ab M7 dauerhaft als Dienst läuft.

## Was wir uns angesehen haben

| Gerät | Urteil |
|---|---|
| SSK USB-Stick, bezeichnet als „USB 3.2 Gen 2 Solid State Flash-Laufwerk“, 550 MB/s, USB-A und USB-C | Sieht aus wie ein normaler USB-Stick. Dieselbe Bauform ist auf einem Pi 4 schon als Startplatte gelaufen, das Foto allein beweist den Controller nicht. Am blauen USB-3-Port prüfen: `lsusb -t` zeigt `uas`, und `sudo fstrim --verbose /` meldet freigegebene Blöcke. Fehlt beides, ist es ein schneller USB-Stick und kein Dauerlaufwerk. |
| Normaler USB-Stick | Für gelegentliches Kopieren gebaut. Einfacher Controller, schwache Verteilung der Schreibzyklen, kein verlässliches TRIM. Dieselbe Verschleißklasse wie eine SD-Karte. |
| UGREEN- oder ANYOYO-NVMe-Gehäuse mit USB 3.2 Gen 2, etwa ANYOYO EC-6607 für 18 Euro | Leere Hülle, die SSD kommt extra hinein. Nur NVMe mit M-Key oder B+M-Key, Format 2280. Keine M.2-SATA. Der USB-A-Stecker gehört in eine blaue Buchse. Der Pi 4 schafft 5 Gbit/s, die beworbenen 10 Gbit/s nicht. Risiko ist der Strom: die USB-Ports teilen sich ein knappes Budget, stromhungrige Riegel trennen sich beim Start. Passend wären sparsame Platten ohne eigenen DRAM-Baustein. Das originale Netzteil mit 5,1 V und 3 A gehört dazu. |
| Adapterplatine mit Pogo-Pins, Acryl und beiliegendem USB-Stecker, nur für den Pi 4 Modell B | Macht den Start nicht sicherer. Der Pi 4 hat keine NVMe-Buchse, die Daten laufen weiter über USB 3. Die Pogo-Pins holen 5 V von einem Prüfpunkt und haben bei solchen Adaptern schon verhindert, dass der Pi überhaupt startet. Die Mechanik ist schief sitzend schwerer zu prüfen als ein abziehbarer Stecker. |
| WD Blue SN580 | Für diesen Einsatz zu teuer. Eine 500-GB-Platte lag bei rund 200 Euro, größere Angebote bei etwa 300 Euro. Der USB-Anschluss des Pi bremst diese Geschwindigkeit auf einen Bruchteil. |
| SanDisk SSD Plus M.2, 250 GB, PCIe 3.0, TLC, Modellreihe SDSSDA3N | Die seriöse Platte im Budget. Etwa 60 bis 75 Euro, verkauft über Amazon, drei Jahre Garantie von Western Digital. Zusammen mit dem 18-Euro-Gehäuse liegt das über der Grenze von 80 Euro. Im Angebot muss „M.2 NVMe“ stehen. Dieselbe Serie gibt es auch als 2,5-Zoll-SATA, die passt nicht ins Gehäuse. 250 GB reichen für System und Datenbank. |

## Wann das Thema wieder aufgeht

Vor dem Dauerbetrieb in M7, Schritt 7.4. Bis dahin bleibt die SD-Karte das Startmedium.
Kandidat für den späteren Kauf: SanDisk SSD Plus M.2 250 GB plus ein NVMe-Gehäuse mit
USB-A-Stecker, sofern der Preis dann noch passt. Nach dem ersten Start auf der neuen
Platte: `lsusb`, `lsusb -t` und `sudo fstrim --verbose /`. Ein Realtek-Adapter meldet
sich oft als `0bda:9210`. `fstrim` muss eine Menge freigegebener Blöcke ausgeben.
