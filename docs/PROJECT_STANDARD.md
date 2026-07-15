# Standaard voor toekomstige projecten

Iedere nieuwe repository die via Turbo Repo Launcher wordt beheerd volgt zo veel mogelijk deze structuur:

```text
project/
├── app/ of src/
├── tests/
├── docs/
│   └── previews/
├── migrations/
├── Dockerfile
├── turbo-project.json
├── VERSION
├── CHANGELOG.md
├── ROADMAP.md
├── .env.example
└── README.md
```

## Verplichte bestanden

### `turbo-project.json`

Machineleesbaar contract voor naam, runtime, preview, tests, beveiliging, data, deployment en integraties.

### `VERSION`

Huidige semantische versie, bijvoorbeeld `0.4.0`.

### `CHANGELOG.md`

Bovenaan staat de nieuwste release met korte, menselijke wijzigingen. De launcher toont hiervan een samenvatting.

### `README.md`

Startinstructies, doel, beperkingen en architectuur.

### Preview

Een goedgekeurde afbeelding of SVG onder `docs/previews/latest.svg` of een ander pad dat in het manifest staat.

## UI-workflow

Bij zichtbare interfacewijzigingen:

1. Eerst een visuele preview maken.
2. Feedback verwerken.
3. Pas na goedkeuring de interfacecode wijzigen.
4. Preview in de repository bijwerken.
5. Versie en changelog verhogen.

## Publieke applicaties

Voor iedere openbare applicatie worden minimaal beoordeeld:

• invoerlimieten
• requestgrootte
• rate limiting
• maximale rekentijd
• paralleliteitslimiet
• authenticatie en autorisatie
• logging zonder gevoelige gegevens
• secrets via omgevingsvariabelen
• databasebeleid en back-ups

## Persoonlijke data

Data zoals trainingen, voortgang en voorkeuren krijgt altijd een `user_id`. Bij Supabase/PostgreSQL wordt Row Level Security gebruikt zodat een gebruiker alleen eigen gegevens kan lezen of wijzigen.

## Providers verwisselbaar houden

De kernapp gebruikt interfaces voor:

• dataopslag
• authenticatie
• notificaties
• Home Assistant
• MQTT
• deployment

Een provider mag worden vervangen zonder businesslogica of UI volledig te herschrijven.

## Publicatie

Publiceren mag pas wanneer:

• tests slagen
• lokale Git-status schoon is
• lokale branch gelijkloopt met GitHub
• healthcheck aanwezig is
• securityconfiguratie klopt
• secrets buiten GitHub zijn ingesteld
• database-migraties gecontroleerd zijn

## Repo-pill-regels

• `NIEUW`: online gevonden, nog niet lokaal
• `NIEUWE UPDATE`: remote heeft commits die lokaal ontbreken
• `LOKALE CHANGES`: niet-gecommitte lokale wijzigingen
• `DRAAIT`: door de launcher gestart proces is actief
• `LIVE`: `deployment.public_url` is ingevuld
• `PUBLICATIE KLAAR`: verplichte readiness-checks zijn groen
