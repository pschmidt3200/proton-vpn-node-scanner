# ==============================================================================
# 1. ABHÄNGIGKEITEN PRÜFEN UND INSTALLIEREN
# ==============================================================================
import sys
import subprocess
import importlib.util
import os

def get_distro_specific_advice(packages: list) -> str:
    """Gibt einen spezifischen Installationsbefehl basierend auf der erkannten Linux-Distribution."""
    if not os.path.exists('/etc/os-release'):
        return "Benutze den Paketmanager deiner Distribution."

    with open('/etc/os-release') as f:
        dist_info = {k.strip(): v.strip().strip('"') for k, v in (line.split('=', 1) for line in f if '=' in line)}
    
    dist_id = dist_info.get('ID', '').lower()
    id_like = dist_info.get('ID_LIKE', '').lower()

    pkg_map = {
        'rich': {'debian': 'python3-rich', 'fedora': 'python3-rich', 'arch': 'python-rich', 'gentoo': 'dev-python/rich'},
        'dnspython': {'debian': 'python3-dnspython', 'fedora': 'python3-dnspython', 'arch': 'python-dnspython', 'gentoo': 'dev-python/dnspython'},
        'icmplib': {'debian': 'python3-icmplib', 'fedora': 'python3-icmplib', 'arch': 'python-icmplib', 'gentoo': 'dev-python/icmplib'}
    }

    def map_packages(dist_key):
        return ' '.join([pkg_map.get(p, {}).get(dist_key, p) for p in packages])

    if 'debian' in dist_id or 'ubuntu' in dist_id or 'mint' in dist_id or 'debian' in id_like:
        return f"`sudo apt install {map_packages('debian')}`"
    elif 'fedora' in dist_id or 'rhel' in dist_id or 'centos' in id_like:
        return f"`sudo dnf install {map_packages('fedora')}`"
    elif 'arch' in dist_id or 'arch' in id_like:
        return f"`sudo pacman -S {map_packages('arch')}`"
    elif 'gentoo' in dist_id:
        return f"`sudo emerge --ask {map_packages('gentoo')}`"
    
    return "Benutze den Paketmanager deiner Distribution."


def check_and_install_dependencies():
    """Prüft auf nötige Pakete und bietet eine automatische Installation an."""
    required_packages = {"rich": "rich", "dns": "dnspython", "icmplib": "icmplib"}
    missing_packages = []

    for module_name, package_name in required_packages.items():
        if importlib.util.find_spec(module_name) is None:
            missing_packages.append(package_name)

    if not missing_packages:
        return True# ==============================================================================
# 1. ABHÄNGIGKEITEN PRÜFEN UND INSTALLIEREN
# ==============================================================================
import sys
import subprocess
import importlib.util
import os

def get_distro_specific_advice(packages: list) -> str:
    """Gibt einen spezifischen Installationsbefehl basierend auf der erkannten Linux-Distribution."""
    if not os.path.exists('/etc/os-release'):
        return "Benutze den Paketmanager deiner Distribution."

    with open('/etc/os-release') as f:
        dist_info = {k.strip(): v.strip().strip('"') for k, v in (line.split('=', 1) for line in f if '=' in line)}
    
    dist_id = dist_info.get('ID', '').lower()
    id_like = dist_info.get('ID_LIKE', '').lower()

    pkg_map = {
        'rich': {'debian': 'python3-rich', 'fedora': 'python3-rich', 'arch': 'python-rich', 'gentoo': 'dev-python/rich'},
        'dnspython': {'debian': 'python3-dnspython', 'fedora': 'python3-dnspython', 'arch': 'python-dnspython', 'gentoo': 'dev-python/dnspython'},
        'icmplib': {'debian': 'python3-icmplib', 'fedora': 'python3-icmplib', 'arch': 'python-icmplib', 'gentoo': 'dev-python/icmplib'}
    }

    def map_packages(dist_key):
        return ' '.join([pkg_map.get(p, {}).get(dist_key, p) for p in packages])

    if 'debian' in dist_id or 'ubuntu' in dist_id or 'mint' in dist_id or 'debian' in id_like:
        return f"`sudo apt install {map_packages('debian')}`"
    elif 'fedora' in dist_id or 'rhel' in dist_id or 'centos' in id_like:
        return f"`sudo dnf install {map_packages('fedora')}`"
    elif 'arch' in dist_id or 'arch' in id_like:
        return f"`sudo pacman -S {map_packages('arch')}`"
    elif 'gentoo' in dist_id:
        return f"`sudo emerge --ask {map_packages('gentoo')}`"
    
    return "Benutze den Paketmanager deiner Distribution."


def check_and_install_dependencies():
    """Prüft auf nötige Pakete und bietet eine automatische Installation an."""
    required_packages = {"rich": "rich", "dns": "dnspython", "icmplib": "icmplib"}
    missing_packages = []

    for module_name, package_name in required_packages.items():
        if importlib.util.find_spec(module_name) is None:
            missing_packages.append(package_name)

    if not missing_packages:
        return True

    print("--- Abhängigkeitsprüfung ---")
    print("Die folgenden, für das Skript benötigten Pakete fehlen:")
    for pkg in missing_packages:
        print(f"  - {pkg}")
    
    try:
        user_choice = input("Dürfen diese Pakete jetzt mit pip installiert werden? [J/n]: ").lower().strip()
    except KeyboardInterrupt:
        print("\nPrüfung abgebrochen.")
        return False

    if user_choice == 'j' or user_choice == '':
        print("\nInstalliere Pakete...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_packages], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("\n✅ Installation erfolgreich!")
            print("Bitte starten Sie das Skript jetzt neu.")
        except subprocess.CalledProcessError as e:
            error_output = e.stderr.decode() if e.stderr else ""
            if "externally-managed-environment" in error_output:
                advice = get_distro_specific_advice(missing_packages)
                print("\n❌ Fehler: Die Installation wurde vom Betriebssystem blockiert (PEP 668).")
                print("\nEmpfohlene Lösungen:")
                print(f"1. Benutze den System-Paketmanager: {advice}")
                print("2. Oder verwende eine virtuelle Python-Umgebung (`python -m venv .venv`).")
            else:
                print("\n❌ Ein unbekannter Fehler ist bei der Installation aufgetreten.")
                print(f"   Bitte versuchen Sie es manuell: `pip install {' '.join(missing_packages)}`")
    else:
        print("Installation abgebrochen. Das Skript kann ohne die Pakete nicht ausgeführt werden.")

    return False

if not check_and_install_dependencies():
    sys.exit()

import asyncio
import re
from typing import List, Optional

import dns.asyncresolver
import dns.reversename
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.table import Table
from icmplib import async_ping

console = Console()
resolver = dns.asyncresolver.Resolver()
resolver.timeout = 2
resolver.lifetime = 2

async def get_ips(hostname: str) -> dict:
    results = {"a": [], "aaaa": []}
    try:
        v4_lookup, v6_lookup = await asyncio.gather(
            resolver.resolve(hostname, 'A'),
            resolver.resolve(hostname, 'AAAA'),
            return_exceptions=True
        )
        if isinstance(v4_lookup, dns.resolver.Answer):
            results["a"] = [r.to_text() for r in v4_lookup]
        if isinstance(v6_lookup, dns.resolver.Answer):
            results["aaaa"] = [r.to_text() for r in v6_lookup]
    except Exception:
        pass
    return results

async def get_reverse_dns(ip: str) -> Optional[str]:
    try:
        addr = dns.reversename.from_address(ip)
        answer = await resolver.resolve(addr, "PTR")
        return answer[0].to_text()
    except Exception:
        return None

async def check_server(hostname: str, progress, task) -> Optional[dict]:
    ips = await get_ips(hostname)
    progress.update(task, advance=1)
    if not ips["a"] and not ips["aaaa"]:
        return None

    ptr_tasks = [get_reverse_dns(ip) for ip in ips["a"] + ips["aaaa"]]
    ping_tasks = [async_ping(ip, count=1, timeout=1) for ip in ips["a"]]

    ptr_results = await asyncio.gather(*ptr_tasks)
    ping_results = await asyncio.gather(*ping_tasks)

    ptr_map = dict(zip(ips["a"] + ips["aaaa"], ptr_results))
    ping_map = dict(zip(ips["a"], [p.avg_rtt for p in ping_results if p.is_alive]))
    
    return {
        "hostname": hostname,
        "ipv4": [{"ip": ip, "ptr": ptr_map.get(ip), "ping": ping_map.get(ip)} for ip in ips["a"]],
        "ipv6": [{"ip": ip, "ptr": ptr_map.get(ip)} for ip in ips["aaaa"]]
    }

def display_results(results: List[dict]):
    if not any(results):
        console.print("[yellow]Keine Server im angegebenen Bereich gefunden.[/yellow]")
        return

    table = Table(title="Analyse-Ergebnisse", show_header=True, header_style="bold magenta")
    table.add_column("Proton Node", style="cyan")
    table.add_column("IP-Adresse", style="dim")
    table.add_column("Latenz (ms)", style="green")
    table.add_column("Reverse Hostname", style="yellow")

    for res in filter(None, results):
        table.add_row(f"[bold]{res['hostname']}[/bold]", "--- IPv4 ---")
        for ip_info in res['ipv4']:
            ping_str = f"{ip_info['ping']:.2f}" if ip_info.get('ping') is not None else "-"
            table.add_row("", ip_info['ip'], ping_str, ip_info.get('ptr') or "-")
        
        if res['ipv6']:
            table.add_row("", "--- IPv6 ---")
            for ip_info in res['ipv6']:
                table.add_row("", ip_info['ip'], "-", ip_info.get('ptr') or "-")
        table.add_section()
        
    console.print(table)

async def analyze_servers():
    """UI-Funktion für die normale Server-Analyse."""
    console.print("\n[bold]--- Server analysieren ---[/bold]")
    # KORRIGIERTE ZEILE: 'description' entfernt und in den Fragetext integriert.
    mode = Prompt.ask(
        "Wähle den Server-Typ ([1] Klassisch [2] Modern [3] Secure Core [4] Manuell)", 
        choices=["1", "2", "3", "4"], 
        default="1",
        console=console
    )

    prefix, domain = "", ""
    if mode == "1":
        cc = Prompt.ask("Länderkürzel (z.B. de, us-ca)")
        prefix, domain = f"{cc}-", "protonvpn.com"
    elif mode == "2":
        cc = Prompt.ask("Länderkürzel (z.B. de, us)")
        prefix, domain = f"node-{cc}-", "protonvpn.net"
    elif mode == "3":
        entry = Prompt.ask("Eingangsland (z.B. ch)")
        exit_co = Prompt.ask("Ausgangsland (z.B. de)")
        prefix, domain = f"{entry}-{exit_co}-", "protonvpn.com"
    elif mode == "4":
        prefix = Prompt.ask("Hostname-Präfix (z.B. is-nl-)")
        domain = Prompt.ask("Domain (z.B. protonvpn.com)")

    end_number = IntPrompt.ask("Bis zu welcher Nummer suchen?", default=50)
    hostnames = [f"{prefix}{i}.{domain}" if mode != '3' else f"{prefix}{i}a.{domain}" for i in range(1, end_number + 1)]
    
    with Progress(SpinnerColumn(), BarColumn(), "[progress.percentage]{task.percentage:>3.0f}%", TextColumn("{task.description}"), console=console) as progress:
        task = progress.add_task("[cyan]Prüfe Server...", total=len(hostnames))
        tasks = [check_server(h, progress, task) for h in hostnames]
        results = await asyncio.gather(*tasks)

    display_results(results)

async def reverse_search():
    """UI-Funktion für die Reverse-Suche."""
    console.print("\n[bold]--- Node-Finder (Reverse-Suche) ---[/bold]")
    user_input = Prompt.ask("Gib eine IP-Adresse oder einen Hostnamen ein")
    
    target_ip, ip_type = None, None
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", user_input) or ":" in user_input:
        target_ip = user_input
        ip_type = "IPv6" if ":" in user_input else "IPv4"
    else:
        console.print(f"Eingabe als Hostname erkannt. Ermittle IP für [cyan]{user_input}[/cyan]...")
        ips = await get_ips(user_input)
        if ips["aaaa"]:
            target_ip, ip_type = ips["aaaa"][0], "IPv6"
        elif ips["a"]:
            target_ip, ip_type = ips["a"][0], "IPv4"
            
    if not target_ip:
        console.print(f"[red]Fehler: Konnte keine gültige IP für '{user_input}' finden.[/red]")
        return
        
    console.print(f"[green]✅ Ziel-IP ({ip_type}) festgelegt:[/green] [bold]{target_ip}[/bold]")
    
    ccs = Prompt.ask("Zu durchsuchende Länderkürzel (z.B. de ch us)").split()
    end_number = IntPrompt.ask("Bis zu welcher Nummer suchen?", default=200)

    hostnames_to_check = []
    for cc in ccs:
        for i in range(1, end_number + 1):
            hostnames_to_check.append(f"node-{cc}-{i}.protonvpn.net")
            hostnames_to_check.append(f"{cc}-{i}.protonvpn.com")
            
    record_type = 'AAAA' if ip_type == 'IPv6' else 'A'

    with Progress(SpinnerColumn(), BarColumn(), "[progress.percentage]{task.percentage:>3.0f}%", TextColumn("{task.description}"), console=console) as progress:
        task = progress.add_task(f"[cyan]Suche nach {target_ip}...", total=len(hostnames_to_check))
        for hostname in hostnames_to_check:
            progress.update(task, advance=1)
            try:
                result = await resolver.resolve(hostname, record_type)
                for ip in result:
                    if ip.to_text() == target_ip:
                        console.print(f"\n[bold green]✅✅✅ TREFFER GEFUNDEN! ✅✅✅[/bold green]")
                        console.print(f"Die IP-Adresse [bold]{target_ip}[/bold] gehört zu: [bold cyan]{hostname}[/bold cyan]")
                        return
            except Exception:
                continue
    console.print(f"\n[yellow]Suche beendet. Kein Node für die IP {target_ip} gefunden.[/yellow]")

async def main():
    """Hauptmenü und Programmschleife."""
    while True:
        console.print(Panel.fit("[bold blue]Proton-Scanner v15 (Python Edition)[/bold blue]\nEin schnelles Analyse-Werkzeug mit erweiterter Abhängigkeitsprüfung",
                                border_style="blue"))
        # KORRIGIERTE ZEILE: 'description' entfernt und in den Fragetext integriert.
        choice = Prompt.ask(
            "Wähle eine Aktion ([1] Server analysieren [2] Node-Finder [3] Beenden)", 
            choices=["1", "2", "3"], 
            default="1"
        )
        
        if choice == "1":
            await analyze_servers()
        elif choice == "2":
            await reverse_search()
        elif choice == "3":
            console.print("[bold]Skript wird beendet.[/bold]")
            break
        
        if Confirm.ask("\nZurück zum Hauptmenü?", default=True):
            continue
        else:
            console.print("[bold]Skript wird beendet.[/bold]")
            break

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold]Skript vom Benutzer beendet.[/bold]")
        sys.exit(0)

    print("--- Abhängigkeitsprüfung ---")
    print("Die folgenden, für das Skript benötigten Pakete fehlen:")
    for pkg in missing_packages:
        print(f"  - {pkg}")
    
    try:
        user_choice = input("Dürfen diese Pakete jetzt mit pip installiert werden? [J/n]: ").lower().strip()
    except KeyboardInterrupt:
        print("\nPrüfung abgebrochen.")
        return False

    if user_choice == 'j' or user_choice == '':
        print("\nInstalliere Pakete...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_packages], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("\n✅ Installation erfolgreich!")
            print("Bitte starten Sie das Skript jetzt neu.")
        except subprocess.CalledProcessError as e:
            error_output = e.stderr.decode() if e.stderr else ""
            if "externally-managed-environment" in error_output:
                advice = get_distro_specific_advice(missing_packages)
                print("\n❌ Fehler: Die Installation wurde vom Betriebssystem blockiert (PEP 668).")
                print("\nEmpfohlene Lösungen:")
                print(f"1. Benutze den System-Paketmanager: {advice}")
                print("2. Oder verwende eine virtuelle Python-Umgebung (`python -m venv .venv`).")
            else:
                print("\n❌ Ein unbekannter Fehler ist bei der Installation aufgetreten.")
                print(f"   Bitte versuchen Sie es manuell: `pip install {' '.join(missing_packages)}`")
    else:
        print("Installation abgebrochen. Das Skript kann ohne die Pakete nicht ausgeführt werden.")

    return False

if not check_and_install_dependencies():
    sys.exit()

import asyncio
import re
from typing import List, Optional

import dns.asyncresolver
import dns.reversename
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.table import Table
from icmplib import async_ping

console = Console()
resolver = dns.asyncresolver.Resolver()
resolver.timeout = 2
resolver.lifetime = 2

async def get_ips(hostname: str) -> dict:
    results = {"a": [], "aaaa": []}
    try:
        v4_lookup, v6_lookup = await asyncio.gather(
            resolver.resolve(hostname, 'A'),
            resolver.resolve(hostname, 'AAAA'),
            return_exceptions=True
        )
        if isinstance(v4_lookup, dns.resolver.Answer):
            results["a"] = [r.to_text() for r in v4_lookup]
        if isinstance(v6_lookup, dns.resolver.Answer):
            results["aaaa"] = [r.to_text() for r in v6_lookup]
    except Exception:
        pass
    return results

async def get_reverse_dns(ip: str) -> Optional[str]:
    try:
        addr = dns.reversename.from_address(ip)
        answer = await resolver.resolve(addr, "PTR")
        return answer[0].to_text()
    except Exception:
        return None

async def check_server(hostname: str, progress, task) -> Optional[dict]:
    ips = await get_ips(hostname)
    progress.update(task, advance=1)
    if not ips["a"] and not ips["aaaa"]:
        return None

    ptr_tasks = [get_reverse_dns(ip) for ip in ips["a"] + ips["aaaa"]]
    ping_tasks = [async_ping(ip, count=1, timeout=1) for ip in ips["a"]]

    ptr_results = await asyncio.gather(*ptr_tasks)
    ping_results = await asyncio.gather(*ping_tasks)

    ptr_map = dict(zip(ips["a"] + ips["aaaa"], ptr_results))
    ping_map = dict(zip(ips["a"], [p.avg_rtt for p in ping_results if p.is_alive]))
    
    return {
        "hostname": hostname,
        "ipv4": [{"ip": ip, "ptr": ptr_map.get(ip), "ping": ping_map.get(ip)} for ip in ips["a"]],
        "ipv6": [{"ip": ip, "ptr": ptr_map.get(ip)} for ip in ips["aaaa"]]
    }

def display_results(results: List[dict]):
    if not any(results):
        console.print("[yellow]Keine Server im angegebenen Bereich gefunden.[/yellow]")
        return

    table = Table(title="Analyse-Ergebnisse", show_header=True, header_style="bold magenta")
    table.add_column("Proton Node", style="cyan")
    table.add_column("IP-Adresse", style="dim")
    table.add_column("Latenz (ms)", style="green")
    table.add_column("Reverse Hostname", style="yellow")

    for res in filter(None, results):
        table.add_row(f"[bold]{res['hostname']}[/bold]", "--- IPv4 ---")
        for ip_info in res['ipv4']:
            ping_str = f"{ip_info['ping']:.2f}" if ip_info.get('ping') is not None else "-"
            table.add_row("", ip_info['ip'], ping_str, ip_info.get('ptr') or "-")
        
        if res['ipv6']:
            table.add_row("", "--- IPv6 ---")
            for ip_info in res['ipv6']:
                table.add_row("", ip_info['ip'], "-", ip_info.get('ptr') or "-")
        table.add_section()
        
    console.print(table)

async def analyze_servers():
    """UI-Funktion für die normale Server-Analyse."""
    console.print("\n[bold]--- Server analysieren ---[/bold]")
    # KORRIGIERTE ZEILE: 'description' entfernt und in den Fragetext integriert.
    mode = Prompt.ask(
        "Wähle den Server-Typ ([1] Klassisch [2] Modern [3] Secure Core [4] Manuell)", 
        choices=["1", "2", "3", "4"], 
        default="1",
        console=console
    )

    prefix, domain = "", ""
    if mode == "1":
        cc = Prompt.ask("Länderkürzel (z.B. de, us-ca)")
        prefix, domain = f"{cc}-", "protonvpn.com"
    elif mode == "2":
        cc = Prompt.ask("Länderkürzel (z.B. de, us)")
        prefix, domain = f"node-{cc}-", "protonvpn.net"
    elif mode == "3":
        entry = Prompt.ask("Eingangsland (z.B. ch)")
        exit_co = Prompt.ask("Ausgangsland (z.B. de)")
        prefix, domain = f"{entry}-{exit_co}-", "protonvpn.com"
    elif mode == "4":
        prefix = Prompt.ask("Hostname-Präfix (z.B. is-nl-)")
        domain = Prompt.ask("Domain (z.B. protonvpn.com)")

    end_number = IntPrompt.ask("Bis zu welcher Nummer suchen?", default=50)
    hostnames = [f"{prefix}{i}.{domain}" if mode != '3' else f"{prefix}{i}a.{domain}" for i in range(1, end_number + 1)]
    
    with Progress(SpinnerColumn(), BarColumn(), "[progress.percentage]{task.percentage:>3.0f}%", TextColumn("{task.description}"), console=console) as progress:
        task = progress.add_task("[cyan]Prüfe Server...", total=len(hostnames))
        tasks = [check_server(h, progress, task) for h in hostnames]
        results = await asyncio.gather(*tasks)

    display_results(results)

async def reverse_search():
    """UI-Funktion für die Reverse-Suche."""
    console.print("\n[bold]--- Node-Finder (Reverse-Suche) ---[/bold]")
    user_input = Prompt.ask("Gib eine IP-Adresse oder einen Hostnamen ein")
    
    target_ip, ip_type = None, None
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", user_input) or ":" in user_input:
        target_ip = user_input
        ip_type = "IPv6" if ":" in user_input else "IPv4"
    else:
        console.print(f"Eingabe als Hostname erkannt. Ermittle IP für [cyan]{user_input}[/cyan]...")
        ips = await get_ips(user_input)
        if ips["aaaa"]:
            target_ip, ip_type = ips["aaaa"][0], "IPv6"
        elif ips["a"]:
            target_ip, ip_type = ips["a"][0], "IPv4"
            
    if not target_ip:
        console.print(f"[red]Fehler: Konnte keine gültige IP für '{user_input}' finden.[/red]")
        return
        
    console.print(f"[green]✅ Ziel-IP ({ip_type}) festgelegt:[/green] [bold]{target_ip}[/bold]")
    
    ccs = Prompt.ask("Zu durchsuchende Länderkürzel (z.B. de ch us)").split()
    end_number = IntPrompt.ask("Bis zu welcher Nummer suchen?", default=200)

    hostnames_to_check = []
    for cc in ccs:
        for i in range(1, end_number + 1):
            hostnames_to_check.append(f"node-{cc}-{i}.protonvpn.net")
            hostnames_to_check.append(f"{cc}-{i}.protonvpn.com")
            
    record_type = 'AAAA' if ip_type == 'IPv6' else 'A'

    with Progress(SpinnerColumn(), BarColumn(), "[progress.percentage]{task.percentage:>3.0f}%", TextColumn("{task.description}"), console=console) as progress:
        task = progress.add_task(f"[cyan]Suche nach {target_ip}...", total=len(hostnames_to_check))
        for hostname in hostnames_to_check:
            progress.update(task, advance=1)
            try:
                result = await resolver.resolve(hostname, record_type)
                for ip in result:
                    if ip.to_text() == target_ip:
                        console.print(f"\n[bold green]✅✅✅ TREFFER GEFUNDEN! ✅✅✅[/bold green]")
                        console.print(f"Die IP-Adresse [bold]{target_ip}[/bold] gehört zu: [bold cyan]{hostname}[/bold cyan]")
                        return
            except Exception:
                continue
    console.print(f"\n[yellow]Suche beendet. Kein Node für die IP {target_ip} gefunden.[/yellow]")

async def main():
    """Hauptmenü und Programmschleife."""
    while True:
        console.print(Panel.fit("[bold blue]Proton-Scanner v15 (Python Edition)[/bold blue]\nEin schnelles Analyse-Werkzeug mit erweiterter Abhängigkeitsprüfung",
                                border_style="blue"))
        # KORRIGIERTE ZEILE: 'description' entfernt und in den Fragetext integriert.
        choice = Prompt.ask(
            "Wähle eine Aktion ([1] Server analysieren [2] Node-Finder [3] Beenden)", 
            choices=["1", "2", "3"], 
            default="1"
        )
        
        if choice == "1":
            await analyze_servers()
        elif choice == "2":
            await reverse_search()
        elif choice == "3":
            console.print("[bold]Skript wird beendet.[/bold]")
            break
        
        if Confirm.ask("\nZurück zum Hauptmenü?", default=True):
            continue
        else:
            console.print("[bold]Skript wird beendet.[/bold]")
            break

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold]Skript vom Benutzer beendet.[/bold]")
        sys.exit(0)
