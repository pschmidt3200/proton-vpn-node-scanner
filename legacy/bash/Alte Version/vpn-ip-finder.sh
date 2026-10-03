#!/bin/bash

# Fragt den Benutzer nach der höchsten Nummer, die für die Servernamen getestet werden soll.
read -p "Bis zu welcher Node-Nummer soll gesucht werden? (z.B. 100): " end_number

# Überprüft, ob die Eingabe eine positive ganze Zahl ist.
if ! [[ "$end_number" =~ ^[1-9][0-9]*$ ]]; then
    echo "Fehler: Bitte eine gültige positive Zahl eingeben."
    exit 1
fi

echo "Starte Abfrage für node-de-1.protonvpn.net bis node-de-${end_number}.protonvpn.net..."
echo "======================================================================"

# Schleife von 1 bis zur eingegebenen Endnummer.
for i in $(seq 1 "$end_number"); do
    # Baut den Hostnamen zusammen.
    hostname="node-de-${i}.protonvpn.net"

    echo "Prüfe: ${hostname}"

    # Fragt die IPv4-Adresse (A-Record) ab.
    # Der Befehl `+short` sorgt für eine saubere, kurze Ausgabe.
    ipv4_address=$(dig +short A "$hostname")

    # Fragt die IPv6-Adresse (AAAA-Record) ab.
    ipv6_address=$(dig +short AAAA "$hostname")

    # Gibt die gefundenen Adressen aus.
    # Wenn eine Adresse nicht gefunden wurde, wird die Variable leer sein.
    if [ -n "$ipv4_address" ]; then
        echo "  IPv4: ${ipv4_address}"
    else
        echo "  IPv4: Nicht gefunden"
    fi

    if [ -n "$ipv6_address" ]; then
        echo "  IPv6: ${ipv6_address}"
    else
        echo "  IPv6: Nicht gefunden"
    fi
    
    echo # Fügt eine Leerzeile für bessere Lesbarkeit hinzu.
done

echo "======================================================================"
echo "Skript beendet."
