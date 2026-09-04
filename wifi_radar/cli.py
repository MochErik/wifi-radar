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
RED = "\033[31m"


def signal_bar(rssi_str: str) -> str:
    """Format RSSI dBm value into visual signal strength bars."""
    try:
        val = int(re.search(r"-\d+", rssi_str).group(0))
        if val >= -50:
            return f"{GREEN}█████ (Excellent){RESET}"
        elif val >= -65:
            return f"{CYAN}████░ (Good){RESET}"
        elif val >= -75:
            return f"{YELLOW}███░░ (Fair){RESET}"
        else:
            return f"{RED}██░░░ (Weak){RESET}"
    except Exception:
        return ""


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
        "gateway": "N/A",
        "is_redacted": False,
        "nearby": []
    }

    if os_name == "darwin":
        # 1. Local IP & Gateway
        try:
            ip_out = subprocess.check_output(["ipconfig", "getifaddr", "en0"], text=True, stderr=subprocess.DEVNULL).strip()
            data["ip"] = ip_out if ip_out else "N/A"
            if data["ip"] != "N/A":
                data["connected"] = True
        except Exception:
            pass

        try:
            gw_out = subprocess.check_output(["route", "-n", "get", "default"], text=True, stderr=subprocess.DEVNULL)
            m_gw = re.search(r"gateway:\s*([^\n]+)", gw_out)
            if m_gw:
                data["gateway"] = m_gw.group(1).strip()
        except Exception:
            pass

        # 2. Extract deep native Wi-Fi data via system_profiler
        try:
            out = subprocess.check_output(["system_profiler", "SPAirPortDataType"], text=True, stderr=subprocess.DEVNULL)
            
            # Connected SSID
            m_ssid = re.search(r"Current Network Information:\s*\n\s*([^\n:]+):", out)
            if m_ssid:
                raw_ssid = m_ssid.group(1).strip()
                if raw_ssid == "<redacted>":
                    data["is_redacted"] = True
                    data["ssid"] = "Connected Wi-Fi AP (macOS Privacy Protected)"
                else:
                    data["ssid"] = raw_ssid

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
            raw_matches = re.findall(r"\s+PHY Mode:\s*([^\n]+)\n\s+Channel:\s*([^\n]+)\n\s+Network Type:[^\n]+\n\s+Security:\s*([^\n]+)\n\s+Signal / Noise:\s*([^\n]+)", out)
            for idx, (phy, n_chan, n_sec, n_sig) in enumerate(raw_matches, 1):
                sig_val = n_sig.split("/")[0].strip() if "/" in n_sig else n_sig.strip()
                # Friendly PHY label
                phy_label = phy.strip()
                if "ax" in phy_label:
                    gen = "Wi-Fi 6"
                elif "ac" in phy_label:
                    gen = "Wi-Fi 5"
                elif "n" in phy_label:
                    gen = "Wi-Fi 4"
                else:
                    gen = "Legacy"

                data["nearby"].append({
                    "name": f"Access Point #{idx} ({gen})",
                    "phy": phy_label,
                    "channel": n_chan.strip(),
                    "security": n_sec.strip(),
                    "signal": sig_val
                })
        except Exception:
            pass

    elif os_name == "linux":
        data["interface"] = "wlan0"
        try:
            res = subprocess.check_output(["nmcli", "-t", "-f", "active,ssid,bssid,chan,signal,security", "dev", "wifi"], text=True, stderr=subprocess.DEVNULL)
            for idx, line in enumerate(res.splitlines(), 1):
                parts = line.split(":")
                if line.startswith("yes:"):
                    data["connected"] = True
                    data["ssid"] = parts[1]
                    data["channel"] = parts[3]
                    data["rssi"] = f"{parts[4]}% quality"
                    data["security"] = parts[5] if len(parts) > 5 else "WPA2"
                elif len(parts) >= 6 and len(data["nearby"]) < 6:
                    data["nearby"].append({
                        "name": parts[1] or f"Hidden Network #{idx}",
                        "phy": "802.11",
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
    parser.parse_args(args)

    data = get_wifi_telemetry()

    print(f"\n{CYAN}{BOLD}📡 Wi-Fi Radar — Local Wireless Telemetry & Signal Analyzer{RESET}")
    print(f"{DIM}Host: {platform.node()} | OS: {platform.system()} {platform.release()}{RESET}")
    print("═" * 70)
    print(f"  • {BOLD}Network (SSID) :{RESET} {GREEN}{BOLD}{data['ssid']}{RESET}")
    print(f"  • {BOLD}Signal Strength:{RESET} {CYAN}{BOLD}{data['rssi']}{RESET}  {signal_bar(data['rssi'])} (Noise: {data['noise']})")
    print(f"  • {BOLD}Channel & Band :{RESET} {MAGENTA}{data['channel']}{RESET}")
    print(f"  • {BOLD}Transmit Rate  :{RESET} {YELLOW}{data['tx_rate']}{RESET}")
    print(f"  • {BOLD}Security Type  :{RESET} {BLUE}{data['security']}{RESET}")
    print(f"  • {BOLD}Assigned IP    :{RESET} {GREEN}{data['ip']}{RESET} (Gateway: {data['gateway']})")
    print("═" * 70)

    if data["nearby"]:
        print(f"\n{BOLD}🔍 Nearby Wireless Access Points Detected ({len(data['nearby'])} APs in range):{RESET}")
        print(f"  {'Access Point / Standard':<28} {'Signal (RSSI)':<15} {'Channel / Band':<20} {'Security'}")
        print("  " + "─" * 72)
        for net in data["nearby"][:6]:
            print(f"  {CYAN}{net['name']:<28}{RESET} {GREEN}{net['signal']:<15}{RESET} {MAGENTA}{net['channel']:<20}{RESET} {DIM}{net['security']}{RESET}")
        print("")

    if data["is_redacted"]:
        print(f"{DIM}ℹ️  Catatan Privasi macOS: Nama SSID tetangga dimask (<redacted>) oleh Apple untuk perlindungan GPS Location Privacy.{RESET}")
        print(f"{DIM}   Seluruh data RSSI dBm, Channel frekuensi, dan PHY Modes di atas adalah telemetri hardware 100% real-time.{RESET}\n")


if __name__ == "__main__":
    main()
