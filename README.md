# Proton-Scanner (v20)

**English** | [Deutsch](README.de.md)

An asynchronous analysis and diagnostics tool for **ProtonVPN servers**, written in Python 3.10+ using `asyncio`, `dnspython`, and `rich`.

The primary focus of this scanner is **discovering and mapping IPv6-capable ProtonVPN nodes** (AAAA records) to identify their IPv6 addresses for use as dedicated VPN endpoints, compare network latencies, and map technical hostnames.

The program provides both an interactive terminal interface and fully scriptable CLI commands with JSON output for automated pipelines.

---

## Features

* **Targeted IPv6 Discovery:** Reliably resolves active IPv6 addresses (AAAA records) and measures round-trip latency alongside IPv4.
* **IPv6 Filter (`--ipv6-only`):** Filters search results to only include nodes with an active IPv6 address.
* **Latency Sorting (`--sort-latency`):** Sorts discovered servers ascending by lowest latency.
* **Deduplication:** Prevents duplicate entries when ProtonVPN servers share the same IP addresses across naming schemes (e.g. `node-de-01` and `node-de-1`).
* **Controlled Concurrency (`asyncio.Semaphore`):** Rapid server querying without DNS overload or timeouts.
* **Asynchronous Node Finder:** Concurrent reverse lookup of target IP addresses across country codes and node ranges.
* **Native IP Validation:** Strict IPv4 and IPv6 parsing using Python's standard `ipaddress` library.
* **Configurable DNS Resolver:** Uses the system DNS by default with optional switches for public resolvers (e.g. Cloudflare `1.1.1.1`, Google `8.8.8.8`, Quad9 `9.9.9.9`, or custom IPs via CLI).
* **Detailed Error Statistics:** Distinct counters for active servers, IPv6 nodes, `NXDOMAIN`, missing records (`NoAnswer`), timeouts, and network errors.
* **Zero-Setup Ping:** Standardizes on system ping (`/bin/ping`) for both IPv4 and IPv6 without requiring special socket capabilities or root permissions. Optional `icmplib` support for pure Python ICMP.
* **Clean JSON Output:** Progress bars are sent to `stderr`, keeping `stdout` strictly valid JSON when using `--json` (compatible with `jq` and file redirection).
* **CI/CD & Tests:** Full test suite with `pytest`, linting with `ruff`, and GitHub Actions CI workflow.

> **Note on VPN Connectivity:** Discovering a valid AAAA record and responding ICMP pings confirms network reachability of the node's IPv6 address. Whether the VPN service (e.g. WireGuard on UDP port 51820) is enabled for incoming IPv6 connections depends on ProtonVPN's server-side configuration.

---

## Requirements & Installation

Requires **Python 3.10+**.

### 1. Clone the repository

```bash
git clone git@github.com:pschmidt3200/proton-vpn-node-scanner.git
cd proton-vpn-node-scanner
```

### 2. Install dependencies

The tool only requires two base packages: `rich` and `dnspython`.

#### Option A: Virtual Environment (Recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate

# Base installation
pip install .

# For development (includes pytest & ruff):
pip install .[dev]
```

#### Option B: Via Linux Package Manager

To install without a virtual environment, use your distribution's package manager:

* **Gentoo:** `sudo emerge --ask dev-python/rich dev-python/dnspython`
* **Arch Linux:** `sudo pacman -S python-rich python-dnspython`
* **Debian / Ubuntu:** `sudo apt install python3-rich python3-dnspython`
* **Fedora:** `sudo dnf install python3-rich python3-dnspython`

---

## Usage

### 1. Interactive Menu Mode

Run without arguments:

```bash
python3 proton_scanner.py
```

The menu guides you through:
1. **Server analysis:** Select server type (WireGuard, OpenVPN, Secure Core, Custom), country code, range, IPv6 filter, and latency ping.
2. **Node Finder (reverse search):** Identify which ProtonVPN node corresponds to a specific IP address or hostname.
3. **DNS resolver:** Choose between System Default, Cloudflare, Google, or Quad9.

---

### 2. CLI Mode (Scripting & Automation)

Proton-Scanner can be executed directly with command-line arguments:

#### A. Scanning Server Ranges

```bash
# Search for IPv6-capable WireGuard nodes in Germany, sorted by lowest latency:
python3 proton_scanner.py scan --mode 2 --cc de --count 50 --ipv6-only --sort-latency

# Scan WireGuard nodes in the Netherlands (1-50):
python3 proton_scanner.py scan --mode 2 --cc nl --count 50

# Output OpenVPN nodes in Switzerland as clean JSON (no ping):
python3 proton_scanner.py scan --mode 1 --cc ch --count 20 --no-ping --json | jq .

# Use custom DNS resolvers with adjusted concurrency:
python3 proton_scanner.py scan --mode 2 --cc nl --count 100 --dns 1.1.1.1 --concurrency 80
```

#### B. Node Finder (Reverse Lookup)

```bash
# Find which node belongs to a given IP:
python3 proton_scanner.py reverse --target 62.112.9.164 --countries nl de ch --count 50

# Output result as JSON:
python3 proton_scanner.py reverse --target 62.112.9.164 --json
```

---

## Testing & Quality Assurance

Validated using `pytest` and `ruff`:

```bash
# Run test suite
pytest

# Check code quality and formatting
ruff check .
```

---

## History & License

* **History:** Originally started as a set of pragmatic Bash scripts and incrementally evolved into an asynchronous Python application. Historical scripts are preserved in the [`legacy/bash/`](legacy/bash/) directory.
* **License:** Released under the **[MIT License](LICENSE)**.
