# Architectuur

## Doel

Turbo Repo Launcher is de lokale besturingslaag boven GitHub. GitHub blijft de centrale bron van waarheid; de launcher beheert lokale clones, status, previews, tests en publicatiegereedheid.

## Lagen

```text
Mobiele ideeën en instructies
        ↓
GitHub-repositories
        ↓
Turbo Repo Launcher
        ↓
Lokale runtimes en tests
        ↓
Deploymentproviders
```

## Kernmodules

### Repository registry

Bewaart alleen lokale voorkeuren en verwijzingen. Broncode blijft in GitHub.

### GitHub adapter

Gebruikt de officiële GitHub CLI voor login en repository-import. De launcher bewaart zelf geen GitHub-wachtwoord of token.

### Runtime adapter

Leest startcommando, poort en healthcheck uit `turbo-project.json`. Later kunnen adapters voor Python, Node, Docker en Home Assistant-add-ons worden toegevoegd.

### Test adapter

Leest een expliciet testcommando uit het manifest. Zonder expliciet commando gebruikt de launcher alleen een veilige standaard wanneer een `tests`-map aanwezig is.

### Deployment adapter

De huidige versie voert alleen readiness-checks uit. Toekomstige providers implementeren hetzelfde contract voor Render, Docker/VPS of andere hosting.

### Integration adapters

Home Assistant, MQTT, databases, notificaties en webhooks worden als losse adapters gebouwd. Kernlogica mag niet rechtstreeks van één externe provider afhankelijk zijn.

## Beveiliging

• Geen secrets in repositories of manifests
• Lokale wijzigingen blokkeren automatisch pull/update
• Bestandspreviews worden met path traversal-controle geserveerd
• Openbare APIs moeten rate limiting en time-outs declareren
• Publicatie vereist een schoon en actueel Git-project
• Deployment blijft een expliciete handeling

## Data

Projecten kiezen zelf een datamodus:

• `none`: geen permanente data
• `local`: lokale SQLite- of JSON-opslag
• `cloud`: externe PostgreSQL/Supabase-opslag
• `hybrid`: lokale cache met cloudsynchronisatie

De applicatielaag praat met een repository-interface en niet rechtstreeks met Supabase. Hierdoor blijft migratie mogelijk.

## Schaalbaarheid

Zware tools, zoals palletoptimalisatie, krijgen standaard:

• maximale invoerwaarden
• solver-time-out
• begrensde paralleliteit
• rate limiting per gebruiker of IP
• duidelijke `best_found`-status als optimaliteit niet binnen de limiet bewezen is

## Home Assistant

Home Assistant-integraties gebruiken REST, WebSocket of MQTT via een adapter. Tokens blijven lokaal of in de secret store van de hostingomgeving. Apparaten zoals robotmaaiers en robotstofzuigers worden nooit rechtstreeks in de kernlogica hard gecodeerd.
