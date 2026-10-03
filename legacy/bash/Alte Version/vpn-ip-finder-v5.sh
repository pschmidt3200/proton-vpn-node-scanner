#!/bin/bash

# --- FUNKTION ZUR VERARBEITUNG EINES HOSTS ---
# Diese Funktion bündelt alle Abfragen für einen einzelnen Hostnamen.
# Argument 1: Hostname
# Argument 2: Zu scannende Ports (z.B. "1194 51820")
# Argument 3: Ping-Test durchführen? (true/false)
process_host() {
    local hostname=$1
    local ports_to_scan=$2
    local perform_ping=$3
    
    # DNS-Abfragen für IPv4 und IPv6
    local ipv4_addresses=$(dig +short A "$hostname")
    local ipv6_addresses=$(dig +short AAAA "$hostname")

    # Nur fortfahren, wenn der Host überhaupt existiert (eine IP hat).
    if [ -z "$ipv4_addresses" ] && [ -z "$ipv6_addresses" ]; then
        return # Beendet die Funktion für diesen Host
    fi

    echo "📡 Prüfe: ${hostname}"

    # --- PORT-SCAN-LOGIK ---
    local open_ports=""
    if [ -n "$ports_to_scan" ]; then
        # Nur die erste IPv4 für den Port-Scan verwenden, um Redundanz zu vermeiden.
        local first_ip=$(echo "$ipv4_addresses" | head -n 1)
        if [ -n "$first_ip" ]; then
            for port in $ports_to_scan; do
                # Scannt den UDP-Port mit 2s Timeout. `nc` ist hierfür ideal.
                if nc -z -v -u -w 2 "$first_ip" "$port" 2>&1 | grep -q "succeeded"; then
                    # Weist dem offenen Port einen Namen zu.
                    case $port in
                        1194) open_ports+="[OpenVPN-UDP] " ;;
                        51820) open_ports+="[WireGuard] " ;;
                        500|4500) open_ports+="[IKEv2] " ;;
                        *) open_ports+="[Port $port] " ;;
                    esac
                fi
            done
        fi
    fi
    # Wenn Ports gefunden wurden, diese anzeigen.
    if [ -n "$open_ports" ]; then
      echo "   protocols: $open_ports"
    fi

    # --- IPv4, REVERSE DNS & PING ---
    if [ -n "$ipv4_addresses" ]; then
        local ping_done=false
        for ip in $ipv4_addresses; do
            local reverse_hostname=$(dig -x "$ip" +short)
            echo "  IPv4: $ip (Hostname: ${reverse_hostname:-Kein PTR-Eintrag})"
            
            if $perform_ping && ! $ping_done; then
                local ping_output=$(ping -c 1 -W 2 "$ip" 2>/dev/null)
                if [ $? -eq 0 ]; then
                    local latency=$(echo "$ping_output" | grep -o 'time=[0-9.]*' | cut -d'=' -f2)
                    echo "  ⏱️ Ping: ${latency} ms"
                else
                    echo "  ⏱️ Ping: Nicht erreichbar"
                fi
                ping_done=true
            fi
        done
    else
        echo "  IPv4: Nicht gefunden"
    fi

    # --- IPv6 & REVERSE DNS ---
    if [ -n "$ipv6_addresses" ]; then
        for ip in $ipv6_addresses; do
            local reverse_hostname=$(dig -x "$ip" +short)
            echo "  IPv6: $ip (Hostname: ${reverse_hostname:-Kein PTR-Eintrag})"
        done
    else
        echo "  IPv6: Nicht gefunden"
    fi
    echo
}

# --- HAUPTMENÜ ---
echo "ProtonVPN Server Analyse-Skript"
echo "================================="
echo "Was möchten Sie tun?"
echo "1) 🔎 OpenVPN / IKEv2 Server prüfen (Schema: de-XX.protonvpn.com)"
echo "2) 🚀 WireGuard Server prüfen (Schema: node-de-XX.protonvpn.net)"
echo "3) 🔧 Manuelle Abfrage (wie bisheriges Skript)"
read -p "Ihre Wahl [1-3]: " choice

# Allgemeine Eingaben für Ping und Nummernkreis
perform_ping=false
read -p "Ping-Test zur Latenzmessung durchführen? [J/n]: " ping_choice
if [[ "$ping_choice" =~ ^[jJ]?$ ]]; then # Akzeptiert j, J oder leere Eingabe
    perform_ping=true
fi
read -p "Bis zu welcher Node-Nummer soll gesucht werden?: " end_number
if ! [[ "$end_number" =~ ^[1-9][0-9]*$ ]]; then echo "Ungültige Zahl."; exit 1; fi

# --- FALLUNTERSCHEIDUNG BASIEREND AUF DER WAHL ---
case $choice in
    1)
        echo "--- Modus: OpenVPN / IKEv2 ---"
        read -p "Länderkürzel eingeben (z.B. de, ch, us-ca): " country_code
        ports_to_scan="1194 500 4500" # Standardports für OpenVPN-UDP und IKEv2
        for i in $(seq 1 "$end_number"); do
            hostname="${country_code}-${i}.protonvpn.com"
            process_host "$hostname" "$ports_to_scan" "$perform_ping"
        done
        ;;
    2)
        echo "--- Modus: WireGuard ---"
        read -p "Länderkürzel eingeben (z.B. de, ch, us): " country_code
        ports_to_scan="51820" # Standardport für WireGuard
        for i in $(seq 1 "$end_number"); do
            hostname="node-${country_code}-${i}.protonvpn.net"
            process_host "$hostname" "$ports_to_scan" "$perform_ping"
        done
        ;;
    3)
        echo "--- Modus: Manuell ---"
        read -p "Vollständigen Hostnamen-Präfix eingeben (z.B. is-nl-): " prefix
        read -p "Domain eingeben (z.B. protonvpn.com): " domain
        read -p "Zu scannende UDP-Ports (leer lassen für keinen Scan): " ports_to_scan
        for i in $(seq 1 "$end_number"); do
            hostname="${prefix}${i}.${domain}"
            process_host "$hostname" "$ports_to_scan" "$perform_ping"
        done
        ;;
    *)
        echo "Ungültige Auswahl."
        exit 1
        ;;
esac

echo "================================="
echo "Skript beendet."
