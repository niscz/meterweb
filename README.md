Du bist der leitende Coding-Agent für das Projekt „meterweb“.

Deine Aufgabe ist es, eine produktionsreife, selbst gehostete, dockerisierte, Open-Source-Plattform
zur Erfassung von Zählerständen, Berechnung von Verbräuchen und Kosten sowie zur grafischen und
witterungsbereinigten Auswertung zu entwerfen und umzusetzen.

## Produktziel
meterweb ist eine Single-Tenant-Webplattform für genau einen Betreiber mit genau einem Login.
Die Plattform läuft self-hosted via Docker Compose, nutzt ein Python-Backend, SQLite als
Anwendungsdatenbank, Tabler v1.4.0 als UI-Grundlage, eine gekapselte Chart-Adapter-Schicht mit
ApexCharts als Standardrenderer für Standarddiagramme und Bright Sky als Wetterprovider.

## Harte Produktanforderungen
1. Single-Tenant, Single-User, Login/Passwort.
2. Docker Compose Deployment.
3. Backend in Python.
4. SQLite als primäre App-Datenbank.
5. Frontend auf Basis von Tabler v1.4.0, mobile-first, responsive, Dark Mode.
6. Manuelle Eingabe von Zählerständen.
7. Mobile Web-Erfassung.
8. Foto-/Bild-Upload mit OCR-gestützter Zählerstanderkennung.
9. Plausibilitätsprüfungen bei Erfassung und Änderung.
10. Unterstütze absolute Zählerstände, Impulszähler, Smart-Meter-Intervalldaten,
    mehrere Register (z. B. HT/NT), Zählerwechsel, Roll-over, virtuelle Zähler,
    Summenzähler und Differenzzähler.
11. Freie Gruppenbildung für Auswertungen.
12. Flexible Zeitauflösungen: stündlich, täglich, wöchentlich, monatlich, jährlich,
    benutzerdefinierte Aggregation.
13. Verbrauchs- und Kostenauswertungen.
14. Grafische Auswertungen inkl. Linien-, Balken-, Flächen-, Vergleichs-, Lastgang-,
    Heatmap- und Scatter-Diagrammen; Sankey nur über austauschbare Adapterlösung.
15. Witterungsbereinigte Darstellungsoptionen mit Best-Practice-Methoden.
16. Bright Sky per HTTP-API integrieren; Wetterdaten lokal cachen.
17. Wetterpunkt pro Gebäude; automatische Stationswahl plus manuelle Stationsübersteuerung.
18. Stammdatenstruktur flach: Gebäude → Einheit → Zähler, ergänzt um frei definierte Gruppen.
19. Exporte: CSV, Excel, PDF, Druckansicht, Monatsbericht je Objekt.
20. Sprachen: Deutsch und Englisch; korrekte Lokalisierung von Einheiten, Zahlen,
    Datumsformaten und Dezimaltrennzeichen.
21. Open-Source-fähiger Code, testbar, dokumentiert, ohne Platzhalter oder Fake-Funktionen.

## Nicht verhandelbare Architekturregeln
1. Implementiere meterweb als modularen Python-Monolithen.
2. Verwende serverseitig gerenderte HTML-Seiten mit schlanker Interaktivität
   statt einer schweren SPA.
3. Kapsle alle externen Integrationen hinter Interfaces:
   - WeatherProvider
   - OCRProvider
   - ChartAdapter
   - ReportRenderer
4. Bright Sky darf nicht direkt in fachliche Logik eingemischt werden.
   Alle Wetterabfragen laufen über eine WeatherProvider-Schnittstelle mit lokalem Cache.
5. ApexCharts darf nicht direkt in fachliche Business-Komponenten einfließen.
   Diagramme werden über ein internes Chart-DSL/Schema beschrieben.
6. Trenne fachlich zwischen:
   - logical meter point (Messpunkt)
   - physical meter device (konkreter eingebauter Zähler)
   Damit Zählerwechsel und Roll-over sauber modelliert werden.
7. Trenne rohe Messdaten von berechneten Aggregaten.
8. Jede fachliche Berechnung muss testbar und deterministisch sein.
9. Keine UI ohne funktionierende Backend-Anbindung.
10. Keine TODO-Leichen, keine Mock-Daten in Produktionspfaden.

## Bevorzugter Stack
- Python 3.12+
- FastAPI
- Jinja2
- HTMX + leichtes JS für progressive Interaktion
- SQLAlchemy 2.x + Alembic
- SQLite im WAL-Modus
- OpenCV/Pillow + Tesseract als lokaler OCR-Standardpfad
- WeasyPrint oder vergleichbarer HTML→PDF-Renderer
- openpyxl für XLSX
- pytest für Unit/Integrationstests
- Playwright oder vergleichbar für E2E
- Ruff/Black/mypy für Codequalität

## Fachliche Anforderungen im Detail
1. Beliebig viele Medien und beliebig viele Zähler pro Medium.
2. Medien sind in den Einstellungen konfigurierbar, inklusive Einheit, Anzeigeformat,
   Standardregeln und Wetterempfindlichkeit.
3. Gruppen dürfen Gebäude, Einheiten, Messpunkte oder virtuelle Zähler bündeln.
4. Verbrauchsberechnung muss Unterschiede zwischen absoluten Ständen, Intervallen
   und Impulswerten korrekt behandeln.
5. Sparse manuelle Ablesungen müssen in Kalenderperioden darstellbar sein, aber
   geschätzte Verteilungen müssen klar als geschätzt markiert werden.
6. OCR muss Bild speichern, Vorverarbeitung durchführen, Kandidaten extrahieren,
   Konfidenz berechnen und eine Bestätigungsmaske anzeigen.
7. Plausibilitätsprüfung muss mindestens erkennen:
   - negative Differenzen
   - unplausibel hohe Sprünge
   - Stillstand
   - Ausreißer gegenüber Vorperiode
   - Konflikt mit OCR-Konfidenz
   - Konflikt mit typischer Witterung/Erwartung
8. Kostenberechnung muss Arbeitspreise, Grundpreise, Gültigkeitszeiträume,
   Register/Tarife und periodische Zuordnung unterstützen.
9. Wetterbereinigung muss mehrere Modelle unterstützen:
   - Heizgradtage-basierte Normalisierung
   - Basislast + HDD/CDD-Regression
   - temperaturabhängige lineare/segmentierte Regression
10. Nicht jedes Medium ist automatisch sinnvoll witterungsbereinigbar.
    Die UI muss Eignung und Modellgüte transparent anzeigen.
11. Berichte müssen HTML, Druck und PDF aus derselben Templatebasis erzeugen.

## UX-Vorgaben
1. Mobile-first Erfassungsmaske mit großen Touch-Zielen.
2. Schnellerfassung: letzter Stand, erwarteter Bereich, Kamera, OCR-Vorschlag,
   Bestätigung in einem Flow.
3. Dashboard mit KPI-Kacheln, Trends, offenen Warnungen und zuletzt erfassten Zählern.
4. Klare Umschaltung zwischen Rohverbrauch und witterungsbereinigter Sicht.
5. Jede Kennzahl muss rückverfolgbar sein: „Wie wurde das berechnet?“
6. Dark Mode und helle Variante.
7. Keine überfrachtete Navigation; fachlich klare Informationsarchitektur.

## Liefergegenstände
1. Vollständiger Sourcecode.
2. Dockerfile + docker-compose.yml.
3. Datenbankmigrationen.
4. Seed-/Demo-Daten.
5. Technische Dokumentation.
6. Benutzerdokumentation.
7. Backup-/Restore-Dokumentation.
8. Test-Suite.
9. Lizenzhinweise für Drittkomponenten.
10. OpenAPI-Dokumentation für JSON-Endpunkte.

## Arbeitsweise
1. Arbeite iterativ, aber halte das System jederzeit lauffähig.
2. Beginne mit Domänenmodell, Datenbank, Auth, Stammdaten und Erfassung.
3. Danach OCR, Verbrauchslogik, Wetter, Normalisierung, Reports.
4. Dokumentiere Architekturentscheidungen knapp und konkret.
5. Schreibe erst die fachliche Grundlage, dann die schöne Hülle.
6. Bevorzuge saubere, robuste Implementierung vor unnötiger Cleverness.
7. Mache implizite Annahmen explizit im Code und in der Doku.

## Definition of Done
Das Projekt ist fertig, wenn ein Nutzer nach `docker compose up` meterweb öffnen,
sich einloggen, Gebäude/Einheiten/Zähler anlegen, per Mobilgerät Zählerstände und Fotos
erfassen, OCR-Vorschläge bestätigen, Verbräuche und Kosten grafisch analysieren,
witterungsbereinigte Ansichten je Objekt abrufen und Berichte als CSV/XLSX/PDF exportieren kann.

---

# 2) Technische Spezifikation für meterweb

## 2.1 Zielbild

**meterweb** ist eine selbst gehostete Webplattform zur Erfassung, Verwaltung und Analyse von Zählerständen, Verbräuchen und Kosten für beliebige Medien. Der Schwerpunkt liegt auf:

* sauberer Modellierung realer Zählersituationen,
* robuster mobiler Datenerfassung,
* lokaler OCR für Zählerfotos,
* graphischer Auswertung über freie Gruppen,
* witterungsbereinigter Analyse mit nachvollziehbarer Methodik.

Die Plattform ist **single-tenant** und **single-user**. Es gibt genau einen Login mit Passwort. Das ist angenehm schnörkellos und spart ein ganzes Silo an Rollen-, Einladung- und Rechteverwaltung, die später ohnehin nur ungeliebt im Weg steht.

## 2.2 Architektur

### Grundarchitektur

meterweb wird als **modularer Python-Monolith** umgesetzt:

* **FastAPI** als HTTP-Server und JSON-API
* **Jinja2** für serverseitig gerenderte Seiten
* **HTMX** für progressive Interaktivität
* **leichtes JavaScript** für Kamera, OCR-Vorschau, Chart-Initialisierung und kleine UI-Interaktionen
* **Tabler v1.4.0** als visuelles Grundsystem
* **Chart-Adapter-Schicht** mit ApexCharts als Standardrenderer
* **SQLite** als App-Datenbank
* **Dateisystem-Storage** für Uploads, Exporte, Backups
* **separater Worker/Scheduler** als zweiter Compose-Service mit demselben Codeimage

### Services in Docker Compose

1. `web`

   * FastAPI-App
   * HTML + JSON
   * Session-Handling
   * Dateiupload
   * OpenAPI

2. `worker`

   * OCR-Jobs
   * Wetter-Synchronisation
   * Aggregat-Neuberechnung
   * Report-Erzeugung
   * Alarmberechnung
   * geplante Backups

3. optional `proxy`

   * Caddy oder Nginx für TLS und Reverse Proxy
   * nicht zwingend für die App-Logik

### Warum genau so

Diese Architektur ist für deinen Anwendungsfall sauberer als eine SPA- und Message-Broker-Kirmes:

* Single-User + Self-Hosted + SQLite spricht für einen **schlanken Monolithen**
* Tabler funktioniert hervorragend mit SSR
* HTMX reicht für die dynamischen Teile
* Worker trennt schwere Jobs von Request-Latenz
* SQLite bleibt beherrschbar, solange Rohdaten, Aggregate und Schreibpfade diszipliniert getrennt sind

### Externe Integrationen

#### WeatherProvider

meterweb integriert **Bright Sky per HTTP**. Der Provider muss unterstützen:

* `get_current_weather(lat, lon)`
* `get_hourly_weather(lat, lon, from, to)`
* `get_daily_weather(lat, lon, from, to)`
* `find_station(lat, lon, date)`
* `get_station_history(...)`

Zusätzlich:

* konfigurierbare `base_url`
* lokaler Cache
* Retry/Backoff
* Provenienzspeicherung pro Datensatz
* manuelle Stationsfixierung pro Gebäude

Bright Sky liefert in seinen Beispielantworten bereits die fachlich nützlichen Stationsdaten wie DWD-Station-ID, Stationsname, Koordinaten und Distanz. Bright Sky-`source_id` darf aber nur als technische Referenz gespeichert werden, nicht als fachlicher Primärschlüssel. ([Bright Sky][4])

#### OCRProvider

Standardmäßig lokal:

* Bildvorverarbeitung mit OpenCV/Pillow
* OCR mit Tesseract
* meter-spezifische Parsing-Strategien

Später erweiterbar um:

* alternative OCR-Engines
* spezielle Modelle für Trommelzähler
* vision-llm-basierte Experimente, aber nicht als Pflichtpfad

#### ChartAdapter

Interner Renderer-Vertrag:

* Input: normiertes Chart-Schema
* Output: HTML/JS-Initialisierung für die jeweilige Bibliothek

So bleibt die Domäne unabhängig von ApexCharts. Das ist wegen der heutigen Lizenzlage nicht Kür, sondern Hygiene. Standardcharts laufen über ApexCharts; Spezialdiagramme wie Sankey müssen optional über einen separaten Adapter oder lizensierte Zusatzkomponenten laufen. ([ApexCharts.js][5])

---

## 2.3 Fachmodule

### A. Authentifizierung und Installation

Funktionen:

* Login mit Benutzername + Passwort
* Argon2id-Passworthash
* Session-Cookies
* CSRF-Schutz
* CLI-basierter Passwort-Reset
* First-run-Setup
* keine E-Mail-Registrierung
* keine Multi-User-Verwaltung in der UI

Warum: Bei Single-User-Self-Hosting ist E-Mail-Reset unnötige Komplexität. Lokaler Admin-Reset per CLI ist ehrlicher und weniger kapriziös.

### B. Einstellungen und Systemkonfiguration

Globale Einstellungen:

* Sprache: Deutsch / Englisch
* Währung
* Datumsformat
* Dezimaltrennzeichen
* Zeitzone
* Standard-Granularitäten
* Default-Dashboard
* Upload-Limits
* OCR-Defaults
* Wetterprovider-Konfiguration
* Chart-Layer-Konfiguration
* Backup-Pfad
* Open-Source-/Lizenzhinweise

Medienkonfiguration:

* frei definierbare Medien
* Standardmedien vorbefüllt: Strom, Gas, Wasser, Wärme, Warmwasser, PV, Einspeisung, Öl, Pellets etc.
* Einheit je Medium
* Default-Wetterempfindlichkeit
* Default-Plausibilitätsparameter
* Default-Kostenmodell

### C. Stammdaten

Struktur:

* **Gebäude**
* **Einheit**
* **Messpunkt**
* **Zählergerät**
* **Register**

Wichtig: Intern wird zwischen **Messpunkt** und **Zählergerät** getrennt.

* **Messpunkt** = fachliche Messstelle
* **Zählergerät** = konkret eingebautes Gerät mit Seriennummer, Roll-over, Einbaudatum

Das ist entscheidend für:

* Zählerwechsel
* Demontage/Montage
* Geräteserienwechsel
* unterschiedliche Register
* Historienkonsistenz

### D. Erfassung

Unterstützte Erfassungsarten:

* manuelle Eingabe
* mobile Web-Schnellerfassung
* Bild-/Foto-Upload mit OCR
* spätere Erweiterbarkeit für API-/Importpfade

Eingabefluss:

1. Zähler auswählen
2. letzter bestätigter Stand anzeigen
3. erwarteten Bereich anzeigen
4. Stand manuell eingeben oder Foto aufnehmen
5. OCR-Vorschlag berechnen
6. Plausibilität prüfen
7. Bestätigung oder Korrektur
8. speichern

### E. OCR-Modul

Pipeline:

1. Upload speichern
2. EXIF/Rotation normalisieren
3. Bild vorverarbeiten

   * Perspektivkorrektur
   * Kontrast
   * Schärfung
   * Binarisierung
   * Crop-Erkennung
4. OCR ausführen
5. Kandidaten extrahieren
6. dezimale Stellen / Roll-over / Registerlogik berücksichtigen
7. gegen Plausibilität prüfen
8. Benutzer bestätigen lassen

Gespeichert werden:

* Originalbild
* ggf. zugeschnittene Region
* OCR-Rohtext
* OCR-Kandidat
* Konfidenz
* bestätigter Endwert
* Bearbeiter und Zeit

### F. Plausibilitäts- und Qualitätsmodul

Regeln:

* negativer Verbrauch
* Wert kleiner als letzter Wert ohne Roll-over-Ereignis
* unplausibel hoher Sprung
* längerer Stillstand
* Ausreißer gegen gleitenden Durchschnitt
* Ausreißer gegen gleiches Vorjahresintervall
* Konflikt zwischen OCR-Konfidenz und erwartetem Bereich
* fehlende Ablesung nach Intervallregel
* verdächtige Nullwerte
* plötzliche Registersprünge HT/NT

Ausgabe:

* `ok`
* `warn`
* `block`
* `estimated`
* `requires_confirmation`

### G. Verbrauchs-Engine

Die Plattform muss drei Grundtypen sauber rechnen:

1. **absolute Zählerstände**

   * Verbrauch = Delta aufeinanderfolgender bestätigter Stände
   * Roll-over, Reset und Gerätetausch beachten

2. **Impulszähler**

   * Verbrauch = Pulse × Faktor

3. **Intervallwerte / Smart Meter**

   * Verbrauch direkt je Zeitfenster

Zusätzlich:

* mehrere Register pro Gerät
* Summierung über Register
* virtuelle Zähler
* Summen- und Differenzzähler
* frei definierte Gruppen
* Aggregation auf Stunde/Tag/Woche/Monat/Jahr/Custom

Wichtig für sporadische manuelle Ablesungen:

* Kalenderperioden dürfen angezeigt werden
* bei Lücken muss zwischen

  * **exakten Stützpunkten**
  * **Intervallverbrauch**
  * **proratisierter Schätzung**
    unterschieden werden

Die UI muss Schätzanteile sichtbar markieren, sonst ist das am Ende nur hübsch verpackte Fantasie mit Kommastellen.

### H. Kosten-Engine

Ziel ist **Kostenanalyse**, nicht automatisch eine rechtssichere Betriebskostenabrechnung.

Unterstützte Modelle:

* Arbeitspreis
* Grundpreis
* mehrstufige Tarife
* Zeitfenster-/Registerpreise
* Gültigkeitszeiträume
* objektbezogene Tarife
* messpunktbezogene Tarife
* optionale Zuschläge / Steuern / Nebenkostenbestandteile

Kostenansichten:

* Kosten pro Zeitraum
* Kosten pro Medium
* Kosten pro Objekt
* Kosten pro Gruppe
* Vorjahresvergleich
* Kosten/Einheit
* Kosten/Fläche

### I. Wetterintegration

Pro Gebäude gespeichert:

* Adresse
* Breitengrad/Längengrad
* bevorzugte Wetterstation
* Stationsmodus: automatisch / manuell fixiert
* Wettercache-Status
* letzte erfolgreiche Synchronisation

Funktional:

* automatische Stationswahl nach Standort
* manuelle Stationsübersteuerung
* lokales Caching von Tages- und Stundenwerten
* Persistenz der Wetterprovenienz
* Resync bei Stationswechsel

DWD stellt offene Stations- und Klimadaten in mehreren zeitlichen Auflösungen bereit; darunter auch technische Parameter wie Heating Degree Days und Cooling Days. meterweb soll diese Logik nicht als Blackbox verstecken, sondern auf täglicher Temperaturbasis nachvollziehbar selbst ableiten bzw. modellieren. ([Deutscher Wetterdienst][6])

### J. Witterungsbereinigung

#### Grundsatz

Die Plattform unterstützt witterungsbereinigte Ansichten, aber **nicht blind für jedes Medium gleich**.

Default-Eignung:

* **sehr sinnvoll**: Heizung, Gas, Fernwärme, Wärmemenge
* **bedingt sinnvoll**: Strom bei HVAC-/Wärmepumpen-lastigen Objekten
* **meist nur eingeschränkt sinnvoll**: Warmwasser
* **standardmäßig nicht aktiv**: Kaltwasser, Hilfsmedien ohne klare Wetterkopplung

#### Unterstützte Modelle

1. **Heizgradtage-Modell**

   * geeignet für klassische Heizverbräuche
   * Basistemperatur pro Gebäude/Medium konfigurierbar
   * Vergleich gegen Referenzwitterung

2. **Basislast + HDD-Regressionsmodell**

   * `Verbrauch = Basislast + Steigung × HDD`
   * Default für Gas/Wärme/Heizung

3. **HDD/CDD-Regressionsmodell**

   * `Verbrauch = Basislast + a×HDD + b×CDD`
   * Default für witterungssensiblen Strom / Wärmepumpen

4. **segmentierte Temperaturregression**

   * automatische Suche einer Balance-Temperature
   * für anspruchsvollere Fälle mit ausreichend Historie

5. **benutzerdefiniertes Modellprofil**

   * für Fortgeschrittene
   * aber weiterhin mit Visualisierung der Modellgüte

#### Referenzwitterung

Die Plattform bietet drei Referenzmodi:

* Vergleichsperiode gegen andere Periode
* rollierende Mehrjahresreferenz aus lokal gecachten Wetterdaten
* benutzerdefinierte Referenzjahre

#### Qualitätsregeln

Witterungsbereinigung wird nur aktiv angeboten, wenn:

* genügend historische Daten vorhanden sind
* Modellgüte über Mindestschwelle liegt
* Datenlücken nicht zu groß sind

Sonst zeigt die UI:

* Modell ungeeignet
* Datenbasis unzureichend
* Ergebnis nur indikativ

#### Visualisierungen

* Rohverbrauch vs. bereinigter Verbrauch
* HDD/CDD-Overlay
* Scatter Verbrauch vs. Außentemperatur
* Regression + Gütemaße
* Baseload-Anteil vs. wetterabhängiger Anteil
* Vorjahresvergleich roh / bereinigt

---

## 2.4 Datenmodell

### Kernentitäten

#### `user`

* id
* username
* password_hash
* locale
* timezone
* created_at
* updated_at

#### `system_setting`

* key
* value_json

#### `medium_type`

* id
* key
* name_de
* name_en
* base_unit
* display_unit
* category
* weather_sensitivity_default
* cost_enabled
* active

#### `building`

* id
* name
* address_line1
* postal_code
* city
* country
* lat
* lon
* timezone
* floor_area
* heated_area
* notes

#### `unit`

* id
* building_id
* name
* code
* usage_type
* area
* occupants
* notes

### Messlogik

#### `meter_point`

Der **logische Messpunkt**.

* id
* building_id
* unit_id nullable
* medium_type_id
* name
* code
* direction (`consumption`, `production`, `feed_in`, `bidirectional`)
* is_virtual
* aggregation_mode
* active

#### `meter_device`

Das **physische Gerät**.

* id
* meter_point_id
* serial_number
* manufacturer
* model
* reading_mode (`absolute`, `pulse`, `interval`)
* display_type (`digital`, `roller`, `dial`, `unknown`)
* install_date
* removal_date
* rollover_value nullable
* multiplier
* pulse_factor nullable
* photo_capture_enabled
* ocr_profile
* status

#### `meter_register`

* id
* meter_device_id
* register_index
* label
* tariff_code
* unit
* factor
* decimals
* active

#### `meter_reading`

* id
* meter_register_id
* reading_timestamp
* raw_value
* normalized_value
* source (`manual`, `photo_ocr`, `mobile_manual`, `import`, `api`)
* quality (`actual`, `estimated`, `corrected`, `reconstructed`)
* validation_status
* note
* created_at

#### `meter_interval_value`

Für hochaufgelöste Smart-Meter-Daten.

* id
* meter_register_id
* start_ts
* end_ts
* value
* unit
* quality
* source

#### `meter_event`

* id
* meter_point_id
* meter_device_id nullable
* event_type (`install`, `replace`, `remove`, `reset`, `rollover`, `maintenance`)
* event_timestamp
* payload_json
* note

#### `virtual_meter_formula`

* id
* meter_point_id
* expression
* validation_state
* last_eval_at

### Gruppen und Auswertungsobjekte

#### `group`

* id
* name
* description
* group_type (`mixed`, `building`, `unit`, `meter_point`)
* active

#### `group_member`

* id
* group_id
* member_type (`building`, `unit`, `meter_point`, `group`)
* member_id
* weight nullable

### Upload/OCR

#### `file_asset`

* id
* storage_path
* mime_type
* sha256
* width
* height
* size_bytes
* created_at

#### `reading_attachment`

* id
* meter_reading_id
* file_asset_id
* attachment_type (`photo_original`, `photo_crop`, `report`, `export`)

#### `ocr_run`

* id
* file_asset_id
* provider
* ocr_text
* candidate_value
* confidence
* bbox_json
* preprocessing_meta_json
* accepted
* accepted_reading_id nullable

### Wetter

#### `weather_location`

* id
* building_id
* lat
* lon
* station_mode (`auto`, `manual`)
* preferred_source_id nullable
* preferred_dwd_station_id nullable
* preferred_station_name nullable

#### `weather_observation_hourly`

* id
* weather_location_id
* ts
* brightsky_source_id
* dwd_station_id
* station_name
* distance_m
* temperature
* dew_point
* relative_humidity
* precipitation
* pressure_msl
* sunshine
* cloud_cover
* wind_speed
* wind_direction
* solar_radiation nullable
* condition nullable
* icon nullable

#### `weather_observation_daily`

* id
* weather_location_id
* date
* min_temp
* max_temp
* mean_temp
* precipitation_sum
* sunshine_sum
* hdd
* cdd
* source_meta_json

### Normalisierung und Analytik

#### `normalization_profile`

* id
* scope_type (`building`, `meter_point`, `group`)
* scope_id
* medium_type_id
* model_type
* base_temperature_hdd
* base_temperature_cdd
* baseload
* slope_hdd
* slope_cdd
* fit_score
* reference_mode
* reference_period_json
* enabled

#### `consumption_aggregate`

* id
* scope_type
* scope_id
* medium_type_id
* interval_type
* interval_start
* interval_end
* raw_consumption
* normalized_consumption nullable
* estimated_share
* cost_amount nullable
* quality_score

### Kosten

#### `tariff`

* id
* scope_type (`global`, `building`, `meter_point`)
* scope_id nullable
* medium_type_id
* name
* valid_from
* valid_to
* currency
* pricing_model

#### `tariff_component`

* id
* tariff_id
* component_type (`work`, `base`, `tax`, `surcharge`)
* register_label nullable
* unit_price
* unit
* step_from nullable
* step_to nullable
* recurrence (`monthly`, `yearly`, `once`, `per_period`)
* metadata_json

### Alarme und Reports

#### `alert_rule`

* id
* scope_type
* scope_id
* rule_type
* config_json
* enabled

#### `alert_event`

* id
* alert_rule_id nullable
* scope_type
* scope_id
* severity
* title
* message
* detected_at
* resolved_at nullable
* payload_json

#### `report_job`

* id
* report_type
* scope_type
* scope_id
* params_json
* status
* output_file_asset_id nullable
* created_at
* finished_at nullable

#### `audit_log`

* id
* entity_type
* entity_id
* action
* actor
* timestamp
* payload_json

---

## 2.5 Rechenlogik und Regeln

### Messpunkt statt nur „Zähler“

Fachregel: Auswertung erfolgt primär auf **Messpunkt-Ebene**, nicht stumpf auf Geräte-Ebene.

Vorteil:

* Zählerwechsel zerstört keine Historie
* Verbrauchslinien bleiben zusammenhängend
* Gerätehistorie bleibt nachvollziehbar
* OCR- und Roll-over-Parameter bleiben gerätebezogen

### Sparse manuelle Ablesungen

Für seltene Ablesungen gibt es drei Darstellungsmodi:

1. **Kumulierte Stände**
2. **Intervallverbrauch zwischen Ablesungen**
3. **Kalenderperioden mit Proratisierung**

Proratisierte Werte werden visuell gekennzeichnet:

* geschätzt
* teilweise geschätzt
* exakt

### Roll-over und Reset

Bei Differenzbildung gilt:

* wenn neuer Wert < alter Wert:

  * prüfe dokumentiertes Roll-over
  * prüfe dokumentierten Gerätewechsel
  * prüfe Reset-Ereignis
  * sonst Alarm

### Virtuelle Zähler

Virtuelle Zähler verwenden einen Ausdruckseditor:

* `A + B`
* `A - B`
* `SUM(group:X)`
* `A_ht + A_nt`

Regeln:

* nur freigegebene Operatoren
* Zyklenerkennung
* Versionshistorie der Formel
* Vorab-Simulation vor Aktivierung

---

## 2.6 API-Spezifikation

### HTML-Routen

* `/login`
* `/dashboard`
* `/buildings`
* `/buildings/{id}`
* `/units/{id}`
* `/meter-points`
* `/meter-points/{id}`
* `/capture`
* `/capture/{meter_point_id}`
* `/groups`
* `/analytics`
* `/analytics/{scope_type}/{scope_id}`
* `/reports`
* `/alerts`
* `/settings`

### JSON-API v1

#### Auth

* `POST /api/v1/auth/login`
* `POST /api/v1/auth/logout`
* `POST /api/v1/auth/change-password`

#### Stammdaten

* `GET/POST /api/v1/buildings`
* `GET/PATCH/DELETE /api/v1/buildings/{id}`
* `GET/POST /api/v1/units`
* `GET/POST /api/v1/meter-points`
* `GET/POST /api/v1/meter-devices`
* `GET/POST /api/v1/meter-registers`
* `GET/POST /api/v1/groups`

#### Erfassung

* `POST /api/v1/readings/manual`
* `POST /api/v1/readings/photo`
* `POST /api/v1/readings/{id}/confirm`
* `POST /api/v1/readings/{id}/correct`
* `GET /api/v1/meter-points/{id}/latest-reading`

#### OCR

* `POST /api/v1/ocr/run`
* `GET /api/v1/ocr/{id}`
* `POST /api/v1/ocr/{id}/accept`
* `POST /api/v1/ocr/{id}/reject`

#### Wetter

* `GET /api/v1/weather/buildings/{id}/station`
* `POST /api/v1/weather/buildings/{id}/station/auto`
* `POST /api/v1/weather/buildings/{id}/station/manual`
* `POST /api/v1/weather/buildings/{id}/sync`
* `GET /api/v1/weather/buildings/{id}/series`

#### Analytik

* `GET /api/v1/analytics/consumption`
* `GET /api/v1/analytics/costs`
* `GET /api/v1/analytics/normalized`
* `GET /api/v1/analytics/charts/{scope_type}/{scope_id}`
* `GET /api/v1/analytics/scatter/{scope_type}/{scope_id}`

#### Reports / Export

* `POST /api/v1/reports/monthly`
* `POST /api/v1/export/csv`
* `POST /api/v1/export/xlsx`
* `POST /api/v1/export/pdf`
* `GET /api/v1/report-jobs/{id}`

#### Alerts

* `GET /api/v1/alerts`
* `POST /api/v1/alerts/rules`
* `POST /api/v1/alerts/{id}/resolve`

### API-Prinzipien

* JSON only
* OpenAPI automatisch aus FastAPI
* Pydantic-Modelle für Request/Response
* konsistente Zeitangaben in ISO 8601
* Lokalisierung nur in UI, nicht in API-Payloads
* Domainfehler mit sauberen Fehlercodes und maschinenlesbaren Details

---

## 2.7 UX-Spezifikation

## Navigation

Linke Hauptnavigation:

* Dashboard
* Gebäude
* Einheiten
* Zähler
* Erfassung
* Gruppen
* Analysen
* Berichte
* Alarme
* Einstellungen

Topbar:

* Suche
* Sprachumschalter
* Theme Toggle
* Schnellzugriff auf „Neue Ablesung“
* Benutzer-Menü

## Dashboard

KPI-Karten:

* heutige / aktuelle offene Alarme
* zuletzt erfasste Zähler
* fehlende Ablesungen
* aktueller Monatsverbrauch pro Medium
* aktueller Monatskostenstand
* Roh vs. bereinigt
* Top-Ausreißer

Charts:

* Verbrauch Trend 12 Monate
* Kosten Trend
* Roh/Bereinigt Toggle
* Witterungs-Overlay
* Gruppenvergleich

## Mobile Erfassung

Die wichtigste Seite im Projekt. Nicht das hübscheste Diagramm.

Eigenschaften:

* große Touch-Flächen
* numerische Tastatur
* letzter bestätigter Stand prominent
* erwarteter Bereich als Hilfsband
* Kamera-Button direkt im Formular
* OCR-Vorschlag inline
* Warnung sofort, nicht nach Seitenreload
* „nächster Zähler“-Flow für Rundgänge
* optional PWA-artiger Homescreen-Start

## Analyseseiten

Filterleiste:

* Zeitraum
* Granularität
* Scope: Gebäude / Einheit / Messpunkt / Gruppe
* Medium
* Roh / bereinigt
* Kosten / Verbrauch
* Vergleichsmodus
* Normierungsmodell
* Wetter-Overlay

Chartkatalog:

* Linienchart
* Balkenchart
* gestapelter Balkenchart
* Flächenchart
* Kombichart
* Lastgang
* Kalenderheatmap
* Scatterplot mit Regressionslinie
* YoY-Monatsvergleich
* KPI-Tiles
* Sankey nur, wenn lizenz- und adapterseitig verfügbar

Zu jedem Chart gehört eine „Berechnung anzeigen“-Ansicht:

* Datenbasis
* Aggregation
* Schätzanteil
* Modell
* Tarife
* Wetterquelle

## Berichte

Reporttypen:

* Monatsbericht Gebäude
* Monatsbericht Gruppe
* Zählerhistorie
* Alarmbericht
* Kostenbericht

Ausgabeformate:

* HTML
* Druckansicht
* PDF
* CSV
* XLSX

Monatsbericht Gebäude enthält mindestens:

* Stammdatenkopf
* Zeitraum
* letzte Ablesungen
* Verbrauch nach Medium
* Kosten nach Medium
* Roh/Bereinigt-Vergleich
* wichtigste Alarme
* Diagramme
* Tabellenanhang

---

## 2.8 Open-Source-, Lizenz- und Deployment-Regeln

### App-Lizenz

Empfehlung für **meterweb-Code**: **AGPL-3.0-or-later**.

Begründung:

* Self-hosted passt gut
* Änderungen an Netzwerkbereitstellungen bleiben offen
* verhindert, dass jemand das Projekt einfach einsackt und mit Schleifchen verkauft

Falls du permissiver willst, ist **Apache-2.0** die pragmatische Alternative.

### Drittkomponenten

* Tabler ist unkritisch als MIT-basierte UI-Grundlage. ([Tabler][7])
* Bright Sky ist als Open-Source-Service unkritisch integrierbar; beachten muss man die DWD-Nutzungsbedingungen für die abgerufenen Daten. ([Bright Sky][4])
* ApexCharts ist der juristisch empfindliche Teil. meterweb muss deshalb:

  * Lizenzhinweis dokumentieren
  * Adapter-Schicht haben
  * Bundling-/Redistribution-Frage vor öffentlicher OSS-Veröffentlichung aktiv klären ([ApexCharts.js][3])

### Docker Compose

Compose-Datei enthält mindestens:

* `web`
* `worker`
* Volumes:

  * `app_data`
  * `uploads`
  * `reports`
  * `backups`

Environment:

* `SECRET_KEY`
* `ADMIN_USERNAME`
* `ADMIN_PASSWORD`
* `DATABASE_URL=sqlite:////data/meterweb.db`
* `WEATHER_PROVIDER=brightsky`
* `WEATHER_BASE_URL`
* `DEFAULT_LOCALE`
* `DEFAULT_TIMEZONE`

### Backup / Restore

Pflichtfunktionen:

* SQLite-Snapshot/Backup
* Upload-Verzeichnis sichern
* Berichtsausgaben sichern
* Restore-Doku
* optional geplanter Backup-Job

---

## 2.9 Abnahmekriterien

Das Projekt gilt als fachlich fertig, wenn folgende Fälle durchgängig funktionieren:

1. `docker compose up` startet die Plattform ohne manuelles Gefrickel.
2. Erstlogin funktioniert.
3. Ein Gebäude, eine Einheit, mehrere Messpunkte und mehrere Geräte pro Medium können angelegt werden.
4. Manuelle Ablesung funktioniert mobil.
5. Foto-Upload mit OCR-Vorschlag funktioniert.
6. Plausibilitätswarnungen erscheinen korrekt.
7. Zählerwechsel und Roll-over verfälschen die Historie nicht.
8. Verbräuche und Kosten werden auf Messpunkt-, Gebäude- und Gruppenebene korrekt aggregiert.
9. Wetterdaten werden je Gebäude geladen, lokal gecacht und einer Station zugeordnet.
10. Roh- und witterungsbereinigte Darstellung sind umschaltbar.
11. Modellgüte und Schätzanteile sind sichtbar.
12. CSV, XLSX und PDF-Berichte funktionieren.
13. Deutsch/Englisch und Zahlen-/Datumsformate sind korrekt lokalisiert.
14. Unit-, Integrations- und E2E-Tests decken die Kernprozesse ab.
15. Doku beschreibt Installation, Konfiguration, Backup, Restore und bekannte Lizenzgrenzen.

---
