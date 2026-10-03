# Proton-Scanner (v20)

[English](README.md) | **Deutsch**

Asynchrones Analyse- und Diagnose-Werkzeug für **ProtonVPN-Server**, geschrieben in Python 3.10+ mit `asyncio`, `dnspython` und `rich`.

Der primäre Einsatzzweck des Scanners liegt im **Auffinden und Zuordnen von IPv6-fähigen ProtonVPN-Nodes** (AAAA-Records), um deren IPv6-Adressen als dedizierte VPN-Endpunkte zu ermitteln, Latenzen zu vergleichen und technische Hostnamen zuzuordnen.

Das Programm bietet sowohl ein interaktives Terminal-Menü als auch vollwertige CLI-Befehle inklusive JSON-Ausgabe für Scripting und Automatisierung.

---

## Funktionen & Neuerungen

* **Gezielte IPv6-Identifikation:** Ermittelt verlässlich aktive IPv6-Adressen (AAAA-Records) und misst deren Latenzzeiten parallel zu IPv4.
* **IPv6-Filter (`--ipv6-only`):** Filtert Suchläufe auf Nodes, die tatsächlich über eine funktionierende IPv6-Adresse verfügen.
* **Latenz-Sortierung (`--sort-latency`):** Sortiert gefundene Server auf Wunsch aufsteigend nach der niedrigsten gemessenen Antwortzeit.
* **Deduplizierung:** Verhindert doppelte Listung, wenn ProtonVPN-Server unter mehreren Hostnamen (z. B. `node-de-01` und `node-de-1`) dieselben IP-Adressen teilen.
* **Kontrollierte Parallelität (`asyncio.Semaphore`):** Schnelle Abfragen mehrerer Server ohne DNS-Überlastung oder Timeouts.
* **Asynchroner Node-Finder:** Parallele Reverse-Suche nach Ziel-IPs über Länder und Servernummern hinweg.
* **Native IP-Erkennung:** Strikte Validierung von IPv4 und IPv6 über Pythons Standardbibliothek `ipaddress`.
* **Flexibler DNS-Resolver:** Standardmäßige Nutzung des System-DNS mit optionaler Auswahl alternativer Resolver (z. B. Cloudflare `1.1.1.1`, Google `8.8.8.8`, Quad9 `9.9.9.9` oder per CLI konfigurierbar).
* **Differenzierte Fehlerstatistik:** Saubere Erfassung von aktiven Servern, IPv6-fähigen Nodes, `NXDOMAIN`, fehlenden Records (`NoAnswer`), Timeouts und Netzwerkfehlern.
* **Zero-Setup Latenzmessung:** Nutzt standardmäßig das System-Ping (`/bin/ping`) für IPv4 und IPv6 ohne zusätzliche Socket-Rechte. Optional kann `icmplib` für reinen Python-Socket-Ping verwendet werden.
* **Saubere JSON-Pipes:** Progress-Bars werden auf `stderr` geroutet, sodass `stdout` bei `--json` zu 100 % valide und pipebar bleibt (z. B. mit `jq`).
* **CI/CD & Tests:** Vollständig getestete Kernfunktionen mit `pytest`, Linting via `ruff` und GitHub Actions CI.

> **Hinweis zur VPN-Konnektivität:** Das Auffinden eines AAAA-Records und erfolgreiche ICMP-Pings bestätigen die Erreichbarkeit der IPv6-Adresse des Nodes. Ob der VPN-Dienst (z. B. WireGuard auf Port 51820) auf dem spezifischen Node für IPv6 freigeschaltet ist, hängt von der jeweiligen Server-Konfiguration ab.

---

## Voraussetzungen & Installation

Benötigt **Python 3.10+**.

### 1. Repository klonen

```bash
git clone git@github.com:pschmidt3200/proton-vpn-node-scanner.git
cd proton-vpn-node-scanner
```

### 2. Abhängigkeiten installieren

Das Tool benötigt zwei Basis-Pakete: `rich` und `dnspython`.

#### Variante A: Virtuelle Umgebung (empfohlen)

```bash
python3 -m venv .venv
source .venv/bin/activate

# Basis-Installation
pip install .

# Für Entwickler (inkl. pytest & ruff):
pip install .[dev]
```

#### Variante B: Über den Linux-Paketmanager

Wer keine virtuelle Umgebung nutzen möchte, kann die beiden Pakete über den Paketmanager der Distribution installieren:

* **Gentoo:** `sudo emerge --ask dev-python/rich dev-python/dnspython`
* **Arch Linux:** `sudo pacman -S python-rich python-dnspython`
* **Debian / Ubuntu:** `sudo apt install python3-rich python3-dnspython`
* **Fedora:** `sudo dnf install python3-rich python3-dnspython`

---

## Verwendung

### 1. Interaktiver Menü-Modus

Start ohne zusätzliche Argumente:

```bash
python3 proton_scanner.py
```

Das Menü führt durch folgende Optionen:
1. **Server analysieren:** Auswahl des Server-Typs (WireGuard, OpenVPN, Secure Core, Manuell), Länderauswahl, Bereichsgröße, Filter auf IPv6-Nodes und Ping-Messung.
2. **Node-Finder (Reverse-Suche):** Ermittelt, welcher ProtonVPN-Node zu einer bestimmten IP-Adresse gehört.
3. **DNS-Resolver:** Wählbar zwischen System-Standard, Cloudflare, Google oder Quad9.

---

### 2. CLI-Modus (Scripting & Automation)

Proton-Scanner kann direkt über Parameter in Shell-Skripten, Cronjobs oder Monitoring-Pipelines verwendet werden:

#### A. Server-Bereich scannen

```bash
# Nur IPv6-fähige WireGuard-Nodes für Deutschland suchen, sortiert nach schnellster Latenz:
python3 proton_scanner.py scan --mode 2 --cc de --count 50 --ipv6-only --sort-latency

# WireGuard-Nodes für die Niederlande scannen (1-50):
python3 proton_scanner.py scan --mode 2 --cc nl --count 50

# OpenVPN-Server für die Schweiz als JSON ausgeben (ohne Ping, sauber pipebar):
python3 proton_scanner.py scan --mode 1 --cc ch --count 20 --no-ping --json | jq .

# Mit spezifischem DNS-Resolver und angepasster Parallelität:
python3 proton_scanner.py scan --mode 2 --cc nl --count 100 --dns 1.1.1.1 --concurrency 80
```

#### B. Node-Finder (Reverse-Suche)

```bash
# Node zu einer Ziel-IP ermitteln:
python3 proton_scanner.py reverse --target 62.112.9.164 --countries nl de ch --count 50

# Strukturierte Ausgabe als JSON:
python3 proton_scanner.py reverse --target 62.112.9.164 --json
```

---

## Tests & Qualitätssicherung

Das Projekt wird mit `pytest` und `ruff` validiert:

```bash
# Tests ausführen
pytest

# Code-Qualität und Linting prüfen
ruff check .
```

---

## Historie & Lizenz

* **Historie:** Das Projekt entstand ursprünglich als Sammlung einfacher Bash-Skripte und wurde schrittweise auf Python und `asyncio` umgestellt. Die früheren Versionen sind zur Dokumentation im Verzeichnis [`legacy/bash/`](legacy/bash/) archiviert.
* **Lizenz:** Dieses Projekt steht unter der **[MIT-Lizenz](LICENSE)**.
