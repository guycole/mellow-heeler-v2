#
# Title: parser.py
# Description: 
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#

from __future__ import annotations

import json
import re
from typing import Any

class Parser:

    def _parse_frequency_mhz(self, line: str) -> int | None:
        match = re.search(r"Frequency:([0-9.]+)\s*(GHz|MHz)", line)
        if not match:
            return None

        value = float(match.group(1))
        unit = match.group(2)
        if unit == "GHz":
            return int(round(value * 1000.0))
        return int(round(value))

    def _finalize_cell(self, cell: dict[str, Any]) -> dict[str, Any]:
        """Normalize internal parse state into the public cell schema.

        Public keys (only): bssid, frequency_mhz, signal_dbm, ssid,
        capabilities, cipher_type.
        """

        encryption_key = cell.pop("_encryption_key", None)
        rsn = cell.pop("_rsn", None)
        wpa = cell.pop("_wpa", None)

        capabilities: str
        cipher_type: str | None = None

        def _best_cipher(security: dict[str, Any]) -> str | None:
            pairwise = security.get("pairwise_ciphers") or []
            if pairwise:
                return str(pairwise[0])
            group_cipher = security.get("group_cipher")
            return str(group_cipher) if group_cipher else None

        if rsn is not None:
            # WPA2 (RSN)
            auth_suites = rsn.get("auth_suites") or []
            if "PSK" in auth_suites:
                capabilities = "wpa2-psk"
            elif "802.1X" in auth_suites:
                capabilities = "wpa2-8021x"
            else:
                capabilities = "wpa2"
            cipher_type = _best_cipher(rsn)
        elif wpa is not None:
            # WPA (older, less common)
            auth_suites = wpa.get("auth_suites") or []
            if "PSK" in auth_suites:
                capabilities = "wpa-psk"
            elif "802.1X" in auth_suites:
                capabilities = "wpa-8021x"
            else:
                capabilities = "wpa"
            cipher_type = _best_cipher(wpa)
        else:
            # Fallback based on Encryption key
            if encryption_key == "off":
                capabilities = "open"
            elif encryption_key == "on":
                capabilities = "encrypted"
            else:
                capabilities = "unknown"
            cipher_type = None

        cell["capabilities"] = capabilities
        cell["cipher_type"] = cipher_type
        return cell

    def parser(self, raw_buffer: list[str]) -> list[dict[str, Any]]:
        cells: list[dict[str, Any]] = []
        current: dict[str, Any] | None = None
        in_rsn = False
        in_wpa = False

        for raw_line in raw_buffer:
            line = raw_line.rstrip("\n")

            match = re.match(r"\s*Cell\s+\d+\s+-\s+Address:\s+([0-9A-Fa-f:]{17})", line)
            if match:
                if current is not None:
                    cells.append(self._finalize_cell(current))

                current = {
                    "bssid": match.group(1).upper(),
                    "frequency_mhz": None,
                    "signal_dbm": None,
                    "ssid": None,
                    "capabilities": None,
                    "cipher_type": None,
                    "_encryption_key": None,
                    "_rsn": None,
                    "_wpa": None,
                }
                in_rsn = False
                in_wpa = False
                continue

            if current is None:
                continue

            # Leaving an RSN/WPA stanza when a new IE starts.
            if (in_rsn or in_wpa) and re.match(r"\s*IE:", line):
                in_rsn = False
                in_wpa = False
                # fall through to process this IE line

            if "Encryption key:" in line:
                match = re.search(r"Encryption key:(on|off)", line)
                if match:
                    current["_encryption_key"] = match.group(1)
                continue

            if "Frequency:" in line:
                mhz = self._parse_frequency_mhz(line)
                if mhz is not None:
                    current["frequency_mhz"] = mhz
                continue

            if "Signal level=" in line:
                match = re.search(r"Signal level=\s*(-?\d+)\s*dBm", line)
                if match:
                    current["signal_dbm"] = int(match.group(1))
                continue

            if "ESSID:" in line:
                match = re.search(r'ESSID:"(.*)"', line)
                if match:
                    ssid = match.group(1)
                    if ssid == "off/any":
                        ssid = ""
                    current["ssid"] = ssid
                continue

            # Security: RSN (WPA2)
            if "IE: IEEE 802.11i/WPA2" in line:
                current["_rsn"] = {
                    "group_cipher": None,
                    "pairwise_ciphers": [],
                    "auth_suites": [],
                }
                in_rsn = True
                continue

            # Security: WPA (often printed as decoded by iwlist)
            if re.search(r"\bIE:\s*WPA\s+Version\s+1\b", line):
                current["_wpa"] = {
                    "group_cipher": None,
                    "pairwise_ciphers": [],
                    "auth_suites": [],
                }
                in_wpa = True
                continue

            if in_rsn and current.get("_rsn") is not None:
                rsn = current["_rsn"]
                match = re.search(r"Group Cipher\s*:\s*(\S+)", line)
                if match:
                    rsn["group_cipher"] = match.group(1)
                    continue

                match = re.search(r"Pairwise Ciphers.*:\s*(.+)$", line)
                if match:
                    ciphers = [c.strip() for c in match.group(1).split() if c.strip()]
                    rsn["pairwise_ciphers"].extend(ciphers)
                    rsn["pairwise_ciphers"] = list(dict.fromkeys(rsn["pairwise_ciphers"]))
                    continue

                match = re.search(r"Authentication Suites.*:\s*(.+)$", line)
                if match:
                    suites = [s.strip() for s in match.group(1).split() if s.strip()]
                    rsn["auth_suites"].extend(suites)
                    rsn["auth_suites"] = list(dict.fromkeys(rsn["auth_suites"]))
                    continue

            if in_wpa and current.get("_wpa") is not None:
                wpa = current["_wpa"]
                match = re.search(r"Group Cipher\s*:\s*(\S+)", line)
                if match:
                    wpa["group_cipher"] = match.group(1)
                    continue

                match = re.search(r"Pairwise Ciphers.*:\s*(.+)$", line)
                if match:
                    ciphers = [c.strip() for c in match.group(1).split() if c.strip()]
                    wpa["pairwise_ciphers"].extend(ciphers)
                    wpa["pairwise_ciphers"] = list(dict.fromkeys(wpa["pairwise_ciphers"]))
                    continue

                match = re.search(r"Authentication Suites.*:\s*(.+)$", line)
                if match:
                    suites = [s.strip() for s in match.group(1).split() if s.strip()]
                    wpa["auth_suites"].extend(suites)
                    wpa["auth_suites"] = list(dict.fromkeys(wpa["auth_suites"]))
                    continue

        if current is not None:
            cells.append(self._finalize_cell(current))

        return cells

    def file_reader(self, file_name: str) -> list[str]:
        raw_buffer = []

        try:
            with open(file_name, "r", encoding="utf-8") as in_file:
                raw_buffer = in_file.readlines()
        except Exception as error:
            print(error)

        return raw_buffer

    def execute(self, file_name: str) -> list[dict[str, Any]]:
        print(f"execute: {file_name}")
        raw_buffer = self.file_reader(file_name)
        if len(raw_buffer) < 3:
            print("execute: empty file")
            return []
        
        return self.parser(raw_buffer)

#
# argv[1] = configuration filename
#
if __name__ == "__main__":
    scan_file = "/Users/gsc/Documents/github/mellow-heeler-v2/samples/fef1594a-6360-4fe4-ad1e-dbdf942e3ebf"
    scan_file = "/Users/gsc/Documents/github/mellow-heeler-v2/samples/ff0ff19a-a5c0-4b26-91b2-ff4770c4414e"
    scan_file = "/Users/gsc/Documents/github/mellow-heeler-v2/samples/ff4678a8-939b-44f5-b899-e17ea40cbcaa"
    scan_file = "/Users/gsc/Documents/github/mellow-heeler-v2/samples/06d3289c-bae5-4841-a815-0edb13004c27"
    scan_file = "/Users/gsc/Documents/github/mellow-heeler-v2/samples/a019d33e-56b8-4acd-afce-6fcfb8b7d05d"

    parser = Parser()
    result = parser.execute(scan_file)
    print(json.dumps(result, indent=2))

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
