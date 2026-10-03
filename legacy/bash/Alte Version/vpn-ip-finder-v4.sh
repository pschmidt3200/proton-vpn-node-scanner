#!/bin/bash

# --- BENUTZEREINGABEN ---
# Fragt den Benutzer nach dem Hostnamen-Präfix und bietet einen Standardwert an.
read -p "Hostname-Präfix eingeben [Standard: node-de-]: " prefix
# Wenn die Eingabe leer ist, wird der Standardwert "node-de-" verwendet.
prefix=${prefix:-node-de-}

# Fragt nach der Endnummer.
read -p "Bis zu welcher Node-Nummer soll gesucht werden? (z.B. 100): " end_number

# Überprüft, ob die Eingabe eine positive ganze Zahl ist.
if ! [[ "$end_number" =~ ^[1-9][0-9]*$ ]]; then
    echo "Fehler: Bitte eine gültige positive Zahl eingeben."
    exit 1
fi

# Fragt, ob ein Ping-Test durchgeführt werden soll.
read -p "Ping-Test zur Latenzmessung durchführen? [J/n]: " perform_ping
# Wandelt die Eingabe in Kleinbuchstaben um.
perform_ping_lower=$(echo "$perform_ping" | tr '[:upper:]' '[:lower:]')


# --- SKRIPT-AUSFÜHRUNG ---
echo
echo "Starte Abfrage für ${prefix}1.protonvpn.net bis ${prefix}${end_number}.protonvpn.net..."
echo "======================================================================"

# Schleife von 1 bis zur eingegebenen Endnummer.
for i in $(seq 1 "$end_number"); do
    # Baut den Hostnamen dynamisch zusammen.
    hostname="${prefix}${i}.protonvpn.net"

    # Fragt zuerst BEIDE Adresstypen ab.
    ipv4_addresses=$(dig +short A "$hostname")
    ipv6_addresses=$(dig +short AAAA "$hostname")

    # Nur wenn mindestens eine IP-Adresse gefunden wurde, wird der Block ausgegeben.
    if [ -n "$ipv4_addresses" ] || [ -n "$ipv6_addresses" ]; then
        
        echo "📡 Prüfe: ${hostname}"

        # --- IPv4-VERARBEITUNG ---
        if [ -n "$ipv4_addresses" ]; then
            # Variable, um sicherzustellen, dass Ping nur einmal pro Host ausgeführt wird.
            ping_done=false
            for ip in $ipv4_addresses; do
                reverse_hostname=$(dig -x "$ip" +short)
                echo "  IPv4: $ip (Hostname: ${reverse_hostname:-Kein PTR-Eintrag})"

                # --- Optionaler Ping-Test ---
                # Führt den Ping nur aus, wenn der Benutzer 'j' (oder nichts) eingegeben hat und der Ping für diesen Host noch nicht erfolgt ist.
                if [[ "$perform_ping_lower" == "j" || -z "$perform_ping_lower" ]] && ! $ping_done; then
                    # Ping mit 1 Paket und 2 Sekunden Timeout.
                    ping_output=$(ping -c 1 -W 2 "$ip" 2>/dev/null)
                    if [ $? -eq 0 ]; then
                        # Extrahiert die Latenzzeit aus der Ausgabe.
                        latency=$(echo "$ping_output" | grep -o 'time=[0-9.]*' | cut -d'=' -f2)
                        echo "  ⏱️ Ping: ${latency} ms"
                    else
                        echo "  ⏱️ Ping: Nicht erreichbar"
                    fi
                    ping_done=true # Verhindert weitere Pings für denselben Host.
                fi
            done
        else
            echo "  IPv4: Nicht gefunden"
        fi

        # --- IPv6-VERARBEITUNG ---
        if [ -n "$ipv6_addresses" ]; then
            for ip in $ipv6_addresses; do
                reverse_hostname=$(dig -x "$ip" +short)
                echo "  IPv6: $ip (Hostname: ${reverse_hostname:-Kein PTR-Eintrag})"
            done
        else
            echo "  IPv6: Nicht gefunden"
        fi
        
        echo # Fügt eine Leerzeile für bessere Lesbarkeit hinzu.
    fi
done

echo "======================================================================"
echo "Skript beendet."
