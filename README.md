# Turbo Repo Launcher

Jouw lokale, toekomstbestendige softwarefabriek. Ideeën worden eerst visueel uitgewerkt, daarna als modulaire GitHub-repo gebouwd, lokaal getest en pas na duidelijke controles gepubliceerd.

![Turbo Repo Launcher preview](docs/previews/latest.svg)

## De vaste workflow

```text
Idee inspreken op telefoon
        ↓
Analyse van nut, kosten, veiligheid en techniek
        ↓
Visuele preview ter goedkeuring
        ↓
Lege GitHub-repo handmatig aanmaken
        ↓
Complete code en documentatie naar GitHub schrijven
        ↓
Turbo Repo Launcher ontdekt de repo
        ↓
Clone / Update → Start → Test → Goedkeuren
        ↓
Publicatiecheck → hostingprovider kiezen → publiceren
```

De launcher schrijft niet ongemerkt rechtstreeks naar je computer. GitHub is de centrale bron. Met **Clone** of **Update** haal je gecontroleerd de nieuwste code binnen.

## Dashboard

Iedere repository krijgt automatisch een moderne projectkaart met:

• previewafbeelding uit de repository
• projectnaam, beschrijving, versie en technologie
• datum en omschrijving van de laatste wijziging
• lokale en online Git-status
• start-, test-, map- en VS Code-acties
• database-, integratie- en hostinginformatie
• publicatiecheck

Automatische statuspills:

| Pill | Betekenis |
|---|---|
| `NIEUW` | De repo bestaat in GitHub maar is nog niet lokaal gekloond |
| `NIEUWE UPDATE` | GitHub bevat commits die lokaal nog ontbreken |
| `DRAAIT` | De lokale app is gestart |
| `LIVE` | In het manifest staat een openbare URL |
| `PRIVÉ` | Het is een private GitHub-repository |
| `LOKALE CHANGES` | Lokaal staan niet-gecommitte wijzigingen |
| `PUBLICATIE KLAAR` | De technische basiscontroles zijn geslaagd |

## Starten op Windows

```bash
git clone https://github.com/tommyvercettiseh/turbo-repo-launcher.git
```

Dubbelklik daarna op:

```text
Start Turbo Repo Launcher.bat
```

De app opent op:

```text
http://127.0.0.1:8787
```

## GitHub-account koppelen

De launcher gebruikt de officiële GitHub CLI. Daardoor hoef je geen wachtwoord of persoonlijk token in deze app op te slaan.

1. Klik zo nodig op **GitHub CLI installeren**.
2. Start de launcher opnieuw.
3. Klik op **Inloggen met GitHub**.
4. Rond de officiële browserlogin af.
5. Klik op **Alle repo's ophalen**.

Daarna worden jouw openbare en privé-repositories automatisch geïmporteerd.

## Standaard projectmap

```text
%USERPROFILE%\TurboRepos
```

Dit pad is vanuit het dashboard aanpasbaar.

## Het projectcontract

Iedere nieuwe app krijgt een `turbo-project.json`. Voorbeeld:

```json
{
  "schema_version": 1,
  "name": "Rep Counter",
  "slug": "rep-counter",
  "version": "0.1.0",
  "description": "Workouttracker met online voortgang.",
  "preview": "docs/previews/latest.svg",
  "tags": ["FastAPI", "PWA", "PostgreSQL"],
  "runtime": {
    "type": "python-fastapi",
    "port": 8100,
    "start_command": "Start Rep Counter.bat",
    "health_path": "/health"
  },
  "testing": {
    "command": "python -m pytest -q"
  },
  "security": {
    "public_api": true,
    "rate_limiting": true,
    "max_request_seconds": 10
  },
  "data": {
    "mode": "cloud",
    "provider": "supabase"
  },
  "deployment": {
    "enabled": true,
    "provider": null,
    "public_url": null
  },
  "integrations": {
    "home_assistant": false,
    "mqtt": false
  }
}
```

## Veilig publiceren

De knop **Publiceer** voert bewust nog geen blind deploymentcommando uit. Eerst worden onder andere deze punten gecontroleerd:

• manifest aanwezig
• Git-status schoon
• lokale code gelijk aan GitHub
• runtime en startcommando geconfigureerd
• healthcheck aanwezig
• rate limiting gedeclareerd wanneer een openbare API wordt gebruikt
• tests uitvoerbaar

Daarna kan een deploymentprovider worden aangesloten. Dit voorkomt dat een ongeteste of onbeveiligde app per ongeluk openbaar wordt.

## Toekomstige data en accounts

Apps met persoonlijke gegevens, zoals een rep counter, gebruiken een verwisselbare opslaglaag. De eerste logische cloudoptie is Supabase/PostgreSQL met Row Level Security. De appcode blijft echter gekoppeld aan een eigen repository-interface, zodat later naar een eigen PostgreSQL-server of andere provider kan worden gemigreerd.

Niet iedere tool krijgt automatisch accounts:

| Type app | Standaard |
|---|---|
| Open calculator | geen account, geen permanente data |
| Pallet Optimizer | rate limiting en rekentijdlimieten |
| Rep Counter | account en online database |
| Home Assistant-tool | lokaal token en lokale netwerktoegang |

## Home Assistant en Raspberry Pi

Nieuwe automatiseringsprojecten worden opgebouwd met losse adapters:

```text
Core applicatie
├── Webinterface
├── Database-adapter
├── Home Assistant-adapter
├── MQTT-adapter
├── Webhook-adapter
└── Notification-adapter
```

Zo kunnen robotstofzuiger-, robotmaaier-, energie- en Raspberry Pi-modules later worden toegevoegd of verwijderd zonder de kernapp te breken.

## Ontwerpprincipes

• modulair en vervangbaar
• preview vóór codewijzigingen aan de interface
• geen secrets in GitHub
• expliciete invoerlimieten, time-outs en rate limiting
• hosting en database nooit hard aan de kernlogica vastzetten
• tests en healthchecks vóór publicatie
• lokale wijzigingen nooit automatisch overschrijven

Meer informatie staat in [ARCHITECTURE.md](docs/ARCHITECTURE.md) en [PROJECT_STANDARD.md](docs/PROJECT_STANDARD.md).
