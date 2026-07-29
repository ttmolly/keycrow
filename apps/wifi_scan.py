import subprocess

def scan_networks():
    try:
        result = subprocess.check_output(
            ["nmcli", "-t", "-f", "SSID,SIGNAL", "dev", "wifi", "list"],
            stderr=subprocess.DEVNULL
        ).decode()

        networks = []
        for line in result.strip().split("\n"):
            if line:
                parts = line.split(":")
                ssid = parts[0]
                if ssid:
                    networks.append(ssid)

        return networks[:10] if networks else ["No networks found"]
    except Exception:
        return ["Scan failed"]
