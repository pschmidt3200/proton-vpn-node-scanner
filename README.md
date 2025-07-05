# 🛡️ Proton-Scanner: Ein KI-unterstütztes Analyse-Werkzeug

Ein schnelles, modernes und interaktives Kommandozeilen-Werkzeug zur Analyse von ProtonVPN-Servern, geschrieben in Python mit `asyncio`.

Dieses Projekt wurde maßgeblich mit Unterstützung der **KI Gemini von Google** entwickelt und ist ein Beispiel für eine interaktive Zusammenarbeit zwischen Mensch und KI.

## 🤖 Über das Projekt: Eine Mensch-KI-Kollaboration

Dieses Werkzeug begann als einfaches Bash-Skript. In einer fortlaufenden Konversation mit Gemini wurde es schrittweise zu dieser performanten Python-Anwendung ausgebaut. Jeder Entwicklungsschritt – von der ersten Code-Zeile über die Umstellung auf Python, die Implementierung von asynchronen Abfragen bis hin zur automatischen Abhängigkeitsprüfung – entstand in diesem Dialog.

Der Hinweis auf die Beteiligung der KI dient der Transparenz und soll zeigen, wie Mensch-Maschine-Kollaboration heute aussehen kann.

## ✨ Merkmale

* **Extrem Schnell:** Nutzt asynchrone Abfragen (`asyncio`), um hunderte von Servern in Sekunden statt Minuten zu prüfen.
* **Interaktives Menü:** Eine benutzerfreundliche Oberfläche zur Auswahl verschiedener Analyse-Modi.
* **Umfassende Server-Analyse:**
    * Findet IPv4- und IPv6-Adressen.
    * Ermittelt Latenzzeiten durch einen asynchronen Ping-Test.
    * Sucht den Reverse-DNS-Hostnamen für jede IP.
* **Node-Finder (Reverse-Suche):** Findet heraus, welcher ProtonVPN-Node zu einer bestimmten IP-Adresse oder einem technischen Hostnamen gehört.
* **Spezifische Suchmodi:** Enthält vordefinierte Suchen für klassische, moderne und Secure-Core-Server.
* **Automatische Abhängigkeitsprüfung:** Überprüft beim Start, ob alle nötigen Python-Pakete installiert sind, und bietet eine automatische Installation an.

## ⚙️ Installation

Das Skript benötigt **Python 3.7+**.

1.  **Klone das Repository:**
    ```sh
    git clone https://github.com/pschmidt3200/proton-vpn-scanner.git
    cd proton-vpn-scanner
    ```

2.  **Abhängigkeiten installieren:**
    Das Skript bietet beim ersten Start eine automatische Installation der Abhängigkeiten an. Alternativ kannst du sie manuell oder in einer virtuellen Umgebung installieren:
    ```sh
    # Optional, aber empfohlen: Virtuelle Umgebung erstellen
    python -m venv .venv
    source .venv/bin/activate

    # Pakete installieren
    pip install rich dnspython icmplib
    ```

## 🚀 Verwendung

Führe das Skript einfach mit Python aus:

```sh
python proton_scanner.py
```

Du wirst von einem interaktiven Menü begrüßt, das dich durch die verfügbaren Optionen führt:

1.  **Server analysieren:** Finde IPs, Latenzen und mehr für eine Reihe von ProtonVPN-Servern.
2.  **Node-Finder (Reverse-Suche):** Gib eine IP oder einen Hostnamen ein, um den zugehörigen ProtonVPN-Node zu finden.
3.  **Beenden:** Schließt das Programm.

## Lizenz

Dieses Projekt steht unter der **MIT-Lizenz**. Die Lizenzdetails findest du in der `LICENSE`-Datei.
