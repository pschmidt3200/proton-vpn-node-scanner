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

    # Fragt die IPv4-Adressen (A-Record) ab.
    ipv4_addresses=$(dig +short A "$hostname")

    if [ -n "$ipv4_addresses" ]; then
        # Geht jede gefundene IPv4-Adresse durch.
        for ip in $ipv4_addresses; do
            # Führt eine Reverse-DNS-Abfrage (PTR) für die IP durch.
            # Die Option -x ist für die Reverse-Abfrage.
            reverse_hostname=$(dig -x "$ip" +short)
            # Gibt die IP mit dem dazugehörigen Hostnamen aus.
            # Falls kein Hostname gefunden wird, gibt es einen Hinweis.
            echo "  IPv4: $ip (Hostname: ${reverse_hostname:-Kein PTR-Eintrag})"
        done
    else
        echo "  IPv4: Nicht gefunden"
    fi

    # Fragt die IPv6-Adressen (AAAA-Record) ab.
    ipv6_addresses=$(dig +short AAAA "$hostname")

    if [ -n "$ipv6_addresses" ]; then
        # Geht jede gefundene IPv6-Adresse durch.
        for ip in $ipv6_addresses; do
            # Führt eine Reverse-DNS-Abfrage (PTR) für die IP durch.
            reverse_hostname=$(dig -x "$ip" +short)
            echo "  IPv6: $ip (Hostname: ${reverse_hostname:-Kein PTR-Eintrag})"
        done
    else
        echo "  IPv6: Nicht gefunden"
    fi
    
    echo # Fügt eine Leerzeile für bessere Lesbarkeit hinzu.
done

echo "======================================================================"
echo "Skript beendet."
