# Roadmap

## 0.4.0 — Deployment providers

• Providerinterface voor Render, VPS/Docker en toekomstige hosting
• Bewuste providerkeuze per project
• Deploymentlogs en rollbackinformatie
• Automatische HTTPS- en healthcheckcontrole
• Ondersteuning voor subdomeinen zoals `palletoptimizer.hessel.nl`

## 0.5.0 — Data en accounts

• Supabase- en generieke PostgreSQL-adapter
• Google- en GitHub-login als verwisselbare authenticatiemodules
• Offline-first opslag met latere synchronisatie
• Database-migraties en back-upcontrole
• Row Level Security-checks voor gebruikersdata

## 0.6.0 — Automation hub

• Home Assistant-adapter
• MQTT-adapter voor Raspberry Pi en lokale apparaten
• Robotstofzuiger-, robotmaaier- en energiemodules
• Webhooks, notificaties en geplande taken
• Centrale secrets-configuratie zonder sleutels in GitHub

## Permanente ontwerpregels

• Eerst preview, daarna code
• Iedere repo gebruikt hetzelfde `turbo-project.json` contract
• Kernlogica blijft los van hosting, database en externe integraties
• Rate limiting, invoerlimieten en time-outs worden per openbare app beoordeeld
• Publiceren gebeurt pas nadat tests, Git-status, healthcheck en securitychecks groen zijn
• Modules moeten in- en uitgeplugd kunnen worden zonder de kernapp te breken
