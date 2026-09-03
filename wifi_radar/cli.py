"""Wi-Fi Radar - Local Wi-Fi SSID, RSSI dBm & Signal Quality Analyzer CLI."""

import argparse
import subprocess
import platform
import os
import re
import sys
from typing import Dict, Any

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"


def get_wifi_info() -> Dict[str, Any]:
    """Retrieve detailed Wi-Fi connection info across macOS, Linux, and Windows."""
    os_name = platform.system().lower()
    info = {
        "connected": False,
        "ssid": "Not connected",
        "bssid": "N/A",
        "rssi": "N/A",
        "channel": "N/A",
        "ip": "N/A",
        "interface": "N/A"
    }

    if os_name == "darwin":
        # 1. Get Wi-Fi interface (usually en0)
        try:
            hw_out = subprocess.check_output(["networksetup", "-listallhardwareports"], text=True, stderr=subprocess.DEVNULL)
            m = re.search(r"Hardware Port: (?:Wi-Fi|AirPort)\s+Device: (\w+)", hw_out)
            if m:
                info["interface"] = m.group(1)
            else:
                info["interface"] = "en0"
        except Exception:
            info["interface"] = "en0"

        # 2. Get IP on interface
        try:
            ip_out = subprocess.check_output(["ipconfig", "getifaddr", info["interface"]], text=True, stderr=subprocess.DEVNULL).strip()
            if ip_out:
                info["ip"] = ip_out
                info["connected"] = True
        except Exception:
            pass

        # 3. Get SSID via networksetup
        try:
            ssid_out = subprocess.check_output(["networksetup", "-getairportnetwork", info["interface"]], text=True, stderr=subprocess.DEVNULL).strip()
            if "Current Wi-Fi Network:" in ssid_out:
                info["ssid"] = ssid_out.split("Current Wi-Fi Network:")[1].strip()
                info["connected"] = True
            elif "not associated" in ssid_out:
                info["ssid"] = "Ethernet / Disconnected from Wi-Fi AP"
        except Exception:
            pass

        # 4. Try getting RSSI & Channel via airport utility silently without deprecation warnings
        airport_bin = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
        if os.path.exists(airport_bin):
            try:
                proc = subprocess.run([airport_bin, "-I"], capture_output=True, text=True)
                stdout = proc.stdout
                for line in stdout.splitlines():
                    line = line.strip()
                    if line.startswith("agrCtlRSSI:"):
                        info["rssi"] = f"{line.split(':')[1].strip()} dBm"
                    elif line.startswith("BSSID:"):
                        info["bssid"] = line.split(":", 1)[1].strip()
                    elif line.startswith("channel:"):
                        info["channel"] = line.split(":", 1)[1].strip()
            except Exception:
                pass

    elif os_name == "linux":
        # Linux nmcli or iwconfig
        info["interface"] = "wlan0"
        try:
            res = subprocess.check_output(["nmcli", "-t", "-f", "active,ssid,bssid,chan,signal", "dev", "wifi"], text=True, stderr=subprocess.DEVNULL)
            for line in res.splitlines():
                if line.startswith("yes:"):
                    parts = line.split(":")
                    info["connected"] = True
                    info["ssid"] = parts[1]
                    info["bssid"] = parts[2]
                    info["channel"] = parts[3]
                    info["rssi"] = f"{parts[4]}% quality"
                    break
        except Exception:
            pass

    return info


def main(args=None):
    parser = argparse.ArgumentParser(
        prog="wifi-radar",
        description="📡 Wi-Fi Radar - Local Wi-Fi SSID, RSSI dBm & Signal Quality Analyzer CLI"
    )
    parser.parse_args(args)

    data = get_wifi_info()

    print(f"\n{CYAN}{BOLD}📡 Wi-Fi Radar — Local Network & Wireless Telemetry{RESET}")
    print(f"{DIM}Host: {platform.node()} | Platform: {platform.system()} {platform.release()}{RESET}")
    print("═" * 60)
    print(f"  • {BOLD}Interface     :{RESET} {GREEN}{data['interface']}{RESET}")
    print(f"  • {BOLD}Network (SSID):{RESET} {CYAN}{BOLD}{data['ssid']}{RESET}")
    print(f"  • {BOLD}Local IP      :{RESET} {GREEN}{data['ip']}{RESET}")
    print(f"  • {BOLD}Signal (RSSI) :{RESET} {YELLOW}{data['rssi']}{RESET}")
    print(f"  • {BOLD}Channel / Band:{RESET} {MAGENTA}{data['channel']}{RESET}")
    print(f"  • {BOLD}Access Pt MAC :{RESET} {DIM}{data['bssid']}{RESET}")
    print("═" * 60 + "\n")


if __name__ == "__main__":
    main()
