"""Wi-Fi Radar - Local Wi-Fi SSID, RSSI dBm & Signal Quality Analyzer CLI."""

import argparse
import subprocess
import platform
import os
import re
import sys
from typing import Dict, Any, List

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"


def get_wifi_telemetry() -> Dict[str, Any]:
    """Retrieve deep Wi-Fi telemetry across macOS, Linux, and Windows."""
    os_name = platform.system().lower()
    data = {
        "connected": False,
        "interface": "en0",
        "ssid": "Disconnected",
        "rssi": "N/A",
        "noise": "N/A",
        "channel": "N/A",
        "security": "N/A",
        "tx_rate": "N/A",
        "ip": "N/A",
        "nearby": []
    }

    if os_name == "darwin":
        # 1. Local IP
        try:
            ip_out = subprocess.check_output(["ipconfig", "getifaddr", "en0"], text=True, stderr=subprocess.DEVNULL).strip()
            data["ip"] = ip_out if ip_out else "N/A"
        except Exception:
            pass

        # 2. Extract deep native Wi-Fi data via system_profiler
        try:
            out = subprocess.check_output(["system_profiler", "SPAirPortDataType"], text=True, stderr=subprocess.DEVNULL)
            
            # Connected SSID
            m_ssid = re.search(r"Current Network Information:\s*\n\s*([^\n:]+):", out)
            if m_ssid:
                data["ssid"] = m_ssid.group(1).strip()
                data["connected"] = True

            # Signal / Noise
            m_sig = re.search(r"Signal / Noise:\s*([^\n]+)", out)
            if m_sig:
                parts = m_sig.group(1).split("/")
                data["rssi"] = parts[0].strip()
                if len(parts) > 1:
                    data["noise"] = parts[1].strip()

            # Channel
            m_chan = re.search(r"Channel:\s*([^\n]+)", out)
            if m_chan:
                data["channel"] = m_chan.group(1).strip()

            # Security
            m_sec = re.search(r"Security:\s*([^\n]+)", out)
            if m_sec:
                data["security"] = m_sec.group(1).strip()

            # Transmit Rate
            m_rate = re.search(r"Transmit Rate:\s*([^\n]+)", out)
            if m_rate:
                data["tx_rate"] = f"{m_rate.group(1).strip()} Mbps"

            # Parse nearby networks
            nearby_section = re.search(r"Other Local Wi-Fi Networks:\s*\n((?:[^\n]+\n)+)", out)
            if nearby_section:
                nets = re.findall(r"\s{12}([^\n:]+):\s*\n\s+PHY Mode:[^\n]+\n\s+Channel:\s*([^\n]+)\n\s+Network Type:[^\n]+\n\s+Security:\s*([^\n]+)\n\s+Signal / Noise:\s*([^\n]+)", out)
                for n_ssid, n_chan, n_sec, n_sig in nets[:5]:
                    data["nearby"].append({
                        "ssid": n_ssid.strip(),
                        "channel": n_chan.strip(),
                        "security": n_sec.strip(),
                        "signal": n_sig.split("/")[0].strip() if "/" in n_sig else n_sig.strip()
                    })
        except Exception:
            pass

    elif os_name == "linux":
        data["interface"] = "wlan0"
        try:
            res = subprocess.check_output(["nmcli", "-t", "-f", "active,ssid,bssid,chan,signal,security", "dev", "wifi"], text=True, stderr=subprocess.DEVNULL)
            for line in res.splitlines():
                parts = line.split(":")
                if line.startswith("yes:"):
                    data["connected"] = True
                    data["ssid"] = parts[1]
                    data["channel"] = parts[3]
                    data["rssi"] = f"{parts[4]}% quality"
                    data["security"] = parts[5] if len(parts) > 5 else "WPA2"
                elif len(parts) >= 6 and len(data["nearby"]) < 5:
                    data["nearby"].append({
                        "ssid": parts[1],
                        "channel": parts[3],
                        "signal": f"{parts[4]}%",
                        "security": parts[5]
                    })
        except Exception:
            pass

    return data


def main(args=None):
    parser = argparse.ArgumentParser(
        prog="wifi-radar",
        description="📡 Wi-Fi Radar - Local Wi-Fi SSID, RSSI dBm & Signal Quality Analyzer CLI"
    )
    parser.add_argument("--scan", action="store_true", help="Scan nearby Wi-Fi access points")
    parser.parse_args(args)

    data = get_wifi_telemetry()

    print(f"\n{CYAN}{BOLD}📡 Wi-Fi Radar — Local Wireless Telemetry & Signal Analyzer{RESET}")
    print(f"{DIM}Host: {platform.node()} | OS: {platform.system()} {platform.release()}{RESET}")
    print("═" * 65)
    print(f"  • {BOLD}Network (SSID) :{RESET} {GREEN}{BOLD}{data['ssid']}{RESET}")
    print(f"  • {BOLD}Signal Strength:{RESET} {CYAN}{BOLD}{data['rssi']}{RESET}  (Noise Floor: {data['noise']})")
    print(f"  • {BOLD}Channel & Band :{RESET} {MAGENTA}{data['channel']}{RESET}")
    print(f"  • {BOLD}Transmit Rate  :{RESET} {YELLOW}{data['tx_rate']}{RESET}")
    print(f"  • {BOLD}Security Type  :{RESET} {BLUE}{data['security']}{RESET}")
    print(f"  • {BOLD}Assigned IP    :{RESET} {GREEN}{data['ip']}{RESET} (Interface: {data['interface']})")
    print("═" * 65)

    if data["nearby"]:
        print(f"\n{BOLD}🔍 Nearby Local Wi-Fi Networks Detected:{RESET}")
        print(f"  {'SSID':<25} {'Signal (RSSI)':<15} {'Channel':<15} {'Security'}")
        print("  " + "─" * 63)
        for net in data["nearby"]:
            print(f"  {CYAN}{net['ssid']:<25}{RESET} {GREEN}{net['signal']:<15}{RESET} {MAGENTA}{net['channel']:<15}{RESET} {DIM}{net['security']}{RESET}")
        print("")


if __name__ == "__main__":
    main()
