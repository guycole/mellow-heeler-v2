#
# Title: bootboy.py
# Description: generate configuration file
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#

import datetime
import json
import socket
import sys
import time
import uuid
import zoneinfo

from parser import Parser

import yaml
from yaml.loader import SafeLoader

class BootBoy:

    def configuration(self, target: str) -> None:
        print(f"BootBoy: configuring {target}")

        # Build the path to the admin JSON file
        admin_json_path = f"/var/wombat/admin/{target}.json"

        try:
            with open(admin_json_path, "r") as f:
                config_data = json.load(f)
        except Exception as e:
            print(f"Error reading {admin_json_path}: {e}")
            sys.exit(1)

        # Set required fields
        config_data["freshDir"] = "/var/wombat/fresh/heeler"
        config_data["gpsEnable"] = False
        config_data["scanFile"] = "/tmp/iwlist.scan"

        # Build equipment section
        receiver = config_data.get("receiver", {})
        equipment = {
            "antenna": receiver.get("antenna", "xxx"),
            "crate": config_data.get("crateName", "xxx"),
            "receiver": str(receiver.get("id", "xxx")),
            "platform": target,
            "type": receiver.get("type", config_data.get("type", "xxx")),
        }
        config_data["equipment"] = equipment

        # Write to config.yaml in the current directory
        try:
            with open("config.yaml", "w") as f:
                yaml.dump(config_data, f, default_flow_style=False)
            print("config.yaml generated successfully.")
        except Exception as e:
            print(f"Error writing config.yaml: {e}")
            sys.exit(1)

    def crontab(self) -> None:
        import subprocess
        crontab_entry = "*/10 * * * * /home/wombat/Documents/github/mellow-heeler-v2/bin/collector.sh > /dev/null 2>&1"

        try:
            # Always operate on the 'wombat' user's crontab
            result = subprocess.run(["crontab", "-u", "wombat", "-l"], capture_output=True, text=True)
            if result.returncode == 0:
                current_crontab = result.stdout.splitlines()
            else:
                current_crontab = []
        except Exception as e:
            print(f"Error reading wombat's crontab: {e}")
            return

        # Check if entry already exists
        if any(crontab_entry in line for line in current_crontab):
            print("Crontab entry already exists for wombat.")
            return

        # Add the new entry
        current_crontab.append(crontab_entry)
        new_crontab = "\n".join(current_crontab) + "\n"
        try:
            proc = subprocess.run(["crontab", "-u", "wombat", "-"], input=new_crontab, text=True)
            if proc.returncode == 0:
                print("Crontab updated successfully for wombat.")
            else:
                print("Failed to update wombat's crontab.")
        except Exception as e:
            print(f"Error updating wombat's crontab: {e}")


    def execute(self, target: str) -> None:
        self.configuration(target)
        self.crontab()

#
# 
#
if __name__ == "__main__":
    target = socket.gethostname()
    target = "pi3b"

    bb = BootBoy()
    bb.execute(target)

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
