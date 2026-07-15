# Changelog

## 0.7.0

• Bovenin de bestaande layout staat nu compact de actuele status van Turbo Repo Hub zelf
• Toont de lokale commit, actieve branch en het tijdstip van de laatste GitHub-controle
• Maakt onderscheid tussen `Up-to-date`, `Update beschikbaar`, `Lokale wijzigingen`, `Lokaal voor op GitHub` en `Controle mislukt`
• De bestaande dashboardlayout en repositorykaarten zijn verder ongewijzigd gebleven

## 0.6.0

• Centrale knop `Open FTP settings` toegevoegd aan het bestaande instellingenpaneel
• FTP- en FTPS-instellingen kunnen lokaal worden opgeslagen en getest
• FTP-wachtwoorden worden op Windows versleuteld opgeslagen
• Per repository kan een aparte Hostnet-publicatiemap worden ingesteld

## 0.5.0

• Statuslabels gewijzigd naar rustige afgeronde rechthoeken voor `Update`, `Updated` en `Publiceer`
• Nieuwe knop `Open repo` opent de lokale projectmap
• Nieuwe knop `Open GitHub` opent direct de juiste repositorypagina
• Nieuwe knop `Start repo` voert het startcommando uit `turbo-project.json` uit
• Draaiende projecten tonen automatisch `Stop repo`
• Localhost opent automatisch nadat een project is gestart wanneer een health-URL beschikbaar is
• Kaarten behouden een vaste compacte breedte, ook wanneer maar één repository zichtbaar is
• Actieknoppen en metadata zijn opgesplitst voor een rustiger en duidelijker kaartontwerp

## 0.4.0

• Nieuw vereenvoudigd kaartdashboard voor alle lokale en gekoppelde repositories
• Per repository alleen de kernstatussen `Update`, `Updated` en `Publiceer`
• Compacte preview bij hover zonder het dashboard vol te zetten
• Zoekfunctie en eenvoudige filters voor updates, bijgewerkte projecten en publicatie
• GitHub- en mapinstellingen verplaatst naar een rustig uitklapbaar paneel
• WinGet-detectie hersteld via het volledige WindowsApps-pad
• Launcher voegt WindowsApps automatisch toe aan PATH voor de actieve sessie
• Duidelijkere foutmelding wanneer Microsoft App Installer echt ontbreekt

## 0.3.0

• Volledig modern dashboard met grote projectkaarten, gradients en vector-previews
• Automatische pills voor `NIEUW`, `NIEUWE UPDATE`, `DRAAIT`, `LIVE`, `PRIVÉ` en `PUBLICATIE KLAAR`
• Lokale commit vergelijken met de GitHub-versie
• Nieuwe GitHub-repo's automatisch bovenaan tonen
• Alle openbare en privé-repo's importeren via officiële GitHub CLI-login
• Filters voor nieuw, updates, draaiend en live
• Laatste wijzigingsdatum en changelog-samenvatting per project
• Testknop met zichtbaar testresultaat
• Veilige publicatiecheck zonder blind te deployen
• Uitgebreid modulair `turbo-project.json` contract
• Voorbereiding voor databases, authenticatie, Home Assistant en MQTT

## 0.2.0

• GitHub CLI installeren vanuit de launcher
• Eenmalig via de browser inloggen bij GitHub
• Alle repositories automatisch importeren
• Metadata voor openbare en privé-repositories bewaren

## 0.1.0

• Eerste werkende Turbo Repo Launcher
• Moderne dashboard-UI met gradients en cards
• GitHub-repo toevoegen via URL
• Repo lokaal clonen en synchroniseren
• Project lokaal starten en stoppen
• Projectmap en Visual Studio Code openen
• Preview, versie, poort en Git-status per project tonen
