#!/bin/bash

# ==============================================================================
# HILFSFUNKTIONEN
# ==============================================================================

# Diese Funktion bündelt alle Abfragen für einen einzelnen Hostnamen (normale Suche).
# Argument 1: Hostname
# Argument 2: Zu scannende Ports (z.B. "1194 51820")
# Argument 3: Ping-Test durchführen? (true/false)
function process_host() {
    local hostname=$1
    local ports_to_scan=$2
    local perform_ping=$3
    
    local ipv4_addresses=$(dig +short A "$hostname")
    local ipv6_addresses=$(dig +short AAAA "$hostname")

    if [ -z "$ipv4_addresses" ] && [ -z "$ipv6_addresses" ]; then
        return
    fi

    echo "📡 Prüfe: ${hostname}"
    local open_ports=""
    if [ -n "$ports_to_scan" ]; then
        local first_ip=$(echo "$ipv4_addresses" | head -n 1)
        if [ -n "$first_ip" ]; then
            for port in $ports_to_scan; do
                if nc -z -v -u -w 2 "$first_ip" "$port" 2>&1 | grep -q "succeeded"; then
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
    if [ -n "$open_ports" ]; then
      echo "   Protokolle: $open_ports"
    fi

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

# ==============================================================================
# HAUPTFUNKTIONEN (Aktionen aus dem Menü)
# ==============================================================================

# Funktion für die normale Server-Analyse (Menüpunkt 1)
function analyze_servers() {
    echo
    echo "--- Server analysieren ---"
    echo "1) 🔎 OpenVPN / IKEv2 Server prüfen (Schema: de-XX.protonvpn.com)"
    echo "2) 🚀 WireGuard Server prüfen (Schema: node-de-XX.protonvpn.net)"
    echo "3) 🔧 Manuelle Abfrage"
    read -p "Ihre Wahl [1-3]: " choice

    local perform_ping=false
    read -p "Ping-Test zur Latenzmessung durchführen? [J/n]: " ping_choice
    if [[ "$ping_choice" =~ ^[jJ]?$ ]]; then
        perform_ping=true
    fi
    read -p "Bis zu welcher Node-Nummer soll gesucht werden?: " end_number
    if ! [[ "$end_number" =~ ^[1-9][0-9]*$ ]]; then echo "Ungültige Zahl."; return; fi

    case $choice in
        1)
            read -p "Länderkürzel eingeben (z.B. de, ch, us-ca): " country_code
            local ports_to_scan="1194 500 4500"
            for i in $(seq 1 "$end_number"); do
                process_host "${country_code}-${i}.protonvpn.com" "$ports_to_scan" "$perform_ping"
            done
            ;;
        2)
            read -p "Länderkürzel eingeben (z.B. de, ch, us): " country_code
            local ports_to_scan="51820"
            for i in $(seq 1 "$end_number"); do
                process_host "node-${country_code}-${i}.protonvpn.net" "$ports_to_scan" "$perform_ping"
            done
            ;;
        3)
            read -p "Vollständigen Hostnamen-Präfix eingeben (z.B. is-nl-): " prefix
            read -p "Domain eingeben (z.B. protonvpn.com): " domain
            read -p "Zu scannende UDP-Ports (leer lassen für keinen Scan): " ports_to_scan
            for i in $(seq 1 "$end_number"); do
                process_host "${prefix}${i}.${domain}" "$ports_to_scan" "$perform_ping"
            done
            ;;
        *) echo "Ungültige Auswahl." ;;
    esac
}

# Funktion für die Reverse-Suche (Menüpunkt 2)
function reverse_search() {
    echo
    echo "--- Hostnamen zuordnen (Reverse-Suche) ---"
    read -p "Geben Sie den bekannten Hostnamen ein (z.B. unn-XXX-XX-XX-XX...): " target_hostname
    local target_ip=$(dig +short A "$target_hostname")

    if [ -z "$target_ip" ]; then
        echo "❌ Fehler: Konnte keine IP-Adresse für '$target_hostname' finden."
        return
    fi
    echo "✅ Ziel-IP gefunden: $target_ip"
    
    read -p "Zu durchsuchende Länderkürzel (getrennt durch Leerzeichen): " country_codes
    read -p "Bis zu welcher Node-Nummer soll pro Land gesucht werden?: " end_number
    if ! [[ "$end_number" =~ ^[1-9][0-9]*$ ]]; then echo "Ungültige Zahl."; return; fi
    
    echo "In welchem Namensschema soll gesucht werden?"
    echo "1) Modernes Schema (node-de-XX.protonvpn.net)"
    echo "2) Klassisches Schema (de-XX.protonvpn.com)"
    read -p "Ihre Wahl [1-2]: " schema_choice
    echo "🚀 Suche wird gestartet... Dies kann dauern."

    for cc in $country_codes; do
        echo "--- Durchsuche Land: $cc ---"
        for i in $(seq 1 "$end_number"); do
            local hostname
            case $schema_choice in
                1) hostname="node-${cc}-${i}.protonvpn.net" ;;
                2) hostname="${cc}-${i}.protonvpn.com" ;;
                *) echo "Ungültige Schema-Wahl."; return ;;
            esac
            
            echo -n "Prüfe: $hostname -> "
            local candidate_ips=$(dig +short A "$hostname")
            if [ -z "$candidate_ips" ]; then
                echo "existiert nicht."
                continue
            fi
            for candidate_ip in $candidate_ips; do
                echo -n "[$candidate_ip] "
                if [[ "$candidate_ip" == "$target_ip" ]]; then
                    echo -e "\n✅✅✅ TREFFER GEFUNDEN! ✅✅✅"
                    echo "Die IP-Adresse $target_ip gehört zu: $hostname"
                    return # Erfolgreich, zurück zum Hauptmenü
                fi
            done
            echo "kein Treffer."
        done
    done
    echo "❌ Suche beendet. Es wurde kein passender Node gefunden."
}

# ==============================================================================
# HAUPTSKRIPT & MENÜ
# ==============================================================================

while true; do
    echo
    echo "=========================================="
    echo "ProtonVPN Universal-Analyse-Skript"
    echo "=========================================="
    echo "Was möchten Sie tun?"
    echo "1) 🔎 Server analysieren (IP, Protokolle, Latenz finden)"
    echo "2) 🔄 Hostnamen zuordnen (Finde Node für eine IP/Hostname)"
    echo "3) 🚪 Beenden"
    read -p "Ihre Wahl [1-3]: " main_choice

    case $main_choice in
        1)
            analyze_servers
            ;;
        2)
            reverse_search
            ;;
        3)
            echo "Skript wird beendet."
            break
            ;;
        *)
            echo "Ungültige Auswahl. Bitte 1, 2 oder 3 eingeben."
            ;;
    esac
    # Pausiert, bevor das Menü erneut angezeigt wird (außer beim Beenden).
    if [[ "$main_choice" != "3" ]]; then
        read -p "Drücken Sie Enter, um zum Hauptmenü zurückzukehren..."
    fi
done
