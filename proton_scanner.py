#!/usr/bin/env python3
"""
Proton-Scanner (v20)
Asynchrones Analyse- und Diagnose-Werkzeug für ProtonVPN-Server.
Unterstützt interaktive Terminal-Bedienung sowie Kommandozeilen-Parameter.
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import ipaddress
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any

# ==============================================================================
# 1. LAUFZEIT- & ABHÄNGIGKEITSPRÜFUNG
# ==============================================================================

MIN_PYTHON = (3, 10)
if sys.version_info < MIN_PYTHON:
    sys.exit(
        f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ erforderlich. "
        f"Installiert: Python {sys.version_info.major}.{sys.version_info.minor}"
    )


def get_distro_specific_advice(packages: list[str]) -> str:
    """Gibt einen spezifischen Installationsbefehl basierend auf der Linux-Distribution zurück."""
    if not os.path.exists("/etc/os-release"):
        return "Benutze den Paketmanager deiner Distribution."

    with open("/etc/os-release", encoding="utf-8") as f:
        dist_info = {
            k.strip(): v.strip().strip('"')
            for k, v in (line.split("=", 1) for line in f if "=" in line)
        }

    dist_id = dist_info.get("ID", "").lower()
    id_like = dist_info.get("ID_LIKE", "").lower()

    pkg_map = {
        "rich": {
            "debian": "python3-rich",
            "fedora": "python3-rich",
            "arch": "python-rich",
            "gentoo": "dev-python/rich",
        },
        "dnspython": {
            "debian": "python3-dnspython",
            "fedora": "python3-dnspython",
            "arch": "python-dnspython",
            "gentoo": "dev-python/dnspython",
        },
        "icmplib": {
            "debian": "python3-icmplib",
            "fedora": "python3-icmplib",
            "arch": "python-icmplib",
            "gentoo": "dev-python/icmplib",
        },
    }

    def map_pkgs(dist_key: str) -> str:
        return " ".join([pkg_map.get(p, {}).get(dist_key, p) for p in packages])

    if any(k in dist_id or k in id_like for k in ("debian", "ubuntu", "mint")):
        return f"sudo apt install {map_pkgs('debian')}"
    if any(k in dist_id or k in id_like for k in ("fedora", "rhel", "centos")):
        return f"sudo dnf install {map_pkgs('fedora')}"
    if "arch" in dist_id or "arch" in id_like:
        return f"sudo pacman -S {map_pkgs('arch')}"
    if "gentoo" in dist_id:
        return f"sudo emerge --ask {map_pkgs('gentoo')}"

    return "Benutze den Paketmanager deiner Distribution."


def check_and_install_dependencies() -> bool:
    """Prüft zwingend benötigte Pakete (rich, dnspython) und bietet bei Bedarf Installation an."""
    # icmplib ist optional: wenn es fehlt, greift automatisch der System-Ping (/bin/ping)
    required = {"rich": "rich", "dns": "dnspython"}
    missing = [pkg for mod, pkg in required.items() if importlib.util.find_spec(mod) is None]

    if not missing:
        return True

    print("--- Abhängigkeitsprüfung ---")
    print("Die folgenden Basis-Pakete fehlen für Proton-Scanner:")
    for pkg in missing:
        print(f"  - {pkg}")

    try:
        user_choice = input(
            "\nDürfen diese Pakete jetzt mit pip installiert werden? [J/n]: "
        ).lower().strip()
    except (KeyboardInterrupt, EOFError):
        print("\nPrüfung abgebrochen.")
        return False

    if user_choice in ("j", "y", ""):
        print("\nInstalliere Pakete...")
        res = subprocess.run(
            [sys.executable, "-m", "pip", "install", *missing],
            capture_output=True,
            text=True,
        )
        if res.returncode == 0:
            print("Installation erfolgreich. Bitte starte das Skript neu.")
            return False
        else:
            err = (res.stderr or res.stdout).strip()
            if "externally-managed-environment" in err.lower():
                advice = get_distro_specific_advice(missing)
                print("\nFehler: Systemumgebung ist extern verwaltet (PEP 668).")
                print("Lösungsmöglichkeiten:")
                print(f"  1. System-Paketmanager: `{advice}`")
                print("  2. Virtuelle Umgebung: `python -m venv .venv && source .venv/bin/activate`")
            else:
                print(f"\nInstallationsfehler:\n{err or 'Unbekannter Fehler'}")
                print(f"   Manuell ausführen: `pip install {' '.join(missing)}`")
    else:
        print("Installation abgebrochen.")
    return False


if not check_and_install_dependencies():
    sys.exit(0)

# ==============================================================================
# 2. IMPORTE & DATENMODELLE
# ==============================================================================

import dns.asyncresolver
import dns.exception
import dns.resolver
import dns.reversename

try:
    from icmplib import async_ping
    from icmplib import exceptions as icmp_exceptions
    HAS_ICMPLIB = True
except ImportError:
    async_ping = None
    icmp_exceptions = None
    HAS_ICMPLIB = False

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

console = Console()


@dataclass
class ScanStats:
    total: int = 0
    found: int = 0
    nxdomain: int = 0
    no_answer: int = 0
    timeout: int = 0
    errors: int = 0

    def summary(self) -> str:
        parts = [f"Gesamt: {self.total}", f"Gefunden: {self.found}"]
        if self.nxdomain:
            parts.append(f"Nicht existent (NXDOMAIN): {self.nxdomain}")
        if self.no_answer:
            parts.append(f"Ohne IP-Record: {self.no_answer}")
        if self.timeout:
            parts.append(f"Timeouts: {self.timeout}")
        if self.errors:
            parts.append(f"Fehler: {self.errors}")
        return " | ".join(parts)


@dataclass
class IpResult:
    ip: str
    ptr: str | None = None
    ping_ms: float | None = None


@dataclass
class ServerResult:
    hostname: str
    ipv4: list[IpResult] = field(default_factory=list)
    ipv6: list[IpResult] = field(default_factory=list)


# ==============================================================================
# 3. HELFERFUNKTIONEN & KERNLOGIK
# ==============================================================================


def validate_ip(ip_str: str) -> tuple[str, str] | None:
    """
    Validiert eine IP-Adresse via ipaddress.
    Gibt (ip_str, 'IPv4' | 'IPv6') zurück oder None bei ungültiger IP.
    """
    try:
        addr = ipaddress.ip_address(ip_str.strip())
        return str(addr), ("IPv6" if addr.version == 6 else "IPv4")
    except ValueError:
        return None


def generate_hostnames(
    mode: str,
    country_code: str,
    end_number: int,
    exit_country: str = "",
    custom_prefix: str = "",
    custom_domain: str = "protonvpn.com",
) -> tuple[list[str], str]:
    """Erzeugt deterministische Server-Hostnamen basierend auf dem gewählten Modus."""
    cc = country_code.strip().lower()
    hostnames: list[str] = []

    if mode == "1":
        prefix, domain = f"{cc}-", "protonvpn.com"
        desc = f"Klassische (OpenVPN/IKEv2) Server ({cc.upper()})"
        hostnames = [f"{prefix}{i}.{domain}" for i in range(1, end_number + 1)]
    elif mode == "2":
        prefix, domain = f"node-{cc}-", "protonvpn.net"
        desc = f"Moderne (WireGuard) Server ({cc.upper()})"
        hostnames = []
        for i in range(1, end_number + 1):
            if i < 10:
                hostnames.append(f"{prefix}{i:02d}.{domain}")
            hostnames.append(f"{prefix}{i}.{domain}")
    elif mode == "3":
        entry = cc
        exit_co = exit_country.strip().lower()
        prefix, domain = f"{entry}-{exit_co}-", "protonvpn.com"
        desc = f"Secure Core Server ({entry.upper()} -> {exit_co.upper()})"
        hostnames = [f"{prefix}{i}a.{domain}" for i in range(1, end_number + 1)]
    elif mode == "4":
        p = custom_prefix.strip()
        d = custom_domain.strip()
        desc = f"Manuelle Server ({p}*.{d})"
        hostnames = [f"{p}{i}.{d}" for i in range(1, end_number + 1)]
    else:
        raise ValueError(f"Unbekannter Modus: {mode}")

    return hostnames, desc


def create_resolver(nameservers: list[str] | None = None, timeout: float = 2.0) -> dns.asyncresolver.Resolver:
    """Erstellt einen DNS-Resolver. Standardmäßig wird der System-DNS verwendet."""
    res = dns.asyncresolver.Resolver()
    if nameservers:
        res.nameservers = nameservers
    res.timeout = timeout
    res.lifetime = timeout
    return res


async def ping_ip(ip: str, timeout: float = 1.0) -> float | None:
    """
    Führt einen Ping-Test durch.
    Nutzt icmplib falls installiert, ansonsten transparenten Fallback auf System-Ping (/bin/ping).
    """
    if HAS_ICMPLIB and async_ping is not None:
        try:
            host = await async_ping(ip, count=1, timeout=timeout, privileged=False)
            if host.is_alive:
                return round(host.avg_rtt, 2)
        except Exception:
            pass

    # Fallback auf Standard-System-Ping (/bin/ping oder /usr/bin/ping)
    try:
        cmd = ["ping", "-c", "1", "-W", str(int(max(1, timeout))), ip]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout + 0.5)
        if proc.returncode == 0:
            out = stdout.decode(errors="replace")
            m = re.search(r"time[=<]\s*([\d.]+)\s*ms", out, re.IGNORECASE) or re.search(
                r"= [\d.]+/([\d.]+)/[\d.]+", out
            )
            if m:
                return round(float(m.group(1)), 2)
    except Exception:
        return None
    return None


async def resolve_ips_and_ptrs(
    hostname: str,
    resolver: dns.asyncresolver.Resolver,
    stats: ScanStats,
) -> tuple[list[str], list[str]]:
    """Ermittelt IPv4- und IPv6-Adressen und klassifiziert das DNS-Ergebnis statistisch."""
    v4_ips: list[str] = []
    v6_ips: list[str] = []

    try:
        v4_res, v6_res = await asyncio.gather(
            resolver.resolve(hostname, "A"),
            resolver.resolve(hostname, "AAAA"),
            return_exceptions=True,
        )

        has_nxdomain = False
        has_timeout = False
        has_no_answer = False

        if isinstance(v4_res, dns.resolver.Answer):
            v4_ips = [r.to_text() for r in v4_res]
        elif isinstance(v4_res, dns.resolver.NXDOMAIN):
            has_nxdomain = True
        elif isinstance(v4_res, dns.resolver.NoAnswer):
            has_no_answer = True
        elif isinstance(v4_res, (dns.exception.Timeout, dns.asyncresolver.LifetimeTimeout)):
            has_timeout = True

        if isinstance(v6_res, dns.resolver.Answer):
            v6_ips = [r.to_text() for r in v6_res]
        elif isinstance(v6_res, dns.resolver.NXDOMAIN):
            has_nxdomain = True
        elif isinstance(v6_res, dns.resolver.NoAnswer):
            has_no_answer = True
        elif isinstance(v6_res, (dns.exception.Timeout, dns.asyncresolver.LifetimeTimeout)):
            has_timeout = True

        if v4_ips or v6_ips:
            stats.found += 1
        elif has_nxdomain:
            stats.nxdomain += 1
        elif has_timeout:
            stats.timeout += 1
        elif has_no_answer:
            stats.no_answer += 1
        else:
            stats.errors += 1

    except Exception:
        stats.errors += 1

    return v4_ips, v6_ips


async def get_ptr(ip: str, resolver: dns.asyncresolver.Resolver) -> str | None:
    """Löst die Reverse-DNS-Adresse (PTR) für eine gegebene IP auf."""
    try:
        addr = dns.reversename.from_address(ip)
        answer = await resolver.resolve(addr, "PTR")
        return answer[0].to_text().rstrip(".")
    except Exception:
        return None


async def check_single_server(
    hostname: str,
    resolver: dns.asyncresolver.Resolver,
    stats: ScanStats,
    sem: asyncio.Semaphore,
    perform_ping: bool,
    progress: Progress | None = None,
    task_id: Any = None,
) -> ServerResult | None:
    """Überprüft einen einzelnen Server mit kontrollierter Parallelität."""
    async with sem:
        v4_ips, v6_ips = await resolve_ips_and_ptrs(hostname, resolver, stats)
        if progress and task_id is not None:
            progress.update(task_id, advance=1)

        if not v4_ips and not v6_ips:
            return None

        # PTR-Lookups
        all_ips = v4_ips + v6_ips
        ptr_tasks = [get_ptr(ip, resolver) for ip in all_ips]
        ptrs = await asyncio.gather(*ptr_tasks)
        ptr_map = dict(zip(all_ips, ptrs, strict=True))

        # Ping-Tests (IPv4)
        ping_map: dict[str, float | None] = {}
        if perform_ping and v4_ips:
            ping_tasks = [ping_ip(ip) for ip in v4_ips]
            pings = await asyncio.gather(*ping_tasks)
            ping_map = dict(zip(v4_ips, pings, strict=True))

        v4_res = [IpResult(ip=ip, ptr=ptr_map.get(ip), ping_ms=ping_map.get(ip)) for ip in v4_ips]
        v6_res = [IpResult(ip=ip, ptr=ptr_map.get(ip)) for ip in v6_ips]

        return ServerResult(hostname=hostname, ipv4=v4_res, ipv6=v6_res)


# ==============================================================================
# 4. TABELLEN- & ERGEBNISAUSGABE
# ==============================================================================


def display_results_table(results: list[ServerResult], search_description: str, stats: ScanStats):
    """Gibt eine strukturierte Rich-Tabelle und die Scan-Statistik aus."""
    if not results:
        console.print(f"\n[yellow]Keine aktiven Server für '{search_description}' gefunden.[/yellow]")
        console.print(f"[dim]{stats.summary()}[/dim]")
        return

    table = Table(
        title=f"Ergebnisse: {search_description}",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Proton Node", style="cyan", no_wrap=True)
    table.add_column("Typ", style="blue")
    table.add_column("IP-Adresse", style="dim")
    table.add_column("Latenz (ms)", style="green", justify="right")
    table.add_column("Reverse Hostname (PTR)", style="yellow")

    for res in results:
        for idx, ip_info in enumerate(res.ipv4):
            ping_str = f"{ip_info.ping_ms:.2f}" if ip_info.ping_ms is not None else "-"
            node_label = f"[bold]{res.hostname}[/bold]" if idx == 0 else ""
            table.add_row(node_label, "IPv4", ip_info.ip, ping_str, ip_info.ptr or "-")
        for idx, ip_info in enumerate(res.ipv6):
            node_label = f"[bold]{res.hostname}[/bold]" if not res.ipv4 and idx == 0 else ""
            table.add_row(node_label, "IPv6", ip_info.ip, "-", ip_info.ptr or "-")
        table.add_section()

    console.print(table)
    console.print(f"\n[bold cyan]Statistik:[/bold cyan] {stats.summary()}")


# ==============================================================================
# 5. ASYNCHRONE WORKFLOWS
# ==============================================================================


async def run_server_scan(
    hostnames: list[str],
    search_desc: str,
    resolver: dns.asyncresolver.Resolver,
    perform_ping: bool = True,
    concurrency: int = 50,
) -> tuple[list[ServerResult], ScanStats]:
    """Scannt eine Hostnamen-Liste mit kontrollierter Parallelität."""
    stats = ScanStats(total=len(hostnames))
    sem = asyncio.Semaphore(concurrency)

    with Progress(
        SpinnerColumn(),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TextColumn("{task.description}"),
        console=console,
    ) as progress:
        task_id = progress.add_task(f"[cyan]Prüfe {len(hostnames)} Server...", total=len(hostnames))
        tasks = [
            check_single_server(h, resolver, stats, sem, perform_ping, progress, task_id)
            for h in hostnames
        ]
        raw_results = await asyncio.gather(*tasks)

    results = [r for r in raw_results if r is not None]
    return results, stats


async def run_reverse_search(
    target_ip: str,
    ip_type: str,
    countries: list[str],
    end_number: int,
    resolver: dns.asyncresolver.Resolver,
    concurrency: int = 60,
) -> list[str]:
    """
    Führt eine asynchrone, parallele Suche nach einem Node für eine bestimmte IP durch.
    Nutzt Semaphore zur Lastbegrenzung.
    """
    hostnames_to_check: list[str] = []
    for cc in countries:
        c = cc.strip().lower()
        for i in range(1, end_number + 1):
            if i < 10:
                hostnames_to_check.append(f"node-{c}-{i:02d}.protonvpn.net")
            hostnames_to_check.extend([
                f"node-{c}-{i}.protonvpn.net",
                f"{c}-{i}.protonvpn.com",
            ])

    record_type = "AAAA" if ip_type == "IPv6" else "A"
    sem = asyncio.Semaphore(concurrency)
    found_nodes: list[str] = []
    stop_event = asyncio.Event()

    async def probe(hostname: str, progress: Progress, task_id: Any):
        if stop_event.is_set():
            progress.update(task_id, advance=1)
            return

        async with sem:
            if stop_event.is_set():
                progress.update(task_id, advance=1)
                return
            try:
                ans = await resolver.resolve(hostname, record_type)
                for rdata in ans:
                    if rdata.to_text() == target_ip:
                        found_nodes.append(hostname)
                        stop_event.set()
                        break
            except Exception:
                pass
            finally:
                progress.update(task_id, advance=1)

    with Progress(
        SpinnerColumn(),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TextColumn("{task.description}"),
        console=console,
    ) as progress:
        task_id = progress.add_task(
            f"[cyan]Suche nach {target_ip} in {len(hostnames_to_check)} Nodes...",
            total=len(hostnames_to_check),
        )
        tasks = [probe(h, progress, task_id) for h in hostnames_to_check]
        await asyncio.gather(*tasks)

    return found_nodes


# ==============================================================================
# 6. INTERAKTIVE MENÜ-FÜHRUNG
# ==============================================================================


async def interactive_analyze_servers(resolver: dns.asyncresolver.Resolver, perform_ping: bool):
    """Interaktiver Dialog für Server-Scans."""
    console.print("\n[bold]--- Server analysieren ---[/bold]")
    mode = Prompt.ask(
        "Wähle den Server-Typ ([1] Klassisch (OpenVPN) [2] Modern (WireGuard) [3] Secure Core [4] Manuell)",
        choices=["1", "2", "3", "4"],
        default="1",
        console=console,
    )

    cc, exit_co, prefix, domain = "", "", "", "protonvpn.com"
    if mode == "1":
        cc = Prompt.ask("Länderkürzel (z.B. de, ch, us-ca)", default="de", console=console)
    elif mode == "2":
        cc = Prompt.ask("Länderkürzel (z.B. de, ch, us)", default="de", console=console)
    elif mode == "3":
        cc = Prompt.ask("Eingangsland (z.B. ch, is, se)", default="ch", console=console)
        exit_co = Prompt.ask("Ausgangsland (z.B. de, us)", default="de", console=console)
    elif mode == "4":
        prefix = Prompt.ask("Hostname-Präfix (z.B. is-nl-)", console=console)
        domain = Prompt.ask("Domain", default="protonvpn.com", console=console)

    end_number = IntPrompt.ask("Bis zu welcher Nummer suchen?", default=50, console=console)
    hostnames, desc = generate_hostnames(
        mode=mode,
        country_code=cc,
        end_number=end_number,
        exit_country=exit_co,
        custom_prefix=prefix,
        custom_domain=domain,
    )

    results, stats = await run_server_scan(hostnames, desc, resolver, perform_ping=perform_ping)
    display_results_table(results, desc, stats)


async def interactive_reverse_search(resolver: dns.asyncresolver.Resolver):
    """Interaktiver Dialog für Node-Finder (Reverse-Suche)."""
    console.print("\n[bold]--- Node-Finder (Reverse-Suche) ---[/bold]")
    user_input = Prompt.ask("Gib eine IP-Adresse oder einen Hostnamen ein", console=console).strip()

    parsed = validate_ip(user_input)
    if parsed:
        target_ip, ip_type = parsed
    else:
        console.print(f"Eingabe als Hostname erkannt. Löse IP für [cyan]{user_input}[/cyan] auf...")
        dummy_stats = ScanStats()
        v4_ips, v6_ips = await resolve_ips_and_ptrs(user_input, resolver, dummy_stats)
        if v6_ips:
            target_ip, ip_type = v6_ips[0], "IPv6"
        elif v4_ips:
            target_ip, ip_type = v4_ips[0], "IPv4"
        else:
            console.print(f"[red]Fehler: Konnte keine IP für '{user_input}' auflösen.[/red]")
            return

    console.print(f"[green]Ziel-IP ({ip_type}):[/green] [bold]{target_ip}[/bold]")
    ccs_raw = Prompt.ask(
        "Zu durchsuchende Länderkürzel (getrennt durch Leerzeichen)",
        default="de ch at us",
        console=console,
    )
    countries = ccs_raw.split()
    end_number = IntPrompt.ask("Bis zu welcher Nummer je Land prüfen?", default=150, console=console)

    hits = await run_reverse_search(target_ip, ip_type, countries, end_number, resolver)

    if hits:
        console.print(f"\n[bold green]Treffer gefunden ({len(hits)}):[/bold green]")
        for h in hits:
            console.print(f"  Die IP [bold]{target_ip}[/bold] gehört zu: [bold cyan]{h}[/bold cyan]")
    else:
        console.print(f"\n[yellow]Suche beendet. Kein Node für IP {target_ip} gefunden.[/yellow]")


async def interactive_main():
    """Startet das interaktive Rich-Hauptmenü."""
    console.print(
        Panel.fit(
            "[bold blue]Proton-Scanner v20[/bold blue]\n"
            "Asynchrones Analyse-Werkzeug mit kontrollierter Parallelität & nativer IP-Validierung",
            border_style="blue",
        )
    )

    # DNS-Konfiguration abfragen
    dns_choice = Prompt.ask(
        "DNS-Resolver wählen: [1] System-Standard [2] Cloudflare (1.1.1.1) [3] Google (8.8.8.8) [4] Quad9 (9.9.9.9)",
        choices=["1", "2", "3", "4"],
        default="1",
        console=console,
    )
    dns_map = {
        "1": None,
        "2": ["1.1.1.1", "1.0.0.1"],
        "3": ["8.8.8.8", "8.8.4.4"],
        "4": ["9.9.9.9", "149.112.112.112"],
    }
    resolver = create_resolver(dns_map[dns_choice])

    perform_ping = Confirm.ask("Ping-Test zur Latenzmessung durchführen?", default=True, console=console)

    while True:
        choice = Prompt.ask(
            "\nAktion wählen: [1] Server analysieren [2] Node-Finder [3] Beenden",
            choices=["1", "2", "3"],
            default="1",
            console=console,
        )
        if choice == "1":
            await interactive_analyze_servers(resolver, perform_ping)
        elif choice == "2":
            await interactive_reverse_search(resolver)
        elif choice == "3":
            break

        if not Confirm.ask("\nZurück zum Hauptmenü?", default=True, console=console):
            break

    console.print("[bold]Programm beendet.[/bold]")


# ==============================================================================
# 7. CLI-MODUS & ARGPARSE
# ==============================================================================


def parse_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Proton-Scanner: Asynchrone Analyse von ProtonVPN-Servern",
    )
    subparsers = parser.add_subparsers(dest="command", help="Verfügbare Befehle")

    # Scan-Befehl
    scan_p = subparsers.add_parser("scan", help="Server-Bereiche analysieren")
    scan_p.add_argument("--mode", choices=["1", "2", "3", "4"], default="1", help="1=Klassisch, 2=WireGuard, 3=Secure Core, 4=Manuell")
    scan_p.add_argument("--cc", default="de", help="Länderkürzel (z.B. de, ch, us)")
    scan_p.add_argument("--exit-cc", default="de", help="Ausgangsland für Secure Core (z.B. de)")
    scan_p.add_argument("--prefix", default="", help="Präfix für manuelle Suche")
    scan_p.add_argument("--domain", default="protonvpn.com", help="Domain für manuelle Suche")
    scan_p.add_argument("--count", type=int, default=50, help="Anzahl der Server")
    scan_p.add_argument("--dns", nargs="+", help="Spezifische DNS-Server nutzen (z.B. 1.1.1.1 8.8.8.8)")
    scan_p.add_argument("--no-ping", action="store_true", help="Ping-Messung deaktivieren")
    scan_p.add_argument("--concurrency", type=int, default=50, help="Gleichzeitige Abfragen (Default: 50)")
    scan_p.add_argument("--json", action="store_true", help="Ergebnisse als JSON ausgeben")

    # Reverse-Befehl
    rev_p = subparsers.add_parser("reverse", help="Node-Finder (Reverse-Suche von IP zu Server)")
    rev_p.add_argument("--target", required=True, help="Ziel-IP oder Hostname")
    rev_p.add_argument("--countries", nargs="+", default=["de", "ch", "at", "us"], help="Länderkürzel")
    rev_p.add_argument("--count", type=int, default=150, help="Server-Anzahl pro Land")
    rev_p.add_argument("--dns", nargs="+", help="Spezifische DNS-Server")
    rev_p.add_argument("--concurrency", type=int, default=60, help="Gleichzeitige Abfragen")
    rev_p.add_argument("--json", action="store_true", help="Ergebnisse als JSON ausgeben")

    return parser.parse_args()


async def cli_main(args: argparse.Namespace):
    resolver = create_resolver(args.dns)

    if args.command == "scan":
        hostnames, desc = generate_hostnames(
            mode=args.mode,
            country_code=args.cc,
            end_number=args.count,
            exit_country=args.exit_cc,
            custom_prefix=args.prefix,
            custom_domain=args.domain,
        )
        results, stats = await run_server_scan(
            hostnames,
            desc,
            resolver,
            perform_ping=not args.no_ping,
            concurrency=args.concurrency,
        )

        if args.json:
            out = {
                "description": desc,
                "stats": {
                    "total": stats.total,
                    "found": stats.found,
                    "nxdomain": stats.nxdomain,
                    "no_answer": stats.no_answer,
                    "timeout": stats.timeout,
                    "errors": stats.errors,
                },
                "servers": [
                    {
                        "hostname": s.hostname,
                        "ipv4": [{"ip": i.ip, "ptr": i.ptr, "ping_ms": i.ping_ms} for i in s.ipv4],
                        "ipv6": [{"ip": i.ip, "ptr": i.ptr} for i in s.ipv6],
                    }
                    for s in results
                ],
            }
            print(json.dumps(out, indent=2))
        else:
            display_results_table(results, desc, stats)

    elif args.command == "reverse":
        target = args.target.strip()
        parsed = validate_ip(target)
        if parsed:
            target_ip, ip_type = parsed
        else:
            dummy_stats = ScanStats()
            v4, v6 = await resolve_ips_and_ptrs(target, resolver, dummy_stats)
            if v6:
                target_ip, ip_type = v6[0], "IPv6"
            elif v4:
                target_ip, ip_type = v4[0], "IPv4"
            else:
                if args.json:
                    print(json.dumps({"error": f"Could not resolve {target}"}))
                else:
                    console.print(f"[red]Konnte IP für '{target}' nicht auflösen.[/red]")
                return

        hits = await run_reverse_search(
            target_ip,
            ip_type,
            args.countries,
            args.count,
            resolver,
            concurrency=args.concurrency,
        )

        if args.json:
            print(json.dumps({"target_ip": target_ip, "ip_type": ip_type, "hits": hits}, indent=2))
        else:
            if hits:
                console.print(f"[bold green]Treffer für {target_ip}:[/bold green] {', '.join(hits)}")
            else:
                console.print(f"[yellow]Kein Node für {target_ip} gefunden.[/yellow]")


def main():
    args = parse_cli_args()
    try:
        if args.command:
            asyncio.run(cli_main(args))
        else:
            asyncio.run(interactive_main())
    except KeyboardInterrupt:
        console.print("\n[bold]Vorgang vom Benutzer abgebrochen.[/bold]")
        sys.exit(0)


if __name__ == "__main__":
    main()
