# SAFV Import

## Ziel

`tt-analytics` soll SAFV-Spielseiten als ergaenzende Quelle fuer offiziellen Spielkontext und spielbezogene Kaderdaten nutzen.

Die SAFV-Daten ersetzen weder Videoanalyse noch manuelles Review.

Sie liefern vor allem:

- offizielles Spiel-Metadaten- und Event-Backing
- Kader pro Spiel mit Rueckennummern
- Spieler-Mapping fuer spaetere Video- oder Report-Zuordnung

## URL-Modell

Die Quelle ist spielbasiert aufgebaut:

- `https://www.safv.ch/games/{game_id}`
- `https://www.safv.ch/games/{game_id}/lineup`
- `https://www.safv.ch/games/{game_id}/gamesheet`

Fuer den MVP reicht es, pro `game` eine externe Spiel-ID oder Basis-URL zu speichern.

## Produktrolle der SAFV-Daten

SAFV ist in `tt-analytics` eine `official context source`.

Das bedeutet:

- SAFV liefert offizielle Spielkontextdaten
- SAFV liefert keine vollstaendige Gegner-Scouting-Taxonomie
- SAFV ist kein Ersatz fuer Clip-Analyse
- SAFV ist kein Ersatz fuer Hudl- oder manuell gepflegte Breakdown-Felder

## Was aus SAFV direkt importiert werden soll

### Aus `games/{id}`

- externe Spiel-ID
- Heimteam
- Auswaertsteam
- Spieltitel oder Label
- Spielstatus, falls vorhanden
- Spieldatum, falls vorhanden

### Aus `games/{id}/lineup`

- Teamnamen
- spielbezogener Kader je Team
- Rueckennummer
- Spielername
- Staff-Mitglieder je Team
- Staff-Rolle, falls vorhanden
- offiziell angezeigte Einzelstatistiken, falls gepflegt

### Aus `games/{id}/gamesheet`

- Endstand
- Viertel- oder Abschnittsscores
- Event-Liste in offizieller Reihenfolge
- Event-Typen wie Touchdown, Try, Penalty, Personal Foul
- Teambezug pro Event
- Spielerbezug pro Event, falls angegeben

## Was explizit nicht aus SAFV abgeleitet werden soll

Diese Aussagen sind aus `lineup` und `gamesheet` allein fachlich nicht belastbar:

- `most blitzing LB`
- `top receiver`, wenn Receiving-Stats nicht explizit vorhanden sind
- Formation-, Personnel- oder Coverage-Tendenzen
- Positionssicherheit wie `LB`, `CB`, `slot`, `boundary`
- Snap Counts
- Route-Trees
- Fronts, Pressure, Coverage, Checks

Solche Aussagen duerfen erst entstehen, wenn weitere Quellen vorliegen:

- Video- oder Clip-Analyse
- manuelle Review
- optionale Kader- oder Positionspflege
- externe Breakdown-Daten

## Fachliche Nutzung in Analysen und Reports

SAFV-Daten sollen in drei Ebenen einfliessen.

### 1. Spielkontext

Verwendbar fuer:

- offiziellen Endstand
- Viertelverlauf
- auffaellige Penalty-Haeufungen
- Scoring-Zusammenfassung
- Berichtssektion `Sample und Datenbasis`

### 2. Roster-Mapping

Verwendbar fuer:

- Zuordnung `Nummer -> Spielername`
- Abgleich von im Video erkannten Nummern
- personbezogene Report-Referenzen mit klarer Quellenlage

### 3. Offizielle Events

Verwendbar fuer:

- Penalty-Trends auf Team-Ebene
- namentlich genannte Penalty-Spieler
- Gegenpruefung gegen Video oder manuelles Tagging
- Kontext fuer auffaellige Drives oder Punktewechsel

## Spielerbezogene Aussagen: Erlaubt vs. nicht erlaubt

### Erlaubt

- `Spieler X war im offiziellen Kader fuer dieses Spiel`
- `Nummer 87 entspricht Thomas Schrepfer`
- `Spieler X wird im Gamesheet bei einer Personal-Foul-Strafe genannt`
- `Team Y hatte im offiziellen Spielbericht mehrere Penalty-Events`

### Nur mit Zusatzquellen erlaubt

- `Spieler X war der top receiver`
- `Spieler Y war der most blitzing LB`
- `Spieler Z war der wichtigste Edge-Rusher`
- `Nummer 24 ist mit hoher Wahrscheinlichkeit der Balltraeger in mehreren Clips`

Fuer solche Aussagen muss `tt-analytics` die Herkunft kenntlich machen:

- `official`
- `ai_inferred`
- `manually_reviewed`
- `mixed_confidence`

## Vorschlag fuer das Datenmodell

Der bestehende Kern in `game`, `clip`, `clip_metadata` und `report` reicht im Grundsatz aus.

Fuer den MVP ist keine neue grosse Objektfamilie noetig.

Sinnvoll sind drei zusaetzliche Strukturen.

### A. Externe Spielreferenz am `game`

Empfohlene Felder:

- `external_source` mit Wert `safv`
- `external_game_id`
- `external_base_url`
- `external_last_synced_at`

Beispiel:

```json
{
  "external_source": "safv",
  "external_game_id": "2442561",
  "external_base_url": "https://www.safv.ch/games/2442561"
}
```

### B. Spielweite SAFV-Metadaten

Empfehlung:

- neue Tabelle `game_external_data`
- oder fuer den MVP ein JSON-Feld an `game`

Empfohlene Payload-Struktur:

```json
{
  "source": "safv",
  "official_game_context": {
    "final_score": {
      "home": 13,
      "away": 7
    },
    "period_scores": [
      {"period": 1, "home": 7, "away": 0},
      {"period": 2, "home": 0, "away": 0},
      {"period": 3, "home": 6, "away": 0},
      {"period": 4, "home": 0, "away": 7}
    ]
  },
  "sync_meta": {
    "imported_at": "2026-04-12T18:00:00Z",
    "parser_version": "v1"
  }
}
```

### C. Spielbezogener Roster-Snapshot

Empfehlung:

- neue Tabelle `game_roster_entry`
- alternativ MVP-Start als JSON unter `game_external_data`

Empfohlene Struktur:

```json
{
  "team_name": "St.Gallen Bears",
  "players": [
    {
      "jersey_number": "87",
      "player_name": "Thomas Schrepfer",
      "position": null,
      "source": "official"
    }
  ],
  "staff": [
    {
      "name": "Giorgio Giovanni Volpi",
      "role": "Cheftrainer"
    }
  ]
}
```

### D. Offizielle Event-Liste

Empfehlung:

- neue Tabelle `game_event`
- oder MVP-seitig JSON-Liste unter `game_external_data`

Empfohlene Struktur:

```json
{
  "sequence": 8,
  "period": 2,
  "clock": "12:00",
  "event_type": "personal_foul",
  "team_name": "St.Gallen Bears",
  "player_name": "Thomas Schrepfer",
  "jersey_number": "87",
  "yards": 15,
  "source": "official"
}
```

## Integration in bestehende Objekte

### `game`

`game` bleibt neutral und traegt nur die Spielidentitaet plus Referenz zur SAFV-Quelle.

### `clip_metadata`

`clip_metadata` bleibt die richtige Stelle fuer clipnahe Felder wie:

- `PLAY #`
- `DN`
- `DIST`
- `HASH`
- `PLAY TYPE`

SAFV-Daten gehoeren nur dann an einen Clip, wenn eine bewusste Zuordnung von Spiel-Event zu Clip erfolgt.

### `report`

Reports sollen SAFV als eigene Herkunft sichtbar machen, zum Beispiel:

- `official game context`
- `official roster`
- `official event log`

So bleibt klar, welche Aussagen aus offiziellen Daten stammen und welche aus AI-Analyse.

## Abgeleitete Metriken fuer den MVP

Aus SAFV allein sind nur wenige belastbare Kennzahlen sinnvoll.

### Sofort nutzbar

- Penalties pro Team
- Personal Fouls pro Team
- namentlich genannte Penalty-Spieler
- Punkteverlauf nach Vierteln
- Kadergroesse je Spiel

### Nur vorsichtig nutzbar

- `top scorer`, wenn Touchdowns in der Statistik oder im Event-Log personbezogen sichtbar sind
- `haeufig genannter Spieler im offiziellen Event-Log`

### Nicht als SAFV-only-Metrik ausgeben

- `top receiver`
- `top tackler`
- `most blitzing LB`
- `most targeted DB`
- `pressure leader`

## Ableitungslogik mit Video

SAFV wird dann besonders wertvoll, wenn Videoanalyse dazukommt.

Beispielpipeline:

1. SAFV importiert Kader und Nummern
2. Videoanalyse erkennt in einem Clip unscharf `#87`
3. das System mappt `#87` auf den offiziellen Spielkader
4. die Aussage wird als `ai_inferred_from_video_with_official_roster_mapping` gekennzeichnet
5. Review bestaetigt oder verwirft die Zuordnung

So koennen spaeter auch personbezogene Aussagen entstehen, obwohl die SAFV-Seite selbst keine Blitz- oder Receiving-Statistiken liefert.

## Vertrauens- und Quellenstufen

Fuer spaetere Reportlogik sind vier Stufen sinnvoll:

1. `official`
2. `official_plus_mapping`
3. `ai_inferred`
4. `manually_reviewed`

Beispiele:

- `Thomas Schrepfer #87 im Kader` -> `official`
- `Penalty gegen #87 Thomas Schrepfer` -> `official`
- `wahrscheinlich #87 als Edge Defender in 4 Clips` -> `ai_inferred`
- `#87 als Starting LB im Report bestaetigt` -> `manually_reviewed`

## Technische Risiken

- SAFV scheint ueber Clubee zu laufen; HTML-Struktur kann sich aendern
- beim Lesen der Seiten traten bereits `429`-Antworten auf
- nicht alle offiziellen Statistikfelder sind fuer jedes Spiel gepflegt
- einzelne Event-Texte koennen ohne stabile IDs nur textbasiert geparst werden

## MVP-Empfehlung

Der kleinste sinnvolle erste Wurf ist:

1. manuelle Hinterlegung von `external_game_id` am `game`
2. Import von `lineup` in einen spielbezogenen Roster-Snapshot
3. Import von `gamesheet` in `official_game_context` plus Event-Liste
4. Anzeige dieser Daten im Spiel-Detail und im Report
5. keine automatischen Aussagen ueber Positionen, Blitzes oder Receiving-Leader ohne Zusatzquellen

## Spaeterer Ausbau

- Matching von SAFV-Roster gegen intern gepflegte Spielerprofile
- optionale Positionspflege pro spielbezogenem Roster-Eintrag
- Zuordnung offizieller Events zu Clips
- Nutzung offizieller Namen in Review-UI und Report-Tables
- abgeleitete personbezogene Tendenzen nur mit Quellenkennzeichnung