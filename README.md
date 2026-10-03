# 🛡️ Proton-Scanner (v20)

Ein schnelles, modernes und asynchrones Analyse- und Diagnose-Werkzeug für **ProtonVPN-Server**, geschrieben in Python 3.10+ mit `asyncio`, `dnspython`, `icmplib` und `rich`.

Das Tool bietet sowohl ein komfortables, interaktives Terminal-Menü als auch vollwertige CLI-Befehle (inkl. JSON-Export) für Scripting und Automatisierung.

---

## ✨ Features & Neuerungen (v20)

* **Kontrollierte Parallelität (`asyncio.Semaphore`):** Schnelle Abfragen hunderter Server ohne DNS-Überlastung oder Timeouts.
* **Vollständig asynchroner Node-Finder:** Parallele Reverse-Suche nach Ziel-IPs über Länder und Servernummern hinweg in Sekunden.
* **Native IP-Erkennung:** Strikte Validierung von IPv4 und IPv6 über Pythons Standardbibliothek `ipaddress`.
* **Flexibler DNS-Resolver:** Nutzt standardmäßig den System-DNS und erlaubt die optionale Wahl schneller Resolver (Cloudflare `1.1.1.1`, Google `8.8.8.8`, Quad9 `9.9.9.9` oder eigene Resolver via CLI).
* **Detaillierte Fehlerstatistik:** Saubere Differenzierung von aktiven Servern, `NXDOMAIN`, fehlenden Records (`NoAnswer`), Timeouts und Fehlern.
* **Robuste Latenzmessung:** Asynchroner Ping mit automatischem Fallback auf das System-Ping-Binary bei restriktiven Socket-Rechten.
* **Dualer Betriebsmodus:** Interaktives Menü oder automatisierbare CLI-Flags (`scan`, `reverse`, `--json`).
* **CI/CD & Tests:** 100 % getestete Kernfunktionen mit `pytest`, Linting via `ruff` und GitHub Actions CI.
* **Saubere Sprachstatistik:** Historische Bash-Skripte sind unter `legacy/bash/` archiviert und via `.gitattributes` markiert, sodass das Repository auf GitHub sauber als Python-Projekt geführt wird.

---

## ⚙️ Voraussetzungen & Installation

Benötigt **Python 3.10+**.

### 1. Repository klonen

```bash
git clone https://github.com/pschmidt3200/proton-vpn-scanner.git
cd proton-vpn-scanner
```

### 2. Virtuelle Umgebung & Abhängigkeiten

```bash
# Virtuelle Umgebung erstellen und aktivieren
python3 -m venv .venv
source .venv/bin/activate

# Abhängigkeiten via pyproject.toml installieren
pip install .

# Für Entwickler (inkl. pytest & ruff):
pip install .[dev]
```

Alternativ prüft das Skript beim Direktstart `python3 proton_scanner.py` fehlende Abhängigkeiten und bietet passende Paketmanager-Befehle (Debian/Ubuntu, Arch, Fedora, Gentoo) unter Berücksichtigung von **PEP 668** an.

---

## 🚀 Verwendung

### 1. Interaktiver Menü-Modus

Starte das Skript ohne Argumente:

```bash
python3 proton_scanner.py
```

Das Menü führt durch alle Optionen:
1. **Server analysieren:** Auswahl des Server-Typs (WireGuard, OpenVPN, Secure Core, Manuell), Länderauswahl, Bereichsgröße und Ping-Test.
2. **Node-Finder (Reverse-Suche):** Ermittelt in Sekundenschnelle, welcher ProtonVPN-Node zu einer bestimmten IP-Adresse gehört.
3. **DNS-Resolver:** Wählbar zwischen System-Standard, Cloudflare, Google oder Quad9.

---

### 2. CLI-Modus (Scripting & Automation)

Proton-Scanner kann direkt über Parameter in Shell-Skripten, Cronjobs oder Monitoring-Pipelines verwendet werden:

#### A. Server-Bereich scannen

```bash
# Moderne WireGuard-Nodes für Deutschland scannen (1-50):
python3 proton_scanner.py scan --mode 2 --cc de --count 50

# Klassische OpenVPN-Server für die Schweiz als JSON ausgeben (ohne Ping):
python3 proton_scanner.py scan --mode 1 --cc ch --count 20 --no-ping --json

# Mit spezifischem DNS-Resolver und angepasster Parallelität:
python3 proton_scanner.py scan --mode 2 --cc nl --count 100 --dns 1.1.1.1 --concurrency 80
```

#### B. Node-Finder (Reverse-Suche)

```bash
# Herausfinden, zu welchem Node eine IP gehört:
python3 proton_scanner.py reverse --target 62.112.9.164 --countries nl de ch --count 50

# Maschinenlesbare Ausgabe als JSON:
python3 proton_scanner.py reverse --target 62.112.9.164 --json
```

---

## 🧪 Tests & Qualitätssicherung

Das Projekt wird mit `pytest` und `ruff` validiert:

```bash
# Tests ausführen
pytest

# Code-Qualität und Linting prüfen
ruff check .
```

---

## 📜 Historie & Lizenz

* **Historie:** Das Projekt begann als Sammlung pragmatischer Bash-Skripte und entwickelte sich schrittweise zu einer performanten Python-Lösung. Die früheren Skripte sind zur Dokumentation im Ordner [`legacy/bash/`](legacy/bash/) archiviert.
* **Lizenz:** Dieses Projekt steht unter der **[MIT-Lizenz](LICENSE)**.
