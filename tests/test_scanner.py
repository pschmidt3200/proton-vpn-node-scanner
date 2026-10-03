"""
Tests für Proton-Scanner (v20)
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import dns.resolver
import pytest

from proton_scanner import (
    IpResult,
    ScanStats,
    ServerResult,
    create_resolver,
    generate_hostnames,
    get_ptr,
    ping_ip,
    resolve_ips_and_ptrs,
    validate_ip,
)

# ==============================================================================
# 1. IP VALIDIERUNG
# ==============================================================================


@pytest.mark.parametrize(
    "input_val, expected",
    [
        ("185.159.157.1", ("185.159.157.1", "IPv4")),
        ("  185.159.157.1 \n", ("185.159.157.1", "IPv4")),
        ("2a02:6ea0:c400::1", ("2a02:6ea0:c400::1", "IPv6")),
        ("::1", ("::1", "IPv6")),
        ("999.999.999.999", None),
        ("node-de-1.protonvpn.net", None),
        ("invalid-ip", None),
        ("1.2.3.4.5", None),
        ("", None),
    ],
)
def test_validate_ip(input_val: str, expected: tuple[str, str] | None):
    assert validate_ip(input_val) == expected


# ==============================================================================
# 2. HOSTNAMEN-GENERIERUNG
# ==============================================================================


def test_generate_hostnames_classic():
    names, desc = generate_hostnames(mode="1", country_code="de", end_number=3)
    assert names == ["de-1.protonvpn.com", "de-2.protonvpn.com", "de-3.protonvpn.com"]
    assert "Klassische" in desc
    assert "DE" in desc


def test_generate_hostnames_wireguard():
    names, desc = generate_hostnames(mode="2", country_code="CH", end_number=2)
    assert names == [
        "node-ch-01.protonvpn.net",
        "node-ch-1.protonvpn.net",
        "node-ch-02.protonvpn.net",
        "node-ch-2.protonvpn.net",
    ]
    assert "WireGuard" in desc
    assert "CH" in desc


def test_generate_hostnames_secure_core():
    names, desc = generate_hostnames(mode="3", country_code="is", exit_country="de", end_number=2)
    assert names == ["is-de-1a.protonvpn.com", "is-de-2a.protonvpn.com"]
    assert "Secure Core" in desc
    assert "IS -> DE" in desc


def test_generate_hostnames_manual():
    names, desc = generate_hostnames(
        mode="4",
        country_code="",
        end_number=2,
        custom_prefix="custom-node-",
        custom_domain="example.org",
    )
    assert names == ["custom-node-1.example.org", "custom-node-2.example.org"]
    assert "Manuelle Server" in desc


def test_generate_hostnames_invalid_mode():
    with pytest.raises(ValueError, match="Unbekannter Modus"):
        generate_hostnames(mode="99", country_code="de", end_number=1)


# ==============================================================================
# 3. STATISTIKEN & RESOLVER
# ==============================================================================


def test_scan_stats_summary():
    stats = ScanStats(total=10, found=4, nxdomain=5, timeout=1)
    summary = stats.summary()
    assert "Gesamt: 10" in summary
    assert "Gefunden: 4" in summary
    assert "Nicht existent (NXDOMAIN): 5" in summary
    assert "Timeouts: 1" in summary


def test_create_resolver_custom_and_default():
    custom = create_resolver(["1.1.1.1", "1.0.0.1"], timeout=3.5)
    assert custom.nameservers == ["1.1.1.1", "1.0.0.1"]
    assert custom.timeout == 3.5

    default_res = create_resolver()
    assert default_res.timeout == 2.0


# ==============================================================================
# 4. ASYNCHRONE DNS & PING FUNKTIONEN (MOCKED)
# ==============================================================================


def test_resolve_ips_and_ptrs_success():
    async def _test():
        stats = ScanStats()
        resolver = MagicMock()

        mock_answer_v4 = MagicMock(spec=dns.resolver.Answer)
        mock_rdata_v4 = MagicMock()
        mock_rdata_v4.to_text.return_value = "185.159.157.1"
        mock_answer_v4.__iter__.return_value = [mock_rdata_v4]

        resolver.resolve = AsyncMock(side_effect=[mock_answer_v4, dns.resolver.NXDOMAIN()])
        v4, v6 = await resolve_ips_and_ptrs("test.protonvpn.net", resolver, stats)
        assert v4 == ["185.159.157.1"]
        assert v6 == []
        assert stats.found == 1

    asyncio.run(_test())


def test_get_ptr_success():
    async def _test():
        resolver = MagicMock()
        mock_ptr_rdata = MagicMock()
        mock_ptr_rdata.to_text.return_value = "node-de-01.protonvpn.net."
        resolver.resolve = AsyncMock(return_value=[mock_ptr_rdata])

        ptr = await get_ptr("185.159.157.1", resolver)
        assert ptr == "node-de-01.protonvpn.net"

    asyncio.run(_test())


def test_ping_ip_icmplib_alive():
    async def _test():
        with (
            patch("proton_scanner.HAS_ICMPLIB", True),
            patch("proton_scanner.async_ping", new_callable=AsyncMock) as mock_ping,
        ):
            mock_host = MagicMock()
            mock_host.is_alive = True
            mock_host.avg_rtt = 14.567
            mock_ping.return_value = mock_host

            rtt = await ping_ip("185.159.157.1")
            assert rtt == 14.57

    asyncio.run(_test())


def test_ping_ip_system_fallback():
    async def _test():
        with (
            patch("proton_scanner.HAS_ICMPLIB", False),
            patch("asyncio.create_subprocess_exec") as mock_exec,
        ):
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.communicate = AsyncMock(
                return_value=(b"64 bytes from 1.1.1.1: icmp_seq=1 ttl=53 time=18.72 ms\n", b"")
            )
            mock_exec.return_value = mock_proc

            rtt = await ping_ip("1.1.1.1")
            assert rtt == 18.72

    asyncio.run(_test())


def test_data_classes():
    ip_res = IpResult(ip="1.2.3.4", ptr="test.local", ping_ms=12.3)
    server_res = ServerResult(hostname="test-1", ipv4=[ip_res])
    assert server_res.hostname == "test-1"
    assert len(server_res.ipv4) == 1
    assert server_res.ipv4[0].ping_ms == 12.3
