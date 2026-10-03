#!/bin/bash

# ==============================================================================
# HILFSFUNKTION: process_host
# Bündelt alle Abfragen für einen einzelnen Hostnamen.
# ==============================================================================
function process_host() {
    local hostname=$1
    local ports_to_scan=$2
    local perform_ping=$3
    
    local ipv4_addresses=$(dig +short A "$hostname")
    local ipv6_addresses=$(dig +short AAAA "$hostname")

    if [ -z "$ipv4_addresses" ] && [ -z "$ipv6_addresses" ]; then return; fi

    echo # Beendet die Fortschrittsanzeige der vorigen Zeile
    echo "📡 Ergebnis für: ${hostname}"
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
    if [ -n "$open_ports" ]; then echo "   Protokolle: $open_ports"; fi

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

function analyze_servers() {
    local end_number=$1
    local perform_ping=$2

    echo
    echo "--- Modus: Server analysieren ---"
    echo "1) 🔎 Klassische Server (de-XX.protonvpn.com) -> OpenVPN/IKEv2"
    echo "2) 🚀 Moderne Server (node-de-XX.protonvpn.net) -> WireGuard"
    echo "3) 🛡️ Secure Core Server (ch-de-XX.protonvpn.com)"
    echo "4) 🔧 Manuelle Abfrage"
    read -p "Ihre Wahl [1-4]: " choice

    case $choice in
        1)
            read -p "Länderkürzel (z.B. de, us-ca): " country_code
            while [ -z "$country_code" ]; do read -p "Eingabe darf nicht leer sein: " country_code; done
            local ports_to_scan="1194 500 4500"
            for i in $(seq 1 "$end_number"); do
                echo -ne "\r\033[KPrüfe Host $i/$end_number..."
                process_host "${country_code}-${i}.protonvpn.com" "$ports_to_scan" "$perform_ping"
            done
            ;;
        2)
            read -p "Länderkürzel (z.B. de, us): " country_code
            while [ -z "$country_code" ]; do read -p "Eingabe darf nicht leer sein: " country_code; done
            local ports_to_scan="51820"
            for i in $(seq 1 "$end_number"); do
                echo -ne "\r\033[KPrüfe Host $i/$end_number..."
                process_host "node-${country_code}-${i}.protonvpn.net" "$ports_to_scan" "$perform_ping"
            done
            ;;
        3)
            read -p "Eingangsland (z.B. ch, se): " entry_country
            read -p "Ausgangsland (z.B. de, us): " exit_country
            while [ -z "$entry_country" ] || [ -z "$exit_country" ]; do echo "Beide Länder müssen angegeben werden."; read -p "Eingangsland: " entry_country; read -p "Ausgangsland: " exit_country; done
            local ports_to_scan="1194 51820" # Secure Core kann beides
            for i in $(seq 1 "$end_number"); do
                echo -ne "\r\033[KPrüfe Host $i/$end_number..."
                process_host "${entry_country}-${exit_country}-${i}a.protonvpn.com" "$ports_to_scan" "$perform_ping"
            done
            ;;
        4)
            read -p "Hostname-Präfix (z.B. is-nl-): " prefix
            read -p "Domain (z.B. protonvpn.com): " domain
            read -p "UDP-Ports (optional, z.B. 1194 51820): " ports_to_scan
            for i in $(seq 1 "$end_number"); do
                echo -ne "\r\033[KPrüfe Host $i/$end_number..."
                process_host "${prefix}${i}.${domain}" "$ports_to_scan" "$perform_ping"
            done
            ;;
        *) echo "Ungültige Auswahl." ;;
    esac
    echo -e "\r\033[KAnalyse abgeschlossen."
}

function reverse_search() {
    local end_number=$1

    echo
    echo "--- Modus: Node-Finder (Reverse-Suche) ---"
    read -p "Geben Sie die bekannte IP-Adresse oder den Hostnamen ein: " user_input
    
    local target_ip=""
    local ip_type=""
    if [[ "$user_input" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        target_ip=$user_input; ip_type="IPv4"
    elif [[ "$user_input" =~ : ]]; then
        target_ip=$user_input; ip_type="IPv6"
    else
        echo "🔎 Eingabe als Hostname erkannt. Ermittle IP..."
        target_ip=$(dig +short AAAA "$user_input" || dig +short A "$user_input")
        if [[ "$target_ip" =~ : ]]; then ip_type="IPv6"; else ip_type="IPv4"; fi
    fi

    if [ -z "$target_ip" ]; then echo "❌ Fehler: Konnte keine gültige IP für '$user_input' finden."; return; fi
    echo "✅ Ziel-IP ($ip_type) festgelegt: $target_ip"
    
    read -p "Zu durchsuchende Länderkürzel (getrennt durch Leerzeichen): " country_codes
    while [ -z "$country_codes" ]; do read -p "Eingabe darf nicht leer sein: " country_codes; done
    
    echo "In welchem Namensschema soll gesucht werden?"
    echo "1) Modernes Schema (node-de-XX...)"
    echo "2) Klassisches Schema (de-XX...)"
    read -p "Ihre Wahl [1-2]: " schema_choice
    echo "🚀 Suche wird gestartet..."

    local record_type_to_check="A"; if [[ "$ip_type" == "IPv6" ]]; then record_type_to_check="AAAA"; fi

    local total_checks=$(echo "$country_codes" | wc -w)
    local current_check=0
    for cc in $country_codes; do
        current_check=$((current_check + 1))
        echo "--- Durchsuche Land: $cc ($current_check/$total_checks) ---"
        for i in $(seq 1 "$end_number"); do
            local hostname; case $schema_choice in 1) hostname="node-${cc}-${i}.protonvpn.net" ;; 2) hostname="${cc}-${i}.protonvpn.com" ;; *) echo "Fehler."; return ;; esac
            echo -ne "\r\033[KPrüfe Host $i/$end_number..."
            local candidate_ips=$(dig +short "$record_type_to_check" "$hostname")
            for candidate_ip in $candidate_ips; do
                if [[ "$candidate_ip" == "$target_ip" ]]; then
                    echo -e "\n\n✅✅✅ TREFFER GEFUNDEN! ✅✅✅"
                    echo "Die $ip_type-Adresse $target_ip gehört zu: $hostname"
                    return
                fi
            done
        done
    done
    echo -e "\r\033[KSuche beendet. Es wurde kein passender Node gefunden."
}

# ==============================================================================
# HAUPTSKRIPT & MENÜ
# ==============================================================================
while true; do
    echo
    echo "=========================================="
    echo "ProtonVPN Universal-Analyse-Skript v9"
    echo "=========================================="
    echo "Was möchten Sie tun?"
    echo "1) 🔎 Server analysieren (IPs & Protokolle finden)"
    echo "2) 🔄 Node-Finder (IP/Hostname zuordnen)"
    echo "3) 🚪 Beenden"
    read -p "Ihre Wahl [1-3]: " main_choice

    if [[ "$main_choice" == "3" ]]; then echo "Skript wird beendet."; break; fi
    if [[ "$main_choice" != "1" ]] && [[ "$main_choice" != "2" ]]; then echo "Ungültige Auswahl."; continue; fi

    # Allgemeine Einstellungen pro Sitzung
    echo "--- Allgemeine Einstellungen ---"
    read -p "Bis zu welcher Node-Nummer soll maximal gesucht werden? [500]: " end_number
    end_number=${end_number:-500}
    
    perform_ping=false
    if [[ "$main_choice" == "1" ]]; then
        read -p "Ping-Test zur Latenzmessung durchführen? [J/n]: " ping_choice
        if [[ "$ping_choice" =~ ^[jJ]?$ ]]; then perform_ping=true; fi
    fi
    
    case $main_choice in
        1) analyze_servers "$end_number" "$perform_ping" ;;
        2) reverse_search "$end_number" ;;
    esac
    read -p "Drücken Sie Enter, um zum Hauptmenü zurückzukehren..."
done
