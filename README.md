# tt-analytics

tt-analytics ist der Analyse-Microservice der Tigers-Plattform.

## Versionierung

- verbindliche Service-Version steht in `VERSION`
- Release-Tags folgen `vMAJOR.MINOR.PATCH`
- `main` publisht Beta-Images nach GHCR mit Tag `beta`
- Produktion deployt feste Release-Tags wie `v0.1.0`

Ziel ist eine AI-gestuetzte Spielanalyse fuer American Football:

- Upload von mehreren Spielvideos bzw. vielen einzelnen Clips pro Gegner
- strukturierte Play-by-Play-Analyse per LLM
- Aggregation der Analysen zu Scouting Reports fuer Coaches
- zusaetzlicher Wissenskontext durch Playbooks, PDFs, Praesentationen und Notizen
- zentrale Anmeldung ueber tt-auth

## Betriebsstatus

Aktiver Stack (Beta):

- https://beta.thun-tigers.net/analytics/
- zentrale Anmeldung ueber https://beta.thun-tigers.net/auth/
- Launch ueber tt-auth mit SSO-Token

Lokal im Gesamtstack: Einstieg ueber Caddy-Reverse-Proxy auf `http://localhost:8080`.

- tt-auth: http://localhost:8080/auth/
- tt-agenda: http://localhost:8080/agenda/
- tt-analytics: http://localhost:8080/analytics/
- tt-members: http://localhost:8080/members/
- tt-attendance: http://localhost:8080/attendance/
- tt-infra: http://localhost:8080/infra/

Direkte Service-Ports 8084–8089 sind lokal weiterhin verfuegbar.

Empfohlener Start lokal ueber tt-infra:

```bash
cd ../tt-infra
./setup.sh
```

Details zur Plattform-Konfiguration und zum Reverse-Proxy siehe
`../tt-infra/docs/HANDOFF_CENTRAL_CONFIG_AND_PROXY.md`.

Die Doku fuer den ersten Architektur- und Produktentwurf liegt unter:

- docs/vision.md
- docs/architecture.md
- docs/data-model.md
- docs/use-cases.md
- docs/backlog.md
- docs/decisions.md
- docs/hudl-reference.md
- docs/play-analysis-schema.md
- docs/report-structure.md
- docs/safv-import.md

## Zielbild

Ein Coach kann vor einem Spiel mehrere gegnerische Spiele hochladen, diese in einzelne Plays oder Clips aufteilen lassen, Play-Analysen erzeugen und daraus einen Scouting Report erstellen lassen.

## Technische Leitplanken

- zentrale Authentifizierung ueber tt-auth
- eigene Postgres-Datenbank
- Videos nicht in Postgres speichern, sondern in Object Storage
- AI-Zugriff im aktuellen MVP direkt ueber Gemini
- LiteLLM bleibt als naechste Abstraktionsschicht geplant
- asynchrone Verarbeitung statt synchroner Monster-Requests

## Status

Der aktuelle Stand umfasst:

- Produkt- und Architekturplanung fuer den MVP
- analysierte Hudl-Referenzen und Breakdown-Import
- Flask- und Jinja2-Webanwendung mit SSO ueber tt-auth
- Postgres-faehige Service-Konfiguration fuer lokalen Docker-Betrieb
- Team-, Spiel-, Run- und Report-Verwaltung
- Clip-Upload und Gemini-basierte Play-Analyse mit Retry-Logik
- mehrstufige Report-Synthese mit Executive Overview, Tendency Tables und Full Report
- HTML-basierter PDF-Export, damit Web- und PDF-Darstellung dieselbe Report-Struktur nutzen
